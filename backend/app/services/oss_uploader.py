"""
services/oss_uploader.py

对象存储上传抽象：本地回退 / 阿里云 OSS。
"""

from __future__ import annotations

import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any
from uuid import uuid4

from ..config import BASE_DIR, SETTINGS


class UploadError(Exception):
    """上传异常。"""


class BaseUploader(ABC):
    @abstractmethod
    async def upload(
        self, file_path: Path, object_key: str | None = None
    ) -> dict[str, Any]:
        """上传文件并返回 {url, object_key, provider}。"""
        raise NotImplementedError


class LocalUploader(BaseUploader):
    """本地文件系统上传（无 OSS Key 时回退）。"""

    def __init__(self, upload_dir: str | Path | None = None):
        self.upload_dir = Path(upload_dir or BASE_DIR / "uploads")
        self.upload_dir.mkdir(exist_ok=True)

    async def upload(
        self, file_path: Path, object_key: str | None = None
    ) -> dict[str, Any]:
        if not file_path.exists():
            raise UploadError(f"File not found: {file_path}")

        key = object_key or f"{uuid4().hex}{file_path.suffix}"
        dest = self.upload_dir / key
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file_path, dest)

        return {
            "url": f"/uploads/{key}",
            "object_key": key,
            "provider": "local",
            "file_path": str(dest),
        }


class OssUploader(BaseUploader):
    """阿里云 OSS 上传器。"""

    def __init__(self):
        self.endpoint = SETTINGS.OSS_ENDPOINT
        self.access_key_id = SETTINGS.OSS_ACCESS_KEY_ID
        self.access_key_secret = SETTINGS.OSS_ACCESS_KEY_SECRET
        self.bucket_name = SETTINGS.OSS_BUCKET

    async def upload(
        self, file_path: Path, object_key: str | None = None
    ) -> dict[str, Any]:
        if not self.bucket_name or not self.access_key_id or not self.access_key_secret:
            raise UploadError("OSS credentials not configured")

        try:
            import oss2
        except ImportError as exc:
            raise UploadError("oss2 package is required for OSS upload") from exc

        key = object_key or f"{uuid4().hex}{file_path.suffix}"
        auth = oss2.Auth(self.access_key_id, self.access_key_secret)
        bucket = oss2.Bucket(auth, self.endpoint, self.bucket_name)
        bucket.put_object_from_file(key, str(file_path))

        # 生成可访问 URL（假设 bucket 为公共读；如需私有，应使用签名 URL）
        url = (
            f"https://{self.bucket_name}.{self.endpoint.replace('https://', '')}/{key}"
        )
        return {
            "url": url,
            "object_key": key,
            "provider": "oss",
            "file_path": str(file_path),
        }


def get_uploader() -> BaseUploader:
    """根据配置选择上传器。"""
    if SETTINGS.UPLOADER_MODE.lower() == "oss":
        return OssUploader()
    return LocalUploader()
