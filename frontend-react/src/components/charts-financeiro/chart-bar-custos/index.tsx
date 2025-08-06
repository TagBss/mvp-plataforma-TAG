import { Bar, BarChart, CartesianGrid, LabelList, XAxis, YAxis } from "recharts"
import { useEffect, useState } from "react"
import { formatCurrencyShort } from "../../../utils/formatters"

type ChartData = {
  classificacao: string
  valor: number
}

// Recebe dados de custos via props (já processados pelo componente pai)
export function ChartCustosFinanceiro({ data }: { data?: Record<string, number> }) {
  const [chartData, setChartData] = useState<ChartData[]>([])

  useEffect(() => {
    if (data && Object.keys(data).length > 0) {
      // Processar dados recebidos do pai
      const arr = Object.entries(data)
        .map(([classificacao, valor]) => ({ classificacao, valor }))
        .filter(item => item.valor > 0) // Filtrar valores zero
        .sort((a, b) => a.valor - b.valor) // Ordenar por valor crescente (melhor para maior)
      
      setChartData(arr)
    } else {
      // Se não receber dados, exibir array vazio
      setChartData([])
    }
  }, [data])

  if (!data || Object.keys(data).length === 0) {
    return (
      <div className="flex items-center justify-center h-24 text-muted-foreground">
        <p>Nenhum dado de custos disponível</p>
      </div>
    )
  }
  
  if (!chartData.length) {
    return (
      <div className="flex items-center justify-center h-24 text-muted-foreground">
        <p>Carregando dados de custos...</p>
      </div>
    )
  }

  return (
    <div className="w-full">
      <BarChart
        data={chartData}
        layout="vertical"
        margin={{ right: 16 }}
        width={500}
        height={300}
      >
        <CartesianGrid horizontal={false} />
        <YAxis
          dataKey="classificacao"
          type="category"
          tick={false}
          tickLine={false}
          tickMargin={10}
          axisLine={false}
          interval={0}
          reversed
        />
        <XAxis 
          dataKey="valor" 
          type="number" 
          tickFormatter={(v) => formatCurrencyShort(v, { noPrefix: true })}
          tickLine={false}
          axisLine={false}
        />
        <Bar
          dataKey="valor"
          fill="#3b82f6"
          radius={[0, 4, 4, 0]}
        >
          <LabelList
            dataKey="valor"
            position="right"
            formatter={(value: any) => formatCurrencyShort(Number(value), { noPrefix: true })}
            style={{
              fontSize: '12px',
              fill: '#6b7280',
            }}
          />
        </Bar>
      </BarChart>
    </div>
  )
} 