"use client"

import { Bar, BarChart, CartesianGrid, LabelList, XAxis, YAxis } from "recharts"
import {
  ChartConfig,
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart"

export const description = "A bar chart with a custom label"

import { useEffect, useState } from "react"

type ChartData = {
  classificacao: string
  valor: number
}

const chartConfig = {
  desktop: {
    label: "Desktop",
    color: "var(--chart-2)",
  },
  mobile: {
    label: "Mobile",
    color: "var(--chart-2)",
  },
  label: {
    color: "var(--background)",
  },
} satisfies ChartConfig

// Recebe dados de custos via props (já processados pelo componente pai)
export function ChartCustosFinanceiro({ data }: { data?: Record<string, number> }) {
  const [chartData, setChartData] = useState<ChartData[]>([])

  useEffect(() => {
    if (data) {
      // Processar dados recebidos do pai
      const arr = Object.entries(data)
        .map(([classificacao, valor]) => ({ classificacao, valor }))
        .sort((a, b) => b.valor - a.valor)
      setChartData(arr)
    } else {
      // Se não receber dados, exibir array vazio
      setChartData([])
    }
  }, [data])

  if (!data) return <div>Carregando dados...</div>
  if (!chartData.length) return <div>Nenhum dado para exibir.</div>

  return (
    <ChartContainer config={chartConfig}>
      <BarChart
        accessibilityLayer
        data={chartData}
        layout="vertical"
        margin={{ right: 16 }}
      >
        <CartesianGrid horizontal={false} />
        <YAxis
          dataKey="classificacao"
          type="category"
          tick={false}
          tickLine={false}
          tickMargin={10}
          axisLine={false}
          interval={0}
          reversed
        />
        <XAxis dataKey="valor" type="number" hide />
        <ChartTooltip
          cursor={false}
          content={<ChartTooltipContent indicator="line" />}
        />
        <Bar
          dataKey="valor"
          layout="vertical"
          fill="var(--color-desktop)"
          radius={4}
        >
          <LabelList
                dataKey="classificacao"
                position="insideLeft"
                offset={8}
                className="fill-(--color-foreground/20)"
                fontSize={10}
                width={400}
              />
        </Bar>
      </BarChart>
    </ChartContainer>
  )
}