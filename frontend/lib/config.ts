/**
 * Base URL for the BankDash API, including the `/api/v1` prefix.
 *
 * Read from `NEXT_PUBLIC_API_BASE_URL` because every call happens in the
 * browser, so the value has to be visible to the client bundle rather than
 * resolved on the Next.js server.
 */
export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";