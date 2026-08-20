"""
services/image_generator.py

图片生成抽象。默认提供 Mock 实现（本地 PIL 绘制），并预留远程 API 调用接口。
"""

from __future__ import annotations

import io
import random
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from ..config import SETTINGS


class ImageGenerationError(Exception):
    """图片生成异常。"""


class BaseImageGenerator(ABC):
    @abstractmethod
    async def generate(self, prompt: str, width: int = 512, height: int = 512) -> bytes:
        """返回图片二进制数据（JPEG/PNG）。"""
        raise NotImplementedError


class MockImageGenerator(BaseImageGenerator):
    """Mock 图片生成器：使用 Pillow 绘制纯色+文字占位图。"""

    def __init__(self, watermark: str = "Mock AI Image"):
        self.watermark = watermark

    async def generate(self, prompt: str, width: int = 512, height: int = 512) -> bytes:
        try:
            from PIL import Image, ImageDraw, ImageFont
        except ImportError as exc:
            raise ImageGenerationError(
                "Pillow is required for mock image generation"
            ) from exc

        img = Image.new("RGB", (width, height), color=self._random_color())
        draw = ImageDraw.Draw(img)

        # 尝试加载默认字体，失败则使用默认内置字体
        font: Any
        try:
            font = ImageFont.truetype("arial.ttf", 24)
        except Exception:
            font = ImageFont.load_default()

        lines = [
            self.watermark,
            f"Prompt: {prompt[:60]}",
            f"Size: {width}x{height}",
        ]
        y = height // 4
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            text_w = bbox[2] - bbox[0]
            x = max(0, (width - text_w) // 2)
            draw.text((x, y), line, fill=(255, 255, 255), font=font)
            y += 40

        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85)
        buf.seek(0)
        return buf.getvalue()

    @staticmethod
    def _random_color() -> tuple[int, int, int]:
        return (
            random.randint(40, 180),
            random.randint(40, 180),
            random.randint(40, 180),
        )


class RemoteImageGenerator(BaseImageGenerator):
    """远程图片生成 API 调用器。配置 IMAGE_API_URL / IMAGE_API_KEY 使用。"""

    def __init__(
        self,
        api_url: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
    ):
        self.api_url = (api_url or SETTINGS.IMAGE_API_URL).rstrip("/")
        self.api_key = api_key or SETTINGS.IMAGE_API_KEY
        self.model = model or SETTINGS.IMAGE_MODEL
        self.timeout = SETTINGS.IMAGE_TIMEOUT

    async def generate(self, prompt: str, width: int = 512, height: int = 512) -> bytes:
        import httpx

        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {
            "model": self.model,
            "prompt": prompt,
            "width": width,
            "height": height,
            "n": 1,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(self.api_url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        # 兼容常见格式：{ "data": [{ "url": "..." }] } 或 { "images": ["base64..."] }
        image_url = data.get("data", [{}])[0].get("url") if "data" in data else None
        image_b64 = data.get("images", [None])[0] if "images" in data else None

        if image_url:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                img_resp = await client.get(image_url)
                img_resp.raise_for_status()
                return img_resp.content
        if image_b64:
            import base64

            return base64.b64decode(image_b64)

        raise ImageGenerationError(
            f"Unsupported remote image response format: {data.keys()}"
        )


class LocalSdImageGenerator(BaseImageGenerator):
    """本地 Stable Diffusion WebUI / ComfyUI 接口调用器。"""

    def __init__(self, api_url: str | None = None):
        self.api_url = (api_url or SETTINGS.IMAGE_API_URL).rstrip("/")
        self.timeout = SETTINGS.IMAGE_TIMEOUT

    async def generate(self, prompt: str, width: int = 512, height: int = 512) -> bytes:
        import httpx

        payload = {
            "prompt": prompt,
            "width": width,
            "height": height,
            "steps": 20,
            "batch_size": 1,
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(f"{self.api_url}/sdapi/v1/txt2img", json=payload)
            resp.raise_for_status()
            data = resp.json()

        import base64

        b64_image = data.get("images", [None])[0]
        if not b64_image:
            raise ImageGenerationError("No image returned from local SD")
        return base64.b64decode(b64_image)


def get_image_generator() -> BaseImageGenerator:
    mode = SETTINGS.IMAGE_GENERATOR_MODE.lower()
    if mode == "mock":
        return MockImageGenerator()
    if mode == "remote":
        return RemoteImageGenerator()
    if mode in ("sd", "stable_diffusion"):
        return LocalSdImageGenerator()
    raise ImageGenerationError(f"Unknown image generator mode: {mode}")


def save_image_bytes(data: bytes, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
