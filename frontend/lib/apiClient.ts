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

import { API_BASE_URL } from "@/lib/config";

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