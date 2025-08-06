import { useEffect, useState } from "react";
import { Bar, ComposedChart, CartesianGrid, XAxis, YAxis, Line } from "recharts";
import { formatCurrencyShort } from "../../../utils/formatters";

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
        const car = carMap[mes]?.valor_atual || 0;
        const cap = capMap[mes]?.valor_atual || 0;
        const mov = movMap[mes]?.valor_atual || 0;
        
        return {
          mes,
          mesLabel: formatMes(mes),
          CAR: car,
          CAP: cap,
          Movimentacoes: mov,
        };
      });
      
      setChartData(data);
    }
  }, [momReceber, momPagar, momMovimentacoes]);

  if (!chartData.length) {
    return (
      <div className="flex items-center justify-center h-24 text-muted-foreground">
        <p>Carregando dados de movimentações...</p>
      </div>
    );
  }

  return (
    <div className="w-full">
      <ComposedChart
        data={chartData}
        margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
        width={500}
        height={300}
      >
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis 
          dataKey="mesLabel" 
          tickLine={false}
          axisLine={false}
        />
        <YAxis 
          tickFormatter={(v) => formatCurrencyShort(v, { noPrefix: true })}
          tickLine={false}
          axisLine={false}
        />
        <Bar 
          dataKey="CAR" 
          fill="#3b82f6" 
          radius={[4, 4, 0, 0]}
        />
        <Bar 
          dataKey="CAP" 
          fill="#ef4444" 
          radius={[4, 4, 0, 0]}
        />
        <Line 
          type="monotone" 
          dataKey="Movimentacoes" 
          stroke="#ff651a" 
          strokeWidth={2}
          dot={<CustomizedLineDot />}
          activeDot={{
            r: 8,
            fill: "#ff651a",
            stroke: "#fff",
            strokeWidth: 2,
          }}
        />
      </ComposedChart>
    </div>
  );
} 