import { api, paginated } from "@/lib/apiClient";
import type {
  CreateLoanRequest,
  Loan,
  LoanRepayment,
  LoanSummary,
  Page,
} from "@/types/api";

/** The signed-in user's loans, newest first. */
export const getMyLoans = (page = 0, size = 5): Promise<Page<Loan>> =>
  paginated<Loan>("/loans", page, size);

/** Every loan on file - administrator only. */
export const getAllActiveLoans = (page = 0, size = 10): Promise<Page<Loan>> =>
  paginated<Loan>("/loans/all", page, size);

/** Outstanding totals per loan type, for the summary cards. */
export const getLoanDetailData = (): Promise<LoanSummary> =>
  api.get<LoanSummary>("/loans/summary");

export const getActiveLoanById = (id: string): Promise<Loan> =>
  api.get<Loan>(`/loans/${id}`);

export const createActiveLoan = (loanData: CreateLoanRequest): Promise<Loan> =>
  api.post<Loan>("/loans", loanData);

export const approveActiveLoan = (id: string): Promise<Loan> =>
  api.post<Loan>(`/loans/${id}/approve`);

export const rejectActiveLoan = (id: string): Promise<Loan> =>
  api.post<Loan>(`/loans/${id}/reject`);

/**
 * Repay a loan, debiting the account balance.
 *
 * Omit `amount` to clear the full outstanding balance; an amount above what is
 * owed is clamped down to it.
 */
export const repayLoan = (id: string, amount?: number): Promise<LoanRepayment> =>
  api.post<LoanRepayment>(`/loans/${id}/repay`, { amount });