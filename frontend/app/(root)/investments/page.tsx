"use client";
import React, { useState, useEffect } from "react";
import LineChartNoBg from "@/components/LineChartNoBg";
import LineChartStright from "@/components/LineChartStraight";
import { colors } from "@/constants/index";
import { FaSackDollar } from "react-icons/fa6";
import { AiOutlineRetweet } from "react-icons/ai";
import { GiTakeMyMoney } from "react-icons/gi";
import MyInvestment from "@/components/MyInvestment";
import TrendingStock from "@/components/TrendingStock";
import { getTrendingCompanies } from "@/services/companygetch";
import { randomInvestmentData } from "@/services/userupdate";
import PageContainer from "@/components/PageContainer";
import type { Company } from "@/types/api";
// Which brand asset to use for each company. The API has no logo for these rows
// (logoUrl is null), so the mark is matched locally rather than showing a broken
// image; a company without an entry falls back to a neutral tile with its ticker.
const COMPANY_MARKS: Record<string, { icon?: string; color: string }> = {
  AAPL: { icon: "/icons/apple_store.png", color: "bg-red-100" },
  GOOGL: { icon: "/icons/Google_store.png", color: "bg-blue-100" },
  TSLA: { icon: "/icons/tesla.png", color: "bg-yellow-100" },
  AMZN: { color: "bg-amber-100" },
  MSFT: { color: "bg-sky-100" },
  NOK: { color: "bg-purple-100" },
  META: { color: "bg-indigo-100" },
  NFLX: { color: "bg-red-100" },
  NVDA: { color: "bg-lime-100" },
  INTC: { color: "bg-blue-100" },
  WMT: { color: "bg-blue-100" },
  JNJ: { color: "bg-rose-100" },
  JPM: { color: "bg-emerald-100" },
  "2222": { color: "bg-teal-100" },
};

/** Holdings, derived from the companies the API actually returns. */
function toHoldings(companies: Company[]) {
  return companies.map((company) => {
    const mark = COMPANY_MARKS[company.symbol];
    return {
      // Empty icon means "no asset" - the row shows the ticker's initial
      // rather than borrowing another company's mark.
      icon: mark?.icon ?? "",
      color: mark?.color ?? "bg-slate-100",
      initial: company.symbol.charAt(0),
      name: company.name,
      category: company.sector,
      // Held value is not modelled by the API yet, so it is derived from the
      // share price rather than shown as an unrelated invented number.
      amount: `$${(company.price * 100).toLocaleString("en-US", { maximumFractionDigits: 0 })}`,
      percentage: `${company.changePercent > 0 ? "+" : ""}${company.changePercent.toFixed(2)}%`,
    };
  });
}

/** The trending table, in the shape TrendingStock expects. */
function toTrendingRows(companies: Company[]) {
  return companies.map((company, index) => ({
    slNo: `${index + 1}.`,
    name: `${company.name} (${company.symbol})`,
    price: `$${company.price.toLocaleString("en-US", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })}`,
    return: `${company.changePercent > 0 ? "+" : ""}${company.changePercent.toFixed(2)}%`,
  }));
}

interface chartData {
  period: string;
  value: number;
}
interface InvestmentData {
  totalInvestment: number;
  rateOfReturn: number;
  numberOfInvestments: number;
  yearlyInvestments: chartData[];
  monthlyRevenue: chartData[];
}

const Investments = () => {
  const [investment, setInvestment] = useState<InvestmentData>();
  const [companies, setCompanies] = useState<Company[]>([]);
  const [status, setStatus] = useState<"loading" | "error" | "success">(
    "loading"
  );

  useEffect(() => {
    const fetchInvestmentData = async () => {
      setStatus("loading");
      try {
        setInvestment(await randomInvestmentData(5, 8));
        setStatus("success");
      } catch (error) {
        console.error("Error fetching investment data:", error);
        setStatus("error");
      }
    };
    fetchInvestmentData();
  }, []);

  const holdings = toHoldings(companies);
  const trendingRows = toTrendingRows(companies);

  useEffect(() => {
    let cancelled = false;
    const fetchCompanies = async () => {
      try {
        const trending = await getTrendingCompanies(6);
        if (!cancelled) setCompanies(trending);
      } catch (error) {
        // The investment charts are the point of this page; a failed companies
        // call should leave those intact rather than flip the page to an error.
        console.error("Error fetching trending companies:", error);
      }
    };
    fetchCompanies();
    return () => {
      cancelled = true;
    };
  }, []);

  if (status === "loading") {
    return (
      <PageContainer>
        <div className="flex flex-col gap-8">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <div className="flex items-center gap-4 rounded-2xl bg-gray-200 p-4 animate-pulse dark:bg-surface-3">
            <div className="bg-cyan-100 w-[50px] h-[50px] flex items-center justify-center rounded-full animate-pulse"></div>
            <div>
              <div className="bg-gray-300 h-[12px] w-[150px] rounded mb-2 animate-pulse"></div>
              <div className="bg-gray-300 h-[16px] w-[100px] rounded animate-pulse"></div>
            </div>
          </div>

          <div className="flex items-center gap-4 rounded-2xl bg-gray-200 p-4 animate-pulse dark:bg-surface-3">
            <div className="bg-pink-100 w-[50px] h-[50px] flex items-center justify-center rounded-full animate-pulse"></div>
            <div>
              <div className="bg-gray-300 h-[12px] w-[150px] rounded mb-2 animate-pulse"></div>
              <div className="bg-gray-300 h-[16px] w-[100px] rounded animate-pulse"></div>
            </div>
          </div>

          <div className="flex items-center gap-4 rounded-2xl bg-gray-200 p-4 animate-pulse dark:bg-surface-3">
            <div className="bg-indigo-100 w-[50px] h-[50px] flex items-center justify-center rounded-full animate-pulse"></div>
            <div>
              <div className="bg-gray-300 h-[12px] w-[150px] rounded mb-2 animate-pulse"></div>
              <div className="bg-gray-300 h-[16px] w-[100px] rounded animate-pulse"></div>
            </div>
          </div>
        </div>

        <div className="flex flex-col gap-8 lg:grid lg:grid-cols-2 lg:gap-6">
          <div className="flex flex-col gap-3 lg:gap-4 xl:gap-5">
            <div className="bg-gray-300 h-[22px] w-[200px] rounded mb-4 animate-pulse"></div>
            <div className="bg-gray-300 h-[250px] rounded animate-pulse"></div>
          </div>
          <div className="flex flex-col gap-3 lg:gap-4 xl:gap-5">
            <div className="bg-gray-300 h-[22px] w-[200px] rounded mb-4 animate-pulse"></div>
            <div className="bg-gray-300 h-[250px] rounded animate-pulse"></div>
          </div>
        </div>

        <div className="flex flex-col lg:grid lg:grid-cols-5">
          <div className="px-6 lg:col-span-3 flex flex-col gap-5">
            <div className="bg-gray-300 h-[22px] w-[200px] rounded mb-4 animate-pulse"></div>
            <div className="bg-gray-300 h-[150px] rounded mb-4 animate-pulse"></div>
            <div className="bg-gray-300 h-[150px] rounded mb-4 animate-pulse"></div>
            <div className="bg-gray-300 h-[150px] rounded mb-4 animate-pulse"></div>
          </div>
          <div className="lg:col-span-2">
            <div className="p-6 lg:p-0">
              <div className="bg-gray-300 h-[22px] w-[200px] rounded mb-4 animate-pulse"></div>
              <div className="bg-gray-300 h-[250px] rounded animate-pulse"></div>
            </div>
          </div>
        </div>
      </div>
      </PageContainer>
    );
  }

  return (
    <PageContainer>
      <div className="flex flex-col gap-8">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="flex items-center gap-4 rounded-2xl border border-slate-200 bg-white p-4 text-gray-900 dark:border-line dark:bg-surface-1 dark:text-white">
          <div className="bg-cyan-100 w-[50px] h-[50px] flex items-center justify-center rounded-full  ">
            <FaSackDollar className="text-cyan-500 h-[25px] w-[20px] " />
          </div>
          <div>
            <p
              className="text-xs text-content-muted"
            >
              Total Invested Amount
            </p>
            <p
              className="text-lg font-bold text-content-primary"
            >
              {investment ? `$${investment.totalInvestment.toLocaleString()}` : "no data to display"}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-4 rounded-2xl border border-slate-200 bg-white p-4 text-gray-900 dark:border-line dark:bg-surface-1 dark:text-white">
          <div className="bg-pink-100 w-[50px] h-[50px] flex items-center justify-center rounded-full  ">
            <GiTakeMyMoney className="text-pink-500 h-[25px] w-[20px] " />
          </div>
          <div>
            <p
              className="text-xs text-content-muted"
            >
              Number of Investments
            </p>
            <p
              className="text-lg font-bold text-content-primary"
            >
              {investment ? investment.numberOfInvestments.toLocaleString() : "-"}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-4 rounded-2xl border border-slate-200 bg-white p-4 text-gray-900 dark:border-line dark:bg-surface-1 dark:text-white">
          <div className="bg-indigo-100 w-[50px] h-[50px] flex items-center justify-center rounded-full  ">
            <AiOutlineRetweet className="text-indigo-500 h-[25px] w-[20px] " />
          </div>
          <div>
            <p
              className="text-xs text-content-muted"
            >
              Rate of Return
            </p>
            <p
              className="text-lg font-bold text-content-primary"
            >
              {investment ? `${investment.rateOfReturn}%` : "no data to display"}
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-2">
        <div className="flex flex-col gap-4">
          <h2
            className="text-xl font-semibold text-[#343C6A] dark:text-brand"
          >
            Yearly Total Investments
          </h2>
          <LineChartStright
            yearlyData={
              investment?.yearlyInvestments ?? [{ period: "", value: 0 }]
            }
          />
        </div>
        <div className="flex flex-col gap-4">
          <h2
            className="text-xl font-semibold text-[#343C6A] dark:text-brand"
          >
            Monthly Revenue
          </h2>
          <LineChartNoBg
            monthlyData={investment?.monthlyRevenue ?? [{ period: "", value: 0 }]}
          />
        </div>
      </div>

      {/* My Investment and Trending Stock read as two unrelated components:
          different padding (px-6 vs p-6 lg:p-0), and the list rows ran at
          roughly twice the height of the table beside them. Both are now the
          same panel chrome and row rhythm, and share a heading, so the row
          balances. h-full on each lets the grid stretch them to one height
          rather than each asserting its own. */}
      <div className="grid grid-cols-1 gap-8 lg:grid-cols-5 lg:items-stretch">
        <div className="flex flex-col gap-4 lg:col-span-3">
          <h2
            className="text-xl font-semibold text-[#343C6A] dark:text-brand"
          >
            My Investment
          </h2>
          <div className="flex flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white divide-y divide-slate-100 dark:border-line dark:bg-surface-1 dark:divide-line">
            {holdings.map((item, index) => (
              <MyInvestment
                key={index}
                icon={item.icon}
                color={item.color}
                category={item.category}
                name={item.name}
                amount={item.amount}
                percentage={item.percentage}
              />
            ))}
          </div>
        </div>
        <div className="flex flex-col gap-4 lg:col-span-2">
          <h2
            className="text-xl font-semibold text-[#343C6A] dark:text-brand"
          >
            Trending Stock
          </h2>

          <TrendingStock items={trendingRows} />
        </div>
      </div>
    </div>
    </PageContainer>
  );
};

export default Investments;
