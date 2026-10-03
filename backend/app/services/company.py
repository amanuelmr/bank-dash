"""Company CRUD and trending listings."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError, NotFoundError
from app.models.company import Company
from app.models.user import User
from app.schemas.common import Page
from app.schemas.company import (
    CompanyOut,
    CreateCompanyRequest,
    UpdateCompanyRequest,
)


async def list_companies(db: AsyncSession, *, page: int, size: int) -> Page[CompanyOut]:
    total = int(await db.scalar(select(func.count()).select_from(Company)) or 0)
    rows = (
        await db.scalars(
            select(Company)
            .order_by(Company.name.asc())
            .offset(page * size)
            .limit(size)
        )
    ).all()
    return Page[CompanyOut].build(
        items=[CompanyOut.model_validate(c) for c in rows], total=total, page=page, size=size
    )


async def trending_companies(db: AsyncSession, limit: int = 6) -> list[CompanyOut]:
    rows = (
        await db.scalars(
            select(Company)
            .where(Company.is_trending.is_(True))
            .order_by(Company.change_percent.desc())
            .limit(limit)
        )
    ).all()
    return [CompanyOut.model_validate(c) for c in rows]


async def get_company(db: AsyncSession, company_id: str) -> CompanyOut:
    company = await db.get(Company, company_id)
    if company is None:
        raise NotFoundError("Company not found")
    return CompanyOut.model_validate(company)


async def create_company(
    db: AsyncSession, actor: User, payload: CreateCompanyRequest
) -> CompanyOut:
    if await db.scalar(select(Company).where(Company.name == payload.name)):
        raise ConflictError("A company with that name already exists")
    company = Company(**payload.model_dump())
    db.add(company)
    await db.commit()
    await db.refresh(company)
    return CompanyOut.model_validate(company)


async def update_company(
    db: AsyncSession, company_id: str, payload: UpdateCompanyRequest
) -> CompanyOut:
    company = await db.get(Company, company_id)
    if company is None:
        raise NotFoundError("Company not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(company, field, value)
    await db.commit()
    await db.refresh(company)
    return CompanyOut.model_validate(company)


async def delete_company(db: AsyncSession, company_id: str) -> None:
    company = await db.get(Company, company_id)
    if company is None:
        raise NotFoundError("Company not found")
    await db.delete(company)
    await db.commit()