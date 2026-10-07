import { useEffect, useState } from "react";
import { getAllCards } from "@/services/cardfetch";
import type { Card } from "@/types/api";

/**
 * The signed-in user's cards.
 *
 * Dashboard, Accounts, Credit Card and Transaction each carried an identical
 * copy of this fetch-with-cancellation effect.
 */
export function useCards() {
  const [cards, setCards] = useState<Card[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    const fetchCards = async () => {
      try {
        const { items } = await getAllCards(0, 20);
        if (!cancelled) {
          setCards(items);
          setError(null);
        }
      } catch {
        if (!cancelled) setError("Couldn't load your cards.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    fetchCards();
    return () => {
      cancelled = true;
    };
  }, []);

  return { cards, error, loading };
}
