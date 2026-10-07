"use client";
import { useState, useEffect } from "react";
import BalanceCards from "@/components/AccountSmallCard";
import LastTransactionCard from "@/components/LastTransactionCard";
import InvoicesCard from "@/components/InvoicesCard";
import AccountBarChart from "@/components/AccountBarChart";
import Link from "next/link";
import ResponsiveCreditCard from "@/components/CreditCard";
import { getAllCards } from "@/services/cardfetch";
import type { Card } from "@/types/api";
import { TbFileSad } from "react-icons/tb";
import MyCardsLoad from "@/components/loadingComponents/MyCardsLoad";
import CurrencyConverter from "@/components/CurrencyConverter";
import PageContainer from "@/components/PageContainer";

const Accounts = () => {
  const [cards, setCards] = useState<Card[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    const fetchCards = async () => {
      try {
        const { items } = await getAllCards(0, 20);
        if (!cancelled) {
          setCards(items.slice(0, 1));
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
    <PageContainer>
        {/* Top Section */}
        <div className="mb-8">
          <h1 className="text-2xl font-semibold mb-6 dark:text-brand">
            Accounts
          </h1>
          {/* <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-8"> */}
          <BalanceCards />
          {/* </div> */}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-[minmax(0,1fr)_350px] gap-4 sm:gap-6 mb-8">
          <div className="flex flex-col">
            <h2 className="text-lg font-semibold mb-3 dark:text-brand">
              Last Transaction
            </h2>
            <div>
              <LastTransactionCard />
            </div>
          </div>
          <div className="flex flex-col h-full">
            <div className="mb-3 flex justify-between items-center text-lg font-semibold">
              <h2 className="dark:text-brand">My Card</h2>
              <Link
                href="/credit-card"
                className="font-normal self-end dark:text-brand"
              >
                See All
              </Link>
            </div>
            <div className="flex flex-1 items-stretch">
              {loading ? (
                <MyCardsLoad count={1} />
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
                    className={`text-gray-300 dark:text-danger w-[80px] h-[80px] pb-2 block mx-auto font-thin`}
                    strokeWidth={1}
                  />

                  <span className="mx-auto my-auto md:text-xl text-sm text-[#993d4b] mb-5">
                    {error ? error : "There are no cards for now!"}
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Bottom Section */}
        <div className="grid grid-cols-1 lg:grid-cols-[minmax(0,1fr)_350px] gap-4 sm:gap-6 mt-8">
          <div className="flex flex-col">
            <h2 className="text-lg font-semibold mb-4 dark:text-brand">
              Debit & Credit Overview
            </h2>
            <div className="h-[360px]">
              <AccountBarChart />
            </div>
          </div>
          <div className="flex flex-col h-full">
            <h2 className="text-lg font-semibold mb-4">Invoices Sent</h2>
            <div className="h-fit ">
              <InvoicesCard />
            </div>
            {/* <h2 className="text-lg font-semibold mb-4">Currency Converter</h2> */}
            {/* <div className="py-10 ">
              <h2 className="text-lg font-semibold mt-2 py-4">
                Currency Converter
              </h2>
              <CurrencyConverter />
            </div> */}
          </div>
        </div>
    </PageContainer>
  );
};

export default Accounts;

// "use client";
// import { useState, useEffect } from "react";
// import BalanceCard from "@/components/AccountSmallCard";
// import LastTransactionCard from "@/components/LastTransactionCard";
// import InvoicesCard from "@/components/InvoicesCard";
// import AccountBarChart from "@/components/AccountBarChart";
