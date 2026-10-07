"use client"
import { Cell, Pie, PieChart } from "recharts"
import {
  Card,
  CardContent,
} from "@/components/ui/card"
import {
  ChartConfig,
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart"

const chartData = [
  { category: "Entertainment", amount: 375, fill: "#6172F3" },
  { category: "Shopping", amount: 200, fill: "#FF8900" },
  { category: "Groceries", amount: 387, fill: "#EE46BC" },
  { category: "Bills", amount: 173, fill: "#2E90FA" },
]

const TOTAL = chartData.reduce((sum, row) => sum + row.amount, 0)

/**
 * Expense breakdown.
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
 *    matched to a category - the numbers were unreadable in practice.
 */
export default function Component() {
  return (
    <Card className="w-[100%] h-full flex flex-col">
      <CardContent className="flex-1 flex flex-col items-center justify-center gap-5 px-4 py-6">
        <ChartContainer className="mx-auto w-full max-w-[210px] aspect-square" config={{}}>
          <PieChart>
            <ChartTooltip content={<ChartTooltipContent nameKey="category" />} />
            <Pie
              data={chartData}
              dataKey="amount"
              nameKey="category"
              cx="50%"
              cy="50%"
              // Percentage-based so the ring scales with whatever panel it lands
              // in, rather than with the window.
              innerRadius="55%"
              outerRadius="88%"
              paddingAngle={2}
              strokeWidth={0}
            >
              {chartData.map((entry) => (
                <Cell key={entry.category} fill={entry.fill} />
              ))}
            </Pie>
          </PieChart>
        </ChartContainer>

        {/* Legend: without it the percentages cannot be attributed. Wrapped in a
            grid rather than a Recharts <Legend> so the labels align into tidy
            columns instead of drifting with the ring. */}
        <ul className="w-full grid grid-cols-2 gap-x-4 gap-y-2">
          {chartData.map((entry) => (
            <li key={entry.category} className="flex items-center gap-2 min-w-0">
              <span
                aria-hidden
                className="h-2.5 w-2.5 shrink-0 rounded-full"
                style={{ backgroundColor: entry.fill }}
              />
              <span className="truncate text-sm text-content-secondary">
                {entry.category}
              </span>
              <span className="ml-auto shrink-0 text-sm font-medium tabular-nums text-content-primary">
                {Math.round((entry.amount / TOTAL) * 100)}%
              </span>
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  )
}