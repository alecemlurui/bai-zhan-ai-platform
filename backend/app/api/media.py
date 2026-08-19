"""
api/media.py

媒体上传 API。
"""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from ..dependencies import get_current_active_user
from ..models import Media, User
from ..services.media import save_upload_file

router = APIRouter(prefix="/api/v1/media", tags=["media"])


@router.post("/upload")
async def upload(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
):
    try:
        result = await save_upload_file(file, current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    media = await Media.create(
        owner=current_user,
        url=result["url"],
        type=result["type"],
        width=result["width"],
        height=result["height"],
        size_bytes=result["size_bytes"],
    )
    return {
        "id": media.id,
        "url": media.url,
        "type": media.type,
        "width": media.width,
        "height": media.height,
    }
