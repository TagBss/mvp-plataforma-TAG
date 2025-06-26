"use client"

import { useEffect, useState } from "react"
import { ChevronDown } from "lucide-react"
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Checkbox } from "@/components/ui/checkbox"
import * as XLSX from "xlsx"

type DreItem = {
  tipo: string
  nome: string
  valor: number
  valores_mensais?: Record<string, number>
  classificacoes?: {
    nome: string
    valor: number
    valores_mensais?: Record<string, number>
  }[]
}

type DreResponse = {
  meses: string[]
  data: DreItem[]
}

export default function DreTable() {
  const [data, setData] = useState<DreItem[]>([])
  const [meses, setMeses] = useState<string[]>([])
  const [openSections, setOpenSections] = useState<Record<string, boolean>>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filtroAno, setFiltroAno] = useState<string>("")
  const [showVertical, setShowVertical] = useState(true)
  const [showHorizontal, setShowHorizontal] = useState(true)

  useEffect(() => {
    fetch("http://127.0.0.1:8000/dre")
      .then(res => res.json())
      .then((result: DreResponse | { error: string }) => {
        if ("error" in result) {
          setError(result.error)
        } else {
          setData(result.data)
          setMeses(result.meses || [])

          const anos = Array.from(new Set(result.meses.map(m => m.split("-")[0])))
          const ultimoAno = anos.sort((a, b) => parseInt(a) - parseInt(b)).pop()
          if (ultimoAno) setFiltroAno(ultimoAno)
        }
      })
      .catch(err => setError(`Erro ao carregar dados: ${err.message}`))
      .finally(() => setLoading(false))
  }, [])

  const toggle = (nome: string) => {
    setOpenSections(prev => ({ ...prev, [nome]: !prev[nome] }))
  }

  const anosDisponiveis = Array.from(new Set(meses.map(m => m.split("-")[0])))
  const mesesFiltrados = filtroAno === "todos" ? meses : meses.filter(m => m.startsWith(filtroAno))

  const getPaiValorMensal = (nomePai: string, mes: string) => {
    const itemPai = data.find(d => d.nome === nomePai)
    return itemPai?.valores_mensais?.[mes] || 0
  }

  const getVerticalPercent = (valor: number, base: number) => {
    if (!base || base === 0) return "–"
    return ((valor / base) * 100).toFixed(1) + "%"
  }

  const getHorizontalPercent = (valorAtual: number, valorAnterior: number) => {
    if (!valorAnterior || valorAnterior === 0) return "–"
    const diff = ((valorAtual - valorAnterior) / valorAnterior) * 100
    return `${diff.toFixed(1)}%`
  }

  const renderValor = (valor: number, verticalPct?: string, horizontalPct?: string) => (
    <div className="flex flex-col text-right">
      <span>{valor.toLocaleString("pt-BR", { style: "currency", currency: "BRL", minimumFractionDigits: 0 })}</span>
      {showVertical && verticalPct && (
        <span className="text-xs text-muted-foreground">AV {verticalPct}</span>
      )}
      {showHorizontal && horizontalPct && (
        <span className="text-xs text-muted-foreground">AH {horizontalPct}</span>
      )}
    </div>
  )

  const exportExcel = () => {
    const wsData: Array<(string | number)[]> = []
    wsData.push(["Descrição", ...mesesFiltrados, "Total"])
    data.forEach(item => {
      wsData.push([item.nome, ...mesesFiltrados.map(m => item.valores_mensais?.[m] ?? 0), item.valor])
      item.classificacoes?.forEach(sub => {
        wsData.push(["  " + sub.nome, ...mesesFiltrados.map(m => sub.valores_mensais?.[m] ?? 0), sub.valor])
      })
    })
    const wb = XLSX.utils.book_new()
    const ws = XLSX.utils.aoa_to_sheet(wsData)
    XLSX.utils.book_append_sheet(wb, ws, "DRE")
    XLSX.writeFile(wb, "dre.xlsx")
  }

  if (loading || !filtroAno)
    return <Card className="py-4 min-w-1/2"><CardHeader><CardTitle>Carregando...</CardTitle></CardHeader></Card>

  if (error)
    return <Card className="py-4 min-w-1/2"><CardHeader><CardTitle>{error}</CardTitle></CardHeader></Card>

  return (
    <Card className="max-w-full">
      <CardHeader>
        <div className="flex flex-col lg:flex-row lg:justify-between lg:items-center gap-4 mt-2">
          <div>
            <CardTitle>DRE - Roriz Instrumentos</CardTitle>
            <CardDescription>{filtroAno === "todos" ? "Todo o período" : `Ano: ${filtroAno}`}</CardDescription>
          </div>
          <div className="flex flex-col gap-2 lg:flex-row lg:items-center lg:gap-4">
            <label className="flex items-center gap-2 text-sm cursor-pointer">
              <Checkbox checked={showVertical} onCheckedChange={val => setShowVertical(!!val)} /> Vertical %
            </label>
            <label className="flex items-center gap-2 text-sm cursor-pointer">
              <Checkbox checked={showHorizontal} onCheckedChange={val => setShowHorizontal(!!val)} /> Horizontal %
            </label>
            <button onClick={exportExcel} className="text-sm border px-2 py-1 rounded max-w-1/2 cursor-pointer">Exportar Excel</button>
            <select
              className="text-sm border rounded px-2 py-1 max-w-1/2 cursor-pointer"
              value={filtroAno}
              onChange={e => setFiltroAno(e.target.value)}
            >
              <option value="todos">Todos</option>
              {anosDisponiveis.map(ano => <option key={ano} value={ano}>{ano}</option>)}
            </select>
          </div>
        </div>
      </CardHeader>
      
      <div className="relative overflow-auto max-w-full max-h-[80vh] px-6">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="min-w-[300px] md:sticky md:left-0 md:z-20 bg-muted">Descrição</TableHead>
              {mesesFiltrados.map(mes => (
                <TableHead key={mes} className="text-right min-w-[120px] bg-muted/20">{mes}</TableHead>
              ))}
              <TableHead className="text-right min-w-[120px] bg-muted/20">Total</TableHead>
            </TableRow>
          </TableHeader>

          <TableBody>
            {data.map((item, idx) => {
              const isExpandable = item.classificacoes && item.classificacoes.length > 0
              const isOpen = openSections[item.nome] ?? false
              const isTotalizador = item.tipo === "="

              return (
                <>
                  <TableRow key={idx}
                    className={`${isExpandable ? "cursor-pointer hover:bg-muted/50" : ""} ${
                      isTotalizador ? "bg-muted/30" : ""
                    }`}
                    onClick={() => isExpandable && toggle(item.nome)}
                  >
                    <TableCell
                      className={`py-3 md:sticky md:left-0 z-20 ${
                        isTotalizador ? "font-bold bg-muted" : "bg-background"
                      }`}
                    >
                      <div className="flex items-center gap-2">
                        {isExpandable && (
                          <ChevronDown size={16} className={`transition-transform ${isOpen ? "rotate-0" : "-rotate-90"}`} />
                        )}
                        <span className="text-sm w-4">{item.tipo}</span>
                        <span>{item.nome}</span>
                      </div>
                    </TableCell>

                    {mesesFiltrados.map((mes, i) => {
                      const valor = item.valores_mensais?.[mes] || 0
                      const anterior = i > 0 ? item.valores_mensais?.[mesesFiltrados[i - 1]] || 0 : 0
                      const verticalPct = getVerticalPercent(valor, item.valor)
                      const horizontalPct = getHorizontalPercent(valor, anterior)
                      return (
                        <TableCell key={mes}
                          className={`py-3 text-right ${isTotalizador ? "font-bold" : "text-foreground"}`}
                        >
                          {renderValor(valor, verticalPct, horizontalPct)}
                        </TableCell>
                      )
                    })}

                    <TableCell className={`py-3 text-right ${isTotalizador ? "font-bold" : "text-foreground"} bg-muted/20`}>
                      {renderValor(item.valor)}
                    </TableCell>
                  </TableRow>

                  {isOpen && item.classificacoes?.map((sub, j) => (
                    <TableRow key={`${idx}-${j}`} className="bg-muted/10">
                      <TableCell className="md:sticky md:left-0 md:z-20 bg-muted pl-10 text-sm text-muted-foreground">
                        <div className="flex items-center gap-2">
                          <div className="w-2 h-2 rounded-full bg-muted-foreground/50" />
                          {sub.nome}
                        </div>
                      </TableCell>

                      {mesesFiltrados.map((mes, i) => {
                        const valor = sub.valores_mensais?.[mes] || 0
                        const anterior = i > 0 ? sub.valores_mensais?.[mesesFiltrados[i - 1]] || 0 : 0
                        const verticalPct = getVerticalPercent(valor, getPaiValorMensal(item.nome, mes))
                        const horizontalPct = getHorizontalPercent(valor, anterior)
                        return (
                          <TableCell key={mes}>
                            {renderValor(valor, verticalPct, horizontalPct)}
                          </TableCell>
                        )
                      })}

                      <TableCell>
                        {renderValor(sub.valor, getVerticalPercent(sub.valor, item.valor))}
                      </TableCell>
                    </TableRow>
                  ))}
                </>
              )
            })}
          </TableBody>
        </Table>
      </div>

    </Card>
  )
}