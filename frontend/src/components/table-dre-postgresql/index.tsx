import { useEffect, useState } from "react"
import { ChevronDown, ChevronsDown, ChevronsUp, ChevronUp } from "lucide-react"
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
  descricao?: string // Adicionado para a nova renderização
  // Análise Horizontal e Vertical (campos padrão)
  analise_horizontal_mensal?: Record<string, number | string>
  analise_vertical_mensal?: Record<string, number | string>
  analise_horizontal_trimestral?: Record<string, number | string>
  analise_vertical_trimestral?: Record<string, number | string>
  analise_horizontal_anual?: Record<string, number | string>
  analise_vertical_anual?: Record<string, number | string>
  // Análise Horizontal e Vertical (campos das classificações)
  horizontal_mensais?: Record<string, number | string>
  vertical_mensais?: Record<string, number | string>
  horizontal_trimestrais?: Record<string, number | string>
  vertical_trimestrais?: Record<string, number | string>
  horizontal_anuais?: Record<string, number | string>
  vertical_anuais?: Record<string, number | string>
  // NOVAS COLUNAS: AV total calculada no backend
  av_total_percentual?: number
  av_total_formatada?: string
  // NOVAS COLUNAS: AV total dinâmica por período
  av_total_mensal?: Record<string, number>
  av_total_trimestral?: Record<string, number>
  av_total_anual?: Record<string, number>
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
  const [showAnaliseVertical, setShowAnaliseVertical] = useState(false)
  const [showAnaliseHorizontal, setShowAnaliseHorizontal] = useState(false)
  const [allExpanded, setAllExpanded] = useState(false)
  const [periodo, setPeriodo] = useState<"mes" | "trimestre" | "ano">("mes")
  const [dataSource, setDataSource] = useState<string>("")
  const [expandedItems, setExpandedItems] = useState<Record<string, boolean>>({})
  const [classificacoesCache, setClassificacoesCache] = useState<Record<string, DreItem[]>>({})
  const [showValoresZerados, setShowValoresZerados] = useState<boolean>(false)

  useEffect(() => {
    console.log("🔄 Iniciando carregamento DRE N0 PostgreSQL...")
    
    api.get("/dre-n0/")
      .then(res => {
        console.log("✅ Resposta recebida:", res.status, res.data)
        
        const result: DreResponse = res.data
        if (result.success) {
          setData(result.data)
          setMeses(result.meses)
          setTrimestres(result.trimestres)
          setAnos(result.anos)
          setDataSource(result.source)
          
          if (result.anos && result.anos.length > 0) {
            const ultimoAno = Math.max(...result.anos)
            setFiltroAno(String(ultimoAno))
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

  // Função para buscar classificações de uma conta DRE N2
  const buscarClassificacoes = async (dreN2Name: string) => {
    try {
      // Verificar se já está no cache
      if (classificacoesCache[dreN2Name]) {
        return classificacoesCache[dreN2Name]
      }

      const response = await api.get(`/dre-n0/classificacoes/${encodeURIComponent(dreN2Name)}`)
      
      if (response.data.success) {
        const classificacoes = response.data.data
        
        // Adicionar ao cache
        setClassificacoesCache(prev => ({
          ...prev,
          [dreN2Name]: classificacoes
        }))
        
        return classificacoes
      } else {
        return []
      }
    } catch (error) {
      console.error(`❌ Erro ao buscar classificações para ${dreN2Name}:`, error)
      return []
    }
  }

  // Função para expandir todas as classificações
  const expandirTodasClassificacoes = async () => {
    console.log("🔽 Expandindo todas as classificações...")
    
    // Buscar classificações para todas as contas expansíveis
    const novasExpansoes: Record<string, boolean> = {}
    const novasClassificacoes: Record<string, DreItem[]> = {}
    
    for (const item of data) {
      if (item.expandivel) {
        console.log(`🔽 Expandindo: ${item.nome}`)
        novasExpansoes[item.nome] = true
        
        // Buscar classificações se ainda não estiverem no cache
        if (!classificacoesCache[item.nome]) {
          try {
            const classificacoes = await buscarClassificacoes(item.nome)
            novasClassificacoes[item.nome] = classificacoes
          } catch (error) {
            console.error(`❌ Erro ao buscar classificações para ${item.nome}:`, error)
          }
        } else {
          novasClassificacoes[item.nome] = classificacoesCache[item.nome]
        }
      }
      
      // Atualizar estado de expansão
      setExpandedItems(novasExpansoes)
      
      // Atualizar dados com classificações
      if (Object.keys(novasClassificacoes).length > 0) {
        setData(prevData => 
          prevData.map(d => 
            novasClassificacoes[d.nome] 
              ? { ...d, classificacoes: novasClassificacoes[d.nome] }
              : d
          )
        )
      }
    }
    
    // Atualizar estado de expansão
    setExpandedItems(novasExpansoes)
    
    // Atualizar dados com classificações
    if (Object.keys(novasClassificacoes).length > 0) {
      setData(prevData => 
        prevData.map(d => 
          novasClassificacoes[d.nome] 
            ? { ...d, classificacoes: novasClassificacoes[d.nome] }
            : d
        )
      )
    }
    
    console.log(`✅ ${Object.keys(novasExpansoes).length} classificações expandidas`)
  }

  // Função para recolher todas as classificações
  const recolherTodasClassificacoes = () => {
    console.log("🔼 Recolhendo todas as classificações...")
    
    // Limpar todas as expansões
    setExpandedItems({})
    
    console.log("✅ Todas as classificações recolhidas")
  }

  // Função para expandir/colapsar item com classificações
  const toggleExpansao = async (item: DreItem) => {
    if (!item.expandivel) return

    const isExpanded = expandedItems[item.nome] || false
    
    if (!isExpanded) {
      // Expandir: buscar classificações
      console.log(`🔽 Expandindo classificações para: ${item.nome}`)
      const classificacoes = await buscarClassificacoes(item.nome)
      
      // Atualizar o item com as classificações
      setData(prevData => 
        prevData.map(d => 
          d.nome === item.nome 
            ? { ...d, classificacoes } 
            : d
        )
      )
      
      // Atualizar cache
      setClassificacoesCache(prev => ({
        ...prev,
        [item.nome]: classificacoes
      }))
    }
    
    // Alternar estado de expansão
    setExpandedItems(prev => ({
      ...prev,
      [item.nome]: !isExpanded
    }))
    
    console.log(`✅ Estado de expansão para ${item.nome}: ${!isExpanded}`)
  }

  let periodosFiltrados: string[] = []
  
  // Validação para evitar erros quando os arrays estão vazios
  if (periodo === "mes" && meses && meses.length > 0) {
    periodosFiltrados = meses.filter(m => filtroAno === "todos" ? true : m.startsWith(filtroAno)).sort()
  } else if (periodo === "trimestre" && trimestres && trimestres.length > 0) {
    // CORREÇÃO: Agora com formato "2025-Q1", startsWith funciona perfeitamente
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
    const resultado = periodosFiltrados.reduce((total, p) => {
      const valor = valores?.[p] ?? 0;
      return total + valor;
    }, 0);
    
    return resultado;
  }

  const calcularTotalOrcamento = (orcamentos: Record<string, number> | undefined): number => {
    return periodosFiltrados.reduce((total, p) => total + (orcamentos?.[p] ?? 0), 0)
  }

  const calcularDiffPct = (real: number, orcado: number): string | undefined => {
    if (orcado === 0) return undefined
    const diff = ((real - orcado) / orcado) * 100
    return `${diff.toFixed(1)}%`
  }

  // Função para calcular análise vertical dinâmica do total
  const calcularVerticalTotalDinamica = (): number => {
    // CORREÇÃO: Usar apenas o Faturamento como base, não a soma de todas as contas
    const faturamentoItem = data.find(item => item.nome === "Faturamento");
    
    if (!faturamentoItem) {
      return 0;
    }
    
    const totalFaturamento = calcularTotal(
      periodo === "mes" ? faturamentoItem.valores_mensais :
      periodo === "trimestre" ? faturamentoItem.valores_trimestrais :
      faturamentoItem.valores_anuais
    );
    
    return Math.abs(totalFaturamento);
  };

  // Função para calcular AV% dinâmica do total
  const calcularAVTotalDinamica = (valorTotal: number): string | undefined => {
    const totalGeral = calcularVerticalTotalDinamica();
    
    if (totalGeral === 0) {
      return undefined;
    }
    
    // CORREÇÃO: Manter o sinal do valor original
    const percentual = (valorTotal / totalGeral) * 100;
    const resultado = `${percentual.toFixed(1)}%`;
    
    return resultado;
  };

  // Função para calcular análise horizontal (variação vs período anterior)
  const calcularAnaliseHorizontal = (item: DreItem, periodoLabel: string): number => {
    let valor: any = 0
    
    // Tentar primeiro os campos das classificações (horizontal_*)
    if (periodo === "mes") valor = item.horizontal_mensais?.[periodoLabel]
    else if (periodo === "trimestre") valor = item.horizontal_trimestrais?.[periodoLabel]
    else if (periodo === "ano") valor = item.horizontal_anuais?.[periodoLabel]
    
    // Se não encontrar, tentar os campos padrão (analise_horizontal_*)
    if (valor === undefined || valor === 0) {
      if (periodo === "mes") valor = item.analise_horizontal_mensal?.[periodoLabel]
      else if (periodo === "trimestre") valor = item.analise_horizontal_trimestral?.[periodoLabel]
      else if (periodo === "ano") valor = item.analise_horizontal_anual?.[periodoLabel]
    }
    
    // Se o valor for uma string (ex: "105.17%"), extrair o número
    if (typeof valor === 'string') {
      const numero = parseFloat(valor.replace('%', ''))
      return isNaN(numero) ? 0 : numero
    }
    
    // Se for número, retornar diretamente
    if (typeof valor === 'number') return valor
    
    return 0
  }

  // Função para calcular análise vertical (representatividade sobre Faturamento)
  const calcularAnaliseVertical = (item: DreItem, periodoLabel: string): number => {
    let valor: any = 0
    
    // Tentar primeiro os campos das classificações (vertical_*)
    if (periodo === "mes") valor = item.vertical_mensais?.[periodoLabel]
    else if (periodo === "trimestre") valor = item.vertical_trimestrais?.[periodoLabel]
    else if (periodo === "ano") valor = item.vertical_anuais?.[periodoLabel]
    
    // Se não encontrar, tentar os campos padrão (analise_vertical_*)
    if (valor === undefined || valor === 0) {
      if (periodo === "mes") valor = item.analise_vertical_mensal?.[periodoLabel]
      else if (periodo === "trimestre") valor = item.analise_vertical_trimestral?.[periodoLabel]
      else if (periodo === "ano") valor = item.analise_vertical_anual?.[periodoLabel]
    }
    
    // Se o valor for uma string (ex: "100.00%"), extrair o número
    if (typeof valor === 'string') {
      const numero = parseFloat(valor.replace('%', ''))
      return isNaN(numero) ? 0 : numero
    }
    
    // Se for número, retornar diretamente
    if (typeof valor === 'number') return valor
    
    return 0
  }

  // Função para renderizar análise horizontal com setas
  const renderAnaliseHorizontal = (valor: number) => {
    // Validação adicional para garantir que valor seja um número válido
    if (typeof valor !== 'number' || isNaN(valor) || valor === 0) {
      return <span className="text-muted-foreground">-</span>
    }
    
    const isPositive = valor > 0
    const sign = isPositive ? "+" : "-"
    
    return (
      <span>
        {sign}{Math.abs(valor).toFixed(1)}%
      </span>
    )
  }

  // Função para renderizar análise vertical
  const renderAnaliseVertical = (valor: number) => {
    // Validação adicional para garantir que valor seja um número válido
    if (typeof valor !== 'number' || isNaN(valor) || valor === 0) {
      return <span className="text-muted-foreground">-</span>
    }
    
    return (
      <span className="font-medium">
        {valor.toFixed(1)}%
      </span>
    )
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
    // CORREÇÃO: Usar descricao se disponível, senão usar nome (que já vem com operador do backend)
    const nomeExibicao = item.descricao || item.nome
    
    return (
      <span className={item.tipo === "=" ? "font-semibold" : ""}>
        {nomeExibicao}
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
      if (showAnaliseVertical) {
        headerRow1.push("") // AV
      }
      if (showAnaliseHorizontal) {
        headerRow1.push("") // AH
      }
    })
    headerRow1.push("Total")
    if (showOrcado) headerRow1.push("")
    if (showDiferenca) headerRow1.push("")
    if (showAnaliseVertical) {
      headerRow1.push("") // AV
    }
    if (showAnaliseHorizontal) {
      headerRow1.push("") // AH
    }

    const excelHeader1 = ws.addRow(headerRow1)
    excelHeader1.font = { bold: true }

    // Segunda linha do cabeçalho - Real, Orçado, Dif., AV, AH
    const headerRow2 = [""]
    periodosFiltrados.forEach(() => {
      headerRow2.push("Real")
      if (showOrcado) headerRow2.push("Orçado")
      if (showDiferenca) headerRow2.push("Dif.")
      if (showAnaliseVertical) {
        headerRow2.push("AV")
      }
      if (showAnaliseHorizontal) {
        headerRow2.push("AH")
      }
    })
    headerRow2.push("Real")
    if (showOrcado) headerRow2.push("Orçado")
    if (showDiferenca) headerRow2.push("Dif.")
    if (showAnaliseVertical) {
      headerRow2.push("AV")
    }
    if (showAnaliseHorizontal) {
      headerRow2.push("AH")
    }

    const excelHeader2 = ws.addRow(headerRow2)
    excelHeader2.font = { bold: true }

    // Mesclar células da primeira linha - só se houver segunda linha
    if (showOrcado || showDiferenca || showAnaliseVertical || showAnaliseHorizontal) {
      ws.mergeCells(1, 1, 2, 1) // Coluna Descrição
      let colIndex = 2
      periodosFiltrados.forEach(() => {
        const colSpan = 1 + (showOrcado ? 1 : 0) + (showDiferenca ? 1 : 0) + (showAnaliseVertical ? 1 : 0) + (showAnaliseHorizontal ? 1 : 0) // Real + Orçado + Dif. + AV + AH
        if (colSpan > 1) {
          ws.mergeCells(1, colIndex, 1, colIndex + colSpan - 1)
        }
        colIndex += colSpan
      })
      // Mesclar colunas do total
      const totalColSpan = 1 + (showOrcado ? 1 : 0) + (showDiferenca ? 1 : 0) + (showAnaliseVertical ? 1 : 0) // Real + Orçado + Dif. + AV
      if (totalColSpan > 1) {
        ws.mergeCells(1, colIndex, 1, colIndex + totalColSpan - 1)
      }
    }

    // Adicionar dados (respeitando filtro de valores zerados)
    data.filter(item => temValoresZerados(item)).forEach(item => {
      // CORREÇÃO: Usar descricao se disponível, senão usar nome (que já vem com operador do backend)
      const nomeExibicao = item.descricao || item.nome

      const row: (string | number)[] = [nomeExibicao]
      periodosFiltrados.forEach(p => {
        const real = Math.round(calcularValor(item, p))
        const orcado = Math.round(calcularOrcamento(item, p))
        const analiseHorizontal = calcularAnaliseHorizontal(item, p)
        const analiseVertical = calcularAnaliseVertical(item, p)
        
        row.push(real)
        if (showOrcado) row.push(orcado)
        if (showDiferenca) row.push(real - orcado)
        if (showAnaliseVertical) {
          row.push(analiseVertical)
        }
        if (showAnaliseHorizontal) {
          row.push(analiseHorizontal)
        }
      })
      
      // Total
      const total = Math.round(calcularTotal(
        periodo === "mes" ? item.valores_mensais :
        periodo === "trimestre" ? item.valores_trimestrais :
        item.valores_anuais
      ))
      const totalOrc = Math.round(calcularTotalOrcamento(
        periodo === "mes" ? item.orcamentos_mensais :
        periodo === "trimestre" ? item.orcamentos_trimestrais :
        item.orcamentos_anuais
      ))
      
      row.push(total)
      if (showOrcado) row.push(totalOrc)
      if (showDiferenca) row.push(total - totalOrc)
      
      // Total AV e AH (média ponderada) - apenas se estiverem ativos
      if (showAnaliseVertical) {
        const totalAnaliseVertical = periodosFiltrados.reduce((sum, p) => {
          const av = calcularAnaliseVertical(item, p)
          return sum + av
        }, 0) / periodosFiltrados.length
        
        row.push(totalAnaliseVertical)
      }
      
      if (showAnaliseHorizontal) {
        const totalAnaliseHorizontal = periodosFiltrados.reduce((sum, p) => {
          const ah = calcularAnaliseHorizontal(item, p)
          return sum + ah
        }, 0) / periodosFiltrados.length
        
        row.push(totalAnaliseHorizontal)
      }

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

  // Função para verificar se um item tem valores não-zerados no período atual
  const temValoresZerados = (item: DreItem): boolean => {
    if (showValoresZerados) return true; // Se mostrar valores zerados, retorna true para todos
    
    const valores = periodo === "mes" ? item.valores_mensais :
                   periodo === "trimestre" ? item.valores_trimestrais :
                   item.valores_anuais;
    
    if (!valores) return false;
    
    // Verificar se há pelo menos um valor não-zerado (> 0.01 para evitar problemas de precisão)
    return periodosFiltrados.some(p => {
      const valor = valores[p] || 0;
      return Math.abs(valor) > 0.01;
    });
  };

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
                <DropdownMenuItem onClick={() => setShowAnaliseVertical(!showAnaliseVertical)}>
                  <Checkbox
                    checked={showAnaliseVertical}
                    onCheckedChange={setShowAnaliseVertical}
                    className="mr-2"
                  />
                  Análise Vertical (AV)
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => setShowAnaliseHorizontal(!showAnaliseHorizontal)}>
                  <Checkbox
                    checked={showAnaliseHorizontal}
                    onCheckedChange={setShowAnaliseHorizontal}
                    className="mr-2"
                  />
                  Análise Horizontal (AH)
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>

          <div className="flex items-center gap-2">
            <Button 
              onClick={expandirTodasClassificacoes} 
              variant="outline" 
              size="sm"
              title="Expandir todas as classificações"
            >
              <ChevronsDown className="h-4 w-4" />
            </Button>
            <Button 
              onClick={recolherTodasClassificacoes} 
              variant="outline" 
              size="sm"
              title="Recolher todas as classificações"
            >
              <ChevronsUp className="h-4 w-4" />
            </Button>
          </div>

          <div className="flex items-center gap-2">
            <Button 
              onClick={() => setShowValoresZerados(!showValoresZerados)} 
              variant="outline"
              size="sm"
              title={showValoresZerados ? "Ocultar valores zerados" : "Mostrar valores zerados"}
            >
              {showValoresZerados ? "Com valores zerados" : "Sem valores zerados"}
            </Button>
          </div>

          <div className="text-sm text-muted-foreground">
            {data.filter(item => temValoresZerados(item)).length} categorias visíveis
          </div>
        </div>

        {/* Tabela */}
        <div className="relative overflow-auto max-h-[80vh] px-6">
          <Table>
            <TableHeader>
              {/* Primeira linha do cabeçalho - períodos */}
              <TableRow>
                <TableHead
                  rowSpan={2} 
                  className="min-w-[300px] md:sticky md:left-0 md:z-10 bg-background border-r font-semibold"
                >
                  Descrição
                </TableHead>
                {periodosFiltrados.map((p) => (
                  <TableHead 
                    key={p} 
                    colSpan={1 + (showOrcado ? 1 : 0) + (showDiferenca ? 1 : 0) + (showAnaliseVertical ? 1 : 0) + (showAnaliseHorizontal ? 1 : 0)} 
                    className="text-center min-w-[120px] bg-muted/30 border-r font-semibold"
                  >
                    {p}
                  </TableHead>
                ))}
                <TableHead 
                  colSpan={1 + (showOrcado ? 1 : 0) + (showDiferenca ? 1 : 0) + (showAnaliseVertical ? 1 : 0)} 
                  className="text-center min-w-[120px] bg-muted/30 font-semibold"
                >
                  Total
                </TableHead>
              </TableRow>
              {/* Segunda linha do cabeçalho - Real, Orçado, Dif., AV */}
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
                    {showAnaliseVertical && (
                      <TableHead className="text-center min-w-[80px] bg-muted/20 border-l">
                        AV
                      </TableHead>
                    )}
                    {showAnaliseHorizontal && (
                      <TableHead className="text-center min-w-[80px] bg-muted/20 border-l">
                        AH
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
                {showAnaliseVertical && (
                  <TableHead className="text-center min-w-[80px] bg-muted/20 border-l">
                    AV
                  </TableHead>
                )}

              </TableRow>
            </TableHeader>
            <TableBody>
              {data && data.length > 0 ? (
                data.filter(item => temValoresZerados(item)).map(item => {
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

                  return (
                    <React.Fragment key={item.nome}>
                      <TableRow className={item.tipo === "=" ? "font-semibold bg-muted/20" : ""}>
                        <TableCell className="py-3 md:sticky md:left-0 md:z-10 bg-background border-r border-border">
                          <div className="flex items-center gap-2">
                            {renderNomeComOperador(item)}
                            {item.expandivel && (
                              <button
                                onClick={() => toggleExpansao(item)}
                                className="p-1 hover:bg-muted rounded transition-colors"
                                title={expandedItems[item.nome] ? "Colapsar" : "Expandir"}
                              >
                                <ChevronDown 
                                  className={`h-4 w-4 transition-transform ${
                                    expandedItems[item.nome] ? 'rotate-180' : ''
                                  }`} 
                                />
                              </button>
                            )}
                          </div>
                        </TableCell>

                        {periodosFiltrados.map(p => {
                          const valor = calcularValor(item, p)
                          const orcamento = calcularOrcamento(item, p)
                          const analiseHorizontal = calcularAnaliseHorizontal(item, p)
                          const analiseVertical = calcularAnaliseVertical(item, p)
                          
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
                                             {showAnaliseVertical && (
                 <TableCell className="text-center border-l">
                   {renderAnaliseVertical(analiseVertical)}
                 </TableCell>
               )}
               {showAnaliseHorizontal && (
                 <TableCell className="text-center border-l">
                   {renderAnaliseHorizontal(analiseHorizontal)}
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
                        {showAnaliseVertical && (
                          <TableCell className="text-center font-medium border-l">
                            {(() => {
                              // REUTILIZAR LÓGICA EXISTENTE: Calcular AV total usando a mesma lógica das outras colunas
                              let avValue = '0.0%';
                              
                              // Buscar dados de faturamento para calcular a base
                              const faturamentoItem = data.find(item => item.nome === 'Faturamento');
                              if (!faturamentoItem) return '0.0%';
                              
                              // Calcular total da conta atual para o período selecionado
                              let totalConta = 0;
                              if (periodo === 'mes') {
                                totalConta = periodosFiltrados.reduce((sum, mes) => {
                                  return sum + (item.valores_mensais?.[mes] || 0);
                                }, 0);
                              } else if (periodo === 'trimestre') {
                                totalConta = periodosFiltrados.reduce((sum, tri) => {
                                  return sum + (item.valores_trimestrais?.[tri] || 0);
                                }, 0);
                              } else if (periodo === 'ano') {
                                totalConta = periodosFiltrados.reduce((sum, ano) => {
                                  return sum + (item.valores_anuais?.[ano] || 0);
                                }, 0);
                              }
                              
                              // CORREÇÃO: Para a coluna Total, usar o TOTAL do faturamento (soma de todos os períodos)
                              // não o faturamento de um período específico
                              let totalFaturamento = 0;
                              if (periodo === 'mes') {
                                totalFaturamento = periodosFiltrados.reduce((sum, mes) => {
                                  return sum + (faturamentoItem.valores_mensais?.[mes] || 0);
                                }, 0);
                              } else if (periodo === 'trimestre') {
                                totalFaturamento = periodosFiltrados.reduce((sum, tri) => {
                                  return sum + (faturamentoItem.valores_trimestrais?.[tri] || 0);
                                }, 0);
                              } else if (periodo === 'ano') {
                                totalFaturamento = periodosFiltrados.reduce((sum, ano) => {
                                  return sum + (faturamentoItem.valores_anuais?.[ano] || 0);
                                }, 0);
                              }
                              
                              // CORREÇÃO: Para coluna Total, usar totalFaturamento (soma de todos os períodos)
                              // não faturamentoPeriodo (apenas um período)
                              if (totalFaturamento > 0) {
                                  const avPercentual = (totalConta / totalFaturamento) * 100;
                                  avValue = `${avPercentual.toFixed(1)}%`;
                              } else {
                                  // Quando faturamento total é zero, retornar "-"
                                  avValue = '-';
                              }
                              
                              return avValue;
                            })()}
                          </TableCell>
                        )}

                      </TableRow>

                      {/* Renderizar classificações expandidas */}
                      {item.expandivel && expandedItems[item.nome] && item.classificacoes && Array.isArray(item.classificacoes) && item.classificacoes.length > 0 && (
                        item.classificacoes.filter(classificacao => temValoresZerados(classificacao)).map(classificacao => {
                          const totalClass = calcularTotal(
                            periodo === "mes" ? classificacao.valores_mensais :
                            periodo === "trimestre" ? classificacao.valores_trimestrais :
                            classificacao.valores_anuais
                          )
                          
                          return (
                            <TableRow key={`${item.nome}-${classificacao.nome}`} className="bg-muted">
                              <TableCell className="py-2 md:sticky md:left-0 md:z-20 bg-muted border-r border-border pl-8">
                                <div className="flex items-center gap-2">
                                  <span className="text-sm text-muted-foreground">
                                    {classificacao.nome}
                                  </span>
                                </div>
                              </TableCell>

                              {periodosFiltrados.map(p => {
                                const valor = calcularValor(classificacao, p)
                                const orcamento = calcularOrcamento(classificacao, p)
                                const analiseHorizontal = calcularAnaliseHorizontal(classificacao, p)
                                const analiseVertical = calcularAnaliseVertical(classificacao, p)
                                
                                return (
                                  <React.Fragment key={`${p}-class`}>
                                    <TableCell className="text-right py-2">
                                      {renderValor(valor)}
                                    </TableCell>
                                    {showOrcado && (
                                      <TableCell className="text-right py-2">
                                        {renderValorOrcamento(orcamento)}
                                      </TableCell>
                                    )}
                                    {showDiferenca && (
                                      <TableCell className="text-right py-2">
                                        {renderValorDiferenca(valor, orcamento)}
                                      </TableCell>
                                    )}
                                    {showAnaliseVertical && (
                                      <TableCell className="text-center py-2 border-l">
                                        {renderAnaliseVertical(analiseVertical)}
                                      </TableCell>
                                    )}
                                    {showAnaliseHorizontal && (
                                      <TableCell className="text-center py-2 border-l">
                                        {renderAnaliseHorizontal(analiseHorizontal)}
                                      </TableCell>
                                    )}
                                  </React.Fragment>
                                )
                              })}

                              <TableCell className="text-right font-medium py-2">
                                {renderValor(totalClass)}
                              </TableCell>
                              {showOrcado && (
                                <TableCell className="text-right font-medium py-2">
                                  {renderValorOrcamento(0)}
                                </TableCell>
                              )}
                              {showDiferenca && (
                                <TableCell className="text-right font-medium py-2">
                                  {renderValorDiferenca(totalClass, 0)}
                                </TableCell>
                              )}
                              {showAnaliseVertical && (
                                <TableCell className="text-center font-medium py-2 border-l">
                                  {(() => {
                                    // REUTILIZAR LÓGICA EXISTENTE: Calcular AV total usando a mesma lógica das outras colunas
                                    let avValue = '0.0%';
                                    
                                    // Buscar dados de faturamento para calcular a base
                                    const faturamentoItem = data.find(item => item.nome === 'Faturamento');
                                    if (!faturamentoItem) return '0.0%';
                                    
                                    // Calcular total da classificação para o período selecionado
                                    let totalClassificacao = 0;
                                    if (periodo === 'mes') {
                                      totalClassificacao = periodosFiltrados.reduce((sum, mes) => {
                                        return sum + (classificacao.valores_mensais?.[mes] || 0);
                                      }, 0);
                                    } else if (periodo === 'trimestre') {
                                      totalClassificacao = periodosFiltrados.reduce((sum, tri) => {
                                        return sum + (classificacao.valores_trimestrais?.[tri] || 0);
                                      }, 0);
                                    } else if (periodo === 'ano') {
                                      totalClassificacao = periodosFiltrados.reduce((sum, ano) => {
                                        return sum + (classificacao.valores_anuais?.[ano] || 0);
                                      }, 0);
                                    }
                                    
                                    // CORREÇÃO: Para a coluna Total, usar o TOTAL do faturamento (soma de todos os períodos)
                                    // não o faturamento de um período específico
                                    let totalFaturamento = 0;
                                    if (periodo === 'mes') {
                                      totalFaturamento = periodosFiltrados.reduce((sum, mes) => {
                                        return sum + (faturamentoItem.valores_mensais?.[mes] || 0);
                                      }, 0);
                                    } else if (periodo === 'trimestre') {
                                      totalFaturamento = periodosFiltrados.reduce((sum, tri) => {
                                        return sum + (faturamentoItem.valores_trimestrais?.[tri] || 0);
                                      }, 0);
                                    } else if (periodo === 'ano') {
                                      totalFaturamento = periodosFiltrados.reduce((sum, ano) => {
                                        return sum + (faturamentoItem.valores_anuais?.[ano] || 0);
                                      }, 0);
                                    }
                                    
                                    // CORREÇÃO: Para coluna Total, usar totalFaturamento (soma de todos os períodos)
                                    // não faturamentoPeriodo (apenas um período)
                                    if (totalFaturamento > 0) {
                                        const avPercentual = (totalClassificacao / totalFaturamento) * 100;
                                        avValue = `${avPercentual.toFixed(1)}%`;
                                    } else {
                                        // Quando faturamento total é zero, retornar "-"
                                        avValue = '-';
                                    }
                                    
                                    return avValue;
                                  })()}
                                </TableCell>
                              )}

                            </TableRow>
                          )
                        })
                      )}
                    </React.Fragment>
                  )
                })
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
