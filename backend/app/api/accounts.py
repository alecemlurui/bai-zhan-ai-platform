"""
api/accounts.py

第三方平台账号管理 API。
"""

from fastapi import APIRouter, Depends, HTTPException

from ..dependencies import get_current_active_user
from ..models import PlatformAccount, User
from ..schemas import (
    PlatformAccountCreateRequest,
    PlatformAccountResponse,
)

router = APIRouter(prefix="/api/v1/accounts", tags=["accounts"])


@router.post("", response_model=PlatformAccountResponse)
async def create(
    payload: PlatformAccountCreateRequest,
    current_user: User = Depends(get_current_active_user),
):
    account = await PlatformAccount.create(
        owner=current_user,
        platform=payload.platform,
        account_name=payload.account_name,
        credentials=payload.credentials,
    )
    return account


@router.get("", response_model=list[PlatformAccountResponse])
async def list_all(
    platform: str | None = None,
    current_user: User = Depends(get_current_active_user),
):
    query = PlatformAccount.filter(owner=current_user, is_active=True)
    if platform:
        query = query.filter(platform=platform)
    return await query.order_by("-created_at").all()


@router.get("/{account_id}", response_model=PlatformAccountResponse)
async def detail(
    account_id: int,
    current_user: User = Depends(get_current_active_user),
):
    try:
        return await PlatformAccount.get(owner=current_user, id=account_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Account not found")


@router.delete("/{account_id}")
async def delete(
    account_id: int,
    current_user: User = Depends(get_current_active_user),
):
    try:
        account = await PlatformAccount.get(owner=current_user, id=account_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Account not found")
    account.is_active = False
    await account.save(update_fields=["is_active"])
    return {"message": "Deactivated"}
