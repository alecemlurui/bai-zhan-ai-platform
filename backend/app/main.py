"""
main.py

FastAPI 应用入口。
集成 Tortoise ORM、Sentry 错误追踪与 Prometheus 指标暴露。
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles

from .config import SETTINGS, TORTOISE_ORM
from .router import api_router


def _init_sentry() -> None:
    if not SETTINGS.SENTRY_DSN:
        return
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.starlette import StarletteIntegration
    except ImportError:
        return

    sentry_sdk.init(
        dsn=SETTINGS.SENTRY_DSN,
        environment=SETTINGS.ENVIRONMENT,
        integrations=[
            StarletteIntegration(),
            FastApiIntegration(),
        ],
        traces_sample_rate=0.1,
    )


def _make_prometheus_middleware():
    try:
        from prometheus_client import Counter, Histogram
    except ImportError:
        return None, None

    request_count = Counter(
        "http_requests_total",
        "Total HTTP requests",
        ["method", "endpoint", "status_code"],
    )
    request_latency = Histogram(
        "http_request_duration_seconds",
        "HTTP request latency",
        ["method", "endpoint"],
    )
    return request_count, request_latency


@asynccontextmanager
async def lifespan(app: FastAPI):
    from tortoise import Tortoise

    _init_sentry()
    await Tortoise.init(config=TORTOISE_ORM)
    await Tortoise.generate_schemas()
    yield
    await Tortoise.close_connections()


def create_app() -> FastAPI:
    app = FastAPI(
        title=SETTINGS.APP_NAME,
        version=SETTINGS.APP_VERSION,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    request_count, request_latency = _make_prometheus_middleware()
    if request_count and request_latency:

        @app.middleware("http")
        async def prometheus_middleware(request: Request, call_next):
            from time import time

            start = time()
            response = await call_next(request)
            duration = time() - start
            route = request.url.path
            status = str(response.status_code)
            request_count.labels(
                method=request.method, endpoint=route, status_code=status
            ).inc()
            request_latency.labels(method=request.method, endpoint=route).observe(
                duration
            )
            return response

    @app.get("/metrics", tags=["monitoring"])
    async def metrics():
        try:
            from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
        except ImportError:
            return PlainTextResponse("prometheus-client not installed", status_code=503)
        return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    app.include_router(api_router, prefix="")

    # 静态文件（上传的图片）
    from .services.media import UPLOAD_DIR

    UPLOAD_DIR.mkdir(exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

    return app


app = create_app()
