import { api, clearTokens, getRefreshToken, setTokens } from "@/lib/apiClient";
import type {
  ChangePasswordRequest,
  RegisterRequest,
  TokenPair,
  User,
} from "@/types/api";

/** Create an account. The caller is redirected to sign-in afterwards. */
export const registerUser = (payload: RegisterRequest): Promise<User> =>
  api.post<User>("/auth/register", payload);

/**
 * Exchange credentials for tokens and store them for later requests.
 *
 * Storing here (rather than in the form) keeps every caller of `loginUser`
 * authenticated automatically.
 */
export const loginUser = async (username: string, password: string): Promise<TokenPair> => {
  const tokens = await api.post<TokenPair>("/auth/login", { username, password });
  setTokens(tokens);
  return tokens;
};

export const refreshToken = (): Promise<TokenPair> => {
  const refreshToken = getRefreshToken();
  if (!refreshToken) return Promise.reject(new Error("Not signed in"));
  return api.post<TokenPair>("/auth/refresh", { refreshToken });
};

export const changePassword = (payload: ChangePasswordRequest): Promise<null> =>
  api.post<null>("/auth/change-password", payload);

/** Revoke the stored refresh token server-side, then drop it locally. */
export const logout = async (): Promise<void> => {
  try {
    await api.post<null>("/auth/logout", { refreshToken: getRefreshToken() });
  } finally {
    clearTokens();
  }
};