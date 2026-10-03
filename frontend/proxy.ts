import { NextRequest, NextResponse } from "next/server";

import { ACCESS_COOKIE, SIGN_IN_PATH } from "@/lib/config";

/**
 * Gate the authenticated routes on session *presence*, never on validity.
 *
 * Next 16 renamed `middleware.ts` to `proxy.ts`; `middleware` is deprecated.
 *
 * An earlier version decoded the JWT payload and honoured `exp`, which was a
 * real improvement over "does a cookie exist" at the time - it was added before
 * the client could recover from an expired token on its own. Now that
 * `apiClient` refreshes and replays on a 401, that check works against the
 * user: an expired access token alongside a live refresh token is an entirely
 * normal state that the client repairs in one request, but this gate would
 * bounce it to sign-in first.
 *
 * Only the access cookie is consulted, and that is not an oversight. The
 * refresh cookie is scoped to the API's `/api/v1/auth` routes, so the browser
 * never attaches it to a Next.js request - there is nothing else to read here.
 * That is also why the API gives that cookie a much longer browser lifetime than
 * the JWT inside the access cookie: the access cookie is the only proof of
 * session this gate can see, so if it expired alongside the token, a session
 * with plenty of refresh token left would be bounced before the client ever
 * got a chance to renew. See `Settings.access_cookie_max_age`.
 *
 * Expiry is deliberately not reimplemented here. This runs on the edge, where
 * the signing secret is unavailable, so any check is unverified - and the API
 * verifies every request anyway.
 */
export function proxy(request: NextRequest) {
  const accessToken = request.cookies.get(ACCESS_COOKIE)?.value;

  // No session at all - either never signed in, or signed out and the server
  // expired the cookies. Anything else is allowed through to be judged by the
  // API, which is the only component that can actually tell.
  if (!accessToken) {
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