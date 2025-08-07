"use client"

import { Area, AreaChart, CartesianGrid, XAxis, YAxis } from "recharts"
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart"
import { formatCurrencyShort } from "../../kpis-competencia"

export interface AreaChartFaturamentoProps {
  data: Array<{
    mes: string
    faturamento: number
  }>
  config?: {
    faturamento?: { label: string; color: string }
  }
  mesSelecionado?: string;
}

export function ChartAreaFaturamento({ data, config, mesSelecionado }: AreaChartFaturamentoProps) {
  // Cores e labels padrão, pode sobrescrever via config
  const chartConfig = {
    faturamento: {
      label: config?.faturamento?.label || "Faturamento",
      color: config?.faturamento?.color || "var(--chart-5)",
    },
  };

  // Componente customizado para renderizar pontos destacados
  type DotProps = {
    cx?: number;
    cy?: number;
    payload?: { mes?: string };
  };
  const CustomizedDot = (props: DotProps) => {
    const { cx, cy, payload } = props;
    if (!mesSelecionado || !payload || payload.mes !== mesSelecionado) {
      // Retorna um círculo invisível para manter o tipo correto
      return <circle cx={cx} cy={cy} r={0} fill="none" />;
    }
    return (
      <circle
        cx={cx}
        cy={cy}
        r={6}
        fill="var(--chart-5)"
        strokeWidth={3}
        style={{ filter: 'drop-shadow(0 0 6px var(--chart-5))' }}
      />
    );
  };

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
          <linearGradient id="fillFaturamento" x1="0" y1="0" x2="0" y2="1">
            <stop
              offset="5%"
              stopColor={chartConfig.faturamento.color}
              stopOpacity={0.8}
            />
            <stop
              offset="95%"
              stopColor={chartConfig.faturamento.color}
              stopOpacity={0.1}
            />
          </linearGradient>
        </defs>
        <Area
          dataKey="faturamento"
          name={chartConfig.faturamento.label}
          type="natural"
          fill="url(#fillFaturamento)"
          fillOpacity={0.4}
          stroke={chartConfig.faturamento.color}
          stackId="a"
          dot={CustomizedDot}
        />
      </AreaChart>
    </ChartContainer>
  );
}
