"""Company routes."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.deps import Pagination, get_current_admin, get_current_user, get_pagination
from app.models.user import User
from app.schemas.common import ApiResponse, Page
from app.schemas.company import (
    CompanyOut,
    CreateCompanyRequest,
    UpdateCompanyRequest,
)
from app.services import company as company_service

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("", response_model=ApiResponse[Page[CompanyOut]], summary="List companies")
async def list_companies(
    pagination: Pagination = Depends(get_pagination),
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[Page[CompanyOut]]:
    page = await company_service.list_companies(
        db, page=pagination.page, size=pagination.size
    )
    return ApiResponse(data=page)


@router.get("/trending", response_model=ApiResponse[list[CompanyOut]], summary="Trending stocks")
async def trending(
    limit: int = Query(6, ge=1, le=50),
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[list[CompanyOut]]:
    return ApiResponse(data=await company_service.trending_companies(db, limit))


@router.post(
    "",
    response_model=ApiResponse[CompanyOut],
    status_code=status.HTTP_201_CREATED,
    summary="Create a company (admin)",
)
async def create_company(
    payload: CreateCompanyRequest,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[CompanyOut]:
    created = await company_service.create_company(db, admin, payload)
    return ApiResponse(message="Company created", data=created)


@router.get("/{company_id}", response_model=ApiResponse[CompanyOut], summary="One company")
async def get_company(
    company_id: str,
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[CompanyOut]:
    return ApiResponse(data=await company_service.get_company(db, company_id))


@router.put("/{company_id}", response_model=ApiResponse[CompanyOut], summary="Update (admin)")
async def update_company(
    company_id: str,
    payload: UpdateCompanyRequest,
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[CompanyOut]:
    updated = await company_service.update_company(db, company_id, payload)
    return ApiResponse(message="Company updated", data=updated)


@router.delete("/{company_id}", response_model=ApiResponse[None], summary="Delete (admin)")
async def delete_company(
    company_id: str,
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[None]:
    await company_service.delete_company(db, company_id)
    return ApiResponse(message="Company deleted", data=None)