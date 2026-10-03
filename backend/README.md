# BankDash API

FastAPI backend for the BankDash dashboard. See the repository root
[README](../README.md) for the full-stack quickstart.

## Setup

```bash
uv venv --python 3.12
source .venv/bin/activate
uv pip install -e ".[dev]"

cp .env.example .env
alembic upgrade head
python -m app.seed

uvicorn app.main:app --reload --port 8000
```

Docs at <http://localhost:8000/docs>.

## Layout

```
app/
├── core/          config, database, security (JWT + argon2), error envelope
├── models/        SQLAlchemy ORM models
├── schemas/       Pydantic request/response models
├── services/      business logic; routers stay thin
├── routers/       HTTP layer, one module per resource
├── deps.py        bearer auth, current user, pagination
├── main.py        app factory wiring
└── seed/          demo data loader
```

## Conventions

Every endpoint returns the same envelope:

```jsonc
{ "success": true,  "message": null, "data": { } }
{ "success": false, "message": "Insufficient funds", "data": null }
```

List endpoints take `page` (0-indexed) and `size`, returning:

```jsonc
{ "items": [], "page": 0, "size": 10, "totalItems": 0,
  "totalPages": 0, "hasNext": false, "hasPrevious": false }
```

Fields are declared snake_case in Python and serialised camelCase, so
`account_balance` reaches the client as `accountBalance`.

## Notes on the ledger

* **Double-entry.** A transfer writes one row per party (`OUT` for the sender,
  `IN` for the receiver) sharing a `group_id`. `direction` is therefore correct
  for whoever reads the row, and every per-user query is an indexed lookup.
* **Balances are locked.** Transfers take a `SELECT ... FOR UPDATE` over both
  accounts in a single statement ordered by id, so concurrent transfers cannot
  overdraw an account or deadlock against each other. SQLite has no row locks
  but serialises writes, so the clause is applied on Postgres only.
* **Cards never store a PAN.** Only a masked number is persisted.
* **Refresh tokens rotate.** Only their SHA-256 is stored, and each is revoked
  when exchanged.
* **Tokens are httpOnly cookies.** `login`/`refresh` set them and return the
  user instead of the tokens; a body token would undo the protection. The
  `Authorization: Bearer` header is still accepted for CLI clients and
  `scripts/smoke.sh`. For a separately hosted production frontend set
  `COOKIE_SAMESITE=none` and `COOKIE_SECURE=true`, since a cross-site cookie
  without `Secure` is rejected by browsers.
* **`balance-history` is real.** It is reconstructed by walking the ledger
  backwards from the current balance, not generated.
* **`investment-summary` is synthetic** — seeded per username so it is stable
  across requests. Replace it when a holdings model exists.