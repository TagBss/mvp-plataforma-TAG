"use client"

import { useEffect, useState } from "react"
import { ChevronDown } from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Checkbox } from "@/components/ui/checkbox"
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem
} from "@/components/ui/dropdown-menu"
import ExcelJS from "exceljs"
import { saveAs } from "file-saver"
import React from "react"
import {
  FinancialItem
} from '@/lib/financial-utils'

type DfcItem = FinancialItem & {
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
  vertical_orcamentos_total?: string
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
  const [showOrcado, setShowOrcado] = useState(false)
  const [showDiferenca, setShowDiferenca] = useState(false)
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

  // Função para calcular análise vertical dinâmica do total
  const calcularVerticalTotalDinamica = (): number => {
    // Soma todos os totais dos itens principais para o período filtrado
    return data.reduce((somaGeral, item) => {
      const totalItem = calcularTotal(
        periodo === "mes" ? item.valores_mensais :
        periodo === "trimestre" ? item.valores_trimestrais :
        item.valores_anuais
      )
      return somaGeral + Math.abs(totalItem) // Usa valor absoluto para o denominador
    }, 0)
  }

  // Função para calcular AV% dinâmica do total
  const calcularAVTotalDinamica = (valorTotal: number): string | undefined => {
    const totalGeral = calcularVerticalTotalDinamica()
    if (totalGeral === 0) return undefined
    const percentual = (Math.abs(valorTotal) / totalGeral) * 100
    return `${percentual.toFixed(1)}%`
  }

  // Nova função para renderizar valor da diferença
  const renderValorDiferenca = (real: number, orcado: number) => {
    const diff = real - orcado
    const diffPct = calcularDiffPct(real, orcado)
    
    return (
      <div className="flex flex-col text-right">
        <span className={diff < 0 ? "text-red-500" : ""}>
          {diff.toLocaleString("pt-BR", {
            minimumFractionDigits: 0,
          })}
        </span>
        {diffPct && (
          <span className="text-xs text-muted-foreground">
            {diffPct}
          </span>
        )}
      </div>
    )
  }

  const renderValor = (
    valor: number,
    verticalPct?: string,
    horizontalPct?: string
  ) => (
    <div className="flex flex-col text-right">
      <span className={valor < 0 ? "text-red-500" : ""}>
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

  // Nova função para renderizar valor orçamento com AV/AH do orçamento
  const renderValorOrcamento = (
    valor: number,
    verticalPct?: string,
    horizontalPct?: string
  ) => (
    <div className="flex flex-col text-right">
      <span className={valor < 0 ? "text-red-500" : ""}>
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

    // Primeira linha do cabeçalho - períodos
    const headerRow1 = ["Descrição"]
    periodosFiltrados.forEach(p => {
      headerRow1.push(p)
      if (showOrcado) headerRow1.push("")
      if (showDiferenca) headerRow1.push("")
    })
    headerRow1.push("Total")
    if (showOrcado) headerRow1.push("")
    if (showDiferenca) headerRow1.push("")

    const excelHeader1 = ws.addRow(headerRow1)
    excelHeader1.font = { bold: true }

    // Segunda linha do cabeçalho - só adiciona se houver mais de uma coluna
    if (showOrcado || showDiferenca) {
      const headerRow2 = [""]
      periodosFiltrados.forEach(() => {
        headerRow2.push("Real")
        if (showOrcado) headerRow2.push("Orçado")
        if (showDiferenca) headerRow2.push("Dif.")
      })
      headerRow2.push("Real")
      if (showOrcado) headerRow2.push("Orçado")
      if (showDiferenca) headerRow2.push("Dif.")

      const excelHeader2 = ws.addRow(headerRow2)
      excelHeader2.font = { bold: true }
    }

    // Mesclar células da primeira linha - só se houver segunda linha
    if (showOrcado || showDiferenca) {
      ws.mergeCells(1, 1, 2, 1) // Coluna Descrição
      let colIndex = 2
      periodosFiltrados.forEach(() => {
        const colSpan = 1 + (showOrcado ? 1 : 0) + (showDiferenca ? 1 : 0)
        if (colSpan > 1) {
          ws.mergeCells(1, colIndex, 1, colIndex + colSpan - 1)
        }
        colIndex += colSpan
      })
      // Mesclar colunas do total
      const totalColSpan = 1 + (showOrcado ? 1 : 0) + (showDiferenca ? 1 : 0)
      if (totalColSpan > 1) {
        ws.mergeCells(1, colIndex, 1, colIndex + totalColSpan - 1)
      }
    }

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
        const real = calcularValor(item, p)
        const orcado = calcularOrcamento(item, p)
        row.push(real)
        if (showOrcado) row.push(orcado)
        if (showDiferenca) row.push(real - orcado)
      })
      row.push(total)
      if (showOrcado) row.push(totalOrc)
      if (showDiferenca) row.push(total - totalOrc)

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
            const real = calcularValor(sub, p)
            const orcado = calcularOrcamento(sub, p)
            subRow.push(real)
            if (showOrcado) subRow.push(orcado)
            if (showDiferenca) subRow.push(real - orcado)
          })
          subRow.push(subTotal)
          if (showOrcado) subRow.push(subTotalOrc)
          if (showDiferenca) subRow.push(subTotal - subTotalOrc)

          ws.addRow(subRow)
        })
      }
    })

    wb.xlsx.writeBuffer().then(buffer => {
      const blob = new Blob([buffer], { type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" })
      saveAs(blob, "dfc.xlsx")
    })
  }


if (loading || !filtroAno) return (
  <Card className="m-4">
    <CardHeader>
      <CardTitle>
        <Skeleton className="h-6 w-40 mb-2" />
      </CardTitle>
    </CardHeader>
    <CardContent>
      <Skeleton className="h-8 w-full mb-2" />
      <Skeleton className="h-8 w-3/4 mb-2" />
      <Skeleton className="h-8 w-1/2" />
    </CardContent>
  </Card>
)
if (error) return <Card className="m-4"><CardHeader><CardTitle>{error}</CardTitle></CardHeader></Card>

  return (
    <Card className="max-w-fit m-4">
      <CardHeader>
        <div className="flex flex-col lg:flex-row lg:flex-wrap lg:justify-between gap-2 lg:gap-4 overflow-x-auto">
          <div>
            <CardTitle>DFC - Roriz Instrumentos</CardTitle>
            <CardDescription>{filtroAno === "todos" ? "Todo o período" : `Ano: ${filtroAno}`}</CardDescription>
          </div>
          <div className="flex flex-col sm:flex-row flex-wrap items-start sm:items-center gap-2 sm:gap-4">
            {/* DropdownMenu sofisticado para toggles de exibição */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <button className="text-sm border rounded px-2 py-1 bg-card text-foreground cursor-pointer select-none flex items-center gap-2">
                  Indicadores
                  <svg width="16" height="16" fill="none" viewBox="0 0 24 24"><path d="M7 10l5 5 5-5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/></svg>
                </button>
              </DropdownMenuTrigger>
              <DropdownMenuContent className="min-w-[200px] p-2 flex flex-col gap-2">
                <DropdownMenuItem asChild>
                  <label className="flex items-center gap-2 text-sm cursor-pointer w-full">
                    <Checkbox checked={showVertical} onCheckedChange={val => setShowVertical(!!val)} /> Vertical %
                  </label>
                </DropdownMenuItem>
                <DropdownMenuItem asChild>
                  <label className="flex items-center gap-2 text-sm cursor-pointer w-full">
                    <Checkbox checked={showHorizontal} onCheckedChange={val => setShowHorizontal(!!val)} /> Horizontal %
                  </label>
                </DropdownMenuItem>
                <DropdownMenuItem asChild>
                  <label className="flex items-center gap-2 text-sm cursor-pointer w-full">
                    <Checkbox checked={showOrcado} onCheckedChange={val => setShowOrcado(!!val)} /> Orçado
                  </label>
                </DropdownMenuItem>
                <DropdownMenuItem asChild>
                  <label className="flex items-center gap-2 text-sm cursor-pointer w-full">
                    <Checkbox checked={showDiferenca} onCheckedChange={val => setShowDiferenca(!!val)} /> Diferença
                  </label>
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
            <button onClick={toggleAll} className="text-sm border px-2 py-1 rounded cursor-pointer">
              {allExpanded ? "- Recolher todos" : "+ Expandir todos"}
            </button>
            <button onClick={exportExcel} className="text-sm border px-2 py-1 rounded cursor-pointer">Exportar Excel</button>
            {/* DropdownMenu para seleção de período */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <button className="text-sm border rounded px-2 py-1 bg-card text-foreground cursor-pointer select-none flex items-center gap-2 min-w-fit">
                  {periodo === "mes" ? "Mensal" : periodo === "trimestre" ? "Trimestral" : "Anual"}
                  <svg width="16" height="16" fill="none" viewBox="0 0 24 24"><path d="M7 10l5 5 5-5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/></svg>
                </button>
              </DropdownMenuTrigger>
              <DropdownMenuContent className="min-w-fit p-1 flex flex-col gap-1">
                <DropdownMenuItem onSelect={() => setPeriodo("mes")}>Mensal</DropdownMenuItem>
                <DropdownMenuItem onSelect={() => setPeriodo("trimestre")}>Trimestral</DropdownMenuItem>
                <DropdownMenuItem onSelect={() => setPeriodo("ano")}>Anual</DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>

            {/* DropdownMenu para seleção de ano */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <button className="text-sm border rounded px-2 py-1 bg-card text-foreground cursor-pointer select-none flex items-center gap-2 min-w-fit">
                  {filtroAno === "todos" ? "Todos" : filtroAno}
                  <svg width="16" height="16" fill="none" viewBox="0 0 24 24"><path d="M7 10l5 5 5-5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/></svg>
                </button>
              </DropdownMenuTrigger>
              <DropdownMenuContent className="min-w-fit p-1 flex flex-col gap-1 max-h-60 overflow-y-auto">
                <DropdownMenuItem onSelect={() => setFiltroAno("todos")}>Todos</DropdownMenuItem>
                {anos.sort().map(ano => (
                  <DropdownMenuItem key={ano} onSelect={() => setFiltroAno(String(ano))}>{ano}</DropdownMenuItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </CardHeader>

      <div className="relative overflow-auto max-h-[80vh] px-6">
      <Table>
        <TableHeader>
          {/* Primeira linha do cabeçalho - períodos */}
          <TableRow>
            <TableHead 
              rowSpan={showOrcado || showDiferenca ? 2 : 1} 
              className="min-w-[300px] md:sticky md:left-0 md:z-20 bg-card border-r"
            >
              Descrição
            </TableHead>
            {periodosFiltrados.map((p) => (
              <TableHead 
                key={p} 
                colSpan={1 + (showOrcado ? 1 : 0) + (showDiferenca ? 1 : 0)} 
                rowSpan={showOrcado || showDiferenca ? 1 : 1}
                className="text-center min-w-[120px] bg-muted/20 border-r"
              >
                {p}
              </TableHead>
            ))}
            <TableHead 
              colSpan={1 + (showOrcado ? 1 : 0) + (showDiferenca ? 1 : 0)} 
              rowSpan={showOrcado || showDiferenca ? 1 : 1}
              className="text-center min-w-[120px] bg-muted/20"
            >
              Total
            </TableHead>
          </TableRow>
          {/* Segunda linha do cabeçalho - Real, Orçado, Dif. - só aparece se houver mais de uma coluna */}
          {(showOrcado || showDiferenca) && (
            <TableRow>
              {periodosFiltrados.map((p) => (
                <React.Fragment key={`${p}-sub`}>
                  <TableHead className="text-right min-w-[120px] bg-muted/20">
                    Real
                  </TableHead>
                  {showOrcado && (
                    <TableHead className="text-right min-w-[120px] bg-secondary/40">
                      Orçado
                    </TableHead>
                  )}
                  {showDiferenca && (
                    <TableHead className="text-right min-w-[120px] bg-accent/20">
                      Dif.
                    </TableHead>
                  )}
                </React.Fragment>
              ))}
              {/* Colunas do Total */}
              <TableHead className="text-right min-w-[120px] bg-muted/20">
                Real
              </TableHead>
              {showOrcado && (
                <TableHead className="text-right min-w-[120px] bg-secondary/40">
                  Orçado
                </TableHead>
              )}
              {showDiferenca && (
                <TableHead className="text-right min-w-[120px] bg-accent/20">
                  Dif.
                </TableHead>
              )}
            </TableRow>
          )}
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
                    return (
                      <React.Fragment key={p}>
                        {/* Coluna Real */}
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
                              : item.horizontal_anuais?.[p]
                          )}
                        </TableCell>
                        {/* Coluna Orçado */}
                        {showOrcado && (
                          <TableCell>
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
                        {/* Coluna Diferença */}
                        {showDiferenca && (
                          <TableCell>
                            {renderValorDiferenca(real, orcado)}
                          </TableCell>
                        )}
                      </React.Fragment>
                    );
                  })}

                  {/* Colunas do Total - Real, Orçado, Dif. */}
                  <TableCell className="py-3 text-right">
                    {renderValor(total, calcularAVTotalDinamica(total))}
                  </TableCell>
                  {showOrcado && (
                    <TableCell className="py-3 text-right">
                      {renderValorOrcamento(
                        totalOrc,
                        item.vertical_orcamentos_total,
                        undefined
                      )}
                    </TableCell>
                  )}
                  {showDiferenca && (
                    <TableCell className="py-3 text-right">
                      {renderValorDiferenca(total, totalOrc)}
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
                          return (
                            <React.Fragment key={`${p}-${sub.nome}`}>
                              {/* Coluna Real */}
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
                                    : sub.horizontal_anuais?.[p]
                                )}
                              </TableCell>
                              {/* Coluna Orçado */}
                              {showOrcado && (
                                <TableCell>
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
                              {/* Coluna Diferença */}
                              {showDiferenca && (
                                <TableCell>
                                  {renderValorDiferenca(real, orcado)}
                                </TableCell>
                              )}
                            </React.Fragment>
                          );
                        })}
                        {/* Colunas do Total para subitens - Real, Orçado, Dif. */}
                        <TableCell className="text-right">
                          {renderValor(subTotal, calcularAVTotalDinamica(subTotal))}
                        </TableCell>
                        {showOrcado && (
                          <TableCell className="text-right">
                            {renderValorOrcamento(
                              subTotalOrc,
                              sub.vertical_orcamentos_total,
                              undefined
                            )}
                          </TableCell>
                        )}
                        {showDiferenca && (
                          <TableCell className="text-right">
                            {renderValorDiferenca(subTotal, subTotalOrc)}
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