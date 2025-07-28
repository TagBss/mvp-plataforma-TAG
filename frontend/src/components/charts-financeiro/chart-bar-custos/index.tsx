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
import { formatCurrencyShort } from "../../kpis-competencia"

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
    if (data && Object.keys(data).length > 0) {
      // Processar dados recebidos do pai
      const arr = Object.entries(data)
        .map(([classificacao, valor]) => ({ classificacao, valor }))
        .filter(item => item.valor > 0) // Filtrar valores zero
        .sort((a, b) => a.valor - b.valor) // Ordenar por valor crescente (melhor para maior)
      
      setChartData(arr)
    } else {
      // Se não receber dados, exibir array vazio
      setChartData([])
    }
  }, [data])

  if (!data || Object.keys(data).length === 0) {
    return (
      <div className="flex items-center justify-center h-24 text-muted-foreground">
        <p>Nenhum dado de custos disponível</p>
      </div>
    )
  }
  
  if (!chartData.length) {
    return (
      <div className="flex items-center justify-center h-24 text-muted-foreground">
        <p>Carregando dados de custos...</p>
      </div>
    )
  }

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
        <XAxis 
                  dataKey="valor" 
                  type="number" 
                  tickFormatter={(v) => formatCurrencyShort(v, { noPrefix: true })}
                  tickLine={false}
                  axisLine={false}
                />
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