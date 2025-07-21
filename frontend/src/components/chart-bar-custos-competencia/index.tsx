"use client"

import { Bar, BarChart, CartesianGrid, LabelList, XAxis, YAxis } from "recharts"
import {
  ChartConfig,
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart"
import { useEffect, useState } from "react"
import { formatCurrencyShort } from "../kpis-competencia"

type ChartData = {
  categoria: string
  valor: number
  valorOriginal: number
}

const chartConfig = {
  valor: {
    label: "Valor",
    color: "var(--chart-2)",
  },
} satisfies ChartConfig

interface ChartCustosCompetenciaProps {
  mesSelecionado?: string;
}

export function ChartCustosCompetencia({ mesSelecionado }: ChartCustosCompetenciaProps) {
  const [chartData, setChartData] = useState<ChartData[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchData() {
      setLoading(true)
      setError(null)
      try {
        const response = await fetch(`https://mvp-plataforma-tag-3s9u.onrender.com/dre`)
        if (!response.ok) throw new Error("Erro ao buscar dados do backend")
        
        const data = await response.json()
        let linhas: Array<{
          nome: string;
          valor: number;
          valores_mensais: Record<string, number>;
        }> = []
        
        if (Array.isArray(data?.data)) {
          linhas = data.data
        } else if (Array.isArray(data)) {
          linhas = data
        }

        // Filtrar apenas as linhas de custos
        const custosLinhas = linhas.filter(linha => 
          linha.nome === "Custo com Importação" || 
          linha.nome === "Custo com Mercadoria Interna"
        )

        // Processar dados para o gráfico
        const processedData: ChartData[] = custosLinhas.map(linha => {
          const valorOriginal = mesSelecionado && linha.valores_mensais?.[mesSelecionado] !== undefined
            ? linha.valores_mensais[mesSelecionado]
            : linha.valor ?? 0

          return {
            categoria: linha.nome, // Manter nome completo
            valor: valorOriginal, // Usar valor original (negativo)
            valorOriginal: valorOriginal // Manter valor original para ordenação
          }
        }).sort((a, b) => b.valor - a.valor) // Ordenar como no gráfico financeiro (maior para menor)

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

  if (loading) return <div className="flex items-center justify-center h-64"><div className="text-sm text-muted-foreground">Carregando...</div></div>
  if (error) return <div className="flex items-center justify-center h-64"><div className="text-sm text-red-500">Erro: {error}</div></div>
  if (!chartData.length) return <div className="flex items-center justify-center h-64"><div className="text-sm text-muted-foreground">Nenhum dado para exibir</div></div>

  return (
    <ChartContainer config={chartConfig}>
      <BarChart
        accessibilityLayer
        data={chartData}
        layout="vertical"
        margin={{ right: 16 }}
      >
        <CartesianGrid horizontal={false} />
        <YAxis
          dataKey="categoria"
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
        <ChartTooltip
          cursor={false}
          content={<ChartTooltipContent indicator="line" />}
        />
        <Bar
          dataKey="valor"
          layout="vertical"
          fill="var(--color-valor)"
          radius={4}
        >
          <LabelList
            dataKey="categoria"
            position="insideLeft"
            offset={8}
            className="fill-(--color-foreground/20)"
            fontSize={11}
            width={400}
          />
        </Bar>
      </BarChart>
    </ChartContainer>
  )
}
