"""
services/media.py

媒体处理：上传文件保存、图片生成、OSS/本地上传。
"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import UploadFile
from PIL import Image

from ..config import BASE_DIR, SETTINGS
from .image_generator import ImageGenerationError, get_image_generator
from .oss_uploader import UploadError, get_uploader

UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)


async def save_upload_file(file: UploadFile, owner_id: int) -> dict[str, Any]:
    """保存上传文件到本地，并返回 URL 与元数据。"""
    ext = Path(file.filename or "unknown").suffix.lower()
    if ext not in (".jpg", ".jpeg", ".png", ".gif", ".webp"):
        raise ValueError(f"Unsupported file type: {ext}")

    filename = f"{uuid4().hex}{ext}"
    file_path = UPLOAD_DIR / filename

    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return _extract_image_meta(file_path)


async def generate_image(
    prompt: str,
    width: int = 512,
    height: int = 512,
    object_key: str | None = None,
) -> dict[str, Any]:
    """生成图片并上传到存储，返回 URL 与元数据。"""
    generator = get_image_generator()
    uploader = get_uploader()

    try:
        image_bytes = await generator.generate(prompt, width=width, height=height)
    except ImageGenerationError:
        raise
    except Exception as exc:
        raise ImageGenerationError(f"Image generation failed: {exc}") from exc

    suffix = ".jpg"
    filename = f"{uuid4().hex}{suffix}"
    tmp_path = Path(tempfile.gettempdir()) / f"bai_zhan_gen_{filename}"
    tmp_path.write_bytes(image_bytes)

    try:
        upload_result = await uploader.upload(tmp_path, object_key=object_key)
    except UploadError:
        # 上传失败时回退到本地保存
        upload_result = await _fallback_local_upload(tmp_path, object_key)

    meta = _extract_image_meta(Path(upload_result["file_path"]))
    meta.update(upload_result)
    return meta


async def _fallback_local_upload(
    file_path: Path, object_key: str | None = None
) -> dict[str, Any]:
    from .oss_uploader import LocalUploader

    uploader = LocalUploader()
    return await uploader.upload(file_path, object_key=object_key)


def _extract_image_meta(file_path: Path) -> dict[str, Any]:
    width, height = None, None
    size_bytes = file_path.stat().st_size
    try:
        with Image.open(file_path) as img:
            width, height = img.size
    except Exception:
        pass

    url_path = f"/uploads/{file_path.name}"
    if str(file_path).startswith(str(UPLOAD_DIR)):
        url_path = f"/uploads/{file_path.relative_to(UPLOAD_DIR).as_posix()}"

    return {
        "url": url_path,
        "file_path": str(file_path),
        "type": "image",
        "width": width,
        "height": height,
        "size_bytes": size_bytes,
    }


async def upload_to_oss(file_path: Path, object_key: str) -> str:
    """
    兼容旧接口：上传文件到阿里云 OSS。
    未配置 OSS 时抛出 NotImplementedError。
    """
    if not SETTINGS.OSS_BUCKET:
        raise NotImplementedError("OSS not configured")

    try:
        import oss2
    except ImportError as exc:
        raise ImportError("oss2 not installed") from exc

    auth = oss2.Auth(SETTINGS.OSS_ACCESS_KEY_ID, SETTINGS.OSS_ACCESS_KEY_SECRET)
    bucket = oss2.Bucket(auth, SETTINGS.OSS_ENDPOINT, SETTINGS.OSS_BUCKET)
    bucket.put_object_from_file(object_key, str(file_path))
    return f"{SETTINGS.OSS_ENDPOINT}/{SETTINGS.OSS_BUCKET}/{object_key}"
