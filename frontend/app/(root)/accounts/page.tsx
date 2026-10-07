"use client";
import BalanceCards from "@/components/AccountSmallCard";
import LastTransactionCard from "@/components/LastTransactionCard";
import InvoicesCard from "@/components/InvoicesCard";
import AccountBarChart from "@/components/AccountBarChart";
import PageContainer from "@/components/PageContainer";
import Section from "@/components/Section";
import CardStrip from "@/components/CardStrip";
import { useCards } from "@/hooks/useCards";

// Both rows share one 3:2 template. The right column used to be a fixed 350px
// beside a full-width left one, so Last Transaction sprawled while My Card and
// Invoices looked squeezed.
const ROW = "grid grid-cols-1 gap-8 lg:grid-cols-[minmax(0,3fr)_minmax(0,2fr)]";

const Accounts = () => {
  const { cards, error, loading } = useCards();

  return (
    <PageContainer>
      <BalanceCards />

      <div className={ROW}>
        <Section title="Last Transaction">
          <LastTransactionCard />
        </Section>
        <Section title="My Card" action={{ href: "/credit-card", label: "See All" }}>
          <CardStrip cards={cards} loading={loading} error={error} limit={1} />
        </Section>
      </div>

      <div className={ROW}>
        <Section title="Debit & Credit Overview">
          <div className="h-[360px]">
            <AccountBarChart />
          </div>
        </Section>
        <Section title="Invoices Sent">
          <InvoicesCard />
        </Section>
      </div>
    </PageContainer>
  );
};

export default Accounts;
