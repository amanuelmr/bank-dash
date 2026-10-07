"use client";

import React from "react";
import RecentTransactions from "@/components/RecentTransaction";
import ExpensesChart from "@/components/ExpensesCart";
import PageContainer from "@/components/PageContainer";
import Section from "@/components/Section";
import CardStrip from "@/components/CardStrip";
import { Card } from "@/components/ui/card";
import { useCards } from "@/hooks/useCards";

/**
 * Two cards need ~716px at their desktop size. The old 50/50 split gave them
 * less than that, so the second card was cut off behind a scrollbar while the
 * chart beside it stretched to fill half the page. The cards column now takes
 * exactly what the two cards need and the chart takes the rest; on screens
 * too narrow for both, the chart drops below the cards.
 */
const Transaction: React.FC = () => {
  const { cards, error, loading } = useCards();

  return (
    <PageContainer>
      <div className="grid grid-cols-1 gap-8 min-[1360px]:grid-cols-[auto_minmax(0,1fr)]">
        <Section title="My Cards" action={{ href: "/credit-card", label: "See All" }}>
          <CardStrip cards={cards} loading={loading} error={error} limit={2} />
        </Section>
        <Section title="My Expenses">
          <Card className="h-[235px] p-5">
            <ExpensesChart />
          </Card>
        </Section>
      </div>

      <Section title="Recent Transactions">
        <RecentTransactions />
      </Section>
    </PageContainer>
  );
};

export default Transaction;
