'use client';
import { Bar, BarChart, ResponsiveContainer, XAxis } from "recharts";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { useState, useEffect } from "react";
import { getExpenses, getIncomes } from "@/services/transactionfetch";
import type { Transaction } from "@/types/api";
import {
  ChartConfig, 
  ChartContainer, 
  ChartTooltip, 
  ChartTooltipContent
} from "@/components/ui/chart";

import { TbFileSad } from "react-icons/tb";

/** Static weekday skeleton; totals are filled in once the data arrives. */
const WEEKDAY_SKELETON = ["Sat", "Sun", "Mon", "Tue", "Wed", "Thu", "Fri"].map((day) => ({
  day,
  debit: 0,
  credit: 0,
}));

export default function Component() {
  const [bottomMargin, setBottomMargin] = useState(90);
  const [barSize, setBarSize] = useState(20);
  const [chartData, setChartData] = useState(WEEKDAY_SKELETON);
  const [status, setStatus] = useState<'loading' | 'error' | 'success'>('loading');

  useEffect(() => {
    const handleResize = () => {
      const width = window.innerWidth;
      if (width < 768) {
        setBottomMargin(20);
        setBarSize(10);
      } else if (width >= 768 && width < 1024) {
        setBottomMargin(30);
        setBarSize(15);
      } else {
        setBottomMargin(50);
        setBarSize(20);
      }
    };

    window.addEventListener("resize", handleResize);
    handleResize();
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  const getDayIndex = (day: string) => {
    const days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
    return days.indexOf(day);
  };

  useEffect(() => {
    const fetchTransactions = async () => {
      try {
        const expensesData = await getExpenses(0, 5); 
        const incomesData = await getIncomes(0, 5);

        const updatedChartData = WEEKDAY_SKELETON.map((dayData) => {
          const dayExpenses = expensesData.items.filter(
            ({ occurredAt }: Transaction) =>
              new Date(occurredAt).getDay() === getDayIndex(dayData.day)
          );
          const dayIncomes = incomesData.items.filter(
            ({ occurredAt }: Transaction) =>
              new Date(occurredAt).getDay() === getDayIndex(dayData.day)
          );                                

          return {
            ...dayData,
            debit: dayExpenses.reduce((sum: number, tx: Transaction) => sum + tx.amount, 0),
            credit: dayIncomes.reduce((sum: number, tx: Transaction) => sum + tx.amount, 0),
          };
        });

        setChartData(updatedChartData);
        setStatus('success');
      } catch (error) {
        console.error("Failed to fetch transactions", error);
        setStatus('error');
      }
    };

    fetchTransactions();
  }, []);

  const totalDebit = chartData.reduce((sum, data) => sum + data.debit, 0);
  const totalCredit = chartData.reduce((sum, data) => sum + data.credit, 0);

  const chartConfig = {
    debit: { color: "#1814F3" },
    credit: { color: "#FC7900" },
  } satisfies ChartConfig;

  if (status === 'loading') {
    return (
      <div className="w-full h-full bg-gray-200 rounded-lg animate-pulse">
</div>

    );
  }

  if (status === 'error') {
    return (
      <div className="p-3 gap-4  flex flex-col justify-center items-center h-auto  dark:bg-dark   text-center ">
        <TbFileSad
          className={`text-gray-300 dark:text-danger w-[400px] h-[70px] pb-2 block mx-auto`}
          strokeWidth={1}
        />
        <p className="text-red-500" >Failed to fetch</p>
      </div>
    );
  }

  return (
    <Card className="flex flex-col w-full h-full">
      <CardHeader className="flex justify-between p-4 pb-0">
        <div className="hidden md:flex text-sm font-normal">
          <span className="font-bold">${totalDebit}</span>&nbsp;Debited
          &nbsp;&&nbsp;
          <span className="font-bold">${totalCredit}</span>&nbsp;Credited in this Week
        </div>
        <div className="flex px-3 text-right">
          <span
            className="w-4 h-4 rounded-xl"
            style={{ backgroundColor: chartConfig.debit.color }}
          ></span>
          <span className="text-sm font-normal pl-2 pr-4">Debit</span>
          <span
            className="w-4 h-4 rounded-xl"
            style={{ backgroundColor: chartConfig.credit.color }}
          ></span>
          <span className="text-sm font-normal pl-2">Credit</span>
        </div>
      </CardHeader>
      <CardContent className="flex-1">
        {/* ChartContainer defaults to aspect-video, which at this panel's width
            forces a ~600px SVG and pushed the bars and the x-axis labels out
            through the bottom of the card. aspect-auto lets the plot fill the
            panel it is given instead. */}
        <ChartContainer config={chartConfig} className="p-0 aspect-auto h-full w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={chartData}
              barCategoryGap="10%"
              barGap={5}
              barSize={barSize}
              margin={{ top: 10, right: 20, left: 20, bottom: bottomMargin }}
            >
              <XAxis dataKey="day" axisLine={true} tickLine={false} />
              <ChartTooltip
                cursor={false}
                content={<ChartTooltipContent indicator="dashed" />}
              />
              <Bar
                dataKey="debit"
                fill={chartConfig.debit.color}
                radius={[5, 5, 0, 0]}
              />
              <Bar
                dataKey="credit"
                fill={chartConfig.credit.color}
                radius={[5, 5, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </ChartContainer>
      </CardContent>
    </Card>
  );
}
