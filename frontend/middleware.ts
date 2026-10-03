import { NextRequest, NextResponse } from "next/server";

import { ACCESS_COOKIE, REFRESH_COOKIE, SIGN_IN_PATH } from "@/lib/config";

/**
 * Gate the authenticated routes on session *presence*, never on validity.
 *
 * An earlier version decoded the JWT payload and honoured `exp`, which was a
 * real improvement over "does a cookie exist" at the time - it was added before
 * the client could recover from an expired token on its own. Now that
 * `apiClient` refreshes and replays on a 401, that check works against the
 * user: an expired access token alongside a live 30-day refresh token is an
 * entirely normal state that the client repairs in one request, but this gate
 * would bounce it to sign-in first.
 *
 * Expiry is deliberately not reimplemented here. This runs on the edge, where
 * the signing secret is unavailable, so any check is unverified - and the API
 * verifies every request anyway.
 */
export function middleware(request: NextRequest) {
  const accessToken = request.cookies.get(ACCESS_COOKIE)?.value;
  const refreshToken = request.cookies.get(REFRESH_COOKIE)?.value;

  // No session at all - either never signed in, or signed out and the server
  // expired the cookies. Anything else is allowed through to be judged by the
  // API, which is the only component that can actually tell.
  if (!accessToken && !refreshToken) {
    return NextResponse.redirect(new URL(SIGN_IN_PATH, request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/",
    "/transaction",
    "/accounts",
    "/credit-card",
    "/transfer",
    "/investments",
    "/loans",
    "/services",
    "/setting",
  ],
};