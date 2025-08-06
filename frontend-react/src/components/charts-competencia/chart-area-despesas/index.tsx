"use client"

import { Area, AreaChart, CartesianGrid, XAxis, YAxis } from "recharts"
import { ChartConfig, ChartContainer, ChartTooltip, ChartTooltipContent } from "../../ui/chart"

interface DespesasData {
  mes: string;
  despesas: number;
}

interface ChartAreaDespesasProps {
  data: DespesasData[];
  mesSelecionado?: string;
}

const chartConfig = {
  despesas: {
    label: "Despesas",
    color: "var(--chart-2)",
  },
} satisfies ChartConfig

// Função para formatar mês para exibição (ex: "2024-01" -> "jan/24")
function formatMes(mes: string): string {
  if (!mes.match(/^\d{4}-\d{2}$/)) return mes;
  
  const [ano, m] = mes.split("-");
  const meses = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez'];
  const mesNum = parseInt(m, 10) - 1;
  
  return `${meses[mesNum]}/${ano.slice(-2)}`;
}

export function ChartAreaDespesas({ data, mesSelecionado }: ChartAreaDespesasProps) {
  // Componente customizado para renderizar pontos destacados
  type DotProps = {
    cx?: number;
    cy?: number;
    payload?: { mesOriginal?: string };
  };
  const CustomizedDot = (props: DotProps) => {
    const { cx, cy, payload } = props;
    if (!mesSelecionado || !payload || payload.mesOriginal !== mesSelecionado) {
      // Retorna um círculo invisível para manter o tipo correto
      return <circle cx={cx} cy={cy} r={0} fill="none" />;
    }
    return (
      <circle
        cx={cx}
        cy={cy}
        r={6}
        fill="var(--chart-2)"
        strokeWidth={3}
        style={{ filter: 'drop-shadow(0 0 6px var(--chart-2))' }}
      />
    );
  };

  // Processar dados para o gráfico
  const chartData = data.map(item => ({
    mes: formatMes(item.mes),
    mesOriginal: item.mes,
    despesas: Math.abs(item.despesas), // Usar valor absoluto para despesas
    isSelecionado: item.mes === mesSelecionado
  }));

  return (
    <ChartContainer config={chartConfig}>
      <AreaChart
        accessibilityLayer
        data={chartData}
        margin={{ left: 22, right: 22 }}
      >
        <CartesianGrid vertical={false} />
        <YAxis
          tickLine={false}
          axisLine={false}
          tickMargin={8}
          width={60}
          tickFormatter={(value) => {
            if (value >= 1000000) {
              return `${(value / 1000000).toFixed(1)}M`;
            } else if (value >= 1000) {
              return `${(value / 1000).toFixed(0)}K`;
            }
            return value.toString();
          }}
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
        />
        <ChartTooltip cursor={false} content={<ChartTooltipContent />} />
        <defs>
          <linearGradient id="fillDespesas" x1="0" y1="0" x2="0" y2="1">
            <stop
              offset="5%"
              stopColor={chartConfig.despesas.color}
              stopOpacity={0.8}
            />
            <stop
              offset="95%"
              stopColor={chartConfig.despesas.color}
              stopOpacity={0.1}
            />
          </linearGradient>
        </defs>
        <Area
          dataKey="despesas"
          name={chartConfig.despesas.label}
          type="natural"
          fill="url(#fillDespesas)"
          fillOpacity={0.4}
          stroke={chartConfig.despesas.color}
          stackId="a"
          dot={CustomizedDot}
        />
      </AreaChart>
    </ChartContainer>
  )
}
