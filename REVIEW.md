# Reviewing a BankDash branch

Instructions for an AI reviewer. Point a fresh agent session at this file and
name the branch. Nothing here is a formality — each item below exists because
getting it wrong has produced a wrong review in this repo.

## Setup

```bash
git fetch origin
git checkout <branch>            # or inspect without checking out
git diff origin/main...<branch> --stat
```

**Diff against `origin/main`, never local `main`.** Local `main` goes stale and
a review built on it reports hundreds of phantom changed files. This happened
once and produced a stat of "302 files changed" for a 11-file branch.

## Ground rules

These are the difference between a useful review and a confident wrong one.

1. **Do not trust the commit messages.** They are written by the author, who
   knows what they intended. Verify against the code. A commit message here has
   already claimed a fix was complete while the test guarding it never ran.
2. **Run the suite yourself.** `cd backend && .venv/bin/pytest -q` and
   `.venv/bin/ruff check app tests`. If a commit message says "90 passed", check
   it. Also confirm the tests *can* fail — revert the behaviour a test claims to
   guard and confirm the test goes red.
3. **Reproduce each finding before reporting it.** State the file and line. If you
   cannot make it fail, it is a hypothesis, not a finding — say so.
4. **Check that a suggested fix actually works.** Do not assume. Real example: the
   obvious way to clear cookies on an error path in FastAPI is to set them on the
   injected `Response` and then raise — and that silently does nothing, because
   headers are discarded once an exception handler runs. A review proposing that
   fix would have been confidently wrong.
5. **Distinguish a live defect from a style preference, and say which.** Severity
   inflation wastes the author's time and trains them to ignore you.
6. **Distinguish new breakage from pre-existing problems.** Pre-existing lint
   warnings are not part of the diff.

## What this codebase actually needs checking for

**Auth.** Tokens are httpOnly cookies; the response body must never contain one.
The API also accepts `Authorization: Bearer` for CLI clients — that is
intentional and covered by a regression test. `refresh` takes no body from a
browser. Check the failure paths clear cookies, not just the success paths.

**Cookie paths.** The refresh cookie is scoped to `/api/v1/auth`, so browsers
never present it to Next.js. Anything in `frontend/proxy.ts` that tries to read
it is dead code. Cookies ignore ports but honour paths — this distinction has
caused a real bug.

**Token lifetimes are coupled to the client.** `access_cookie_max_age` must stay
well above `access_token_expire_minutes`, and `proxy.ts` must gate on cookie
presence rather than expiry. Shortening the JWT TTL is only safe because of both.
Treat a change that couples these as high severity.

**The ledger is double-entry.** A transfer writes one row per party sharing a
`group_id`, so `direction` is correct per viewer. Transfers lock both accounts
via `SELECT ... FOR UPDATE` in a single id-ordered statement. Anything that
changes the number of rows per transfer, or the direction logic, is high
severity.

**The API contract is standardised, not inherited.** `{success, message, data}`
envelope, uniform `Page` shape, snake_case in Python serialising to camelCase,
UTC ISO timestamps with an explicit `Z`. Pagination is zero-indexed.

## Output

For each finding: severity, file:line, what breaks, and a fix that works. Put
anything you could not verify in a separate section — do not blend guesses into
findings. End with a clear verdict: merge, merge after fixes, or blocked.

If the branch is sound, say so plainly. Do not manufacture findings to seem
thorough; a review that says "this is correct, and here is what I ran to confirm
it" is worth more than a long list of nits.