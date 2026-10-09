"use client"

import * as React from "react"
import { Label, Legend, Pie, PieChart, Sector } from "recharts"
import { Card, CardContent } from "@/components/ui/card"
import {
  ChartConfig,
  ChartContainer,
  ChartStyle,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart"
import { getSpendByMonth } from "@/services/transactionfetch"
import type { SeriesPoint } from "@/types/api"

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

const SLICE_COLORS = [
  "#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0", "#9966FF", "#546CE3", "#F79009",
]

const chartConfig = {
  value: {
    label: "Spend",
  },
} satisfies ChartConfig

/**
 * Monthly spending breakdown.
 *
 * This rendered five fixed months of invented values (january 186, february
 * 305, ...) with a "desktop"/"mobile"/"visitors" legend inherited from a
 * Recharts example that never applied to this data.
 *
 * Transactions are not linked to a card anywhere in the schema, so a genuine
 * per-card breakdown is not derivable - the panel is labelled "Spending by
 * month" rather than claiming a card split it cannot produce.
 */
export default function Component() {
  const id = "pie-interactive"
  const [activeIndex, setActiveIndex] = React.useState(0)
  const [points, setPoints] = React.useState<SeriesPoint[] | null>(null)

  React.useEffect(() => {
    let cancelled = false
    getSpendByMonth(6)
      .then((data) => {
        if (!cancelled) setPoints(data)
      })
      .catch((error) => {
        console.error("Error fetching monthly spend:", error)
        if (!cancelled) setPoints([])
      })
    return () => {
      cancelled = true
    }
  }, [])

  const rows = React.useMemo(
    () =>
      (points ?? [])
        .filter((point) => point.value > 0)
        .map((point, index) => ({
          month: monthLabel(point.period),
          value: point.value,
          fill: SLICE_COLORS[index % SLICE_COLORS.length],
        })),
    [points]
  )

  const total = rows.reduce((sum, row) => sum + row.value, 0)

  if (points !== null && rows.length === 0) {
    return (
      <Card data-chart={id} className="flex flex-col rounded-3xl">
        <CardContent className="flex flex-1 items-center justify-center p-8">
          <p className="text-sm text-content-muted">No spending in this period.</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card data-chart={id} className="flex flex-col rounded-3xl">
      <ChartStyle id={id} config={chartConfig} />
      <CardContent className="flex flex-1 justify-center pb-0">
        <ChartContainer
          id={id}
          config={chartConfig}
          className="mx-auto aspect-square w-full max-w-[300px]"
        >
          <PieChart>
            <ChartTooltip
              cursor={false}
              content={<ChartTooltipContent hideLabel />}
            />
            <Pie
              data={rows}
              dataKey="value"
              nameKey="month"
              innerRadius={60}
              strokeWidth={5}
              activeIndex={activeIndex}
              onMouseEnter={(_, index) => setActiveIndex(index)}
              className="dark:text-white"
              activeShape={({ outerRadius = 0, ...props }: any) => (
                <g {...props}>
                  <Sector {...props} outerRadius={outerRadius + 10} />
                  <Sector
                    {...props}
                    outerRadius={outerRadius + 25}
                    innerRadius={outerRadius + 12}
                  />
                </g>
              )}
            >
              <Label
                content={({ viewBox }) => {
                  if (viewBox && "cx" in viewBox && "cy" in viewBox) {
                    const row = rows[activeIndex]
                    return (
                      <text
                        x={viewBox.cx}
                        y={viewBox.cy}
                        textAnchor="middle"
                        dominantBaseline="middle"
                        className="dark:text-white]"
                      >
                        <tspan
                          x={viewBox.cx}
                          y={viewBox.cy}
                          className="fill-content-primary text-3xl font-bold"
                        >
                          {row ? row.value.toLocaleString() : total.toLocaleString()}
                        </tspan>
                        <tspan
                          x={viewBox.cx}
                          y={(viewBox.cy || 0) + 24}
                          className="fill-content-muted"
                        >
                          {row ? row.month : "total"}
                        </tspan>
                      </text>
                    )
                  }
                }}
              />
            </Pie>
            <Legend
              layout="horizontal"
              verticalAlign="bottom"
              align="center"
              iconType="circle"
              iconSize={8}
              formatter={(value: string) => value}
              className="text-xs text-content-secondary"
            />
          </PieChart>
        </ChartContainer>
      </CardContent>
    </Card>
  )
}