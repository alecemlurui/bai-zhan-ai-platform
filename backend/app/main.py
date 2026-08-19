"""
main.py

FastAPI 应用入口。
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import SETTINGS, TORTOISE_ORM
from .router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    from tortoise import Tortoise

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

    app.include_router(api_router, prefix="")

    # 静态文件（上传的图片）
    from .services.media import UPLOAD_DIR

    UPLOAD_DIR.mkdir(exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

    return app


app = create_app()
