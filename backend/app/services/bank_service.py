"""Bank service catalogue CRUD and search."""

from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.models.bank_service import BankService
from app.models.user import User
from app.schemas.bank_service import (
    BankServiceOut,
    CreateBankServiceRequest,
    UpdateBankServiceRequest,
)
from app.schemas.common import Page


async def list_services(
    db: AsyncSession,
    *,
    page: int,
    size: int,
    search: str | None = None,
    type_: str | None = None,
    status: str | None = None,
) -> Page[BankServiceOut]:
    filters = []
    if search:
        pattern = f"%{search.strip().lower()}%"
        filters.append(
            or_(
                func.lower(BankService.name).like(pattern),
                func.lower(BankService.details).like(pattern),
            )
        )
    if type_:
        filters.append(BankService.type == type_)
    if status:
        filters.append(BankService.status == status)

    total = int(
        await db.scalar(select(func.count()).select_from(BankService).where(*filters)) or 0
    )
    rows = (
        await db.scalars(
            select(BankService)
            .where(*filters)
            .order_by(BankService.name.asc())
            .offset(page * size)
            .limit(size)
        )
    ).all()
    return Page[BankServiceOut].build(
        items=[BankServiceOut.model_validate(s) for s in rows],
        total=total,
        page=page,
        size=size,
    )


async def search_services(db: AsyncSession, query: str, limit: int = 20) -> list[BankServiceOut]:
    pattern = f"%{query.strip().lower()}%"
    rows = (
        await db.scalars(
            select(BankService)
            .where(
                or_(
                    func.lower(BankService.name).like(pattern),
                    func.lower(BankService.details).like(pattern),
                    func.lower(BankService.type).like(pattern),
                )
            )
            .order_by(BankService.name.asc())
            .limit(limit)
        )
    ).all()
    return [BankServiceOut.model_validate(s) for s in rows]


async def get_service(db: AsyncSession, service_id: str) -> BankServiceOut:
    service = await db.get(BankService, service_id)
    if service is None:
        raise NotFoundError("Bank service not found")
    return BankServiceOut.model_validate(service)


async def create_service(
    db: AsyncSession, actor: User, payload: CreateBankServiceRequest
) -> BankServiceOut:
    service = BankService(**payload.model_dump())
    db.add(service)
    await db.commit()
    await db.refresh(service)
    return BankServiceOut.model_validate(service)


async def update_service(
    db: AsyncSession, service_id: str, payload: UpdateBankServiceRequest
) -> BankServiceOut:
    service = await db.get(BankService, service_id)
    if service is None:
        raise NotFoundError("Bank service not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(service, field, value)
    await db.commit()
    await db.refresh(service)
    return BankServiceOut.model_validate(service)


async def delete_service(db: AsyncSession, service_id: str) -> None:
    service = await db.get(BankService, service_id)
    if service is None:
        raise NotFoundError("Bank service not found")
    await db.delete(service)
    await db.commit()