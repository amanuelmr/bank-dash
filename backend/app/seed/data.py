"""Load demo data: six users, cards, ~14 months of transactions, loans, services.

Run with ``python -m app.seed``. Idempotent - it clears the seeded tables first,
so it can be re-run at any time to reset the demo state.
"""

from __future__ import annotations

import asyncio
import random
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import Base, SessionLocal, engine
from app.core.security import hash_password
from app.models.bank_service import BankService, BankServiceStatus
from app.models.card import Card, CardStatus
from app.models.company import Company
from app.models.loan import Loan, LoanStatus, LoanType
from app.models.transaction import (
    Transaction,
    TransactionDirection,
    TransactionStatus,
    TransactionType,
)
from app.models.user import RefreshToken, User, UserPreference, UserRole
from app.services.loan import compute_installment
from app.services.transaction import (
    CATEGORY_BY_TYPE,
    SYSTEM_USERNAME,
    new_transaction_id,
    round_money,
)

DEMO_PASSWORD = "12345678"

USERS = [
    ("tester", "Test User", "tester@bankdash.dev", "New York", "United States", 12_500.0),
    ("alice", "Alice Nguyen", "alice@bankdash.dev", "San Francisco", "United States", 4_300.0),
    ("bob", "Bob Martinez", "bob@bankdash.dev", "Austin", "United States", 2_150.0),
    ("carol", "Carol Osei", "carol@bankdash.dev", "London", "United Kingdom", 7_800.0),
    ("dave", "Dave Lindqvist", "dave@bankdash.dev", "Berlin", "Germany", 1_640.0),
    ("erin", "Erin Nakamura", "erin@bankdash.dev", "Tokyo", "Japan", 9_250.0),
]

BANK_SERVICES = [
    ("High-Yield Savings", "Earn 4.2% APY with no monthly maintenance fee.", "Savings", "ACTIVE", 4820),
    ("Everyday Checking", "Unlimited transfers and free international ATM access.", "Checking", "ACTIVE", 9310),
    ("Life Insurance Cover", "Whole-life policy with flexible riders from $12/mo.", "Insurance", "ACTIVE", 1245),
    ("Small Business Loan", "Up to $250k with same-day pre-approval for existing customers.", "Loans", "ACTIVE", 612),
    ("Merchant Payments", "Accept card payments with next-day settlement.", "Payments", "ACTIVE", 2870),
    ("Auto Loan", "Refinance an existing vehicle loan from 6.1% APR.", "Loans", "ACTIVE", 940),
    ("Travel Rewards Card", "3x points on dining and travel, no foreign transaction fee.", "Cards", "ACTIVE", 6120),
    ("Student Checking", "No overdraft fees for students under 24.", "Checking", "ACTIVE", 1530),
    ("Fixed-Term Deposit", "Lock in a rate for 6, 12 or 24 months.", "Deposits", "ACTIVE", 760),
    ("Wealth Advisory", "Quarterly portfolio reviews with a dedicated advisor.", "Advisory", "ACTIVE", 210),
    ("Legacy Remittance", "Closed to new customers.", "Payments", "INACTIVE", 84),
    ("Crypto Wallet Access", "Suspended pending regulatory review.", "Digital Assets", "INACTIVE", 0),
]

COMPANIES = [
    ("Apple Inc.", "AAPL", "Technology", 227.4, 1.82, True),
    ("Microsoft Corp.", "MSFT", "Technology", 421.9, -0.44, True),
    ("Amazon.com Inc.", "AMZN", "Consumer Cyclical", 186.3, 2.05, True),
    ("Alphabet Inc.", "GOOGL", "Communication Services", 164.8, 0.91, True),
    ("Tesla Inc.", "TSLA", "Automotive", 248.5, -2.61, True),
    ("Nokia Oyj", "NOK", "Telecommunications", 4.12, 0.18, True),
    ("JPMorgan Chase", "JPM", "Financial Services", 218.7, 0.34, False),
    ("Saudi Aramco", "2222", "Energy", 28.9, -0.12, False),
    ("Meta Platforms", "META", "Communication Services", 512.4, 1.34, True),
    ("Netflix Inc.", "NFLX", "Entertainment", 681.2, -0.87, True),
    ("NVIDIA Corp.", "NVDA", "Technology", 118.6, 3.42, True),
    ("Intel Corp.", "INTC", "Technology", 22.4, -1.15, False),
    ("Walmart Inc.", "WMT", "Consumer Staples", 78.9, 0.56, False),
    ("Johnson & Johnson", "JNJ", "Healthcare", 156.3, -0.27, False),
]

# (description, category, typical amount range)
#
# `category` used to be a copy of `type`, so spending only ever came back as
# "service" or "shopping" - too coarse to break a spend chart down by anything
# meaningful. Each entry now carries its own category and a plausible amount
# band, so groceries look like groceries and rent-sized bills do not land in the
# same bucket as a coffee.
SPEND_CATALOGUE: dict[TransactionType, list[tuple[str, str, tuple[float, float]]]] = {
    TransactionType.SHOPPING: [
        ("Grocery shopping", "Groceries", (28, 140)),
        ("Online order", "Shopping", (15, 220)),
        ("Electronics store", "Electronics", (40, 480)),
        ("Clothing purchase", "Clothing", (25, 190)),
        ("Pharmacy", "Health", (12, 90)),
        ("Home improvement", "Home", (35, 320)),
        ("Coffee shop", "Dining", (3, 18)),
        ("Restaurant", "Dining", (18, 95)),
        ("Fuel", "Transport", (35, 120)),
        ("Train ticket", "Transport", (12, 140)),
    ],
    TransactionType.SERVICE: [
        ("Streaming subscription", "Entertainment", (9, 22)),
        ("Cinema tickets", "Entertainment", (14, 60)),
        ("Utility bill", "Bills", (55, 240)),
        ("Mobile plan", "Bills", (22, 75)),
        ("Internet bill", "Bills", (35, 95)),
        ("Cloud storage", "Bills", (8, 30)),
        ("Gym membership", "Health", (25, 70)),
        ("Health insurance", "Health", (90, 320)),
        ("Car insurance", "Insurance", (75, 240)),
    ],
}

CARD_TYPES = ["Classic", "Platinum", "Signature", "Cashback"]
CARD_BALANCES = [2_700.0, 8_450.0, 14_900.0, 640.0]


def _hash(password: str) -> str:
    """One argon2 hash reused for every demo account (seed speed, not security)."""
    return hash_password(password)


async def _clear(db: AsyncSession) -> None:
    for model in (
        RefreshToken, Transaction, Loan, Card, UserPreference, User,
        BankService, Company,
    ):
        await db.execute(delete(model))
    await db.commit()


async def _seed_users(db: AsyncSession) -> dict[str, User]:
    shared_hash = _hash(DEMO_PASSWORD)
    now = datetime.now(UTC)
    users: dict[str, User] = {}

    for index, (username, name, email, city, country, balance) in enumerate(USERS):
        user = User(
            name=name,
            username=username,
            email=email,
            hashed_password=shared_hash,
            date_of_birth=date(1990 + index, 1 + index * 2, 1 + index * 3),
            permanent_address=f"{100 + index} Elm Street",
            present_address=f"{200 + index} Maple Avenue",
            postal_code=f"10{index:03d}",
            city=city,
            country=country,
            profile_picture=None,
            role=UserRole.ADMIN if username == "tester" else UserRole.USER,
            account_balance=balance,
            is_active=True,
            created_at=now - timedelta(days=400 - index),
        )
        user.preferences = UserPreference(
            currency="USD" if username != "dave" else "EUR",
            time_zone="GMT-5",
            sent_or_receive_digital_currency=username in ("tester", "erin"),
            receive_merchant_order=username in ("tester", "carol"),
            account_recommendations=True,
            two_factor_authentication=username in ("tester", "bob"),
        )
        db.add(user)
        users[username] = user

    await db.commit()
    return users


async def _seed_cards(db: AsyncSession, users: dict[str, User]) -> None:
    now = datetime.now(UTC)
    for username, user in users.items():
        count = 3 if username == "tester" else 1
        for i in range(count):
            db.add(
                Card(
                    user_id=user.id,
                    card_type=CARD_TYPES[(i + 1) % len(CARD_TYPES)],
                    card_holder=user.name,
                    masked_number=f"**** **** **** {(4200 + i * 137 + hash(username) % 400) % 10000:04d}",
                    balance=CARD_BALANCES[(i + 1) % len(CARD_BALANCES)],
                    expiry_date=date(2027 + i, 5 + i, 14),
                    status=CardStatus.ACTIVE,
                    created_at=now - timedelta(days=200 - i * 30),
                )
            )
    await db.commit()


async def _seed_transactions(db: AsyncSession, users: dict[str, User]) -> None:
    """Build a realistic 14-month history.

    Balances are seeded to a known target and then adjusted by the net of every
    movement inserted, so the stored balance always agrees with the ledger.
    """
    rnd = random.Random(20260815)
    usernames = list(users)
    now = datetime.now(UTC)

    entries: list[Transaction] = []
    net_by_user: dict[str, float] = dict.fromkeys((u.id for u in users.values()), 0.0)

    def add(entry: Transaction, *, affects_balance: bool = True) -> None:
        entries.append(entry)
        if affects_balance:
            sign = 1 if entry.direction is TransactionDirection.IN else -1
            net_by_user[entry.user_id] += sign * entry.amount

    # --- income: monthly salary deposits for everyone ------------------------
    for month_offset in range(13, -1, -1):
        month_start = (now.replace(day=1) - timedelta(days=30 * month_offset)).replace(day=1)
        for username in usernames:
            if username == "tester" and month_offset % 2 == 1:
                continue  # vary the shape rather than a perfect monthly rhythm
            amount = round_money(rnd.uniform(1_800, 3_400))
            user = users[username]
            occurred = month_start + timedelta(hours=9, minutes=rnd.randrange(50))
            add(
                Transaction(
                    transaction_id=new_transaction_id(),
                    group_id=f"seed-salary-{username}-{month_start:%Y%m}",
                    user_id=user.id,
                    type=TransactionType.DEPOSIT,
                    direction=TransactionDirection.IN,
                    amount=amount,
                    description="Monthly salary",
                    category=CATEGORY_BY_TYPE[TransactionType.DEPOSIT],
                    status=TransactionStatus.COMPLETED,
                    sender_username=SYSTEM_USERNAME,
                    receiver_username=username,
                    occurred_at=occurred,
                )
            )

    # --- outgoing spending across the 14 months ------------------------------
    for month_offset in range(13, -1, -1):
        month_start = (now.replace(day=1) - timedelta(days=30 * month_offset)).replace(day=1)
        for username in usernames:
            user = users[username]
            for _ in range(rnd.randrange(7) + 3):
                kind = rnd.choice([TransactionType.SHOPPING, TransactionType.SERVICE])
                description, category, (low, high) = rnd.choice(SPEND_CATALOGUE[kind])
                # Amount now comes from the category's own band rather than one
                # flat 8-260 range, so a Cinema ticket and an electricity bill
                # are no longer equally likely to be $250.
                amount = round_money(rnd.uniform(low, high))
                occurred = month_start + timedelta(
                    days=rnd.randrange(28), hours=rnd.randrange(24), minutes=rnd.randrange(60)
                )
                add(
                    Transaction(
                        transaction_id=new_transaction_id(),
                        group_id=f"seed-spend-{user.id}-{occurred:%Y%m%d}",
                        user_id=user.id,
                        type=kind,
                        direction=TransactionDirection.OUT,
                        amount=amount,
                        description=description,
                        category=category,
                        status=TransactionStatus.COMPLETED,
                        sender_username=username,
                        receiver_username=SYSTEM_USERNAME,
                        occurred_at=occurred,
                    )
                )

    # --- transfers between users (both legs recorded) ------------------------
    for _ in range(28):
        sender_name = rnd.choice(usernames)
        receiver_name = rnd.choice([u for u in usernames if u != sender_name])
        sender, receiver = users[sender_name], users[receiver_name]
        amount = round_money(rnd.uniform(25, 400))
        occurred = now - timedelta(days=rnd.randrange(400), hours=rnd.randrange(24))
        group_id = f"seed-transfer-{sender.id}-{receiver.id}-{occurred:%Y%m%d%H%M}"
        description = f"Transfer to {receiver.username}"
        for owner, direction in (
            (sender, TransactionDirection.OUT),
            (receiver, TransactionDirection.IN),
        ):
            add(
                Transaction(
                    transaction_id=new_transaction_id(),
                    group_id=group_id,
                    user_id=owner.id,
                    type=TransactionType.TRANSFER,
                    direction=direction,
                    amount=amount,
                    description=description,
                    category=CATEGORY_BY_TYPE[TransactionType.TRANSFER],
                    status=TransactionStatus.COMPLETED,
                    sender_username=sender.username,
                    receiver_username=receiver.username,
                    occurred_at=occurred,
                )
            )

    db.add_all(entries)
    await db.flush()

    # Reconcile stored balances with the ledger so /users/me/summary and the
    # balance-history series are internally consistent.
    for user in users.values():
        delta = net_by_user[user.id]
        user.account_balance = round_money(max(user.account_balance + delta, 500.0))
    await db.commit()


async def _seed_loans(db: AsyncSession, users: dict[str, User]) -> None:
    now = datetime.now(UTC)
    plans = [
        ("tester", LoanType.PERSONAL, 5_000.0, 3_200.0, 12, 7.5),
        ("tester", LoanType.BUSINESS, 18_000.0, 12_400.0, 24, 9.25),
        ("tester", LoanType.PERSONAL, 2_500.0, 900.0, 6, 6.1),
        ("alice", LoanType.PERSONAL, 3_000.0, 1_450.0, 12, 8.0),
        ("carol", LoanType.CORPORATE, 40_000.0, 0.0, 36, 6.9),
        ("erin", LoanType.BUSINESS, 25_000.0, 18_200.0, 24, 10.5),
        ("bob", LoanType.PERSONAL, 1_200.0, 1_200.0, 6, 11.0),
    ]
    for username, loan_type, amount, remaining, duration, rate in plans:
        user = users[username]
        installment = compute_installment(amount, rate, duration)
        # Instalments already paid, derived from how much has been repaid.
        paid = min(duration, max(0, round((amount - remaining) / installment)))
        start = now.date() - timedelta(days=30 * paid)
        db.add(
            Loan(
                user_id=user.id,
                loan_type=loan_type,
                loan_amount=round_money(amount),
                amount_left_to_repay=round_money(remaining),
                installment=installment,
                interest_rate=rate,
                loan_duration=duration,
                status=LoanStatus.PAID if remaining == 0 else LoanStatus.ACTIVE,
                start_date=start,
                end_date=start + timedelta(days=30 * duration),
                created_at=now - timedelta(days=200),
            )
        )
    await db.commit()


async def _seed_catalogue(db: AsyncSession) -> None:
    db.add_all(
        BankService(name=n, details=d, type=t, status=BankServiceStatus(s), number_of_users=c)
        for n, d, t, s, c in BANK_SERVICES
    )
    db.add_all(
        Company(
            name=n, symbol=sym, sector=sector, price=price,
            change_percent=change, is_trending=trending,
        )
        for n, sym, sector, price, change, trending in COMPANIES
    )
    await db.commit()


async def main() -> None:
    print("Creating tables if missing...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with SessionLocal() as db:
        print("Clearing existing seed data...")
        await _clear(db)

        print("Seeding users...")
        users = await _seed_users(db)
        print("Seeding cards...")
        await _seed_cards(db, users)
        print("Seeding transaction history...")
        await _seed_transactions(db, users)
        print("Seeding loans...")
        await _seed_loans(db, users)
        print("Seeding services and companies...")
        await _seed_catalogue(db)

        tx_count = len((await db.scalars(select(Transaction))).all())
        balances = ", ".join(
            f"{name}={users[name].account_balance:.2f}" for name in usernames_for(users)
        )
        print("\nDone.")
        print(f"  users          : {len(users)}")
        print(f"  transactions   : {tx_count}")
        print(f"  balances       : {balances}")
        print("\nSign in with any of:")
        for username in usernames_for(users):
            print(f"  {username:<8} / {DEMO_PASSWORD}")

    await engine.dispose()


def usernames_for(users: dict[str, User]) -> list[str]:
    return [u.username for u in users.values()]


if __name__ == "__main__":
    asyncio.run(main())