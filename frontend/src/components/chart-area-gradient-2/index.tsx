"use client"


import { Area, AreaChart, CartesianGrid, XAxis, YAxis } from "recharts"
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart"
import { formatCurrencyShort } from "../kpis-financeiro"

export interface AreaChartSaldoProps {
  data: Array<{
    mes: string
    saldo_inicial: number
    saldo_final: number
  }>
  config?: {
    saldo_inicial?: { label: string; color: string }
    saldo_final?: { label: string; color: string }
  }
}

export function ChartAreaSaldoFinal({ data, config }: AreaChartSaldoProps) {
  // Cores e labels padrão, pode sobrescrever via config
  const chartConfig = {
    saldo_inicial: {
      label: config?.saldo_inicial?.label || "Saldo Inicial",
      color: config?.saldo_inicial?.color || "var(--chart-2)",
    },
    saldo_final: {
      label: config?.saldo_final?.label || "Saldo Final",
      color: config?.saldo_final?.color || "var(--chart-5)",
    },
  }

  return (
    <ChartContainer config={chartConfig} className="min-h-[200px] w-full">
      <AreaChart
        accessibilityLayer
        data={data}
        margin={{ left: 22, right: 22 }}
      >
        <CartesianGrid vertical={false} />
        <YAxis
          tickLine={false}
          axisLine={false}
          tickMargin={8}
          width={60}
          tickFormatter={(v) => formatCurrencyShort(v, { noPrefix: true })}
        />
        <XAxis
          dataKey="mes"
          tickLine={false}
          axisLine={false}
          tickMargin={8}
          interval={0}
          tickFormatter={(value: string) => {
            // Espera mes no formato '2025-04', '2024-12', etc
            if (typeof value === 'string' && value.match(/^\d{4}-\d{2}$/)) {
              const [ano, mes] = value.split("-");
              const meses = ["", "jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"];
              const mesNum = parseInt(mes, 10);
              return `${meses[mesNum]}/${ano.slice(-2)}`;
            }
            return value;
          }}
        />
        <ChartTooltip cursor={false} content={<ChartTooltipContent />} />
        <defs>
          <linearGradient id="fillSaldoInicial" x1="0" y1="0" x2="0" y2="1">
            <stop
              offset="5%"
              stopColor={chartConfig.saldo_inicial.color}
              stopOpacity={0.8}
            />
            <stop
              offset="95%"
              stopColor={chartConfig.saldo_inicial.color}
              stopOpacity={0.1}
            />
          </linearGradient>
          <linearGradient id="fillSaldoFinal" x1="0" y1="0" x2="0" y2="1">
            <stop
              offset="5%"
              stopColor={chartConfig.saldo_final.color}
              stopOpacity={0.8}
            />
            <stop
              offset="95%"
              stopColor={chartConfig.saldo_final.color}
              stopOpacity={0.1}
            />
          </linearGradient>
        </defs>
        <Area
          dataKey="saldo_inicial"
          name={chartConfig.saldo_inicial.label}
          type="natural"
          fill="url(#fillSaldoInicial)"
          fillOpacity={0.4}
          stroke={chartConfig.saldo_inicial.color}
          stackId="a"
        />
        <Area
          dataKey="saldo_final"
          name={chartConfig.saldo_final.label}
          type="natural"
          fill="url(#fillSaldoFinal)"
          fillOpacity={0.4}
          stroke={chartConfig.saldo_final.color}
          stackId="a"
        />
      </AreaChart>
    </ChartContainer>
  )
}