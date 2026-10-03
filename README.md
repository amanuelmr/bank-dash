# BankDash.

A banking dashboard monorepo: a Next.js 14 frontend and a FastAPI backend.

```
bank-dash/
├── frontend/   Next.js 14 (App Router, TypeScript, Tailwind)
├── backend/    FastAPI (Python 3.12, SQLAlchemy 2.0 async, SQLite)
└── screenshot/ App screenshots
```

---

## Prerequisites

- **Node.js 18+** and npm — for the frontend
- **Python 3.12+** — for the backend ([uv](https://docs.astral.sh/uv/) recommended)

---

## Backend

```bash
cd backend

# create and activate the virtual environment
uv venv --python 3.12          # or: python3.12 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

# install dependencies
uv pip install -e ".[dev]"     # or: pip install -e ".[dev]"

# create the SQLite database, run migrations, and load demo data
alembic upgrade head
python -m app.seed

# start the dev server on http://localhost:8000
uvicorn app.main:app --reload --port 8000
```

Interactive API docs are served at:

- Swagger UI — <http://localhost:8000/docs>
- ReDoc — <http://localhost:8000/redoc>
- OpenAPI schema — <http://localhost:8000/openapi.json>

### Seeded demo accounts

| Username | Password    |
| -------- | ----------- |
| `tester`  | `12345678`  |
| `alice`   | `12345678`  |
| `bob`     | `12345678`  |
| `carol`   | `12345678`  |
| `dave`    | `12345678`  |
| `erin`    | `12345678`  |

`tester` is the fully-populated account: cards, ~60 transactions spanning 14
months, active loans, and transfers to and from the other five users.

### Switching to PostgreSQL

SQLAlchemy is configured so the only change needed is the `DATABASE_URL` in
`backend/.env`:

```
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/bankdash
```

Then re-run `alembic upgrade head`. All models are portable across both.

---

## Frontend

```bash
cd frontend
npm install
cp .env.example .env.local     # adjust if the backend is not on :8000
npm run dev                    # http://localhost:3000
```

Other scripts:

```bash
npm run build      # production build
npm run start      # serve the production build
npm run lint       # eslint
npm test           # jest
```

---

## API conventions

Every endpoint lives under `/api/v1` and returns the same envelope, with an
appropriate HTTP status code:

```jsonc
{ "success": true,  "message": null, "data": { } }
{ "success": false, "message": "Insufficient funds", "data": null }
```

List endpoints accept `page` (0-indexed) and `size`, and return a uniform page
object:

```jsonc
"data": {
  "items": [ ],
  "page": 0,
  "size": 10,
  "totalItems": 42,
  "totalPages": 5,
  "hasNext": true,
  "hasPrevious": false
}
```

Authentication is a JWT bearer token plus a rotating refresh token. The
frontend stores both in cookies and sends `Authorization: Bearer <accessToken>`.

---

## Deploying the frontend to Vercel

Vercel needs **one project setting**, and this repository cannot substitute for
it:

> **Settings → General → Root Directory → `frontend`**

The deployable app is `frontend/`, so its `package.json` must be the one at the
Root Directory. Without this Vercel cannot find `next` and the build fails with
*"No Next.js version detected."*

No `vercel.json` is used on purpose. With Root Directory set to `frontend`,
Vercel auto-detects the framework and derives the install, build, and output
directories correctly. Adding one with `frontend/`-prefixed paths would break
exactly that, since those paths would resolve relative to `frontend/`.

The Node version does **not** need a dashboard change: `frontend/package.json`
declares `engines#node: 24.x`, and Vercel reports that it overrides the
project-level setting. The root `package.json` mirrors this and exists purely as
a convenience wrapper for running `npm run build` / `lint` / `typecheck` from
the repo root locally.

Set `NEXT_PUBLIC_API_BASE_URL` in the Vercel project's environment variables to
the deployed backend URL.