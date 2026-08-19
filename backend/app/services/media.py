"""
services/media.py

媒体处理：本地保存、尺寸读取、预留 OSS 上传。
"""

import shutil
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import UploadFile
from PIL import Image

from ..config import SETTINGS, BASE_DIR

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

    width, height = None, None
    size_bytes = file_path.stat().st_size
    try:
        with Image.open(file_path) as img:
            width, height = img.size
    except Exception:
        pass

    return {
        "url": f"/uploads/{filename}",
        "file_path": str(file_path),
        "type": "image",
        "width": width,
        "height": height,
        "size_bytes": size_bytes,
    }


async def upload_to_oss(file_path: Path, object_key: str) -> str:
    """
    预留：上传文件到阿里云 OSS。
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
