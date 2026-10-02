import { api, paginated } from "@/lib/apiClient";
import type {
  AccountSummary,
  InvestmentSummary,
  Page,
  Preferences,
  PublicUser,
  UpdateProfileRequest,
  User,
} from "@/types/api";

/** The signed-in user, including balance and preferences. */
export const currentuser = (): Promise<User> => api.get<User>("/users/me");

export const updateUserDetails = (payload: UpdateProfileRequest): Promise<User> =>
  api.put<User>("/users/me", payload);

export const updatePreference = (payload: Partial<Preferences>): Promise<Preferences> =>
  api.put<Preferences>("/users/me/preferences", payload);

/** Another user's public profile - deliberately no email or balance. */
export const fetchUserDetails = (username: string): Promise<PublicUser> =>
  api.get<PublicUser>(`/users/${encodeURIComponent(username)}`);

/** Balance, lifetime income/expense and savings, for the accounts page. */
export const fetchAccountSummary = (): Promise<AccountSummary> =>
  api.get<AccountSummary>("/users/me/summary");

export const randomInvestmentData = (
  years = 5,
  months = 8,
): Promise<InvestmentSummary> =>
  api.get<InvestmentSummary>("/users/me/investment-summary", { years, months });

/** Bank services are paged but never filtered by the caller today. */
export type { Page };