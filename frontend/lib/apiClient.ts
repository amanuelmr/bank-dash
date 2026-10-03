/**
 * The single place every network call goes through.
 *
 * Centralising this fixes a class of bug the old per-service `fetch` calls
 * had: each service file read `Cookies.get("accessToken")` once at module load,
 * so any module evaluated before sign-in kept `undefined` forever and silently
 * sent unauthenticated requests.
 *
 * Auth is cookie based. The API sets httpOnly cookies, which JavaScript cannot
 * read, so nothing here touches the token itself - requests just send
 * `credentials: "include"` and the browser attaches the cookie. A 401 triggers
 * one refresh-and-replay against `/auth/refresh`, which also needs no body.
 */

import { API_BASE_URL, SIGN_IN_PATH } from "@/lib/config";

/** The envelope every endpoint returns. */
export type ApiEnvelope<T> = {
  success: boolean;
  message: string | null;
  data: T | null;
};

export type Page<T> = {
  items: T[];
  page: number;
  size: number;
  totalItems: number;
  totalPages: number;
  hasNext: boolean;
  hasPrevious: boolean;
};

export class ApiError extends Error {
  readonly status: number;
  readonly code: string | null;

  constructor(message: string, status: number, code: string | null = null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
  }

  /** True when the request failed because of auth rather than the request itself. */
  get isAuthError(): boolean {
    return this.status === 401;
  }
}

type RequestOptions = {
  method?: "GET" | "POST" | "PUT" | "DELETE";
  body?: unknown;
  query?: Record<string, string | number | boolean | undefined | null>;
  /** Internal: prevents an infinite refresh loop. */
  skipRefresh?: boolean;
};

function buildUrl(path: string, query?: RequestOptions["query"]): string {
  const url = `${API_BASE_URL}${path}`;
  if (!query) return url;

  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(query)) {
    if (value !== undefined && value !== null && value !== "") {
      params.set(key, String(value));
    }
  }
  const qs = params.toString();
  return qs ? `${url}?${qs}` : url;
}

/**
 * In-flight refresh, shared so that several 401s at once trigger one refresh
 * rather than racing to rotate the same cookie.
 */
let refreshInFlight: Promise<boolean> | null = null;

async function refreshSession(): Promise<boolean> {
  refreshInFlight ??= (async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
        method: "POST",
        credentials: "include",
      });
      return response.ok;
    } catch {
      return false;
    } finally {
      refreshInFlight = null;
    }
  })();

  return refreshInFlight;
}

/**
 * Endpoints where a 401 means "those credentials were wrong" rather than "there
 * is no session", so a failure must not bounce the visitor anywhere.
 */
const CREDENTIAL_CHECKS = ["/auth/login", "/auth/register"];

/**
 * Hand a genuinely dead session over to the sign-in page.
 *
 * `middleware.ts` gates on cookie *presence* only, deliberately: it cannot know
 * whether an expired access token is backed by a live refresh token, and
 * bouncing such a user would throw away a session the client can still renew.
 * The consequence is that ending a dead session becomes the client's job - the
 * API has just expired the cookies on the failed refresh, and nothing else is
 * going to navigate away from a page whose every request now 401s.
 */
function handOffToSignIn(failedPath: string): void {
  if (CREDENTIAL_CHECKS.some((path) => failedPath.startsWith(path))) return;
  if (typeof window !== "undefined") {
    window.location.assign(SIGN_IN_PATH);
  }
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, query, skipRefresh = false } = options;

  const headers: Record<string, string> = {};
  if (body !== undefined) headers["Content-Type"] = "application/json";

  const response = await fetch(buildUrl(path, query), {
    method,
    headers,
    // Send the httpOnly auth cookie. Required, or the API sees no session.
    credentials: "include",
    body: body === undefined ? undefined : JSON.stringify(body),
  });

  // Expired access token: refresh once, then replay the original request.
  if (response.status === 401 && !skipRefresh) {
    if (await refreshSession()) {
      return request<T>(path, { ...options, skipRefresh: true });
    }
    // The refresh cookie is gone or was already used. The server has expired
    // both cookies, so this session cannot continue.
    handOffToSignIn(path);
  }

  if (response.status === 204) return null as T;

  let envelope: ApiEnvelope<T>;
  try {
    envelope = (await response.json()) as ApiEnvelope<T>;
  } catch {
    throw new ApiError(
      `Unexpected response from the server (${response.status})`,
      response.status,
    );
  }

  if (!response.ok || !envelope.success) {
    throw new ApiError(
      envelope.message ?? "Request failed",
      response.status,
      (envelope.data as { code?: string } | null)?.code ?? null,
    );
  }

  return envelope.data as T;
}

export const api = {
  get: <T>(path: string, query?: RequestOptions["query"]) =>
    request<T>(path, { method: "GET", query }),
  post: <T>(path: string, body?: unknown) => request<T>(path, { method: "POST", body }),
  put: <T>(path: string, body?: unknown) => request<T>(path, { method: "PUT", body }),
  delete: <T>(path: string) => request<T>(path, { method: "DELETE" }),
};

/** Convenience helper for the many `page`/`size` list endpoints. */
export const paginated = <T>(
  path: string,
  page: number,
  size: number,
  extra?: RequestOptions["query"],
): Promise<Page<T>> => api.get<Page<T>>(path, { page, size, ...extra });
