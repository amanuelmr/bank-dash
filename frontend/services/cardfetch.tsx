import { api, paginated } from "@/lib/apiClient";
import type { Card, CreateCardRequest, Page } from "@/types/api";

export const getAllCards = (
  page = 0,
  size = 10,
): Promise<Page<Card>> => paginated<Card>("/cards", page, size);

export const getCardById = (id: string): Promise<Card> =>
  api.get<Card>(`/cards/${id}`);

export const createCard = (cardData: CreateCardRequest): Promise<Card> =>
  api.post<Card>("/cards", cardData);

export const deleteCardById = (id: string): Promise<null> =>
  api.delete<null>(`/cards/${id}`);