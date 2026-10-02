"""Router registry - every APIRouter is mounted from here in main.py."""

from app.routers import (
    auth,
    bank_services,
    cards,
    companies,
    health,
    loans,
    transactions,
    users,
)

#: Mounted under the versioned prefix, in the order they appear in the docs.
api_routers = [
    health.router,
    auth.router,
    users.router,
    cards.router,
    transactions.router,
    loans.router,
    bank_services.router,
    companies.router,
]

__all__ = ["api_routers"]