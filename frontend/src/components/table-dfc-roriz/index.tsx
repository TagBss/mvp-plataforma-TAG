"use client"

import { useEffect, useState } from "react"
import { ChevronDown } from "lucide-react"
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Checkbox } from "@/components/ui/checkbox"
import ExcelJS from "exceljs"
import { saveAs } from "file-saver"
import React from "react"

type DfcItem = {
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

  vertical_mensais_orcamento?: Record<string, string>
  vertical_trimestrais_orcamento?: Record<string, string>
  vertical_anuais_orcamento?: Record<string, string>
  vertical_orcamentos_total?: string // ✅ CORRETO AQUI
  horizontal_mensais_orcamento?: Record<string, string>
  horizontal_trimestrais_orcamento?: Record<string, string>
  horizontal_anuais_orcamento?: Record<string, string>

  orcamentos_mensais?: Record<string, number>
  orcamentos_trimestrais?: Record<string, number>
  orcamentos_anuais?: Record<string, number>

  classificacoes?: DfcItem[]
}

type DfcResponse = {
  meses: string[]
  trimestres: string[]
  anos: number[]
  data: DfcItem[]
}

export default function DfcTable() {
  const [data, setData] = useState<DfcItem[]>([])
  const [meses, setMeses] = useState<string[]>([])
  const [trimestres, setTrimestres] = useState<string[]>([])
  const [anos, setAnos] = useState<number[]>([])
  const [openSections, setOpenSections] = useState<Record<string, boolean>>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filtroAno, setFiltroAno] = useState<string>("")
  const [showVertical, setShowVertical] = useState(true)
  const [showHorizontal, setShowHorizontal] = useState(true)
  const [showOrcamento, setShowOrcamento] = useState(false)
  const [showDiffOrcamento, setShowDiffOrcamento] = useState(false)
  const [allExpanded, setAllExpanded] = useState(false)
  const [periodo, setPeriodo] = useState<"mes" | "trimestre" | "ano">("mes")

  useEffect(() => {
    fetch("http://127.0.0.1:8000/dfc")
      .then(res => res.json())
      .then((result: DfcResponse | { error: string }) => {
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
    const marcar = (itens: DfcItem[]) => {
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

  const calcularValor = (item: DfcItem, periodoLabel: string): number => {
    if (periodo === "mes") return item.valores_mensais?.[periodoLabel] ?? 0
    if (periodo === "trimestre") return item.valores_trimestrais?.[periodoLabel] ?? 0
    if (periodo === "ano") return item.valores_anuais?.[periodoLabel] ?? item.valores_anuais?.[`${periodoLabel}.0`] ?? 0
    return 0
  }

  const calcularOrcamento = (item: DfcItem, periodoLabel: string): number => {
    if (periodo === "mes") return item.orcamentos_mensais?.[periodoLabel] ?? 0
    if (periodo === "trimestre") return item.orcamentos_trimestrais?.[periodoLabel] ?? 0
    if (periodo === "ano") return item.orcamentos_anuais?.[periodoLabel] ?? item.orcamentos_anuais?.[`${periodoLabel}.0`] ?? 0
    return 0
  }

  const calcularTotal = (valores: Record<string, number> | undefined): number => {
    return periodosFiltrados.reduce((total, p) => total + (valores?.[p] ?? valores?.[`${p}.0`] ?? 0), 0)
  }

  const calcularTotalOrcamento = (orcamentos: Record<string, number> | undefined): number => {
    return periodosFiltrados.reduce((total, p) => total + (orcamentos?.[p] ?? orcamentos?.[`${p}.0`] ?? 0), 0)
  }

  const calcularDiffPct = (real: number, orcado: number): string | undefined => {
    if (orcado === 0) return undefined
    const diff = ((real - orcado) / orcado) * 100
    return `${diff.toFixed(1)}%`
  }

  const renderValor = (
    valor: number,
    verticalPct?: string,
    horizontalPct?: string,
    diffPct?: string
  ) => (
    <div className="flex flex-col text-right">
      <span>
        {valor.toLocaleString("pt-BR", {
          minimumFractionDigits: 0,
        })}
      </span>
      {showVertical && verticalPct && (
        <span className="text-xs text-muted-foreground">AV {verticalPct}</span>
      )}
      {showHorizontal && horizontalPct && (
        <span className="text-xs text-muted-foreground">AH {horizontalPct}</span>
      )}
      {showDiffOrcamento && diffPct && (
        <span className="text-xs text-muted-foreground">Dif. {diffPct}</span>
      )}
    </div>
  );

  // Nova função para renderizar valor orçamento com AV/AH do orçamento
  const renderValorOrcamento = (
    valor: number,
    verticalPct?: string,
    horizontalPct?: string
  ) => (
    <div className="flex flex-col text-right">
      <span>
        {valor.toLocaleString("pt-BR", {
          minimumFractionDigits: 0,
        })}
      </span>
      {showVertical && verticalPct && (
        <span className="text-xs text-muted-foreground">AV {verticalPct}</span>
      )}
      {showHorizontal && horizontalPct && (
        <span className="text-xs text-muted-foreground">AH {horizontalPct}</span>
      )}
    </div>
  );

  const exportExcel = () => {
  const wb = new ExcelJS.Workbook()
  const ws = wb.addWorksheet("DFC")

  // Cabeçalho
  const headerRow = ["Descrição"]
  periodosFiltrados.forEach(p => {
    headerRow.push(p)
    if (showOrcamento) headerRow.push(`Orç. ${p}`)
  })
  headerRow.push("Total")
  if (showOrcamento) headerRow.push("Orçamento Total")

  const excelHeader = ws.addRow(headerRow)
  excelHeader.font = { bold: true }

  // Linhas principais
  data.forEach(item => {
    const total = calcularTotal(
      periodo === "mes" ? item.valores_mensais :
      periodo === "trimestre" ? item.valores_trimestrais :
      item.valores_anuais
    )
    const totalOrc = calcularTotalOrcamento(
      periodo === "mes" ? item.orcamentos_mensais :
      periodo === "trimestre" ? item.orcamentos_trimestrais :
      item.orcamentos_anuais
    )

    const row: (string | number)[] = [item.nome]
    periodosFiltrados.forEach(p => {
      row.push(calcularValor(item, p))
      if (showOrcamento) row.push(calcularOrcamento(item, p))
    })
    row.push(total)
    if (showOrcamento) row.push(totalOrc)

    const excelRow = ws.addRow(row)
    excelRow.font = { bold: true }

    // Subitens
    if (item.classificacoes?.length) {
      item.classificacoes.forEach(sub => {
        const subTotal = calcularTotal(
          periodo === "mes" ? sub.valores_mensais :
          periodo === "trimestre" ? sub.valores_trimestrais :
          sub.valores_anuais
        )
        const subTotalOrc = calcularTotalOrcamento(
          periodo === "mes" ? sub.orcamentos_mensais :
          periodo === "trimestre" ? sub.orcamentos_trimestrais :
          sub.orcamentos_anuais
        )

        const subRow: (string | number)[] = ["  " + sub.nome]
        periodosFiltrados.forEach(p => {
          subRow.push(calcularValor(sub, p))
          if (showOrcamento) subRow.push(calcularOrcamento(sub, p))
        })
        subRow.push(subTotal)
        if (showOrcamento) subRow.push(subTotalOrc)

        ws.addRow(subRow)
      })
    }
  })

  wb.xlsx.writeBuffer().then(buffer => {
    const blob = new Blob([buffer], { type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" })
    saveAs(blob, "dfc.xlsx")
  })
}

if (loading || !filtroAno) return <Card className="py-4"><CardHeader><CardTitle>Carregando...</CardTitle></CardHeader></Card>
  if (error) return <Card className="py-4"><CardHeader><CardTitle>{error}</CardTitle></CardHeader></Card>

  return (
    <Card className="max-w-full">
      <CardHeader>
        <div className="flex flex-col lg:flex-row lg:flex-wrap lg:justify-between gap-2 lg:gap-4 overflow-x-auto">
          <div>
            <CardTitle>DFC - Roriz Instrumentos</CardTitle>
            <CardDescription>{filtroAno === "todos" ? "Todo o período" : `Ano: ${filtroAno}`}</CardDescription>
          </div>
          <div className="flex flex-col sm:flex-row flex-wrap items-start sm:items-center gap-2 sm:gap-4">
            <label className="flex items-center gap-2 text-sm cursor-pointer">
              <Checkbox checked={showVertical} onCheckedChange={val => setShowVertical(!!val)} /> Vertical %
            </label>
            <label className="flex items-center gap-2 text-sm cursor-pointer">
              <Checkbox checked={showHorizontal} onCheckedChange={val => setShowHorizontal(!!val)} /> Horizontal %
            </label>
            <label className="flex items-center gap-2 text-sm cursor-pointer">
              <Checkbox checked={showOrcamento} onCheckedChange={val => setShowOrcamento(!!val)} /> Orçamento
            </label>
            <label className="flex items-center gap-2 text-sm cursor-pointer">
              <Checkbox checked={showDiffOrcamento} onCheckedChange={val => setShowDiffOrcamento(!!val)} /> Dif. % Real vs Orçado
            </label>
            <button onClick={toggleAll} className="text-sm border px-2 py-1 rounded cursor-pointer">
              {allExpanded ? "- Recolher todos" : "+ Expandir todos"}
            </button>
            <button onClick={exportExcel} className="text-sm border px-2 py-1 rounded cursor-pointer">Exportar Excel</button>
            <select
              value={periodo}
              onChange={(e) => setPeriodo(e.target.value as "mes" | "trimestre" | "ano")}
              className="text-sm border rounded px-2 py-1 bg-card text-foreground cursor-pointer"
            >
              <option value="mes">Mensal</option>
              <option value="trimestre">Trimestral</option>
              <option value="ano">Anual</option>
            </select>

            <select value={filtroAno} onChange={e => setFiltroAno(e.target.value)} className="text-sm border rounded px-2 py-1 bg-card text-foreground cursor-pointer">
              <option value="todos">Todos</option>
              {anos.sort().map(ano => <option key={ano} value={ano}>{ano}</option>)}
            </select>
          </div>
        </div>
      </CardHeader>

      <div className="relative overflow-auto max-h-[80vh] px-6">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="min-w-[300px] md:sticky md:left-0 md:z-20 bg-card">
              Descrição
            </TableHead>
            {periodosFiltrados.map((p) => (
              <React.Fragment key={p}>
                <TableHead className="text-right min-w-[120px] bg-muted/20">
                  {p}
                </TableHead>
                {showOrcamento && (
                  <TableHead
                    key={`${p}-orc`}
                    className="text-right min-w-[120px] bg-secondary/40"
                  >
                    Orç. {p}
                  </TableHead>
                )}
              </React.Fragment>
            ))}
            <TableHead className="text-right min-w-[120px] bg-muted/20">
              Total
            </TableHead>
            {showOrcamento && (
              <TableHead className="text-right min-w-[120px] bg-secondary/40">
                Orçamento Total
              </TableHead>
            )}
          </TableRow>
        </TableHeader>

        <TableBody>
          {data.map((item) => {
            const isExpandable = !!item.classificacoes?.length;
            const isOpen = openSections[item.nome] ?? false;
            const isTotal = item.tipo === "=";

            const total = calcularTotal(
              periodo === "mes"
                ? item.valores_mensais
                : periodo === "trimestre"
                ? item.valores_trimestrais
                : item.valores_anuais
            );
            const totalOrc = calcularTotalOrcamento(
              periodo === "mes"
                ? item.orcamentos_mensais
                : periodo === "trimestre"
                ? item.orcamentos_trimestrais
                : item.orcamentos_anuais
            );

            return (
              <React.Fragment key={item.nome}>
                <TableRow
                  className={`${
                    isExpandable ? "cursor-pointer hover:bg-muted/50" : ""
                  } ${isTotal ? "bg-muted" : "even:bg-muted/20"}`}
                  onClick={() => isExpandable && toggle(item.nome)}
                >
                  <TableCell
                    className={`py-3 md:sticky md:left-0 md:z-20 bg-card ${
                      isTotal ? "font-bold bg-muted" : ""
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      {isExpandable && (
                        <ChevronDown
                          size={16}
                          className={`transition-transform ${
                            isOpen ? "rotate-0" : "-rotate-90"
                          }`}
                        />
                      )}
                      <span className="text-sm">{item.tipo}</span>
                      <span>{item.nome}</span>
                    </div>
                  </TableCell>

                  {periodosFiltrados.map((p) => {
                    const real = calcularValor(item, p);
                    const orcado = calcularOrcamento(item, p);
                    const diffPct = calcularDiffPct(real, orcado);
                    return (
                      <React.Fragment key={p}>
                        <TableCell>
                          {renderValor(
                            real,
                            periodo === "mes"
                              ? item.vertical_mensais?.[p]
                              : periodo === "trimestre"
                              ? item.vertical_trimestrais?.[p]
                              : item.vertical_anuais?.[p],
                            periodo === "mes"
                              ? item.horizontal_mensais?.[p]
                              : periodo === "trimestre"
                              ? item.horizontal_trimestrais?.[p]
                              : item.horizontal_anuais?.[p],
                            diffPct
                          )}
                        </TableCell>
                        {showOrcamento && (
                          <TableCell key={`${p}-orc`}>
                            {renderValorOrcamento(
                              orcado,
                              periodo === "mes"
                                ? item.vertical_mensais_orcamento?.[p]
                                : periodo === "trimestre"
                                ? item.vertical_trimestrais_orcamento?.[p]
                                : item.vertical_anuais_orcamento?.[p],
                              periodo === "mes"
                                ? item.horizontal_mensais_orcamento?.[p]
                                : periodo === "trimestre"
                                ? item.horizontal_trimestrais_orcamento?.[p]
                                : item.horizontal_anuais_orcamento?.[p]
                            )}
                          </TableCell>
                        )}
                      </React.Fragment>
                    );
                  })}

                  <TableCell className="py-3 text-right">
                    {renderValor(total, item.vertical_total)}
                  </TableCell>
                  {showOrcamento && (
                    <TableCell className="py-3 text-right bg-secondary/40">
                      {renderValorOrcamento(
                        totalOrc,
                        item.vertical_orcamentos_total,
                        undefined
                      )}
                    </TableCell>
                  )}
                </TableRow>

                {isOpen &&
                  item.classificacoes?.map((sub) => {
                    const subTotal = calcularTotal(
                      periodo === "mes"
                        ? sub.valores_mensais
                        : periodo === "trimestre"
                        ? sub.valores_trimestrais
                        : sub.valores_anuais
                    );
                    const subTotalOrc = calcularTotalOrcamento(
                      periodo === "mes"
                        ? sub.orcamentos_mensais
                        : periodo === "trimestre"
                        ? sub.orcamentos_trimestrais
                        : sub.orcamentos_anuais
                    );
                    return (
                      <TableRow key={`${item.nome}-${sub.nome}`} className="bg-muted/10">
                        <TableCell className="sticky left-0 z-10 bg-muted pl-10 text-sm">
                          <div className="flex items-center gap-2">
                            <div className="w-2 h-2 rounded-full bg-muted-foreground/50" />
                            {sub.nome}
                          </div>
                        </TableCell>

                        {periodosFiltrados.map((p) => {
                          const real = calcularValor(sub, p);
                          const orcado = calcularOrcamento(sub, p);
                          const diffPct = calcularDiffPct(real, orcado);
                          return (
                            <React.Fragment key={`${p}-${sub.nome}`}>
                              <TableCell>
                                {renderValor(
                                  real,
                                  periodo === "mes"
                                    ? sub.vertical_mensais?.[p]
                                    : periodo === "trimestre"
                                    ? sub.vertical_trimestrais?.[p]
                                    : sub.vertical_anuais?.[p],
                                  periodo === "mes"
                                    ? sub.horizontal_mensais?.[p]
                                    : periodo === "trimestre"
                                    ? sub.horizontal_trimestrais?.[p]
                                    : sub.horizontal_anuais?.[p],
                                  diffPct
                                )}
                              </TableCell>
                              {showOrcamento && (
                                <TableCell key={`${p}-orc-${sub.nome}`}>
                                  {renderValorOrcamento(
                                    orcado,
                                    periodo === "mes"
                                      ? sub.vertical_mensais_orcamento?.[p]
                                      : periodo === "trimestre"
                                      ? sub.vertical_trimestrais_orcamento?.[p]
                                      : sub.vertical_anuais_orcamento?.[p],
                                    periodo === "mes"
                                      ? sub.horizontal_mensais_orcamento?.[p]
                                      : periodo === "trimestre"
                                      ? sub.horizontal_trimestrais_orcamento?.[p]
                                      : sub.horizontal_anuais_orcamento?.[p]
                                  )}
                                </TableCell>
                              )}
                            </React.Fragment>
                          );
                        })}
                        <TableCell className="text-right">
                          {renderValor(subTotal, sub.vertical_total)}
                        </TableCell>
                        {showOrcamento && (
                          <TableCell className="text-right bg-muted">
                            {renderValorOrcamento(
                              subTotalOrc,
                              sub.vertical_orcamentos_total,
                              undefined
                            )}
                          </TableCell>
                        )}
                      </TableRow>
                    );
                  })}
              </React.Fragment>
            );
          })}
        </TableBody>
      </Table>
    </div>
    </Card>
  )
}