"use client"

import { Area, AreaChart, CartesianGrid, XAxis, YAxis } from "recharts"
import { formatCurrencyShort } from "../../../utils/formatters"
import {
  ChartConfig,
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "../../ui/chart"

export interface AreaChartSaldoProps {
  data: Array<{
    mes: string
    saldo_final: number
  }>
  mesSelecionado?: string;
}

const chartConfig = {
  saldo_final: {
    label: "Saldo Final",
    color: "#3b82f6",
  },
} satisfies ChartConfig

export function ChartAreaSaldoFinal({ data, mesSelecionado }: AreaChartSaldoProps) {
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
        fill="#3b82f6"
        strokeWidth={3}
        style={{ filter: 'drop-shadow(0 0 6px #3b82f6)' }}
      />
    );
  };

  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-24 text-muted-foreground">
        <p>Nenhum dado de saldo disponível</p>
      </div>
    );
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
              stopColor="#3b82f6"
              stopOpacity={0.8}
            />
            <stop
              offset="95%"
              stopColor="#3b82f6"
              stopOpacity={0.1}
            />
          </linearGradient>
        </defs>
        <Area
          dataKey="saldo_final"
          name="Saldo Final"
          type="natural"
          fill="url(#fillSaldoFinal)"
          fillOpacity={0.4}
          stroke="#3b82f6"
          stackId="a"
          dot={CustomizedDot}
        />
      </AreaChart>
    </ChartContainer>
  );
} 