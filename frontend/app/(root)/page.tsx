"use client";
import RecentTransaction from "@/components/Recent Transaction";
import BarChart from "@/components/BarChart";
import PieChart from "@/components/PieChart";
import QuickTransfer from "@/components/QuickTransfer";
import LineChart from "@/components/LineChart";
import PageContainer from "@/components/PageContainer";
import Section from "@/components/Section";
import CardStrip from "@/components/CardStrip";
import { useCards } from "@/hooks/useCards";

// Every row uses the same 3:2 split, so the right-hand column has one edge
// all the way down the page. On wide screens the left column never drops
// below the 716px two cards need, so neither card is cut off.
const ROW =
  "grid grid-cols-1 gap-8 lg:grid-cols-[minmax(0,3fr)_minmax(0,2fr)] min-[1360px]:grid-cols-[minmax(716px,3fr)_minmax(0,2fr)]";

const Page = () => {
  const { cards, error, loading } = useCards();

  return (
    <PageContainer>
      <div className={ROW}>
        <Section
          title="My Cards"
          action={{ href: "/credit-card", label: "See All" }}
        >
          <CardStrip cards={cards} loading={loading} error={error} limit={2} />
        </Section>
        <Section title="Recent Transaction">
          <RecentTransaction />
        </Section>
      </div>

      <div className={ROW}>
        <Section title="Weekly Activity">
          <div className="flex-1">
            <BarChart />
          </div>
        </Section>
        <Section title="Expense Statistics">
          <div className="flex-1">
            <PieChart />
          </div>
        </Section>
      </div>

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-[minmax(0,2fr)_minmax(0,3fr)]">
        <Section title="Quick Transfer">
          <div className="flex flex-1">
            <QuickTransfer />
          </div>
        </Section>
        <Section title="Balance History">
          <div className="flex-1">
            <LineChart />
          </div>
        </Section>
      </div>
    </PageContainer>
  );
};

export default Page;
