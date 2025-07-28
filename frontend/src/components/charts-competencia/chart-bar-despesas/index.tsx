"use client"

import { Bar, BarChart, CartesianGrid, LabelList, XAxis, YAxis } from "recharts"
import {
  ChartConfig,
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart"

import { formatCurrencyShort } from "../../kpis-competencia"

export type ChartBarDespesasData = {
  categoria: string
  valor: number
  valorOriginal: number
}


const chartConfig = {
  valor: {
    label: "Valor",
    color: "var(--chart-2)",
  },
} satisfies ChartConfig


interface ChartBarDespesasProps {
  data: ChartBarDespesasData[];
  mesSelecionado?: string;
  loading?: boolean;
  error?: string | null;
}


export function ChartBarDespesas({ data, loading, error }: Omit<ChartBarDespesasProps, 'mesSelecionado'>) {
  if (loading) return <div className="flex items-center justify-center h-64"><div className="text-sm text-muted-foreground">Carregando...</div></div>
  if (error) return <div className="flex items-center justify-center h-64"><div className="text-sm text-red-500">Erro: {error}</div></div>
  if (!data.length) return <div className="flex items-center justify-center h-64"><div className="text-sm text-muted-foreground">Nenhum dado para exibir</div></div>

  return (
    <ChartContainer config={chartConfig}>
      <BarChart
        accessibilityLayer
        data={data}
        layout="vertical"
        margin={{ right: 16 }}
      >
        <CartesianGrid horizontal={false} />
        <YAxis
          dataKey="categoria"
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
          fill="var(--color-valor)"
          radius={4}
        >
          <LabelList
            dataKey="categoria"
            position="insideLeft"
            offset={8}
            className="fill-(--color-foreground/20)"
            fontSize={11}
            width={400}
          />
        </Bar>
      </BarChart>
    </ChartContainer>
  )
}
