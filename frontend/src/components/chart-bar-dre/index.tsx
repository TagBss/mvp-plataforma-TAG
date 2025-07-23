"use client"

import { useEffect, useState } from "react"
import { Bar, BarChart, CartesianGrid, XAxis, YAxis, ResponsiveContainer, ReferenceLine, Cell } from "recharts"
import {
  ChartConfig,
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart"
import { formatCurrencyShort } from "../kpis-competencia"

export const description = "Gráfico de cascata DRE usando Recharts"

interface DreLinha {
  nome: string
  valor: number
  valores_mensais: Record<string, number>
}

interface ChartWaterfallDreProps {
  mesSelecionado?: string
}

interface WaterfallDataPoint {
  nome: string
  valor: number
  valorAcumulado: number
  tipo: 'positivo' | 'negativo' | 'total'
  displayValue: string
  fill: string
}

const chartConfig = {
  valor: {
    label: "Valor",
    color: "var(--chart-1)",
  },
  positivo: {
    label: "Positivo",
    color: "#22c55e",
  },
  negativo: {
    label: "Negativo", 
    color: "#ef4444",
  },
  total: {
    label: "Total",
    color: "var(--chart-4)",
  }
} satisfies ChartConfig

export function ChartBarDre({ mesSelecionado }: ChartWaterfallDreProps) {
  const [chartData, setChartData] = useState<WaterfallDataPoint[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchData() {
      setLoading(true)
      setError(null)
      
      try {
        const response = await fetch(`http://127.0.0.1:8000/dre`)
        if (!response.ok) throw new Error("Erro ao buscar dados do backend")
        
        const data = await response.json()
        let linhas: DreLinha[] = []
        
        if (Array.isArray(data?.data)) {
          linhas = data.data
        } else if (Array.isArray(data)) {
          linhas = data
        }

        // Definir a sequência do gráfico de cascata baseado na DRE
        const sequenciaDre = [
          "Receita Bruta",
          "Receita Líquida", 
          "Resultado Bruto",
          "EBITDA",
          "EBIT",
          "Resultado Financeiro",
          "Resultado Líquido"
        ]

        // Processar os dados para o gráfico de cascata
        let valorAcumulado = 0
        const processedData: WaterfallDataPoint[] = sequenciaDre.map((nome, index) => {
          const linha = linhas.find(item => item.nome === nome)
          
          // Usar valor do mês selecionado ou valor total
          const valor = linha ? (
            mesSelecionado && linha.valores_mensais?.[mesSelecionado] !== undefined
              ? linha.valores_mensais[mesSelecionado]
              : linha.valor ?? 0
          ) : 0

          // Determinar o tipo baseado no valor
          let tipo: 'positivo' | 'negativo' | 'total' = 'positivo'
          if (index === 0) {
            tipo = 'total' // Apenas o primeiro é total
          } else if (valor < 0) {
            tipo = 'negativo'
          } else {
            tipo = 'positivo'
          }

          valorAcumulado += valor
          
          // Determinar a cor baseada no tipo
          const fill = tipo === 'positivo' ? '#22c55e' : 
                      tipo === 'negativo' ? '#ef4444' : 
                      '#22c55e' // fallback
          
          return {
            nome: nome, // Manter nomes completos
            valor: Math.abs(valor),
            valorAcumulado,
            tipo,
            displayValue: formatCurrencyShort(valor, { noPrefix: false }),
            fill
          }
        })

        setChartData(processedData)
      } catch (e: unknown) {
        if (e instanceof Error) {
          setError(e.message)
        } else {
          setError("Erro desconhecido")
        }
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [mesSelecionado])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-sm text-muted-foreground">Carregando...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-sm text-red-500">Erro: {error}</div>
      </div>
    )
  }

  if (!chartData.length) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-sm text-muted-foreground">Nenhum dado para exibir</div>
      </div>
    )
  }

  return (
    <ChartContainer config={chartConfig}>
      <ResponsiveContainer width="100%" height={400}>
        <BarChart
          data={chartData}
          margin={{ top: 20, right: 20, left: 20, bottom: 20 }}
        >
          <CartesianGrid vertical={false} />
          <XAxis 
            dataKey="nome" 
            angle={-45}
            textAnchor="end"
            height={80}
            fontSize={12}
            fontFamily="Geist, sans-serif"
            interval={0}
          />
          <YAxis 
            tickFormatter={(value) => formatCurrencyShort(value, { noPrefix: true })}
            fontSize={12}
            fontFamily="Geist, sans-serif"
            tickLine={false}
            axisLine={false}
          />
          <ChartTooltip cursor={false} content={<ChartTooltipContent />} />
          <ReferenceLine y={0} stroke="hsl(var(--border))" strokeDasharray="2 2" />
          <Bar dataKey="valor" radius={4}>
            {chartData.map((entry, index) => (
              <Cell 
                key={`cell-${index}`} 
                fill={entry.fill}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </ChartContainer>
  )
}
