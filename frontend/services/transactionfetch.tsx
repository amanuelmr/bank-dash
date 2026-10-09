import { api, paginated } from "@/lib/apiClient";
import type {
  CategoryTotal,
  CreateTransactionRequest,
  DepositRequest,
  Page,
  SeriesPoint,
  Transaction,
  TransferRecipient,
} from "@/types/api";

/** The most recent page of everything, newest first. */
export const getAllTransactions = (page = 0, size = 10): Promise<Page<Transaction>> =>
  paginated<Transaction>("/transactions", page, size);

export const getIncomes = (page = 0, size = 10): Promise<Page<Transaction>> =>
  paginated<Transaction>("/transactions/incomes", page, size);

export const getExpenses = (page = 0, size = 10): Promise<Page<Transaction>> =>
  paginated<Transaction>("/transactions/expenses", page, size);

/** Small unpaged fetch for the dashboard's "recent transaction" strip. */
export const getRecentTransactions = (size = 10): Promise<Transaction[]> =>
  getAllTransactions(0, size).then((result) => result.items);

/** Pay, transfer, shop, or repay a loan. */
export const createTransaction = (
  transactionData: CreateTransactionRequest,
): Promise<Transaction> => api.post<Transaction>("/transactions", transactionData);

export const createDeposit = (depositData: DepositRequest): Promise<Transaction> =>
  api.post<Transaction>("/transactions/deposit", depositData);

export const getTransactionById = (id: string): Promise<Transaction> =>
  api.get<Transaction>(`/transactions/${id}`);

/** Month-end balances, oldest first. `period` is `YYYY-MM`. */
export const getBalanceHistory = (months = 12): Promise<SeriesPoint[]> =>
  api.get<SeriesPoint[]>("/transactions/balance-history", { months });

/** People worth transferring to, most recently interacted with first. */
export const getLatestTransfers = (limit = 6): Promise<TransferRecipient[]> =>
  api.get<TransferRecipient[]>("/transactions/transfer-recipients", { limit });

/** Spend grouped by category, largest first. Powers the expense breakdown. */
export const getSpendByCategory = (months = 12): Promise<CategoryTotal[]> =>
  api.get<CategoryTotal[]>("/transactions/summary/categories", { months });

/** Spend grouped by calendar month, oldest first. */
export const getSpendByMonth = (months = 6): Promise<SeriesPoint[]> =>
  api.get<SeriesPoint[]>("/transactions/summary/monthly", { months });
