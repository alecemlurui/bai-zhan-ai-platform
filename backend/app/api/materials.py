"""
api/materials.py

素材库 API。
"""

from fastapi import APIRouter, Depends, HTTPException

from ..dependencies import get_current_active_user
from ..models import Material, User
from ..schemas import MaterialCreateRequest, MaterialResponse

router = APIRouter(prefix="/api/v1/materials", tags=["materials"])


@router.post("", response_model=MaterialResponse)
async def create(
    payload: MaterialCreateRequest,
    current_user: User = Depends(get_current_active_user),
):
    material = await Material.create(
        owner=current_user,
        type=payload.type,
        content=payload.content,
        url=payload.url,
        tags=payload.tags or [],
    )
    return material


@router.get("", response_model=list[MaterialResponse])
async def list_all(
    type: str | None = None,
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_active_user),
):
    query = Material.filter(owner=current_user)
    if type:
        query = query.filter(type=type)
    return await query.order_by("-created_at").offset(offset).limit(limit).all()


@router.get("/{material_id}", response_model=MaterialResponse)
async def detail(
    material_id: int,
    current_user: User = Depends(get_current_active_user),
):
    try:
        return await Material.get(owner=current_user, id=material_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Material not found")


@router.delete("/{material_id}")
async def delete(
    material_id: int,
    current_user: User = Depends(get_current_active_user),
):
    try:
        material = await Material.get(owner=current_user, id=material_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Material not found")
    await material.delete()
    return {"message": "Deleted"}
