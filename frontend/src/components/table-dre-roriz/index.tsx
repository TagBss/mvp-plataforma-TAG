"use client"

import { useEffect, useState } from "react"
import { ChevronDown } from "lucide-react"
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Checkbox } from "@/components/ui/checkbox"
import ExcelJS from "exceljs"
import { saveAs } from "file-saver"

type DreItem = {
  tipo: string
  nome: string
  valores_mensais?: Record<string, number>
  valores_trimestrais?: Record<string, number>
  valores_anuais?: Record<string, number>
  vertical_mensais?: Record<string, string>
  vertical_trimestrais?: Record<string, string>
  vertical_anuais?: Record<string, string>
  vertical_total?: string
  horizontal_mensais?: Record<string, string>
  horizontal_trimestrais?: Record<string, string>
  horizontal_anuais?: Record<string, string>
  classificacoes?: DreItem[]
}

type DreResponse = {
  meses: string[]
  trimestres: string[]
  anos: number[]
  data: DreItem[]
}

export default function DreTable() {
  const [data, setData] = useState<DreItem[]>([])
  const [meses, setMeses] = useState<string[]>([])
  const [trimestres, setTrimestres] = useState<string[]>([])
  const [anos, setAnos] = useState<number[]>([])
  const [openSections, setOpenSections] = useState<Record<string, boolean>>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filtroAno, setFiltroAno] = useState<string>("")
  const [showVertical, setShowVertical] = useState(true)
  const [showHorizontal, setShowHorizontal] = useState(true)
  const [allExpanded, setAllExpanded] = useState(false)
  const [periodo, setPeriodo] = useState<"mes" | "trimestre" | "ano">("mes")

  useEffect(() => {
    fetch("http://127.0.0.1:8000/dre")
      .then(res => res.json())
      .then((result: DreResponse | { error: string }) => {
        console.log("🚩 RESPOSTA DA API:", result)

        if ("error" in result) {
          setError(result.error)
        } else {
          setData(result.data)
          setMeses(result.meses)
          setTrimestres(result.trimestres)
          setAnos(result.anos)

          const ultimoAno = Math.max(...result.anos)
          setFiltroAno(String(ultimoAno))
        }
      })
      .catch(err => setError(`Erro ao carregar dados: ${err.message}`))
      .finally(() => setLoading(false))
  }, [])

  const toggle = (nome: string) => {
    setOpenSections(prev => ({ ...prev, [nome]: !prev[nome] }))
  }

  const toggleAll = () => {
    const novoEstado = !allExpanded
    const novasSecoes: Record<string, boolean> = {}

    const marcar = (itens: DreItem[]) => {
      itens.forEach(item => {
        if (item.classificacoes?.length) {
          novasSecoes[item.nome] = novoEstado
          marcar(item.classificacoes)
        }
      })
    }

    marcar(data)
    setOpenSections(novasSecoes)
    setAllExpanded(novoEstado)
  }

  let periodosFiltrados: string[] = []
  if (periodo === "mes") {
    periodosFiltrados = meses.filter(m => filtroAno === "todos" ? true : m.startsWith(filtroAno)).sort()
  } else if (periodo === "trimestre") {
    periodosFiltrados = trimestres.filter(t => filtroAno === "todos" ? true : t.startsWith(filtroAno)).sort()
  } else if (periodo === "ano") {
    periodosFiltrados = filtroAno === "todos" ? anos.map(String).sort() : [filtroAno]
  }

  const calcularValor = (item: DreItem, periodoLabel: string): number => {
    if (periodo === "mes") return item.valores_mensais?.[periodoLabel] ?? 0
    if (periodo === "trimestre") return item.valores_trimestrais?.[periodoLabel] ?? 0
    if (periodo === "ano") return item.valores_anuais?.[periodoLabel] ?? item.valores_anuais?.[`${periodoLabel}.0`] ?? 0
    return 0
  }

  const calcularTotal = (valores: Record<string, number> | undefined): number => {
    return periodosFiltrados.reduce((total, p) => total + (valores?.[p] ?? valores?.[`${p}.0`] ?? 0), 0)
  }

  const renderValor = (valor: number, verticalPct?: string, horizontalPct?: string) => (
    <div className="flex flex-col text-right">
      <span>{valor.toLocaleString("pt-BR", { style: "currency", currency: "BRL", minimumFractionDigits: 0 })}</span>
      {showVertical && verticalPct && <span className="text-xs text-muted-foreground">AV {verticalPct}</span>}
      {showHorizontal && horizontalPct && <span className="text-xs text-muted-foreground">AH {horizontalPct}</span>}
    </div>
  )

  const exportExcel = () => {
    const wb = new ExcelJS.Workbook()
    const ws = wb.addWorksheet("DRE")

    const headerRow = ["Descrição", ...periodosFiltrados, "Total"]
    ws.addRow(headerRow).font = { bold: true }

    data.forEach(item => {
      const total = calcularTotal(
        periodo === "mes" ? item.valores_mensais :
        periodo === "trimestre" ? item.valores_trimestrais :
        item.valores_anuais
      )
      const row = ws.addRow([item.nome, ...periodosFiltrados.map(p => calcularValor(item, p)), total])
      row.font = { bold: true }

      item.classificacoes?.forEach(sub => {
        const subTotal = calcularTotal(
          periodo === "mes" ? sub.valores_mensais :
          periodo === "trimestre" ? sub.valores_trimestrais :
          sub.valores_anuais
        )
        ws.addRow(["  " + sub.nome, ...periodosFiltrados.map(p => calcularValor(sub, p)), subTotal])
      })
    })

    wb.xlsx.writeBuffer().then(data => {
      const blob = new Blob([data], { type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" })
      saveAs(blob, "dre.xlsx")
    })
  }

  if (loading || !filtroAno) return <Card className="py-4"><CardHeader><CardTitle>Carregando...</CardTitle></CardHeader></Card>
  if (error) return <Card className="py-4"><CardHeader><CardTitle>{error}</CardTitle></CardHeader></Card>

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-wrap justify-between gap-4">
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
            <button onClick={toggleAll} className="text-sm border px-2 py-1 rounded">
              {allExpanded ? "- Recolher todos" : "+ Expandir todos"}
            </button>
            <button onClick={exportExcel} className="text-sm border px-2 py-1 rounded">Exportar Excel</button>
            <select
              value={periodo}
              onChange={(e) => setPeriodo(e.target.value as "mes" | "trimestre" | "ano")}
              className="text-sm border rounded px-2 py-1"
            >
              <option value="mes">Mensal</option>
              <option value="trimestre">Trimestral</option>
              <option value="ano">Anual</option>
            </select>
            <select value={filtroAno} onChange={e => setFiltroAno(e.target.value)} className="text-sm border rounded px-2 py-1">
              <option value="todos">Todos</option>
              {anos.sort().map(ano => <option key={ano} value={ano}>{ano}</option>)}
            </select>
          </div>
        </div>
      </CardHeader>

      <div className="relative overflow-auto max-w-full max-h-[80vh] px-6">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="min-w-[300px] sticky left-0 z-20 bg-muted">Descrição</TableHead>
              {periodosFiltrados.map(p => (
                <TableHead key={p} className="text-right min-w-[120px] bg-muted/20">{p}</TableHead>
              ))}
              <TableHead className="text-right min-w-[120px] bg-muted/20">Total</TableHead>
            </TableRow>
          </TableHeader>

          <TableBody>
            {data.map(item => {
              const isExpandable = !!item.classificacoes?.length
              const isOpen = openSections[item.nome] ?? false
              const isTotal = item.tipo === "="

              const total = calcularTotal(
                periodo === "mes" ? item.valores_mensais :
                periodo === "trimestre" ? item.valores_trimestrais :
                item.valores_anuais
              )

              console.log("🚩 ITEM:", item)

              return (
                <>
                  <TableRow key={item.nome}
                    className={`${isExpandable ? "cursor-pointer hover:bg-muted/50" : ""} ${isTotal ? "bg-muted/30" : ""}`}
                    onClick={() => isExpandable && toggle(item.nome)}
                  >
                    <TableCell className={`py-3 sticky left-0 z-20 ${isTotal ? "font-bold bg-muted" : ""}`}>
                      <div className="flex items-center gap-2">
                        {isExpandable && (
                          <ChevronDown size={16} className={`transition-transform ${isOpen ? "rotate-0" : "-rotate-90"}`} />
                        )}
                        <span className="text-sm">{item.tipo}</span>
                        <span>{item.nome}</span>
                      </div>
                    </TableCell>

                    {periodosFiltrados.map(p => (
                      <TableCell key={p} className="py-3 text-right">
                        {renderValor(
                          calcularValor(item, p),
                          periodo === "mes" ? item.vertical_mensais?.[p] :
                          periodo === "trimestre" ? item.vertical_trimestrais?.[p] :
                          item.vertical_anuais?.[p],
                          periodo === "mes" ? item.horizontal_mensais?.[p] :
                          periodo === "trimestre" ? item.horizontal_trimestrais?.[p] :
                          item.horizontal_anuais?.[p]
                        )}
                      </TableCell>
                    ))}

                    <TableCell className="py-3 text-right">{renderValor(total, item.vertical_total)}</TableCell>
                  </TableRow>

                  {isOpen && item.classificacoes?.map(sub => {
                    const subTotal = calcularTotal(
                      periodo === "mes" ? sub.valores_mensais :
                      periodo === "trimestre" ? sub.valores_trimestrais :
                      sub.valores_anuais
                    )

                    console.log("🚩 SUBITEM:", sub)

                    return (
                      <TableRow key={item.nome + sub.nome} className="bg-muted/10">
                        <TableCell className="sticky left-0 z-10 bg-muted pl-10 text-sm">
                          <div className="flex items-center gap-2">
                            <div className="w-2 h-2 rounded-full bg-muted-foreground/50" />
                            {sub.nome}
                          </div>
                        </TableCell>
                        {periodosFiltrados.map(p => (
                          <TableCell key={p} className="text-right">
                            {renderValor(
                              calcularValor(sub, p),
                              periodo === "mes" ? sub.vertical_mensais?.[p] :
                              periodo === "trimestre" ? sub.vertical_trimestrais?.[p] :
                              sub.vertical_anuais?.[p],
                              periodo === "mes" ? sub.horizontal_mensais?.[p] :
                              periodo === "trimestre" ? sub.horizontal_trimestrais?.[p] :
                              sub.horizontal_anuais?.[p]
                            )}
                          </TableCell>
                        ))}
                        <TableCell className="text-right">{renderValor(subTotal, sub.vertical_total)}</TableCell>
                      </TableRow>
                    )
                  })}
                </>
              )
            })}
          </TableBody>
        </Table>
      </div>
    </Card>
  )
}