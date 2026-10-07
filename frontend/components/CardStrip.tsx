import ResponsiveCreditCard from "@/components/CreditCard";
import MyCardsLoad from "@/components/loadingComponents/MyCardsLoad";
import EmptyState from "@/components/EmptyState";
import { Card as Panel } from "@/components/ui/card";
import type { Card } from "@/types/api";
import type { CardTone } from "@/constants";

const TONES: CardTone[] = ["brand", "midnight", "light"];

/**
 * A row of the user's credit cards. It scrolls sideways only when the cards
 * genuinely do not fit; where they do, they sit side by side in full.
 *
 * Dashboard, Accounts, Credit Card and Transaction each rendered this row with
 * their own wrapper, their own copy of the tone ternary and their own empty
 * state (one of them `w-screen`, which pushed the page sideways).
 */
const CardStrip: React.FC<{
  cards: Card[];
  loading: boolean;
  error: string | null;
  /** How many cards to show; the rest are on /credit-card. */
  limit?: number;
}> = ({ cards, loading, error, limit }) => {
  if (loading) return <MyCardsLoad count={limit ?? 3} />;

  if (error || cards.length === 0) {
    return (
      <Panel>
        <EmptyState
          tone={error ? "error" : "empty"}
          message={error ?? "You don't have any cards yet."}
        />
      </Panel>
    );
  }

  return (
    <div className="flex gap-4 overflow-x-auto pb-2 scrollbar-thin scrollbar-thumb-slate-300 scrollbar-thumb-rounded-full dark:scrollbar-thumb-surface-3">
      {cards.slice(0, limit).map((card, index) => (
        <div key={card.id} className="shrink-0">
          <ResponsiveCreditCard
            tone={TONES[index % TONES.length]}
            balance={card.balance}
            cardHolder={card.cardHolder}
            expiryDate={card.expiryDate}
            maskedNumber={card.maskedNumber}
          />
        </div>
      ))}
    </div>
  );
};

export default CardStrip;
