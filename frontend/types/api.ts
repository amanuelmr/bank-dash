/** Types mirroring the FastAPI backend's response schemas. */

import type { Page } from "@/lib/apiClient";

export type { Page };

export type UserRole = "USER" | "ADMIN";

export type TransactionType =
  | "transfer"
  | "shopping"
  | "deposit"
  | "service"
  | "loan_repayment";

export type TransactionDirection = "IN" | "OUT";
export type TransactionStatus = "COMPLETED" | "FAILED";
export type CardStatus = "ACTIVE" | "FROZEN" | "EXPIRED";
export type LoanStatus = "PENDING" | "APPROVED" | "ACTIVE" | "REJECTED" | "PAID";
export type LoanType = "Personal Loan" | "Corporate Loan" | "Business Loan";
export type BankServiceStatus = "ACTIVE" | "INACTIVE";

export interface Preferences {
  currency: string;
  timeZone: string;
  sentOrReceiveDigitalCurrency: boolean;
  receiveMerchantOrder: boolean;
  accountRecommendations: boolean;
  twoFactorAuthentication: boolean;
}

export interface User {
  id: string;
  name: string;
  username: string;
  email: string;
  dateOfBirth: string;
  permanentAddress: string;
  presentAddress: string;
  city: string;
  country: string;
  postalCode: string;
  profilePicture: string | null;
  role: UserRole;
  accountBalance: number;
  createdAt: string;
  preferences: Preferences | null;
}

export interface PublicUser {
  id: string;
  name: string;
  username: string;
  city: string;
  country: string;
  profilePicture: string | null;
}

export interface TokenPair {
  accessToken: string;
  refreshToken: string;
  tokenType: string;
  expiresIn: number;
}

export interface Card {
  id: string;
  cardType: string;
  cardHolder: string;
  maskedNumber: string;
  balance: number;
  /** `YYYY-MM-DD` - already formatted for display. */
  expiryDate: string;
  status: CardStatus;
  createdAt: string;
}

export interface Transaction {
  id: string;
  transactionId: string;
  type: TransactionType;
  description: string;
  category: string;
  /** Always positive; `direction` carries the sign. */
  amount: number;
  direction: TransactionDirection;
  status: TransactionStatus;
  senderUsername: string;
  receiverUsername: string;
  /** UTC ISO-8601 with a trailing `Z`. */
  occurredAt: string;
}

export interface TransferRecipient {
  id: string;
  username: string;
  name: string;
  city: string;
  country: string;
  profilePicture: string | null;
}

export interface Loan {
  id: string;
  loanType: LoanType;
  loanAmount: number;
  amountLeftToRepay: number;
  installment: number;
  interestRate: number;
  loanDuration: number;
  status: LoanStatus;
  startDate: string | null;
  endDate: string | null;
  createdAt: string;
}

export interface LoanSummary {
  personalLoan: number;
  corporateLoan: number;
  businessLoan: number;
  totalOutstanding: number;
}

export interface LoanRepayment {
  loan: Loan;
  amountPaid: number;
}

export interface BankService {
  id: string;
  name: string;
  details: string;
  type: string;
  status: BankServiceStatus;
  numberOfUsers: number;
}

export interface Company {
  id: string;
  name: string;
  symbol: string;
  sector: string;
  price: number;
  changePercent: number;
  logoUrl: string | null;
  isTrending: boolean;
}

export interface AccountSummary {
  accountBalance: number;
  totalIncome: number;
  totalExpense: number;
  totalSavings: number;
}

export interface SeriesPoint {
  period: string;
  value: number;
}

export interface InvestmentSummary {
  totalInvestment: number;
  rateOfReturn: number;
  numberOfInvestments: number;
  yearlyInvestments: SeriesPoint[];
  monthlyRevenue: SeriesPoint[];
}

/* -------------------------------------------------------------------------- */
/* Request payloads                                                            */
/* -------------------------------------------------------------------------- */

export interface RegisterRequest {
  name: string;
  email: string;
  username: string;
  password: string;
  dateOfBirth: string;
  permanentAddress: string;
  presentAddress: string;
  postalCode: string;
  city: string;
  country: string;
  profilePicture?: string;
  preferences?: Partial<Preferences>;
}

export interface UpdateProfileRequest {
  name?: string;
  email?: string;
  dateOfBirth?: string;
  permanentAddress?: string;
  presentAddress?: string;
  postalCode?: string;
  city?: string;
  country?: string;
  profilePicture?: string;
}

export interface ChangePasswordRequest {
  currentPassword: string;
  newPassword: string;
  twoFactorEnabled?: boolean;
}

export interface CreateCardRequest {
  cardType: string;
  cardHolder: string;
  balance: number;
  expiryDate: string;
  passcode: string;
}

export interface CreateTransactionRequest {
  type: TransactionType;
  amount: number;
  description?: string;
  receiverUsername?: string;
}

export interface DepositRequest {
  amount: number;
  description?: string;
}

export interface CreateLoanRequest {
  loanType: LoanType;
  loanAmount: number;
  loanDuration: number;
  interestRate: number;
}