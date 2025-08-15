import { useEffect, useState } from "react"
import { ChevronDown } from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../ui/card"
import { Skeleton } from "../ui/skeleton"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../ui/table"
import { Checkbox } from "../ui/checkbox"
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem
} from "../ui/dropdown-menu"
import { Button } from "../ui/button"
// @ts-ignore
import ExcelJS from "exceljs"
// @ts-ignore
import { saveAs } from "file-saver"
import React from "react"
import { api } from "../../services/api"

type DreItem = {
  tipo: string
  nome: string
  expandivel?: boolean
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
  const [showOrcado, setShowOrcado] = useState(false)
  const [showDiferenca, setShowDiferenca] = useState(false)
  const [allExpanded, setAllExpanded] = useState(false)
  const [periodo, setPeriodo] = useState<"mes" | "trimestre" | "ano">("mes")

  useEffect(() => {
    fetch("http://127.0.0.1:8000/dre")
      .then(res => res.json())
      .then((result: DreResponse | { error: string }) => {
        if ("error" in result) {
          setError(result.error)
        } else {
          console.log("📊 Dados recebidos:", {
            meses: result.meses?.length,
            trimestres: result.trimestres?.length,
            anos: result.anos?.length,
            trimestres_exemplo: result.trimestres?.slice(0, 3)
          })
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
        if (item.expandivel && item.classificacoes?.length) {
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
    console.log("🔍 Filtro trimestral:", {
      filtroAno,
      trimestres_disponiveis: trimestres,
      trimestres_exemplo: trimestres?.slice(0, 3)
    })
    periodosFiltrados = trimestres.filter(t => filtroAno === "todos" ? true : t.startsWith(filtroAno)).sort()
    console.log("✅ Trimestres filtrados:", periodosFiltrados)
  } else if (periodo === "ano") {
    periodosFiltrados = filtroAno === "todos" ? anos.map(String).sort() : [filtroAno]
  }

  const calcularValor = (item: DreItem, periodoLabel: string): number => {
    if (periodo === "mes") return item.valores_mensais?.[periodoLabel] ?? 0
    if (periodo === "trimestre") {
      const valor = item.valores_trimestrais?.[periodoLabel] ?? 0
      console.log("💰 Valor trimestral:", {
        item: item.nome,
        periodo: periodoLabel,
        valor,
        valores_disponiveis: Object.keys(item.valores_trimestrais || {})
      })
      return valor
    }
    if (periodo === "ano") return item.valores_anuais?.[periodoLabel] ?? item.valores_anuais?.[`${periodoLabel}.0`] ?? 0
    return 0
  }

  const calcularOrcamento = (item: DreItem, periodoLabel: string): number => {
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
    return data.reduce((somaGeral, item) => {
      const totalItem = calcularTotal(
        periodo === "mes" ? item.valores_mensais :
        periodo === "trimestre" ? item.valores_trimestrais :
        item.valores_anuais
      )
      return somaGeral + Math.abs(totalItem)
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

  // Função para renderizar nome com operador matemático
  const renderNomeComOperador = (item: DreItem) => {
    const operadores: Record<string, string> = {
      "+": "+",
      "-": "-", 
      "=": "=",
      "+/-": "±"
    }
    
    const operador = operadores[item.tipo] || ""
    const nomeComOperador = operador ? `(${operador}) ${item.nome}` : item.nome
    
    return (
      <span className={item.tipo === "=" ? "font-semibold" : ""}>
        {nomeComOperador}
      </span>
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
    </div>
  );

  // Função separada para renderizar AV/AH após Orçado e Diferença
  const renderAnalises = (
    verticalPct?: string,
    horizontalPct?: string
  ) => {
    console.log('🎯 renderAnalises chamada com:', { 
      verticalPct, 
      horizontalPct, 
      showVertical, 
      showHorizontal,
      willShowVertical: showVertical && verticalPct && verticalPct !== "–",
      willShowHorizontal: showHorizontal && horizontalPct && horizontalPct !== "–"
    });
    
    return (
      <div className="flex flex-col text-right">
        {showVertical && verticalPct && verticalPct !== "–" && (
          <span className="text-xs text-muted-foreground">AV {verticalPct}</span>
        )}
        {showHorizontal && horizontalPct && horizontalPct !== "–" && (
          <span className="text-xs text-muted-foreground">AH {horizontalPct}</span>
        )}
      </div>
    );
  };

  // Nova função para renderizar valor orçamento sem AV/AH (será renderizado separadamente)
  const renderValorOrcamento = (
    valor: number
  ) => (
    <div className="flex flex-col text-right">
      <span className={valor < 0 ? "text-red-500" : ""}>
        {valor.toLocaleString("pt-BR", {
          minimumFractionDigits: 0,
          maximumFractionDigits: 0,
        })}
      </span>
    </div>
  );

  const exportExcel = () => {
    const wb = new ExcelJS.Workbook()
    const ws = wb.addWorksheet("DRE")

    // Primeira linha do cabeçalho - períodos
    const headerRow1 = ["Descrição"]
    periodosFiltrados.forEach(p => {
      headerRow1.push(p)
      if (showVertical || showHorizontal) headerRow1.push("")
      if (showOrcado) headerRow1.push("")
      if (showDiferenca) headerRow1.push("")
    })
    headerRow1.push("Total")
    if (showVertical || showHorizontal) headerRow1.push("")
    if (showOrcado) headerRow1.push("")
    if (showDiferenca) headerRow1.push("")

    const excelHeader1 = ws.addRow(headerRow1)
    excelHeader1.font = { bold: true }

    // Segunda linha do cabeçalho - só adiciona se houver mais de uma coluna
    if (showOrcado || showDiferenca) {
      const headerRow2 = [""]
      periodosFiltrados.forEach(() => {
        headerRow2.push("Real")
        if (showVertical || showHorizontal) headerRow2.push("AV/AH")
        if (showOrcado) headerRow2.push("Orçado")
        if (showDiferenca) headerRow2.push("Dif.")
      })
      headerRow2.push("Real")
      if (showVertical || showHorizontal) headerRow2.push("AV/AH")
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
        const colSpan = 1 + ((showVertical || showHorizontal) ? 1 : 0) + (showOrcado ? 1 : 0) + (showDiferenca ? 1 : 0)
        if (colSpan > 1) {
          ws.mergeCells(1, colIndex, 1, colIndex + colSpan - 1)
        }
        colIndex += colSpan
      })
      // Mesclar colunas do total
      const totalColSpan = 1 + ((showVertical || showHorizontal) ? 1 : 0) + (showOrcado ? 1 : 0) + (showDiferenca ? 1 : 0)
      if (totalColSpan > 1) {
        ws.mergeCells(1, colIndex, 1, colIndex + totalColSpan - 1)
      }
    }

    // Adicionar dados recursivamente
    const addDataRows = (items: DreItem[], level = 0) => {
      items.forEach(item => {
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

        const operadores: Record<string, string> = {
          "+": "+",
          "-": "-", 
          "=": "=",
          "+/-": "±"
        }
        const operador = operadores[item.tipo] || ""
        const nomeComOperador = operador ? `(${operador}) ${item.nome}` : item.nome

        const row: (string | number)[] = ["  ".repeat(level) + nomeComOperador]
        periodosFiltrados.forEach(p => {
          const real = Math.round(calcularValor(item, p))
          const orcado = Math.round(calcularOrcamento(item, p))
          row.push(real)
          if (showVertical || showHorizontal) {
            const av = item.vertical_mensais?.[p] || item.vertical_trimestrais?.[p] || item.vertical_anuais?.[p] || "–"
            const ah = item.horizontal_mensais?.[p] || item.horizontal_trimestrais?.[p] || item.horizontal_anuais?.[p] || "–"
            row.push(`${av} ${ah}`)
          }
          if (showOrcado) row.push(orcado)
          if (showDiferenca) row.push(real - orcado)
        })
        row.push(Math.round(total))
        if (showVertical || showHorizontal) {
          const avTotal = item.vertical_total || "–"
          row.push(avTotal)
        }
        if (showOrcado) row.push(Math.round(totalOrc))
        if (showDiferenca) row.push(Math.round(total - totalOrc))

        const excelRow = ws.addRow(row)
        if (item.tipo === "=") {
          excelRow.font = { bold: true }
        }

        if (item.expandivel && item.classificacoes) {
          addDataRows(item.classificacoes, level + 1)
        }
      })
    }

    addDataRows(data)

    wb.xlsx.writeBuffer().then((buffer: ArrayBuffer) => {
      const blob = new Blob([buffer], { type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" })
      saveAs(blob, `DRE_${periodo}_${filtroAno}.xlsx`)
    })
  }

  const renderItem = (item: DreItem, level = 0): React.ReactNode => {
    console.log('🎬 renderItem chamada para:', {
      nome: item.nome,
      level,
      expandivel: item.expandivel,
      hasClassificacoes: !!item.classificacoes,
      classificacoesLength: item.classificacoes?.length || 0
    });
    
    const isOpen = openSections[item.nome]
    const hasChildren = item.expandivel && item.classificacoes && item.classificacoes.length > 0

    const total = calcularTotal(
      periodo === "mes" ? item.valores_mensais :
      periodo === "trimestre" ? item.valores_trimestrais :
      item.valores_anuais
    )
    const totalOrcamento = calcularTotalOrcamento(
      periodo === "mes" ? item.orcamentos_mensais :
      periodo === "trimestre" ? item.orcamentos_trimestrais :
      item.orcamentos_anuais
    )

    const totalVerticalPct = calcularAVTotalDinamica(total)

    return (
      <React.Fragment key={item.nome}>
        <TableRow className={item.tipo === "=" ? "font-semibold bg-muted/20" : ""}>
          <TableCell 
            style={{ paddingLeft: `${level * 20 + 16}px` }}
            className="py-3 md:sticky md:left-0 md:z-10 bg-background border-r border-border"
          >
            <div className="flex items-center gap-2">
              {hasChildren && (
                <button
                  onClick={() => toggle(item.nome)}
                  className="p-0 h-4 w-4 flex items-center justify-center hover:bg-muted rounded"
                >
                  <ChevronDown
                    className={`h-3 w-3 transition-transform ${
                      isOpen ? "rotate-180" : ""
                    }`}
                  />
                </button>
              )}
              {renderNomeComOperador(item)}
            </div>
          </TableCell>

          {periodosFiltrados.map(p => {
            const valor = calcularValor(item, p)
            const orcamento = calcularOrcamento(item, p)
            
            const getVerticalPct = () => {
              if (periodo === "mes") return item.vertical_mensais?.[p]
              if (periodo === "trimestre") return item.vertical_trimestrais?.[p]
              if (periodo === "ano") return item.vertical_anuais?.[p] ?? item.vertical_anuais?.[`${p}.0`]
              return undefined
            }

            const getHorizontalPct = () => {
              if (periodo === "mes") return item.horizontal_mensais?.[p]
              if (periodo === "trimestre") return item.horizontal_trimestrais?.[p]
              if (periodo === "ano") return item.horizontal_anuais?.[p] ?? item.horizontal_anuais?.[`${p}.0`]
              return undefined
            }

            const getVerticalOrcPct = () => {
              if (periodo === "mes") return item.vertical_orcamentos_mensais?.[p]
              if (periodo === "trimestre") return item.vertical_orcamentos_trimestrais?.[p]
              if (periodo === "ano") return item.vertical_orcamentos_anuais?.[p] ?? item.vertical_orcamentos_anuais?.[`${p}.0`]
              return undefined
            }

            const getHorizontalOrcPct = () => {
              if (periodo === "mes") return item.horizontal_orcamentos_mensais?.[p]
              if (periodo === "trimestre") return item.horizontal_orcamentos_trimestrais?.[p]
              if (periodo === "ano") return item.horizontal_orcamentos_anuais?.[p] ?? item.horizontal_orcamentos_anuais?.[`${p}.0`]
              return undefined
            }

            return (
              <React.Fragment key={p}>
                <TableCell className="text-right">
                  {renderValor(valor)}
                </TableCell>
                {/* Colunas de AV/AH DEPOIS de Real */}
                {(() => {
                  const shouldShow = showVertical || showHorizontal;
                  const verticalPct = getVerticalPct();
                  const horizontalPct = getHorizontalPct();
                  
                  // Debug mais detalhado para classificações
                  if (level > 0) {
                    console.log('🔍 CLASSIFICAÇÃO - Renderizando coluna AV/AH:', { 
                      shouldShow, 
                      showVertical, 
                      showHorizontal, 
                      itemNome: item.nome,
                      level,
                      verticalPct,
                      horizontalPct,
                      hasVerticalMensais: !!item.vertical_mensais,
                      hasHorizontalMensais: !!item.horizontal_mensais,
                      verticalMensaisKeys: item.vertical_mensais ? Object.keys(item.vertical_mensais) : [],
                      horizontalMensaisKeys: item.horizontal_mensais ? Object.keys(item.horizontal_mensais) : [],
                      itemKeys: Object.keys(item)
                    });
                  }
                  
                  // Log para todos os itens (incluindo principais)
                  console.log('📊 ITEM - Dados de análise:', {
                    itemNome: item.nome,
                    level,
                    shouldShow,
                    showVertical,
                    showHorizontal,
                    verticalPct,
                    horizontalPct,
                    hasVerticalMensais: !!item.vertical_mensais,
                    hasHorizontalMensais: !!item.horizontal_mensais
                  });
                  
                  if (shouldShow) {
                    console.log('✅ Renderizando coluna AV/AH para:', item.nome);
                    return (
                      <TableCell className="text-right">
                        {renderAnalises(verticalPct, horizontalPct)}
                      </TableCell>
                    );
                  } else {
                    console.log('❌ NÃO renderizando coluna AV/AH para:', item.nome, { shouldShow, showVertical, showHorizontal });
                    return null;
                  }
                })()}
                {showOrcado && (
                  <TableCell className="text-right">
                    {renderValorOrcamento(orcamento)}
                  </TableCell>
                )}
                {showDiferenca && (
                  <TableCell className="text-right">
                    {renderValorDiferenca(valor, orcamento)}
                  </TableCell>
                )}
              </React.Fragment>
            )
          })}

          <TableCell className="text-right font-medium">
            {renderValor(total)}
          </TableCell>
          {/* Coluna de AV/AH do Total DEPOIS de Real */}
          {(showVertical || showHorizontal) && (
            <TableCell className="text-right font-medium">
              {renderAnalises(totalVerticalPct, undefined)}
            </TableCell>
          )}
          {showOrcado && (
            <TableCell className="text-right font-medium">
              {renderValorOrcamento(totalOrcamento)}
            </TableCell>
          )}
          {showDiferenca && (
            <TableCell className="text-right font-medium">
              {renderValorDiferenca(total, totalOrcamento)}
            </TableCell>
          )}
        </TableRow>

        {hasChildren && isOpen && item.classificacoes?.map(child => {
          console.log('🔄 Renderizando classificação:', {
            nome: child.nome,
            level: level + 1,
            hasVerticalMensais: !!child.vertical_mensais,
            hasHorizontalMensais: !!child.horizontal_mensais,
            verticalMensaisKeys: child.vertical_mensais ? Object.keys(child.vertical_mensais) : [],
            horizontalMensaisKeys: child.horizontal_mensais ? Object.keys(child.horizontal_mensais) : [],
            allKeys: Object.keys(child)
          });
          return renderItem(child, level + 1);
        })}
      </React.Fragment>
    )
  }

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>DRE - Demonstração do Resultado do Exercício</CardTitle>
          <CardDescription>Carregando dados financeiros...</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {Array.from({ length: 8 }).map((_, i) => (
              <Skeleton key={i} className="h-8 w-full" />
            ))}
          </div>
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>DRE - Demonstração do Resultado do Exercício</CardTitle>
          <CardDescription>Erro ao carregar dados</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-destructive">{error}</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>DRE - Demonstração do Resultado do Exercício</CardTitle>
            <CardDescription>
              Análise detalhada dos resultados financeiros por período
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <Button onClick={exportExcel} variant="outline" size="sm">
              Exportar Excel
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {/* Controles */}
        <div className="flex flex-wrap items-center gap-4 mb-4 p-4 bg-muted/30 rounded-lg">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium">Período:</span>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" size="sm">
                  {periodo === "mes" ? "Mensal" : periodo === "trimestre" ? "Trimestral" : "Anual"}
                  <ChevronDown className="ml-2 h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent>
                <DropdownMenuItem onClick={() => setPeriodo("mes")}>Mensal</DropdownMenuItem>
                <DropdownMenuItem onClick={() => setPeriodo("trimestre")}>Trimestral</DropdownMenuItem>
                <DropdownMenuItem onClick={() => setPeriodo("ano")}>Anual</DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-sm font-medium">Ano:</span>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" size="sm">
                  {filtroAno === "todos" ? "Todos" : filtroAno}
                  <ChevronDown className="ml-2 h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent>
                <DropdownMenuItem onClick={() => setFiltroAno("todos")}>Todos</DropdownMenuItem>
                {anos.map(ano => (
                  <DropdownMenuItem key={ano} onClick={() => setFiltroAno(String(ano))}>
                    {ano}
                  </DropdownMenuItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-sm font-medium">Indicadores:</span>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" size="sm">
                  Opções de Análise
                  <ChevronDown className="ml-2 h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent>
                <DropdownMenuItem onClick={() => setShowVertical(!showVertical)}>
                  <Checkbox
                    checked={showVertical}
                    onCheckedChange={setShowVertical}
                    className="mr-2"
                  />
                  Análise Vertical
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => setShowHorizontal(!showHorizontal)}>
                  <Checkbox
                    checked={showHorizontal}
                    onCheckedChange={setShowHorizontal}
                    className="mr-2"
                  />
                  Análise Horizontal
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => setShowOrcado(!showOrcado)}>
                  <Checkbox
                    checked={showOrcado}
                    onCheckedChange={setShowOrcado}
                    className="mr-2"
                  />
                  Orçado
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => setShowDiferenca(!showDiferenca)}>
                  <Checkbox
                    checked={showDiferenca}
                    onCheckedChange={setShowDiferenca}
                    className="mr-2"
                  />
                  Diferença
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>

          <Button onClick={toggleAll} variant="outline" size="sm">
            {allExpanded ? "Recolher Tudo" : "Expandir Tudo"}
          </Button>
        </div>

        {/* Tabela */}
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
                    colSpan={1 + (showOrcado ? 1 : 0) + (showDiferenca ? 1 : 0) + ((showVertical || showHorizontal) ? 1 : 0)} 
                    className="text-center min-w-[120px] bg-muted/30 border-r font-semibold"
                  >
                    {p}
                  </TableHead>
                ))}
                <TableHead 
                  colSpan={1 + (showOrcado ? 1 : 0) + (showDiferenca ? 1 : 0) + ((showVertical || showHorizontal) ? 1 : 0)} 
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
                      {(showVertical || showHorizontal) && (
                        <TableHead className="text-right min-w-[120px] bg-muted/10">
                          AV/AH
                        </TableHead>
                      )}
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
                  {(showVertical || showHorizontal) && (
                    <TableHead className="text-right min-w-[120px] bg-muted/10">
                      AV/AH
                    </TableHead>
                  )}
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
              {data.map(item => renderItem(item))}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  )
}
