"use client"
import { useEffect, useMemo, useState } from "react"
import { Cell, Pie, PieChart } from "recharts"
import { Card, CardContent } from "@/components/ui/card"
import {
  ChartConfig,
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart"
import { getSpendByCategory } from "@/services/transactionfetch"
import type { CategoryTotal } from "@/types/api"

/**
 * Spend breakdown.
 *
 * Three things were wrong with the original:
 *
 * 1. The responsive breakpoints were in the wrong order. `>= 768` was tested
 *    first, so it matched on every desktop width and the later branches were
 *    unreachable - the pie rendered at its smallest radius (60) on the largest
 *    screens, which is the opposite of the intent.
 * 2. It sized from `window.innerWidth`, so the chart ignored the panel it was
 *    actually in. The panel is now `h-full` alongside a taller bar chart, and a
 *    window-based radius left it floating in empty space.
 * 3. There was no legend, so a coloured slice showing "33%" could not be
 *    matched to a category - the percentages were unreadable in practice.
 *
 * The figures come from GET /transactions/summary/categories, which groups the
 * signed-in user's own transactions by category in SQL. It previously rendered
 * four invented slices (Entertainment 375, Shopping 200, ...) that had no
 * relationship to the account being viewed.
 */
const PALETTE = [
  "#546CE3", // brand
  "#FF8900",
  "#EE46BC",
  "#2E90FA",
  "#16DBCC",
  "#F04438",
  "#7A5AF8",
  "#F79009",
]

const SLICE_COUNT = 5

export default function Component() {
  const [rows, setRows] = useState<CategoryTotal[] | null>(null)

  useEffect(() => {
    let cancelled = false
    getSpendByCategory(12)
      .then((data) => {
        if (!cancelled) setRows(data)
      })
      .catch((error) => {
        console.error("Error fetching spend by category:", error)
        if (!cancelled) setRows([])
      })
    return () => {
      cancelled = true
    }
  }, [])

  const { slices, total } = useMemo(() => {
    // Transfers move the user's own money between accounts; counting them as
    // "spend" would overstate it, so the backend already excludes them.
    const usable = (rows ?? []).filter((row) => row.total > 0)
    const top = usable.slice(0, SLICE_COUNT)
    const rest = usable.slice(SLICE_COUNT)
    const restTotal = rest.reduce((sum, row) => sum + row.total, 0)

    const slices = top.map((row, index) => ({
      category: row.category,
      amount: row.total,
      fill: PALETTE[index % PALETTE.length],
    }))

    // Everything past the top N is folded into one slice rather than dropped,
    // so the ring still accounts for the whole month's spending.
    if (restTotal > 0) {
      slices.push({
        category: "Other",
        amount: restTotal,
        fill: PALETTE[slices.length % PALETTE.length],
      })
    }

    return {
      slices,
      total: slices.reduce((sum, slice) => sum + slice.amount, 0),
    }
  }, [rows])

  const percent = (amount: number) =>
    total > 0 ? Math.round((amount / total) * 100) : 0

  return (
    <Card className="flex h-full w-full flex-col">
      <CardContent className="flex flex-1 flex-col items-center justify-center gap-5 px-4 py-6">
        {slices.length === 0 ? (
          <p className="text-sm text-content-muted">No spending in this period.</p>
        ) : (
          <>
            <ChartContainer
              className="mx-auto aspect-square w-full max-w-[210px]"
              config={{}}
            >
              <PieChart accessibilityLayer>
                <ChartTooltip
                  content={<ChartTooltipContent nameKey="category" />}
                />
                <Pie
                  data={slices}
                  dataKey="amount"
                  nameKey="category"
                  cx="50%"
                  cy="50%"
                  // Percentage-based so the ring scales with whatever panel it
                  // lands in, rather than with the window.
                  innerRadius="55%"
                  outerRadius="88%"
                  paddingAngle={2}
                  strokeWidth={0}
                >
                  {slices.map((entry) => (
                    <Cell key={entry.category} fill={entry.fill} />
                  ))}
                </Pie>
              </PieChart>
            </ChartContainer>

            {/* Wrapped in a grid rather than a Recharts <Legend> so the labels
                align into tidy columns instead of drifting with the ring. */}
            <ul className="grid w-full grid-cols-2 gap-x-4 gap-y-2">
              {slices.map((slice) => (
                <li
                  key={slice.category}
                  className="flex min-w-0 items-center gap-2"
                >
                  <span
                    aria-hidden
                    className="h-2.5 w-2.5 shrink-0 rounded-full"
                    style={{ backgroundColor: slice.fill }}
                  />
                  <span className="truncate text-sm text-content-secondary">
                    {slice.category}
                  </span>
                  <span className="ml-auto shrink-0 text-sm font-medium tabular-nums text-content-primary">
                    {percent(slice.amount)}%
                  </span>
                </li>
              ))}
            </ul>
          </>
        )}
      </CardContent>
    </Card>
  )
}