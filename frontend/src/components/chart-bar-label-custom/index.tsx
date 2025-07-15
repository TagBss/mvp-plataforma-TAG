"use client"

import { Bar, BarChart, CartesianGrid, LabelList, XAxis, YAxis } from "recharts"
import {
  ChartConfig,
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart"

export const description = "A bar chart with a custom label"

import { useEffect, useState } from "react"

type ChartData = {
  classificacao: string
  valor: number
}

const chartConfig = {
  desktop: {
    label: "Desktop",
    color: "var(--chart-2)",
  },
  mobile: {
    label: "Mobile",
    color: "var(--chart-2)",
  },
  label: {
    color: "var(--background)",
  },
} satisfies ChartConfig

// Permite receber dados via props para filtro dinâmico
export function ChartBarLabelCustom({ data }: { data?: Record<string, number> }) {
  // Se receber data via props, usa ela, senão busca do backend (modo antigo)
  const [chartData, setChartData] = useState<ChartData[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (data) {
      // Recebeu dados filtrados do pai
      const arr = Object.entries(data)
        .map(([classificacao, valor]) => ({ classificacao, valor }))
        .sort((a, b) => b.valor - a.valor)
      setChartData(arr)
      setLoading(false)
      setError(null)
      return
    }
    // Modo antigo: busca do backend (todo o período)
    async function fetchData() {
      setLoading(true)
      setError(null)
      try {
        const res = await fetch("http://localhost:8000/custos-visao-financeiro");
        if (!res.ok) throw new Error("Erro ao buscar dados do backend")
        const json = await res.json()
        if (!json.success) throw new Error(json.error || "Erro desconhecido")
        const total = json.data.total_geral_classificacao as Record<string, number>
        const arr = Object.entries(total)
          .map(([classificacao, valor]) => ({ classificacao, valor }))
          .sort((a, b) => b.valor - a.valor)
        setChartData(arr)
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
  }, [data])

  if (loading) return <div>Carregando...</div>
  if (error) return <div>Erro: {error}</div>
  if (!chartData.length) return <div>Nenhum dado para exibir.</div>

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
          dataKey="classificacao"
          type="category"
          tick={false}
          tickLine={false}
          tickMargin={10}
          axisLine={false}
          interval={0}
          reversed
        />
        <XAxis dataKey="valor" type="number" hide />
        <ChartTooltip
          cursor={false}
          content={<ChartTooltipContent indicator="line" />}
        />
        <Bar
          dataKey="valor"
          layout="vertical"
          fill="var(--color-desktop)"
          radius={4}
        >
          <LabelList
                dataKey="classificacao"
                position="insideLeft"
                offset={8}
                className="fill-(--color-foreground/20)"
                fontSize={10}
                width={400}
              />
        </Bar>
      </BarChart>
    </ChartContainer>
  )
}