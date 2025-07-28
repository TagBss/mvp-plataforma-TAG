"use client"

import { useEffect, useState } from "react";
import { ChartConfig, ChartContainer, ChartTooltip, ChartTooltipContent } from "../../ui/chart";
import { Bar, ComposedChart, CartesianGrid, XAxis, YAxis, Line, ResponsiveContainer } from "recharts";
import { formatCurrencyShort } from "@/components/kpis-financeiro";

// Interface para as props do shape da barra
interface BarShapeProps {
  x?: number;
  y?: number;
  width?: number;
  height?: number;
  payload?: ChartDataItem;
}

// Utilitário para formatar mês (YYYY-MM para "abr/25")
const mesesAbreviados = [ '', 'jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez' ];
function formatMes(mes: string) {
  if (!mes || !mes.match(/^\d{4}-\d{2}$/)) return mes;
  const [ano, mesNum] = mes.split("-");
  const mesIdx = parseInt(mesNum, 10);
  return `${mesesAbreviados[mesIdx]}/${ano.slice(-2)}`;
}

type MomAnalysisItem = {
  mes: string;
  valor_atual: number;
  valor_anterior: number | null;
  variacao_absoluta: number | null;
  variacao_percentual: number | null;
};

type ChartDataItem = {
  mes: string;
  mesLabel: string;
  CAR: number;
  CAP: number;
  Movimentacoes: number;
};

interface ChartMovimentacoesProps {
  mesSelecionado?: string;
  // Props obrigatórios para receber dados já carregados pelo componente pai
  momReceber?: MomAnalysisItem[];
  momPagar?: MomAnalysisItem[];
  momMovimentacoes?: MomAnalysisItem[];
}

export default function ChartMovimentacoes({ 
  mesSelecionado, 
  momReceber, 
  momPagar,
  momMovimentacoes 
}: ChartMovimentacoesProps) {
  const [chartData, setChartData] = useState<ChartDataItem[]>([]);

  // Componente customizado para renderizar pontos destacados na linha
  type DotProps = {
    cx?: number;
    cy?: number;
    payload?: { mes?: string };
  };
  const CustomizedLineDot = (props: DotProps) => {
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
        fill="#ff651a"
        strokeWidth={3}
        style={{ filter: 'drop-shadow(0 0 6px #ff651a)' }}
      />
    );
  };

  useEffect(() => {
    // Usar dados que já vêm prontos do DFC via props
    if (momReceber && momPagar && momMovimentacoes) {
      const carMap = momReceber.reduce<Record<string, MomAnalysisItem>>((acc, cur) => { acc[cur.mes] = cur; return acc; }, {});
      const capMap = momPagar.reduce<Record<string, MomAnalysisItem>>((acc, cur) => { acc[cur.mes] = cur; return acc; }, {});
      const movMap = momMovimentacoes.reduce<Record<string, MomAnalysisItem>>((acc, cur) => { acc[cur.mes] = cur; return acc; }, {});
      
      // Unir todos os meses únicos
      const allMeses = Array.from(new Set([
        ...Object.keys(carMap),
        ...Object.keys(capMap),
        ...Object.keys(movMap),
      ])).sort();
      
      // Pegar os últimos 12 meses
      const ultimos12 = allMeses.slice(-12);
      
      // Montar array para o gráfico usando dados que já vêm prontos
      const data: ChartDataItem[] = ultimos12.map(mes => {
        const car = carMap[mes]?.valor_atual ?? 0;
        const cap = capMap[mes]?.valor_atual ?? 0;
        const movimentacoes = movMap[mes]?.valor_atual ?? 0; // Usar dados do DFC
        
        return {
          mes,
          mesLabel: formatMes(mes),
          CAR: car,
          CAP: Math.abs(cap), // CAP sempre positivo para visualização
          Movimentacoes: movimentacoes, // Dados diretos do DFC
        };
      });

      setChartData(data);
    } else {
      // Se não receber dados, exibir array vazio
      setChartData([]);
    }
  }, [momReceber, momPagar, momMovimentacoes]);

  const chartConfig = {
    CAR: {
      label: "Receber (CAR)",
      color: "#2563eb",
    },
    CAP: {
      label: "Pagar (CAP)",
      color: "#60a5fa",
    },
    Movimentacoes: {
      label: "Movimentações",
      color: "#FF894F",
    },
  } satisfies ChartConfig;

  return (
    <ChartContainer config={chartConfig} className="min-h-[200px] w-full">
      <ResponsiveContainer width="100%" height={250}>
        <ComposedChart data={chartData}>
          <CartesianGrid vertical={false} />
          <XAxis
            dataKey="mesLabel"
            tickLine={false}
            tickMargin={10}
            axisLine={false}
          />
          <YAxis tickLine={false} axisLine={false} tickFormatter={(v) => formatCurrencyShort(v, { noPrefix: true })} />
          <ChartTooltip cursor={false} content={<ChartTooltipContent />} />
          {/* <Legend /> */}
          <Bar
            dataKey="CAR"
            fill={chartConfig.CAR.color}
            radius={4}
            name={chartConfig.CAR.label}
            shape={(props: BarShapeProps) => {
              const { x, y, width, height, payload } = props;
              const isSelected = mesSelecionado && payload?.mes === mesSelecionado;
              return (
                <rect
                  x={x}
                  y={y}
                  width={width}
                  height={height}
                  rx={4}
                  fill={isSelected ? '#f59e42' : chartConfig.CAR.color}
                  stroke={isSelected ? '#f59e42' : undefined}
                  strokeWidth={isSelected ? 3 : 0}
                />
              );
            }}
          />
          <Bar
            dataKey="CAP"
            fill={chartConfig.CAP.color}
            radius={4}
            name={chartConfig.CAP.label}
            shape={(props: BarShapeProps) => {
              const { x, y, width, height, payload } = props;
              const isSelected = mesSelecionado && payload?.mes === mesSelecionado;
              return (
                <rect
                  x={x}
                  y={y}
                  width={width}
                  height={height}
                  rx={4}
                  fill={isSelected ? '#f9c38b' : chartConfig.CAP.color}
                  stroke={isSelected ? '#f9c38b' : undefined}
                  strokeWidth={isSelected ? 3 : 0}
                />
              );
            }}
          />
          <Line
            type="monotone"
            dataKey="Movimentacoes"
            stroke={chartConfig.Movimentacoes.color}
            strokeWidth={3}
            dot={CustomizedLineDot}
            name={chartConfig.Movimentacoes.label}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </ChartContainer>
  );
}