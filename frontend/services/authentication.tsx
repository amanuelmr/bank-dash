import { api } from "@/lib/apiClient";
import type {
  ChangePasswordRequest,
  RegisterRequest,
  User,
} from "@/types/api";

/**
 * Create an account. The caller is redirected to sign-in afterwards.
 */
export const registerUser = (payload: RegisterRequest): Promise<User> =>
  api.post<User>("/auth/register", payload);

/**
 * Sign in. The API sets httpOnly auth cookies, so there is no token for this
 * module to store - the browser attaches the session to later requests itself.
 */
export const loginUser = async (
  username: string,
  password: string,
): Promise<User> => api.post<User>("/auth/login", { username, password });

export const refreshSession = (): Promise<User> =>
  api.post<User>("/auth/refresh");

/**
 * Revoke the refresh token server-side and expire the cookies. The endpoint is
 * the authoritative sign-out; no local state needs clearing because the tokens
 * were never readable by JavaScript.
 */
export const logout = (): Promise<null> => api.post<null>("/auth/logout");

export const changePassword = (payload: ChangePasswordRequest): Promise<null> =>
  api.post<null>("/auth/change-password", payload);
