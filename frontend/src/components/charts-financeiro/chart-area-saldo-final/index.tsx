"use client"


import { Area, AreaChart, CartesianGrid, XAxis, YAxis } from "recharts"
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart"
import { formatCurrencyShort } from "../../kpis-financeiro"


export interface AreaChartSaldoProps {
  data: Array<{
    mes: string
    saldo_final: number
  }>
  config?: {
    saldo_final?: { label: string; color: string }
  }
  mesSelecionado?: string;
}

export function ChartAreaSaldoFinal({ data, config, mesSelecionado }: AreaChartSaldoProps) {
  // Cores e labels padrão, pode sobrescrever via config
  const chartConfig = {
    saldo_final: {
      label: config?.saldo_final?.label || "Saldo Final",
      color: config?.saldo_final?.color || "var(--chart-5)",
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
          domain={[
            (dataMin: number) => dataMin * 0.8, // -20%
            (dataMax: number) => dataMax * 1.2   // +20%
          ]}
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
          dataKey="saldo_final"
          name={chartConfig.saldo_final.label}
          type="natural"
          fill="url(#fillSaldoFinal)"
          fillOpacity={0.4}
          stroke={chartConfig.saldo_final.color}
          stackId="a"
          dot={CustomizedDot}
        />
      </AreaChart>
    </ChartContainer>
  );
}