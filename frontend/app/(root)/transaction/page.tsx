"use client";

import React, { Suspense, useEffect, useState } from "react";
import RecentTransactions from "@/components/RecentTransaction";
import ExpensesChart from "@/components/ExpensesCart";
import SlidingCards from "@/components/SlidingCards"; // Import the sliding cards component
import { getAllCards } from "@/services/cardfetch";
import type { Card } from "@/types/api";
import Image from "next/image";
import MyCardsLoad from "@/components/loadingComponents/MyCardsLoad";
import ResponsiveCreditCard from "@/components/CreditCard";
import { TbFileSad } from "react-icons/tb";
import PageContainer from "@/components/PageContainer";

const Transaction: React.FC = () => {
  const [cards, setCards] = useState<Card[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    const fetchCards = async () => {
      try {
        const { items } = await getAllCards(0, 20);
        if (!cancelled) {
          setCards(items.slice(0, 2));
          setError(null);
        }
      } catch {
        if (!cancelled) setError("Failed to fetch cards data!");
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    fetchCards();
    return () => { cancelled = true; };
  }, []);
  return (
    <PageContainer className="pt-6">
      {/* Large Screens Layout. "My Cards" carried mb-4 and "My Expenses" carried a
          pl-8 indent, so the two headings sat at different heights and the chart
          was pushed off its column's left edge. Both headings now share the same
          rhythm and the chart sits in a panel of the same height as the cards. */}
      <div className="hidden lg:grid lg:grid-cols-2 lg:gap-8 lg:pb-8">
        {/* Cards Section */}
        <div className="flex flex-col">
          <h1 className="mb-4 text-2xl font-bold dark:text-brand">
            My Cards
          </h1>
          <div className="w-full overflow-x-auto">
            {loading ? (
              <MyCardsLoad count={2} />
            ) : Array.isArray(cards) && cards.length > 0 ? (
              <div className="flex gap-4 pb-2">
                {cards.map((card: any, index: number) => (
                  <div key={index} className="shrink-0">
                    <ResponsiveCreditCard
                      tone={(index % 3 === 0 ? "brand" : index % 3 === 1 ? "midnight" : "light")}
                      balance={card.balance}
                      cardHolder={card.cardHolder}
                      expiryDate={card.expiryDate}
                      maskedNumber={card.maskedNumber}
                    />
                  </div>
                ))}
              </div>
            ) : (
              <div className="flex flex-col justify-center rounded-xl bg-white py-16 dark:bg-surface-1">
                <TbFileSad
                  className="mx-auto block h-[70px] w-[400px] pb-2 text-gray-300 dark:text-danger"
                  strokeWidth={1}
                />
                <span className="mx-auto my-auto text-sm md:text-xl">
                  {error ? error : "There are no cards for now!"}
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Chart Section */}
        <div className="flex flex-col">
          <h1 className="mb-4 text-2xl font-bold dark:text-brand">
            My Expenses
          </h1>

          <div className="flex-1 rounded-2xl border border-slate-200 bg-white p-5 dark:border-line dark:bg-surface-1">
            <ExpensesChart />
          </div>
        </div>
      </div>

      {/* Mobile Layout */}
      <div className="lg:hidden pt-10">
        <h1 className="text-2xl font-bold mb-4 dark:text-brand">My Cards</h1>
        {loading ? (
          <MyCardsLoad count={2}/>
        ) : Array.isArray(cards) && cards.length > 0 ? (
          cards.map((card: any, index: number) => (
            <div key={index} className="p-1 flex gap-1">
              <ResponsiveCreditCard
                tone={(index % 3 === 0 ? "brand" : index % 3 === 1 ? "midnight" : "light")}
                balance={card.balance}
                cardHolder={card.cardHolder}
                expiryDate={card.expiryDate}
                maskedNumber={card.maskedNumber}
              />
            </div>
          ))
        ) : (
          <div className="w-screen bg-white py-16 rounded-xl flex flex-col justify-center dark:bg-dark dark:border-[1px] dark:border-line">
            <TbFileSad
              className={`text-gray-300 dark:text-danger w-[400px] h-[70px] pb-2 block mx-auto`}
              strokeWidth={1}
            />
            <span className="mx-auto my-auto md:text-xl text-sm text-[#993d4b] mb-5">
              {error ? error : "There are no cards for now!"}
            </span>
          </div>
              )}
        <h1 className="text-2xl font-bold mb-4 dark:text-brand">
          My Expenses
        </h1>
        <div className="w-full">
          <ExpensesChart />
        </div>
      </div>

      {/* Recent Transactions Section */}
      <div>
        <h1 className="mb-4 text-2xl font-bold dark:text-brand">
          Recent Transactions
        </h1>

        <RecentTransactions />
      </div>
    </PageContainer>
  );
};

export default Transaction;
