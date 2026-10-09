"use client"

import { useEffect, useState } from "react"
import { Bar, BarChart, CartesianGrid, Legend, XAxis, YAxis } from "recharts"
import { Card, CardContent } from "@/components/ui/card"
import {
  ChartConfig,
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart"
import { getCashflowByMonth } from "@/services/transactionfetch"
import type { CashflowPoint } from "@/types/api"

const chartConfig = {
  moneyIn: {
    label: "Money in",
    color: "#1814F3",
  },
  moneyOut: {
    label: "Money out",
    color: "#16DBCC",
  },
} satisfies ChartConfig

const MONTHS = [
  "Jan", "Feb", "Mar", "Apr", "May", "Jun",
  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]

/** `2026-04` -> `Apr`. */
function monthLabel(period: string) {
  const match = /^(\d{4})-(\d{2})$/.exec(period)
  if (!match) return period
  return MONTHS[Number(match[2]) - 1] ?? period
}

/**
 * Monthly cashflow.
 *
 * This rendered a fixed six-month array of "desktop"/"mobile" values that had no
 * relationship to anything - there is no desktop or mobile split anywhere in
 * the data model, and transactions are not scoped to a card at all.
 *
 * It now shows money in against money out per month, which is what the panel
 * was evidently reaching for and which the ledger can actually answer. The tick
 * labels also no longer use `value.slice(0, 3)`, which was written for month
 * names and would have cut a period like "2026-04" down to "202".
 */
export default function Component() {
  const [rows, setRows] = useState<CashflowPoint[] | null>(null)

  useEffect(() => {
    let cancelled = false
    getCashflowByMonth(6)
      .then((data) => {
        if (!cancelled) setRows(data)
      })
      .catch((error) => {
        console.error("Error fetching monthly cashflow:", error)
        if (!cancelled) setRows([])
      })
    return () => {
      cancelled = true
    }
  }, [])

  const data = (rows ?? []).map((row) => ({
    month: monthLabel(row.period),
    moneyIn: row.moneyIn,
    moneyOut: row.moneyOut,
  }))

  return (
    <Card className="flex h-full w-full flex-col">
      <CardContent className="w-full flex-1 p-0">
        {data.length === 0 ? (
          <p className="flex h-full items-center justify-center p-6 text-sm text-content-muted">
            No activity in this period.
          </p>
        ) : (
          <ChartContainer className="aspect-auto h-full w-full" config={chartConfig}>
            <BarChart accessibilityLayer barSize={10} data={data}>
              <CartesianGrid vertical={false} />
              <XAxis
                dataKey="month"
                tickLine={false}
                tickMargin={10}
                axisLine={true}
              />
              <YAxis axisLine={true} tickLine={false} />
              <ChartTooltip
                cursor={false}
                content={<ChartTooltipContent indicator="dashed" />}
              />
              <Legend
                verticalAlign="top"
                align="right"
                formatter={(value: string) =>
                  chartConfig[value as keyof typeof chartConfig]?.label ?? value
                }
              />
              <Bar dataKey="moneyIn" fill={chartConfig.moneyIn.color} radius={[10, 10, 10, 10]} />
              <Bar dataKey="moneyOut" fill={chartConfig.moneyOut.color} radius={[10, 10, 10, 10]} />
            </BarChart>
          </ChartContainer>
        )}
      </CardContent>
    </Card>
  )
}