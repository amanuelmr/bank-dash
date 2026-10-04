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
* **Access tokens live 30 minutes.** A token cannot be revoked before it expires,
  so its lifetime is exactly how long a leak stays usable. An active session
  renews itself about twice an hour and the user sees nothing. Nothing depends
  on the token being long-lived: the access *cookie* outlives it deliberately,
  and `proxy.ts` gates on cookie presence rather than expiry, so the route gate
  cannot pre-empt the refresh. If your deployment sets
  `ACCESS_TOKEN_EXPIRE_MINUTES`, that overrides the default - lower it or delete
  the line.
* **Logout is per-device.** It revokes only the refresh token the request
  presented. An earlier version revoked every outstanding token for the user when
  none was presented, so one device with a missing cookie could silently sign
  someone out everywhere. "Sign out everywhere" is a separate feature and should
  be asked for explicitly.
* **Tokens are httpOnly cookies.** `login`/`refresh` set them and return the
  user instead of the tokens; a body token would undo the protection. The
  `Authorization: Bearer` header is still accepted for CLI clients and
  `scripts/smoke.sh`.
* **The refresh cookie is scoped to `/api/v1/auth`**, the only two places it is
  ever presented. On `/` it would ride along with every API call, putting a
  30-day credential within reach of anything that logs request headers.
* **The access cookie outlives the JWT inside it** (30 days vs 24 hours). This
  is load-bearing, not slack. The refresh cookie is scoped to the API's auth
  routes, so the browser never presents it to the frontend — the access cookie
  is the only proof of session the route gate can see. Were it to die alongside
  the token, a user with weeks of refresh token left would be bounced to sign-in
  before the client ever got to renew. An expired JWT in the cookie is harmless:
  the API rejects it and `apiClient` refreshes and replays in one round-trip.
* **A failed refresh expires the cookies.** JavaScript cannot delete an httpOnly
  cookie, so only the server can. Without this the rejected cookie stays
  attached for its full lifetime and every request first pays a refresh that is
  guaranteed to fail. Note the failure is *returned*, not raised: headers set
  on an injected `Response` are discarded once an exception handler takes over,
  so a raised error would silently expire nothing.
* **`SameSite=None` removes the browser's CSRF protection.** It is also the
  only way to send a cookie to a separately hosted frontend, so the two have to
  be considered together. `COOKIE_SAMESITE=none` requires `COOKIE_SECURE=true`
  (validated at startup - browsers reject a cross-site cookie without it), and
  you then need a CSRF token or an `Origin` check on the mutating endpoints.
  Serving the API from the same origin via Next.js rewrites avoids the whole
  problem and is the better option where it is available.
* **`balance-history` is real.** It is reconstructed by walking the ledger
  backwards from the current balance, not generated.
* **`investment-summary` is synthetic** — seeded per username so it is stable
  across requests. Replace it when a holdings model exists.
