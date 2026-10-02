"""Transaction ledger: transfers, deposits, queries, and derived series."""

from __future__ import annotations

import secrets

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import BusinessRuleError, NotFoundError
from app.models.base import utcnow, uuid_pk
from app.models.transaction import (
    Transaction,
    TransactionDirection,
    TransactionStatus,
    TransactionType,
)
from app.models.user import User
from app.schemas.common import Page
from app.schemas.transaction import (
    CreateTransactionRequest,
    DepositRequest,
    TransactionOut,
    TransferRecipientOut,
)
from app.schemas.user import SeriesPoint
from app.services.user import build_balance_series

#: Counterparty recorded for movements that have no human recipient (deposits
#: from outside the bank, card purchases, service payments).
SYSTEM_USERNAME = "BankDash"

CATEGORY_BY_TYPE: dict[TransactionType, str] = {
    TransactionType.TRANSFER: "transfer",
    TransactionType.SHOPPING: "shopping",
    TransactionType.SERVICE: "service",
    TransactionType.DEPOSIT: "income",
    TransactionType.LOAN_REPAYMENT: "loan",
}

_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # no ambiguous 0/O/1/I


def new_transaction_id() -> str:
    return "TXN-" + "".join(secrets.choice(_ALPHABET) for _ in range(8))


def round_money(value: float) -> float:
    return round(value + 0.0, 2)


async def lock_users_for_update(db: AsyncSession, user_ids: list[str]) -> dict[str, User]:
    """Lock the given users for update and return them keyed by id.

    Rows are selected in a single statement ordered by id so every concurrent
    transfer acquires the same rows in the same order. Locking accounts one
    request at a time would deadlock on simultaneous A->B and B->A transfers.
    ``FOR UPDATE`` is only applied on Postgres; SQLite serialises writes itself.
    """
    ids = sorted(set(user_ids))
    stmt = select(User).where(User.id.in_(ids)).order_by(User.id)
    if db.get_bind().dialect.name == "postgresql":
        stmt = stmt.with_for_update()

    rows = (await db.scalars(stmt)).all()
    locked = {user.id: user for user in rows}
    if not locked:
        raise NotFoundError("User not found")
    return locked


async def _load_user_for_update(db: AsyncSession, user_id: str) -> User:
    return (await lock_users_for_update(db, [user_id]))[user_id]


async def create_transfer(
    db: AsyncSession, sender: User, payload: CreateTransactionRequest
) -> Transaction:
    """Record a payment and move the balance.

    Writes two ledger rows (the sender's ``OUT`` and the receiver's ``IN``) so
    each party sees the movement with the correct sign on their own statement.
    """
    if payload.amount <= 0:
        raise BusinessRuleError("Amount must be greater than zero")

    if payload.type is TransactionType.DEPOSIT:
        return await create_deposit(db, sender, DepositRequest(amount=payload.amount))

    is_internal = payload.type is TransactionType.TRANSFER
    receiver_username = (payload.receiver_username or "").strip().lower()

    if is_internal and not receiver_username:
        raise BusinessRuleError("receiverUsername is required for transfer type")
    if not is_internal:
        receiver_username = receiver_username or SYSTEM_USERNAME

    receiver: User | None = None
    if is_internal:
        receiver = await db.scalar(select(User).where(User.username == receiver_username))
        if receiver is None:
            raise NotFoundError(f"No user named '{receiver_username}'")
        if receiver.id == sender.id:
            raise BusinessRuleError("You cannot transfer money to yourself")

    # Lock sender and receiver together, in a consistent order.
    locked = await lock_users_for_update(
        db, [sender.id] + ([receiver.id] if receiver is not None else [])
    )
    locked_sender = locked[sender.id]
    amount = round_money(payload.amount)
    if locked_sender.account_balance < amount:
        raise BusinessRuleError(
            "Insufficient funds",
            code="insufficient_funds",
        )

    locked_sender.account_balance = round_money(locked_sender.account_balance - amount)
    if receiver is not None:
        locked_receiver = locked[receiver.id]
        locked_receiver.account_balance = round_money(locked_receiver.account_balance + amount)

    group_id = uuid_pk()
    occurred_at = utcnow()
    description = payload.resolved_description(locked_sender.username, receiver_username)
    category = CATEGORY_BY_TYPE[payload.type]

    outgoing = Transaction(
        transaction_id=new_transaction_id(),
        group_id=group_id,
        user_id=locked_sender.id,
        type=payload.type,
        direction=TransactionDirection.OUT,
        amount=amount,
        description=description,
        category=category,
        status=TransactionStatus.COMPLETED,
        sender_username=locked_sender.username,
        receiver_username=receiver_username,
        occurred_at=occurred_at,
    )
    db.add(outgoing)

    if receiver is not None:
        db.add(
            Transaction(
                transaction_id=new_transaction_id(),
                group_id=group_id,
                user_id=receiver.id,
                type=payload.type,
                direction=TransactionDirection.IN,
                amount=amount,
                description=description,
                category=category,
                status=TransactionStatus.COMPLETED,
                sender_username=locked_sender.username,
                receiver_username=receiver.username,
                occurred_at=occurred_at,
            )
        )

    await db.commit()
    await db.refresh(outgoing)
    return outgoing


async def create_deposit(
    db: AsyncSession, user: User, payload: DepositRequest
) -> Transaction:
    locked = await _load_user_for_update(db, user.id)
    amount = round_money(payload.amount)
    locked.account_balance = round_money(locked.account_balance + amount)

    entry = Transaction(
        transaction_id=new_transaction_id(),
        group_id=uuid_pk(),
        user_id=locked.id,
        type=TransactionType.DEPOSIT,
        direction=TransactionDirection.IN,
        amount=amount,
        description=payload.description or "Deposit",
        category=CATEGORY_BY_TYPE[TransactionType.DEPOSIT],
        status=TransactionStatus.COMPLETED,
        sender_username=SYSTEM_USERNAME,
        receiver_username=locked.username,
        occurred_at=utcnow(),
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


# ---------------------------------------------------------------------------
# queries
# ---------------------------------------------------------------------------
async def list_transactions(
    db: AsyncSession,
    user: User,
    *,
    page: int,
    size: int,
    direction: TransactionDirection | None = None,
) -> Page[TransactionOut]:
    filters = [Transaction.user_id == user.id]
    if direction is not None:
        filters.append(Transaction.direction == direction)

    total = int(
        await db.scalar(select(func.count()).select_from(Transaction).where(*filters)) or 0
    )
    rows = (
        await db.scalars(
            select(Transaction)
            .where(*filters)
            .order_by(Transaction.occurred_at.desc(), Transaction.id.desc())
            .offset(page * size)
            .limit(size)
        )
    ).all()

    return Page[TransactionOut].build(
        items=[TransactionOut.model_validate(r) for r in rows],
        total=total,
        page=page,
        size=size,
    )


async def get_transaction(db: AsyncSession, user: User, transaction_id: str) -> TransactionOut:
    row = await db.scalar(
        select(Transaction).where(
            Transaction.id == transaction_id, Transaction.user_id == user.id
        )
    )
    if row is None:
        raise NotFoundError("Transaction not found")
    return TransactionOut.model_validate(row)


async def transfer_recipients(
    db: AsyncSession, user: User, limit: int = 6
) -> list[TransferRecipientOut]:
    """People worth transferring to, most-recently-interacted-with first.

    Counterparties come from the user's own ledger; any remaining slots are
    filled with other registered users so the picker is never empty on a fresh
    account.
    """
    recent = (
        await db.scalars(
            select(Transaction)
            .where(Transaction.user_id == user.id)
            .order_by(Transaction.occurred_at.desc())
            .limit(300)
        )
    ).all()

    seen: dict[str, None] = {}
    for tx in recent:
        other = tx.receiver_username if tx.sender_username == user.username else tx.sender_username
        if other and other != user.username:
            seen.setdefault(other, None)

    usernames = list(seen)[:limit]
    if len(usernames) < limit:
        extras = (
            await db.scalars(
                select(User.username).where(User.id != user.id, User.is_active.is_(True))
            )
        ).all()
        for name in extras:
            if len(usernames) >= limit:
                break
            if name not in seen:
                usernames.append(name)

    if not usernames:
        return []

    users = (
        await db.scalars(select(User).where(User.username.in_(usernames), User.is_active.is_(True)))
    ).all()
    by_name = {u.username: u for u in users}
    return [
        TransferRecipientOut.model_validate(by_name[name])
        for name in usernames
        if name in by_name
    ]


async def balance_history(db: AsyncSession, user: User, months: int = 12) -> list[SeriesPoint]:
    transactions = list(
        (
            await db.scalars(
                select(Transaction)
                .where(
                    Transaction.user_id == user.id,
                    Transaction.status == TransactionStatus.COMPLETED,
                )
                .order_by(Transaction.occurred_at.asc())
            )
        ).all()
    )
    return build_balance_series(transactions, user.account_balance, months)