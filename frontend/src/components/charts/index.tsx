"use client"

import { useEffect, useState } from "react";
import { ChartConfig, ChartContainer } from "../ui/chart";
import { Bar, ComposedChart, CartesianGrid, XAxis, YAxis, Line, Legend, ResponsiveContainer, Tooltip } from "recharts";
import { TooltipProps } from 'recharts';
import { ValueType, NameType } from 'recharts/types/component/DefaultTooltipContent';
import { formatCurrencyShort } from "@/components/kpis-financeiro";

// Tooltip customizada para valores resumidos
function CustomTooltip({ active, payload, label }: TooltipProps<ValueType, NameType>) {
  if (active && payload && payload.length) {
    return (
      <div style={{ background: '#18181b', borderRadius: 8, padding: 12, color: '#fff', border: '1px solid #333' }}>
        <div style={{ fontWeight: 600, marginBottom: 4 }}>{label}</div>
        {payload.map((entry) => (
          <div key={entry.dataKey?.toString()} style={{ color: entry.color, marginBottom: 2 }}>
            {entry.name}: <b>{formatCurrencyShort(Number(entry.value))}</b>
          </div>
        ))}
      </div>
    );
  }
  return null;
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

export default function ChartOverview() {
  const [chartData, setChartData] = useState<ChartDataItem[]>([]);

  useEffect(() => {
    async function fetchData() {
      try {
        const [carRes, capRes, movRes] = await Promise.all([
          fetch("http://localhost:8000/receber").then(r => r.json()),
          fetch("http://localhost:8000/pagar").then(r => r.json()),
          fetch("http://localhost:8000/movimentacoes").then(r => r.json()),
        ]);
        if (!carRes.success || !capRes.success || !movRes.success) {
          setChartData([]);
          return;
        }
        // Mapear dados por mês
        const carMap = (carRes.data.mom_analysis as MomAnalysisItem[] || []).reduce<Record<string, MomAnalysisItem>>((acc, cur) => { acc[cur.mes] = cur; return acc; }, {});
        const capMap = (capRes.data.mom_analysis as MomAnalysisItem[] || []).reduce<Record<string, MomAnalysisItem>>((acc, cur) => { acc[cur.mes] = cur; return acc; }, {});
        const movMap = (movRes.data.mom_analysis as MomAnalysisItem[] || []).reduce<Record<string, MomAnalysisItem>>((acc, cur) => { acc[cur.mes] = cur; return acc; }, {});
        // Unir todos os meses únicos
        const allMeses = Array.from(new Set([
          ...Object.keys(carMap),
          ...Object.keys(capMap),
          ...Object.keys(movMap),
        ])).sort();
        // Pegar os últimos 12 meses
        const ultimos12 = allMeses.slice(-12);
        // Montar array para o gráfico
        const data: ChartDataItem[] = ultimos12.map(mes => {
          const car = carMap[mes]?.valor_atual ?? 0;
          const cap = capMap[mes]?.valor_atual ?? 0;
          return {
            mes,
            mesLabel: formatMes(mes),
            CAR: car,
            CAP: Math.abs(cap), // CAP sempre positivo
            Movimentacoes: car - Math.abs(cap), // Saldo líquido: CAR - CAP
          };
        });
        setChartData(data);
      } catch {
        setChartData([]);
      }
    }
    fetchData();
  }, []);

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
      color: "#f59e42",
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
          <Tooltip content={<CustomTooltip />} />
          <Legend />
          <Bar dataKey="CAR" fill={chartConfig.CAR.color} radius={4} name={chartConfig.CAR.label} />
          <Bar dataKey="CAP" fill={chartConfig.CAP.color} radius={4} name={chartConfig.CAP.label} />
          <Line type="monotone" dataKey="Movimentacoes" stroke={chartConfig.Movimentacoes.color} strokeWidth={3} dot={false} name={chartConfig.Movimentacoes.label} />
        </ComposedChart>
      </ResponsiveContainer>
    </ChartContainer>
  );
}