/**
 * The single place every network call goes through.
 *
 * Centralising this fixes a class of bug the old per-service `fetch` calls
 * had: each service file read `Cookies.get("accessToken")` once at module load,
 * so any module evaluated before sign-in kept `undefined` forever and silently
 * sent unauthenticated requests. Here the token is read per request instead.
 *
 * It also adds the refresh-and-retry the old code never had: a 401 triggers one
 * token refresh and a replay of the original request.
 */

import Cookies from "js-cookie";

import { API_BASE_URL } from "@/lib/config";

const ACCESS_TOKEN_KEY = "accessToken";
const REFRESH_TOKEN_KEY = "refreshToken";

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

export const getAccessToken = (): string | undefined =>
  Cookies.get(ACCESS_TOKEN_KEY);

export const getRefreshToken = (): string | undefined =>
  Cookies.get(REFRESH_TOKEN_KEY);

export function setTokens(tokens: {
  accessToken: string;
  refreshToken: string;
}): void {
  // TODO: move these to httpOnly cookies set by the API. js-cookie cannot set
  // httpOnly, so until then the tokens are readable by any script on the page.
  Cookies.set(ACCESS_TOKEN_KEY, tokens.accessToken, { sameSite: "lax" });
  Cookies.set(REFRESH_TOKEN_KEY, tokens.refreshToken, { sameSite: "lax" });
}

export function clearTokens(): void {
  Cookies.remove(ACCESS_TOKEN_KEY);
  Cookies.remove(REFRESH_TOKEN_KEY);
}

type RequestOptions = {
  method?: "GET" | "POST" | "PUT" | "DELETE";
  body?: unknown;
  query?: Record<string, string | number | boolean | undefined | null>;
  /** Internal: prevents an infinite refresh loop. */
  skipRefresh?: boolean;
};

function buildUrl(
  path: string,
  query?: RequestOptions["query"],
): string {
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
 * rather than racing to rotate the same token (which would invalidate it).
 */
let refreshInFlight: Promise<string | null> | null = null;

async function refreshAccessToken(): Promise<string | null> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) return null;

  refreshInFlight ??= (async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refreshToken }),
      });
      if (!response.ok) {
        clearTokens();
        return null;
      }
      const envelope = (await response.json()) as ApiEnvelope<{
        accessToken: string;
        refreshToken: string;
      }>;
      if (!envelope.data) {
        clearTokens();
        return null;
      }
      setTokens(envelope.data);
      return envelope.data.accessToken;
    } catch {
      return null;
    } finally {
      refreshInFlight = null;
    }
  })();

  return refreshInFlight;
}

async function request<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const { method = "GET", body, query, skipRefresh = false } = options;

  const headers: Record<string, string> = {};
  if (body !== undefined) headers["Content-Type"] = "application/json";

  const token = getAccessToken();
  if (token) headers.Authorization = `Bearer ${token}`;

  const response = await fetch(buildUrl(path, query), {
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
  });

  // Expired access token: refresh once, then replay the original request.
  if (response.status === 401 && !skipRefresh) {
    const refreshed = await refreshAccessToken();
    if (refreshed) {
      return request<T>(path, { ...options, skipRefresh: true });
    }
    clearTokens();
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
): Promise<Page<T>> =>
  api.get<Page<T>>(path, { page, size, ...extra });