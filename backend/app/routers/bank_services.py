"""Bank service catalogue routes."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.deps import Pagination, get_current_admin, get_current_user, get_pagination
from app.models.user import User
from app.schemas.bank_service import (
    BankServiceOut,
    CreateBankServiceRequest,
    UpdateBankServiceRequest,
)
from app.schemas.common import ApiResponse, Page
from app.services import bank_service as service

router = APIRouter(prefix="/bank-services", tags=["bank services"])


@router.get("", response_model=ApiResponse[Page[BankServiceOut]], summary="List services")
async def list_services(
    pagination: Pagination = Depends(get_pagination),
    search: str | None = Query(None, description="Match against name and details"),
    type: str | None = Query(None),
    status: str | None = Query(None),
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[Page[BankServiceOut]]:
    page = await service.list_services(
        db,
        page=pagination.page,
        size=pagination.size,
        search=search,
        type_=type,
        status=status,
    )
    return ApiResponse(data=page)


@router.get("/search", response_model=ApiResponse[list[BankServiceOut]], summary="Search services")
async def search_services(
    q: str = Query(min_length=1, description="Search term"),
    limit: int = Query(20, ge=1, le=100),
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[list[BankServiceOut]]:
    return ApiResponse(data=await service.search_services(db, q, limit))


@router.post(
    "",
    response_model=ApiResponse[BankServiceOut],
    status_code=status.HTTP_201_CREATED,
    summary="Create a service (admin)",
)
async def create_service(
    payload: CreateBankServiceRequest,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[BankServiceOut]:
    created = await service.create_service(db, admin, payload)
    return ApiResponse(message="Service created", data=created)


@router.get("/{service_id}", response_model=ApiResponse[BankServiceOut], summary="One service")
async def get_service(
    service_id: str,
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[BankServiceOut]:
    return ApiResponse(data=await service.get_service(db, service_id))


@router.put(
    "/{service_id}", response_model=ApiResponse[BankServiceOut], summary="Update (admin)"
)
async def update_service(
    service_id: str,
    payload: UpdateBankServiceRequest,
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[BankServiceOut]:
    updated = await service.update_service(db, service_id, payload)
    return ApiResponse(message="Service updated", data=updated)


@router.delete("/{service_id}", response_model=ApiResponse[None], summary="Delete (admin)")
async def delete_service(
    service_id: str,
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[None]:
    await service.delete_service(db, service_id)
    return ApiResponse(message="Service deleted", data=None)