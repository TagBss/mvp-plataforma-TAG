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
  orcamentos_mensais?: Record<string, number>
  orcamentos_trimestrais?: Record<string, number>
  orcamentos_anuais?: Record<string, number>
  orcamento_total?: number
  classificacoes?: DreItem[]
}

type DreResponse = {
  success: boolean
  meses: string[]
  trimestres: string[]
  anos: number[]
  data: DreItem[]
  source: string
  total_categorias: number
}

export default function DreTablePostgreSQL() {
  const [data, setData] = useState<DreItem[]>([])
  const [meses, setMeses] = useState<string[]>([])
  const [trimestres, setTrimestres] = useState<string[]>([])
  const [anos, setAnos] = useState<number[]>([])
  const [openSections, setOpenSections] = useState<Record<string, boolean>>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filtroAno, setFiltroAno] = useState<string>("")
  const [showOrcado, setShowOrcado] = useState(false)
  const [showDiferenca, setShowDiferenca] = useState(false)
  const [allExpanded, setAllExpanded] = useState(false)
  const [periodo, setPeriodo] = useState<"mes" | "trimestre" | "ano">("mes")
  const [dataSource, setDataSource] = useState<string>("")

  useEffect(() => {
    console.log("🔄 Iniciando carregamento DRE N0 PostgreSQL...")
    
    api.get("/dre-n0/")
      .then(res => {
        console.log("✅ Resposta recebida:", res.status, res.data)
        
        const result: DreResponse = res.data
        if (result.success) {
          console.log("📊 Dados processados:", {
            categorias: result.data.length,
            meses: result.meses.length,
            trimestres: result.trimestres.length,
            anos: result.anos.length
          })
          
          setData(result.data)
          setMeses(result.meses)
          setTrimestres(result.trimestres)
          setAnos(result.anos)
          setDataSource(result.source)
          
          if (result.anos && result.anos.length > 0) {
            const ultimoAno = Math.max(...result.anos)
            setFiltroAno(String(ultimoAno))
            console.log("📅 Ano filtrado:", ultimoAno)
          }
        } else {
          console.error("❌ Resposta não foi bem-sucedida:", result)
          throw new Error("Resposta não foi bem-sucedida")
        }
      })
      .catch(err => {
        console.error('❌ Erro ao carregar DRE N0 PostgreSQL:', err)
        console.error('❌ Detalhes do erro:', {
          message: err.message,
          response: err.response?.data,
          status: err.response?.status
        })
        setError(`Erro ao carregar dados: ${err.message}`)
      })
      .finally(() => {
        console.log("🏁 Carregamento finalizado")
        setLoading(false)
      })
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
  
  // Validação para evitar erros quando os arrays estão vazios
  if (periodo === "mes" && meses && meses.length > 0) {
    periodosFiltrados = meses.filter(m => filtroAno === "todos" ? true : m.startsWith(filtroAno)).sort()
  } else if (periodo === "trimestre" && trimestres && trimestres.length > 0) {
    periodosFiltrados = trimestres.filter(t => filtroAno === "todos" ? true : t.startsWith(filtroAno)).sort()
  } else if (periodo === "ano" && anos && anos.length > 0) {
    periodosFiltrados = filtroAno === "todos" ? anos.map(String).sort() : [filtroAno]
  }
  
  // Fallback para evitar erro quando não há períodos
  if (periodosFiltrados.length === 0) {
    periodosFiltrados = ["N/A"]
  }

  const calcularValor = (item: DreItem, periodoLabel: string): number => {
    if (periodo === "mes") return item.valores_mensais?.[periodoLabel] ?? 0
    if (periodo === "trimestre") return item.valores_trimestrais?.[periodoLabel] ?? 0
    if (periodo === "ano") return item.valores_anuais?.[periodoLabel] ?? 0
    return 0
  }

  const calcularOrcamento = (item: DreItem, periodoLabel: string): number => {
    if (periodo === "mes") return item.orcamentos_mensais?.[periodoLabel] ?? 0
    if (periodo === "trimestre") return item.orcamentos_trimestrais?.[periodoLabel] ?? 0
    if (periodo === "ano") return item.orcamentos_anuais?.[periodoLabel] ?? 0
    return 0
  }

  const calcularTotal = (valores: Record<string, number> | undefined): number => {
    return periodosFiltrados.reduce((total, p) => total + (valores?.[p] ?? 0), 0)
  }

  const calcularTotalOrcamento = (orcamentos: Record<string, number> | undefined): number => {
    return periodosFiltrados.reduce((total, p) => total + (orcamentos?.[p] ?? 0), 0)
  }

  const calcularDiffPct = (real: number, orcado: number): string | undefined => {
    if (orcado === 0) return undefined
    const diff = ((real - orcado) / orcado) * 100
    return `${diff.toFixed(1)}%`
  }

  // Função para renderizar valor da diferença
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

  const renderValor = (valor: number) => (
    <div className="flex flex-col text-right">
      <span className={valor < 0 ? "text-red-500" : ""}>
        {valor.toLocaleString("pt-BR", {
          minimumFractionDigits: 0,
          maximumFractionDigits: 0,
        })}
      </span>
    </div>
  );

  const renderValorOrcamento = (valor: number) => (
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
    const ws = wb.addWorksheet("DRE PostgreSQL")

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

    // Adicionar dados
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

      const operadores: Record<string, string> = {
        "+": "+",
        "-": "-", 
        "=": "=",
        "+/-": "±"
      }
      const operador = operadores[item.tipo] || ""
      const nomeComOperador = operador ? `(${operador}) ${item.nome}` : item.nome

      const row: (string | number)[] = [nomeComOperador]
      periodosFiltrados.forEach(p => {
        const real = Math.round(calcularValor(item, p))
        const orcado = Math.round(calcularOrcamento(item, p))
        row.push(real)
        if (showOrcado) row.push(orcado)
        if (showDiferenca) row.push(real - orcado)
      })
      row.push(Math.round(total))
      if (showOrcado) row.push(Math.round(totalOrc))
      if (showDiferenca) row.push(Math.round(total - totalOrc))

      const excelRow = ws.addRow(row)
      if (item.tipo === "=") {
        excelRow.font = { bold: true }
      }
    })

    wb.xlsx.writeBuffer().then((buffer: ArrayBuffer) => {
      const blob = new Blob([buffer], { type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" })
      saveAs(blob, `DRE_Nivel0_PostgreSQL_${periodo}_${filtroAno}.xlsx`)
    })
  }

  const renderItem = (item: DreItem): React.ReactNode => {
    const total = calcularTotal(
      periodo === "mes" ? item.valores_mensais :
      periodo === "trimestre" ? item.valores_trimestrais :
      item.valores_anuais
    )
    const totalOrcamento = calcularTotalOrcamento(
      periodo === "mes" ? item.orcamentos_mensais :
      periodo === "trimestre" ? item.orcamentos_trimestrais :
      item.valores_anuais
    )

    return (
      <TableRow key={item.nome} className={item.tipo === "=" ? "font-semibold bg-muted/20" : ""}>
        <TableCell className="py-3 md:sticky md:left-0 md:z-10 bg-background border-r border-border">
          <div className="flex items-center gap-2">
            {renderNomeComOperador(item)}
          </div>
        </TableCell>

        {periodosFiltrados.map(p => {
          const valor = calcularValor(item, p)
          const orcamento = calcularOrcamento(item, p)
          
          return (
            <React.Fragment key={p}>
              <TableCell className="text-right">
                {renderValor(valor)}
              </TableCell>
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
    )
  }

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>DRE Nível 0 - Demonstração do Resultado do Exercício</CardTitle>
          <CardDescription>Carregando dados do PostgreSQL...</CardDescription>
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
          <CardTitle>DRE Nível 0 - Demonstração do Resultado do Exercício</CardTitle>
          <CardDescription>Erro ao carregar dados</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-destructive">{error}</p>
          <div className="mt-4 p-4 bg-muted/30 rounded-lg">
            <h3 className="font-semibold mb-2">🔧 Solução:</h3>
            <ol className="list-decimal list-inside space-y-1 text-sm">
              <li>Verifique se o backend está rodando</li>
              <li>Acesse <code className="bg-muted px-2 py-1 rounded">/admin/debug-views</code> para verificar as views</li>
              <li>Execute <code className="bg-muted px-2 py-1 rounded">/admin/execute-views</code> para criar as views</li>
            </ol>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>DRE Nível 0 - Demonstração do Resultado do Exercício</CardTitle>
            <CardDescription>
              Estrutura principal da DRE com totalizadores agregados - Dados do PostgreSQL
              {dataSource && <span className="ml-2 text-blue-600">({dataSource})</span>}
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

          <div className="text-sm text-muted-foreground">
            📊 {data.length} categorias encontradas
          </div>
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
                    colSpan={1 + (showOrcado ? 1 : 0) + (showDiferenca ? 1 : 0)} 
                    className="text-center min-w-[120px] bg-muted/30 border-r font-semibold"
                  >
                    {p}
                  </TableHead>
                ))}
                <TableHead 
                  colSpan={1 + (showOrcado ? 1 : 0) + (showDiferenca ? 1 : 0)} 
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
              {data && data.length > 0 ? (
                data.map(item => renderItem(item))
              ) : (
                <TableRow>
                  <TableCell colSpan={periodosFiltrados.length + 1} className="text-center py-8 text-muted-foreground">
                    Nenhum dado encontrado
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  )
}
