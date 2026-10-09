"use client";
import Component from "@/components/DoughnutChart";
import AddNewCard from "@/components/AddNewCard";
import CardSetting from "@/components/CardSetting";
import CardList from "@/components/CardList";
import CardListLoad from "@/components/loadingComponents/CardListLoad";
import PageContainer from "@/components/PageContainer";
import Section from "@/components/Section";
import CardStrip from "@/components/CardStrip";
import EmptyState from "@/components/EmptyState";
import { Card } from "@/components/ui/card";
import { useCards } from "@/hooks/useCards";

const CreditCard = () => {
  const { cards, error, loading } = useCards();

  return (
    <PageContainer>
      <Section title="My Cards">
        <CardStrip cards={cards} loading={loading} error={error} />
      </Section>

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-[360px_minmax(0,1fr)]">
        <Section title="Spending by Month">
          <Component />
        </Section>
        <Section title="Card List">
          {loading ? (
            <CardListLoad />
          ) : error ? (
            <Card>
              <EmptyState tone="error" message={error} />
            </Card>
          ) : (
            <CardList card_list={cards} />
          )}
        </Section>
      </div>

      {/* Same 3:2 split as Accounts. Add New Card was a fixed 600-800px box and
          Card Setting a fixed 335x470 one, so the row never lined up. */}
      <div className="grid grid-cols-1 gap-8 lg:grid-cols-[minmax(0,3fr)_minmax(0,2fr)]">
        <Section title="Add New Card">
          <AddNewCard />
        </Section>
        <Section title="Card Setting">
          <CardSetting />
        </Section>
      </div>
    </PageContainer>
  );
};

export default CreditCard;
