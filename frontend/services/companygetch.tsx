import { api, paginated } from "@/lib/apiClient";
import type { Company, Page } from "@/types/api";

export const getAllCompanies = (page = 0, size = 10): Promise<Page<Company>> =>
  paginated<Company>("/companies", page, size);

/** Trending stocks, best day change first. */
export const getTrendingCompanies = (limit = 6): Promise<Company[]> =>
  api.get<Company[]>("/companies/trending", { limit });

export const getCompanyById = (id: string): Promise<Company> =>
  api.get<Company>(`/companies/${id}`);

export const createCompany = (companyData: Partial<Company>): Promise<Company> =>
  api.post<Company>("/companies", companyData);

export const updateCompanyById = (
  id: string,
  updateData: Partial<Company>,
): Promise<Company> => api.put<Company>(`/companies/${id}`, updateData);

export const deleteCompanyById = (id: string): Promise<null> =>
  api.delete<null>(`/companies/${id}`);