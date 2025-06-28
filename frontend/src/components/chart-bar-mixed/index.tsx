"use client"

import { Bar, BarChart, XAxis, YAxis } from "recharts"

import {
  ChartConfig,
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart"

export const description = "A mixed bar chart"

const chartData = [
  { browser: "chrome", visitors: 275, fill: "var(--color-chrome)" },
  { browser: "safari", visitors: 200, fill: "var(--color-safari)" },
  { browser: "firefox", visitors: 187, fill: "var(--color-firefox)" },
  { browser: "edge", visitors: 173, fill: "var(--color-edge)" },
  { browser: "other", visitors: 90, fill: "var(--color-other)" },
]

const chartConfig = {
  visitors: {
    label: "Visitors",
  },
  chrome: {
    label: "Cost A",
    color: "var(--chart-1)",
  },
  safari: {
    label: "Cost B",
    color: "var(--chart-2)",
  },
  firefox: {
    label: "Cost C",
    color: "var(--chart-3)",
  },
  edge: {
    label: "Cost D",
    color: "var(--chart-4)",
  },
  other: {
    label: "Other",
    color: "var(--chart-5)",
  },
} satisfies ChartConfig

export function ChartBarMixed() {
  return (
    <ChartContainer config={chartConfig} className="min-h-[200px] w-full">
        <BarChart
        accessibilityLayer
        data={chartData}
        layout="vertical"
        margin={{
            left: 0,
        }}
        >
        <YAxis
            dataKey="browser"
            type="category"
            tickLine={false}
            tickMargin={10}
            axisLine={false}
            tickFormatter={(value) =>
            chartConfig[value as keyof typeof chartConfig]?.label
            }
        />
        <XAxis dataKey="visitors" type="number" hide />
        <ChartTooltip
            cursor={false}
            content={<ChartTooltipContent hideLabel />}
        />
        <Bar dataKey="visitors" layout="vertical" radius={5} />
        </BarChart>
    </ChartContainer>
  )
}
