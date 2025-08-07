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
  valor?: number  // Adicionando esta propriedade
  orcamento_total?: number  // Adicionando esta propriedade
  
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

  vertical_orcamentos_mensais?: Record<string, string>
  vertical_orcamentos_trimestrais?: Record<string, string>
  vertical_orcamentos_anuais?: Record<string, string>
  vertical_orcamentos_total?: string
  horizontal_orcamentos_mensais?: Record<string, string>
  horizontal_orcamentos_trimestrais?: Record<string, string>
  horizontal_orcamentos_anuais?: Record<string, string>

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
    
    // Primeiro marcar Movimentações
    novasSecoes["Movimentações"] = novoEstado
    
    // Marcar totalizadores e suas contas
    data.forEach(item => {
      if (item.nome === "Movimentações" && item.classificacoes) {
        // Para os totalizadores dentro de Movimentações
        item.classificacoes.forEach(totalizador => {
          novasSecoes[totalizador.nome] = novoEstado
          
          // Marcar contas filhas dos totalizadores
          if (totalizador.classificacoes?.length) {
            totalizador.classificacoes.forEach(conta => {
              if (conta.classificacoes?.length) {
                novasSecoes[`${totalizador.nome}-${conta.nome}`] = novoEstado
              }
            })
          }
        })
      } else {
        // Para outros itens (saldo inicial, saldo final)
        novasSecoes[item.nome] = novoEstado
      }
    })
    
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
            maximumFractionDigits: 0,
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
          maximumFractionDigits: 0,
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
          maximumFractionDigits: 0,
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

    // Linhas principais - Totalizadores e suas contas
    data.forEach(totalizador => {
      const totalTotalizador = calcularTotal(
        periodo === "mes" ? totalizador.valores_mensais :
        periodo === "trimestre" ? totalizador.valores_trimestrais :
        totalizador.valores_anuais
      )
      const totalTotalizadorOrc = calcularTotalOrcamento(
        periodo === "mes" ? totalizador.orcamentos_mensais :
        periodo === "trimestre" ? totalizador.orcamentos_trimestrais :
        totalizador.orcamentos_anuais
      )

      // Linha do totalizador
      const rowTotalizador: (string | number)[] = [totalizador.nome]
      periodosFiltrados.forEach(p => {
        const real = calcularValor(totalizador, p)
        const orcado = calcularOrcamento(totalizador, p)
        rowTotalizador.push(real)
        if (showOrcado) rowTotalizador.push(orcado)
        if (showDiferenca) rowTotalizador.push(real - orcado)
      })
      rowTotalizador.push(totalTotalizador)
      if (showOrcado) rowTotalizador.push(totalTotalizadorOrc)
      if (showDiferenca) rowTotalizador.push(totalTotalizador - totalTotalizadorOrc)

      const excelRowTotalizador = ws.addRow(rowTotalizador)
      excelRowTotalizador.font = { bold: true }

      // Contas filhas do totalizador
      if (totalizador.classificacoes?.length) {
        totalizador.classificacoes.forEach(conta => {
          const totalConta = calcularTotal(
            periodo === "mes" ? conta.valores_mensais :
            periodo === "trimestre" ? conta.valores_trimestrais :
            conta.valores_anuais
          )
          const totalContaOrc = calcularTotalOrcamento(
            periodo === "mes" ? conta.orcamentos_mensais :
            periodo === "trimestre" ? conta.orcamentos_trimestrais :
            conta.orcamentos_anuais
          )

          const rowConta: (string | number)[] = ["  " + conta.nome]
          periodosFiltrados.forEach(p => {
            const real = calcularValor(conta, p)
            const orcado = calcularOrcamento(conta, p)
            rowConta.push(real)
            if (showOrcado) rowConta.push(orcado)
            if (showDiferenca) rowConta.push(real - orcado)
          })
          rowConta.push(totalConta)
          if (showOrcado) rowConta.push(totalContaOrc)
          if (showDiferenca) rowConta.push(totalConta - totalContaOrc)

          ws.addRow(rowConta)

          // Classificações das contas (nível 3)
          if (conta.classificacoes?.length) {
            conta.classificacoes.forEach(classificacao => {
              const totalClassificacao = calcularTotal(
                periodo === "mes" ? classificacao.valores_mensais :
                periodo === "trimestre" ? classificacao.valores_trimestrais :
                classificacao.valores_anuais
              )
              const totalClassificacaoOrc = calcularTotalOrcamento(
                periodo === "mes" ? classificacao.orcamentos_mensais :
                periodo === "trimestre" ? classificacao.orcamentos_trimestrais :
                classificacao.orcamentos_anuais
              )

              const rowClassificacao: (string | number)[] = ["    " + classificacao.nome]
              periodosFiltrados.forEach(p => {
                const real = calcularValor(classificacao, p)
                const orcado = calcularOrcamento(classificacao, p)
                rowClassificacao.push(real)
                if (showOrcado) rowClassificacao.push(orcado)
                if (showDiferenca) rowClassificacao.push(real - orcado)
              })
              rowClassificacao.push(totalClassificacao)
              if (showOrcado) rowClassificacao.push(totalClassificacaoOrc)
              if (showDiferenca) rowClassificacao.push(totalClassificacao - totalClassificacaoOrc)

              ws.addRow(rowClassificacao)
            })
          }
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
            <CardTitle>DFC</CardTitle>
            <CardDescription>
              Valores em Reais (R$)
            </CardDescription>
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
              className="min-w-[300px] md:sticky md:left-0 md:z-10 bg-background border-r font-semibold"
            >
              Descrição
            </TableHead>
            {periodosFiltrados.map((p) => (
              <TableHead 
                key={p} 
                colSpan={1 + (showOrcado ? 1 : 0) + (showDiferenca ? 1 : 0)} 
                rowSpan={showOrcado || showDiferenca ? 1 : 1}
                className="text-center min-w-[120px] bg-muted/30 border-r font-semibold"
              >
                {p}
              </TableHead>
            ))}
            <TableHead 
              colSpan={1 + (showOrcado ? 1 : 0) + (showDiferenca ? 1 : 0)} 
              rowSpan={showOrcado || showDiferenca ? 1 : 1}
              className="text-center min-w-[120px] bg-muted/30 font-semibold"
            >
              Total
            </TableHead>
          </TableRow>
          {/* Segunda linha do cabeçalho - Real, Orçado, Dif. - só aparece se houver mais de uma coluna */}
          {(showOrcado || showDiferenca) && (
            <TableRow>
              {periodosFiltrados.map((p) => (
                <React.Fragment key={`${p}-sub`}>
                  <TableHead className="text-right min-w-[120px] bg-secondary/30">
                    Real
                  </TableHead>
                  {showOrcado && (
                    <TableHead className="text-right min-w-[120px] bg-muted/20">
                      Orçado
                    </TableHead>
                  )}
                  {showDiferenca && (
                    <TableHead className="text-right min-w-[120px] bg-muted/20">
                      Dif.
                    </TableHead>
                  )}
                </React.Fragment>
              ))}
              {/* Colunas do Total */}
              <TableHead className="text-right min-w-[120px] bg-secondary/30">
                Real
              </TableHead>
              {showOrcado && (
                <TableHead className="text-right min-w-[120px] bg-muted/20">
                  Orçado
                </TableHead>
              )}
              {showDiferenca && (
                <TableHead className="text-right min-w-[120px] bg-muted/20">
                  Dif.
                </TableHead>
              )}
            </TableRow>
          )}
        </TableHeader>

        <TableBody>
          {data.map((item) => {
            // Se for "Movimentações", renderizar como item expansível com totalizadores filhos
            if (item.nome === "Movimentações" && item.classificacoes) {
              const isMovimentacoesOpen = openSections["Movimentações"] ?? false;
              
              return (
                <React.Fragment key={item.nome}>
                  {/* LINHA PRINCIPAL DAS MOVIMENTAÇÕES - CLICÁVEL PARA EXPANDIR */}
                  <TableRow 
                    className="bg-primary/5 font-bold cursor-pointer hover:bg-primary/8 transition-colors duration-200"
                    onClick={() => toggle("Movimentações")}
                  >
                    <TableCell className="py-4 md:sticky md:left-0 md:z-10 bg-background font-bold border-r border-border">
                      <div className="flex items-center gap-2">
                        <ChevronDown
                          size={16}
                          className={`transition-transform ${
                            isMovimentacoesOpen ? "rotate-0" : "-rotate-90"
                          }`}
                        />
                        <span className="text-base font-bold text-primary">{item.nome}</span>
                      </div>
                    </TableCell>
                    
                    {periodosFiltrados.map((p) => {
                      const real = calcularValor(item, p);
                      const orcado = calcularOrcamento(item, p);
                      return (
                        <React.Fragment key={p}>
                          <TableCell className="font-bold">
                            {renderValor(real)}
                          </TableCell>
                          {showOrcado && (
                            <TableCell className="font-bold">
                              {renderValorOrcamento(orcado)}
                            </TableCell>
                          )}
                          {showDiferenca && (
                            <TableCell className="font-bold">
                              {renderValorDiferenca(real, orcado)}
                            </TableCell>
                          )}
                        </React.Fragment>
                      );
                    })}

                    <TableCell className="py-4 text-right font-bold">
                      {renderValor(item.valor ?? 0)}
                    </TableCell>
                    {showOrcado && (
                      <TableCell className="py-4 text-right font-bold">
                        {renderValorOrcamento(item.orcamento_total ?? 0)}
                      </TableCell>
                    )}
                    {showDiferenca && (
                      <TableCell className="py-4 text-right font-bold">
                        {renderValorDiferenca(item.valor ?? 0, item.orcamento_total ?? 0)}
                      </TableCell>
                    )}
                  </TableRow>

                  {/* TOTALIZADORES (NÍVEL 1) - SÓ MOSTRA SE MOVIMENTAÇÕES ESTÁ EXPANDIDA */}
                  {isMovimentacoesOpen && item.classificacoes.map((totalizador) => {
                    const isOpen = openSections[totalizador.nome] ?? false;

                    const totalTotalizador = calcularTotal(
                      periodo === "mes"
                        ? totalizador.valores_mensais
                        : periodo === "trimestre"
                        ? totalizador.valores_trimestrais
                        : totalizador.valores_anuais
                    );
                    const totalTotalizadorOrc = calcularTotalOrcamento(
                      periodo === "mes"
                        ? totalizador.orcamentos_mensais
                        : periodo === "trimestre"
                        ? totalizador.orcamentos_trimestrais
                        : totalizador.orcamentos_anuais
                    );

                    return (
                      <React.Fragment key={totalizador.nome}>
                        {/* LINHA DO TOTALIZADOR */}
                        <TableRow
                          className="cursor-pointer hover:bg-muted/20 bg-muted/12 font-semibold border-t border-muted/30 transition-colors duration-200"
                          onClick={() => toggle(totalizador.nome)}
                        >
                          <TableCell className="py-4 md:sticky md:left-0 md:z-10 bg-background font-semibold pl-4 border-r border-border">
                            <div className="flex items-center gap-2">
                              <ChevronDown
                                size={18}
                                className={`transition-transform ${
                                  isOpen ? "rotate-0" : "-rotate-90"
                                }`}
                              />
                              <span className="text-base font-semibold">{totalizador.nome}</span>
                            </div>
                          </TableCell>

                          {periodosFiltrados.map((p) => {
                            const real = calcularValor(totalizador, p);
                            const orcado = calcularOrcamento(totalizador, p);
                            return (
                              <React.Fragment key={p}>
                                <TableCell className="font-bold">
                                  {renderValor(
                                    real,
                                    periodo === "mes"
                                      ? totalizador.vertical_mensais?.[p]
                                      : periodo === "trimestre"
                                      ? totalizador.vertical_trimestrais?.[p]
                                      : totalizador.vertical_anuais?.[p],
                                    periodo === "mes"
                                      ? totalizador.horizontal_mensais?.[p]
                                      : periodo === "trimestre"
                                      ? totalizador.horizontal_trimestrais?.[p]
                                      : totalizador.horizontal_anuais?.[p]
                                  )}
                                </TableCell>
                                {showOrcado && (
                                  <TableCell className="font-bold">
                                    {renderValorOrcamento(
                                      orcado,
                                      periodo === "mes"
                                        ? totalizador.vertical_orcamentos_mensais?.[p]
                                        : periodo === "trimestre"
                                        ? totalizador.vertical_orcamentos_trimestrais?.[p]
                                        : totalizador.vertical_orcamentos_anuais?.[p],
                                      periodo === "mes"
                                        ? totalizador.horizontal_orcamentos_mensais?.[p]
                                        : periodo === "trimestre"
                                        ? totalizador.horizontal_orcamentos_trimestrais?.[p]
                                        : totalizador.horizontal_orcamentos_anuais?.[p]
                                    )}
                                  </TableCell>
                                )}
                                {showDiferenca && (
                                  <TableCell className="font-bold">
                                    {renderValorDiferenca(real, orcado)}
                                  </TableCell>
                                )}
                              </React.Fragment>
                            );
                          })}

                          <TableCell className="py-4 text-right font-bold">
                            {renderValor(totalTotalizador, calcularAVTotalDinamica(totalTotalizador))}
                          </TableCell>
                          {showOrcado && (
                            <TableCell className="py-4 text-right font-bold">
                              {renderValorOrcamento(
                                totalTotalizadorOrc,
                                totalizador.vertical_orcamentos_total,
                                undefined
                              )}
                            </TableCell>
                          )}
                          {showDiferenca && (
                            <TableCell className="py-4 text-right font-bold">
                              {renderValorDiferenca(totalTotalizador, totalTotalizadorOrc)}
                            </TableCell>
                          )}
                        </TableRow>

                        {/* CONTAS FILHAS DO TOTALIZADOR (NÍVEL 2) */}
                        {isOpen &&
                          totalizador.classificacoes?.map((conta) => {
                            const isContaExpandable = !!conta.classificacoes?.length;
                            const isContaOpen = openSections[`${totalizador.nome}-${conta.nome}`] ?? false;

                            const totalConta = calcularTotal(
                              periodo === "mes"
                                ? conta.valores_mensais
                                : periodo === "trimestre"
                                ? conta.valores_trimestrais
                                : conta.valores_anuais
                            );
                            const totalContaOrc = calcularTotalOrcamento(
                              periodo === "mes"
                                ? conta.orcamentos_mensais
                                : periodo === "trimestre"
                                ? conta.orcamentos_trimestrais
                                : conta.orcamentos_anuais
                            );

                            return (
                              <React.Fragment key={`${totalizador.nome}-${conta.nome}`}>
                                {/* LINHA DA CONTA */}
                                <TableRow
                                  className={`${
                                    isContaExpandable ? "cursor-pointer hover:bg-accent/15" : ""
                                  } bg-accent/5 border-t border-border/25 transition-colors duration-200`}
                                  onClick={() => isContaExpandable && toggle(`${totalizador.nome}-${conta.nome}`)}
                                >
                                  <TableCell className="sticky left-0 z-10 bg-background pl-8 border-r border-border/20">
                                    <div className="flex items-center gap-2">
                                      {isContaExpandable && (
                                        <ChevronDown
                                          size={14}
                                          className={`transition-transform ${
                                            isContaOpen ? "rotate-0" : "-rotate-90"
                                          }`}
                                        />
                                      )}
                                      <span className="text-sm text-muted-foreground">{conta.tipo}</span>
                                      <span className="font-medium">{conta.nome}</span>
                                    </div>
                                  </TableCell>

                                  {periodosFiltrados.map((p) => {
                                    const real = calcularValor(conta, p);
                                    const orcado = calcularOrcamento(conta, p);
                                    return (
                                      <React.Fragment key={p}>
                                        <TableCell>
                                          {renderValor(
                                            real,
                                            periodo === "mes"
                                              ? conta.vertical_mensais?.[p]
                                              : periodo === "trimestre"
                                              ? conta.vertical_trimestrais?.[p]
                                              : conta.vertical_anuais?.[p],
                                            periodo === "mes"
                                              ? conta.horizontal_mensais?.[p]
                                              : periodo === "trimestre"
                                              ? conta.horizontal_trimestrais?.[p]
                                              : conta.horizontal_anuais?.[p]
                                          )}
                                        </TableCell>
                                        {showOrcado && (
                                          <TableCell>
                                            {renderValorOrcamento(
                                              orcado,
                                              periodo === "mes"
                                                ? conta.vertical_orcamentos_mensais?.[p]
                                                : periodo === "trimestre"
                                                ? conta.vertical_orcamentos_trimestrais?.[p]
                                                : conta.vertical_orcamentos_anuais?.[p],
                                              periodo === "mes"
                                                ? conta.horizontal_orcamentos_mensais?.[p]
                                                : periodo === "trimestre"
                                                ? conta.horizontal_orcamentos_trimestrais?.[p]
                                                : conta.horizontal_orcamentos_anuais?.[p]
                                            )}
                                          </TableCell>
                                        )}
                                        {showDiferenca && (
                                          <TableCell>
                                            {renderValorDiferenca(real, orcado)}
                                          </TableCell>
                                        )}
                                      </React.Fragment>
                                    );
                                  })}

                                  <TableCell className="text-right">
                                    {renderValor(totalConta, calcularAVTotalDinamica(totalConta))}
                                  </TableCell>
                                  {showOrcado && (
                                    <TableCell className="text-right">
                                      {renderValorOrcamento(
                                        totalContaOrc,
                                        conta.vertical_orcamentos_total,
                                        undefined
                                      )}
                                    </TableCell>
                                  )}
                                  {showDiferenca && (
                                    <TableCell className="text-right">
                                      {renderValorDiferenca(totalConta, totalContaOrc)}
                                    </TableCell>
                                  )}
                                </TableRow>

                                {/* CLASSIFICAÇÕES DA CONTA (NÍVEL 3) */}
                                {isContaOpen &&
                                  conta.classificacoes?.map((classificacao) => {
                                    const totalClassificacao = calcularTotal(
                                      periodo === "mes"
                                        ? classificacao.valores_mensais
                                        : periodo === "trimestre"
                                        ? classificacao.valores_trimestrais
                                        : classificacao.valores_anuais
                                    );
                                    const totalClassificacaoOrc = calcularTotalOrcamento(
                                      periodo === "mes"
                                        ? classificacao.orcamentos_mensais
                                        : periodo === "trimestre"
                                        ? classificacao.orcamentos_trimestrais
                                        : classificacao.orcamentos_anuais
                                    );

                                    return (
                                      <TableRow 
                                        key={`${totalizador.nome}-${conta.nome}-${classificacao.nome}`} 
                                        className="bg-muted/4 border-t border-border/15 hover:bg-muted/8 transition-colors duration-200"
                                      >
                                        <TableCell className="sticky left-0 z-10 bg-background pl-16 text-sm border-r border-border/10">
                                          <div className="flex items-center gap-2">
                                            <div className="w-1.5 h-1.5 rounded-full bg-primary/60" />
                                            <span className="text-muted-foreground">{classificacao.nome}</span>
                                          </div>
                                        </TableCell>

                                        {periodosFiltrados.map((p) => {
                                          const real = calcularValor(classificacao, p);
                                          const orcado = calcularOrcamento(classificacao, p);
                                          return (
                                            <React.Fragment key={p}>
                                              <TableCell className="text-sm">
                                                {renderValor(
                                                  real,
                                                  periodo === "mes"
                                                    ? classificacao.vertical_mensais?.[p]
                                                    : periodo === "trimestre"
                                                    ? classificacao.vertical_trimestrais?.[p]
                                                    : classificacao.vertical_anuais?.[p],
                                                  periodo === "mes"
                                                    ? classificacao.horizontal_mensais?.[p]
                                                    : periodo === "trimestre"
                                                    ? classificacao.horizontal_trimestrais?.[p]
                                                    : classificacao.horizontal_anuais?.[p]
                                                )}
                                              </TableCell>
                                              {showOrcado && (
                                                <TableCell className="text-sm">
                                                  {renderValorOrcamento(
                                                    orcado,
                                                    periodo === "mes"
                                                      ? classificacao.vertical_orcamentos_mensais?.[p]
                                                      : periodo === "trimestre"
                                                      ? classificacao.vertical_orcamentos_trimestrais?.[p]
                                                      : classificacao.vertical_orcamentos_anuais?.[p],
                                                    periodo === "mes"
                                                      ? classificacao.horizontal_orcamentos_mensais?.[p]
                                                      : periodo === "trimestre"
                                                      ? classificacao.horizontal_orcamentos_trimestrais?.[p]
                                                      : classificacao.horizontal_orcamentos_anuais?.[p]
                                                  )}
                                                </TableCell>
                                              )}
                                              {showDiferenca && (
                                                <TableCell className="text-sm">
                                                  {renderValorDiferenca(real, orcado)}
                                                </TableCell>
                                              )}
                                            </React.Fragment>
                                          );
                                        })}

                                        <TableCell className="text-right text-sm">
                                          {renderValor(totalClassificacao, calcularAVTotalDinamica(totalClassificacao))}
                                        </TableCell>
                                        {showOrcado && (
                                          <TableCell className="text-right text-sm">
                                            {renderValorOrcamento(
                                              totalClassificacaoOrc,
                                              classificacao.vertical_orcamentos_total,
                                              undefined
                                            )}
                                          </TableCell>
                                        )}
                                        {showDiferenca && (
                                          <TableCell className="text-right text-sm">
                                            {renderValorDiferenca(totalClassificacao, totalClassificacaoOrc)}
                                          </TableCell>
                                        )}
                                      </TableRow>
                                    );
                                  })}
                              </React.Fragment>
                            );
                          })}
                      </React.Fragment>
                    );
                  })}
                </React.Fragment>
              );
            } else {
              // Para "Saldo inicial" e "Saldo final", renderizar diretamente
              return (
                <TableRow key={item.nome} className="bg-secondary/8 font-semibold hover:bg-secondary/12 transition-colors duration-200">
                  <TableCell className="py-4 md:sticky md:left-0 md:z-10 bg-background font-semibold border-r border-border">
                    <span className="text-base font-semibold text-secondary-foreground">{item.nome}</span>
                  </TableCell>
                  
                  {periodosFiltrados.map((p) => {
                    const real = calcularValor(item, p);
                    const orcado = calcularOrcamento(item, p);
                    return (
                      <React.Fragment key={p}>
                        <TableCell className="font-bold">
                          {renderValor(real)}
                        </TableCell>
                        {showOrcado && (
                          <TableCell className="font-bold">
                            {renderValorOrcamento(orcado)}
                          </TableCell>
                        )}
                        {showDiferenca && (
                          <TableCell className="font-bold">
                            {renderValorDiferenca(real, orcado)}
                          </TableCell>
                        )}
                      </React.Fragment>
                    );
                  })}

                  <TableCell className="py-4 text-right font-bold">
                    {renderValor(item.valor ?? 0)}
                  </TableCell>
                  {showOrcado && (
                    <TableCell className="py-4 text-right font-bold">
                      {renderValorOrcamento(item.orcamento_total ?? 0)}
                    </TableCell>
                  )}
                  {showDiferenca && (
                    <TableCell className="py-4 text-right font-bold">
                      {renderValorDiferenca(item.valor ?? 0, item.orcamento_total ?? 0)}
                    </TableCell>
                  )}
                </TableRow>
              );
            }
          })}
        </TableBody>
      </Table>
    </div>
    </Card>
  )
}