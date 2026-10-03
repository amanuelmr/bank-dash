/**
 * Base URL for the BankDash API, including the `/api/v1` prefix.
 *
 * Read from `NEXT_PUBLIC_API_BASE_URL` because every call happens in the
 * browser, so the value has to be visible to the client bundle rather than
 * resolved on the Next.js server.
 */
export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

/**
 * Names of the auth cookies the API sets.
 *
 * These must match the backend's `access_cookie_name` / `refresh_cookie_name`
 * in `backend/app/core/config.py`. Duplicated here on purpose: `middleware.ts`
 * runs on the edge and cannot import from the backend, so one constant per side
 * is all that keeps the two from drifting. The API tests assert the names it
 * actually sends, so a rename there fails the suite rather than silently
 * logging everyone out.
 */
export const ACCESS_COOKIE = "accessToken";
export const REFRESH_COOKIE = "refreshToken";

/**
 * Where a visitor without a usable session is sent.
 *
 * Shared by `middleware.ts` (which bounces signed-out visitors) and the API
 * client (which gives up once a refresh fails), so both agree on one place
 * rather than drifting to `/` or `/login`.
 */
export const SIGN_IN_PATH = "/home";