import { api, paginated } from "@/lib/apiClient";
import type { BankService, Page } from "@/types/api";

export const getAllBankServices = (page = 0, size = 10): Promise<Page<BankService>> =>
  paginated<BankService>("/bank-services", page, size);

export const searchBankServices = (query: string, limit = 20): Promise<BankService[]> =>
  api.get<BankService[]>("/bank-services/search", { q: query, limit });

export const getBankServiceById = (id: string): Promise<BankService> =>
  api.get<BankService>(`/bank-services/${id}`);

export const createBankService = (serviceData: Partial<BankService>): Promise<BankService> =>
  api.post<BankService>("/bank-services", serviceData);

export const updateBankServiceById = (
  id: string,
  updateData: Partial<BankService>,
): Promise<BankService> => api.put<BankService>(`/bank-services/${id}`, updateData);

export const deleteBankServiceById = (id: string): Promise<null> =>
  api.delete<null>(`/bank-services/${id}`);