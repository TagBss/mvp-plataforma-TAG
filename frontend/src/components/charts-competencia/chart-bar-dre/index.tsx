"use client"


import { Bar, BarChart, CartesianGrid, XAxis, YAxis, ResponsiveContainer, ReferenceLine, Cell } from "recharts"
import {
  ChartConfig,
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart"
import { formatCurrencyShort } from "../../kpis-competencia"

export const description = "Gráfico de cascata DRE usando Recharts"


export interface WaterfallDataPoint {
  nome: string
  valor: number
  valorAcumulado: number
  tipo: 'positivo' | 'negativo' | 'total'
  displayValue: string
  fill: string
}


interface ChartBarDreProps {
  data: WaterfallDataPoint[];
  mesSelecionado?: string;
  loading?: boolean;
  error?: string | null;
}



const chartConfig = {
  valor: {
    label: "Valor",
    color: "var(--chart-1)",
  },
  positivo: {
    label: "Positivo",
    color: "#22c55e",
  },
  negativo: {
    label: "Negativo", 
    color: "#ef4444",
  },
  total: {
    label: "Total",
    color: "var(--chart-4)",
  }
} satisfies ChartConfig


export function ChartBarDre({ data, loading, error }: Omit<ChartBarDreProps, 'mesSelecionado'>) {
  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-sm text-muted-foreground">Carregando...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-sm text-red-500">Erro: {error}</div>
      </div>
    )
  }

  if (!data.length) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-sm text-muted-foreground">Nenhum dado para exibir</div>
      </div>
    )
  }

  return (
    <ChartContainer config={chartConfig}>
      <ResponsiveContainer width="100%" height={400}>
        <BarChart
          data={data}
          margin={{ top: 20, right: 20, left: 20, bottom: 20 }}
        >
          <CartesianGrid vertical={false} />
          <XAxis 
            dataKey="nome" 
            angle={-45}
            textAnchor="end"
            height={80}
            fontSize={12}
            fontFamily="Geist, sans-serif"
            interval={0}
          />
          <YAxis 
            tickFormatter={(value) => formatCurrencyShort(value, { noPrefix: true })}
            fontSize={12}
            fontFamily="Geist, sans-serif"
            tickLine={false}
            axisLine={false}
          />
          <ChartTooltip cursor={false} content={<ChartTooltipContent />} />
          <ReferenceLine y={0} stroke="hsl(var(--border))" strokeDasharray="2 2" />
          <Bar dataKey="valor" radius={4}>
            {data.map((entry, index) => (
              <Cell 
                key={`cell-${index}`} 
                fill={entry.fill}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </ChartContainer>
  )
}
