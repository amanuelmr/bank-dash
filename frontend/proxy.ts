import { NextRequest, NextResponse } from "next/server";

/**
 * Gate the authenticated routes.
 *
 * Next 16 renamed `middleware.ts` to `proxy.ts`; `middleware` is deprecated.
 *
 * The previous version only checked that an `accessToken` *cookie existed*, so
 * an expired or forged token still rendered the whole dashboard before every
 * request came back 401. This decodes the JWT payload and honours `exp`.
 *
 * The signature is deliberately not verified here: this runs on the edge where
 * the signing secret is unavailable, and it is only a UX redirect. Real
 * verification happens in the API, which every request goes through anyway.
 */
function isTokenExpired(token: string): boolean {
  try {
    const payload = token.split(".")[1];
    if (!payload) return true;

    const base64 = payload.replace(/-/g, "+").replace(/_/g, "/");
    const json = atob(base64.padEnd(base64.length + ((4 - (base64.length % 4)) % 4), "="));
    const { exp } = JSON.parse(json);

    return typeof exp !== "number" || exp * 1000 <= Date.now();
  } catch {
    return true;
  }
}

export function proxy(request: NextRequest) {
  const accessToken = request.cookies.get("accessToken")?.value;

  // Signed out, or holding a token that has expired: send them to sign-in.
  if (!accessToken || isTokenExpired(accessToken)) {
    const response = NextResponse.redirect(new URL("/home", request.url));
    if (accessToken) response.cookies.delete("accessToken");
    return response;
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