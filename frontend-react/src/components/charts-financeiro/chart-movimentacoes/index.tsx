"use client"

import { useEffect, useState } from "react";
import { Bar, ComposedChart, CartesianGrid, XAxis, YAxis, Line, ResponsiveContainer } from "recharts";
import { formatCurrencyShort } from "../../../utils/formatters";
import {
  ChartConfig,
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "../../ui/chart";

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
  Saldo: number;
};

interface ChartMovimentacoesProps {
  mesSelecionado?: string;
  // Props obrigatórios para receber dados já carregados pelo componente pai
  momReceber?: MomAnalysisItem[];
  momPagar?: MomAnalysisItem[];
  momMovimentacoes?: MomAnalysisItem[];
}

const chartConfig = {
  CAR: {
    label: "Receber (CAR)",
    color: "#2563eb",
  },
  CAP: {
    label: "Pagar (CAP)",
    color: "#60a5fa",
  },
  Saldo: {
    label: "Saldo",
    color: "#ff651a",
  },
} satisfies ChartConfig;

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
    // Sempre usar dados de receber/pagar para as barras, e movimentações para a linha
    if (momReceber && momPagar) {
      const carMap = momReceber.reduce<Record<string, MomAnalysisItem>>((acc, cur) => { acc[cur.mes] = cur; return acc; }, {});
      const capMap = momPagar.reduce<Record<string, MomAnalysisItem>>((acc, cur) => { acc[cur.mes] = cur; return acc; }, {});
      
      // Unir todos os meses únicos
      const allMeses = Array.from(new Set([
        ...Object.keys(carMap),
        ...Object.keys(capMap),
      ])).sort();
      
      // Pegar os últimos 12 meses
      const ultimos12 = allMeses.slice(-12);
      
      // Montar array para o gráfico
      const data: ChartDataItem[] = ultimos12.map(mes => {
        const car = carMap[mes]?.valor_atual ?? 0;
        const cap = capMap[mes]?.valor_atual ?? 0;
        
        // Se temos dados de movimentações do DFC, usar para a linha de saldo
        let saldo = car - cap; // Fallback
        if (momMovimentacoes && momMovimentacoes.length > 0) {
          const movimentacaoItem = momMovimentacoes.find(item => item.mes === mes);
          if (movimentacaoItem) {
            saldo = movimentacaoItem.valor_atual;
          }
        }
        
        return {
          mes,
          mesLabel: formatMes(mes),
          CAR: car,
          CAP: Math.abs(cap), // CAP sempre positivo para visualização
          Saldo: saldo,
        };
      });

      setChartData(data);
    } else {
      // Se não receber dados, exibir array vazio
      setChartData([]);
    }
  }, [momReceber, momPagar, momMovimentacoes]);

  if (!chartData.length) {
    return (
      <div className="flex items-center justify-center h-24 text-muted-foreground">
        <p>Nenhum dado de movimentações disponível</p>
      </div>
    );
  }

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
          <Bar
            dataKey="CAR"
            fill="#2563eb"
            radius={4}
            name="Receber (CAR)"
            shape={(props: any) => {
              const { x, y, width, height, payload } = props;
              const isSelected = mesSelecionado && payload?.mes === mesSelecionado;
              return (
                <rect
                  x={x}
                  y={y}
                  width={width}
                  height={height}
                  rx={4}
                  fill={isSelected ? '#f59e42' : '#2563eb'}
                  stroke={isSelected ? '#f59e42' : undefined}
                  strokeWidth={isSelected ? 3 : 0}
                />
              );
            }}
          />
          <Bar
            dataKey="CAP"
            fill="#60a5fa"
            radius={4}
            name="Pagar (CAP)"
            shape={(props: any) => {
              const { x, y, width, height, payload } = props;
              const isSelected = mesSelecionado && payload?.mes === mesSelecionado;
              return (
                <rect
                  x={x}
                  y={y}
                  width={width}
                  height={height}
                  rx={4}
                  fill={isSelected ? '#f9c38b' : '#60a5fa'}
                  stroke={isSelected ? '#f9c38b' : undefined}
                  strokeWidth={isSelected ? 3 : 0}
                />
              );
            }}
          />
          <Line
            type="monotone"
            dataKey="Saldo"
            stroke="#ff651a"
            strokeWidth={3}
            dot={CustomizedLineDot}
            name="Saldo"
          />
        </ComposedChart>
      </ResponsiveContainer>
    </ChartContainer>
  );
} 