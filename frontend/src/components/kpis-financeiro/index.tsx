"use client";

import { ChartAreaSaldoFinal } from "@/components/chart-area-saldo-final";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { CardSkeleton, CardSkeletonLarge } from "@/components/ui/card-skeleton";
import {  
  ArrowUpDown,
  Hourglass,
  MinusCircle,
  Package,
  PlusCircle,
  TrendingUp,
  TrendingDown,
  Wallet,
} from "lucide-react";
import { useEffect, useState } from "react";
import { FiltroMes } from "@/components/filtro-mes"
import ChartMovimentacoes from "@/components/chart-movimentacoes";
import { ChartCustosFinanceiro } from "../chart-bar-custos-financeiro";
import { apiCache } from "@/lib/api-cache";

// Função para formatar no estilo curto (Mil / Mi)
export function formatCurrencyShort(value: number, opts?: { noPrefix?: boolean }): string {
  const absValue = Math.abs(value);
  let formatted = "";

  if (absValue >= 1_000_000) {
    formatted = `${(absValue / 1_000_000).toFixed(1)} Mi`;
  } else if (absValue >= 1_000) {
    formatted = `${(absValue / 1_000).toFixed(1)} Mil`;
  } else {
    formatted = absValue.toFixed(0);
  }

  const prefix = opts?.noPrefix ? "" : "R$ ";
  return `${prefix}${value < 0 ? "-" : ""}${formatted.replace(".", ",")}`;
}

// Tipagem para MoM
type MoMData = {
  mes: string;
  valor_atual: number;
  valor_anterior: number | null;
  variacao_absoluta: number | null;
  variacao_percentual: number | null;
};

// Tipagem para análise de saldos
type SaldoData = {
  success: boolean;
  data: {
    saldo_total: number;
    mom_analysis: MoMData[];
    meses_disponiveis?: string[];
    pmr?: string;
    pmp?: string;
  };
};

// Tipagem para DFC com estrutura hierárquica
type DFCClassificacao = {
  nome: string;
  valor: number;
  valores_mensais: Record<string, number>;
  classificacoes?: DFCClassificacao[];
};

type DFCItem = {
  tipo: string;
  nome: string;
  valor: number;
  valores_mensais: Record<string, number>;
  horizontal_mensais: Record<string, string>;
  classificacoes?: DFCClassificacao[];
};

type DFCData = {
  success?: boolean;
  meses: string[];
  trimestres: string[];
  anos: number[];
  data: DFCItem[];
};

// Função utilitária para formatar períodos de meses
const mesesAbreviados = ['', 'jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez'];

function formatarPeriodo(params: { mesSelecionado: string; saldosEvolucao: Array<{ mes: string }> }) {
  const { mesSelecionado, saldosEvolucao } = params;
  
  if (mesSelecionado) {
    // Formatar mesSelecionado para "abr/25"
    if (mesSelecionado.match(/^\d{4}-\d{2}$/)) {
      const [ano, mes] = mesSelecionado.split("-");
      const mesNum = parseInt(mes, 10);
      return `${mesesAbreviados[mesNum]}/${ano.slice(-2)}`;
    }
    return mesSelecionado;
  }
  
  if (saldosEvolucao.length === 0) return "--";
  
  const primeiro = saldosEvolucao[0].mes;
  const ultimo = saldosEvolucao[saldosEvolucao.length - 1].mes;
  
  const formatar = (mes: string) => {
    if (!mes.match(/^\d{4}-\d{2}$/)) return mes;
    const [ano, m] = mes.split("-");
    const mesNum = parseInt(m, 10);
    return `${mesesAbreviados[mesNum]}/${ano.slice(-2)}`;
  };
  
  return `${formatar(primeiro)} - ${formatar(ultimo)}`;
}

function getMoMIndicator(momData: MoMData[], mesSelecionado: string) {
  if (!momData || momData.length === 0) return null;

  // Se mesSelecionado for string vazia ("Todo o período"), não retorna MoM
  if (!mesSelecionado) {
    return {
      percentage: null,
      isPositive: null,
      mesAnterior: "--",
      arrow: "",
      hasValue: false
    };
  }

  let index = -1;
  if (mesSelecionado) {
    index = momData.findIndex((item) => item.mes === mesSelecionado);
  }
  if (index === -1) {
    index = momData.length - 1;
  }
  const entry = momData[index];
  const mesAnteriorRaw = momData[index - 1]?.mes || "--";
  const variacao = entry?.variacao_percentual ?? null;

  // Formatar mesAnterior para "abr/25"
  let mesAnterior = "--";
  if (mesAnteriorRaw && mesAnteriorRaw !== "--" && mesAnteriorRaw.match(/^\d{4}-\d{2}$/)) {
    const [ano, mes] = mesAnteriorRaw.split("-");
    const mesNum = parseInt(mes, 10);
    const anoCurto = ano.slice(-2);
    mesAnterior = `${mesesAbreviados[mesNum]}/${anoCurto}`;
  }

  return {
    percentage: variacao !== null ? Math.abs(variacao) : null,
    isPositive: variacao !== null ? variacao > 0 : null,
    mesAnterior,
    arrow: variacao !== null ? (variacao > 0 ? "↗" : "↙") : "",
    hasValue: variacao !== null
  };
}

const API_BASE_URL = 'http://127.0.0.1:8000';

export default function DashFinanceiro() {
  const [mesSelecionado, setMesSelecionado] = useState<string>("");
  const [inicializado, setInicializado] = useState(false);
  const [loading, setLoading] = useState(false);
  
  // Estados dos dados
  const [saldoReceber, setSaldoReceber] = useState<SaldoData | null>(null);
  const [saldoPagar, setSaldoPagar] = useState<SaldoData | null>(null);
  const [dfc, setDfc] = useState<DFCData | null>(null);

  // Inicializar dados básicos
  useEffect(() => {
    const inicializar = async () => {
      try {
        
        const [receberRes, pagarRes, dfcRes] = await Promise.all([
          apiCache.fetchWithCache<SaldoData>(`${API_BASE_URL}/receber`),
          apiCache.fetchWithCache<SaldoData>(`${API_BASE_URL}/pagar`),
          apiCache.fetchWithCache<DFCData>(`${API_BASE_URL}/dfc`),
        ]);

        setSaldoReceber(receberRes);
        setSaldoPagar(pagarRes);
        setDfc(dfcRes);

        // Definir mês padrão
        if (receberRes.success && receberRes.data?.meses_disponiveis && receberRes.data.meses_disponiveis.length > 0) {
          const meses = receberRes.data.meses_disponiveis;
          const mesPadrao = meses[meses.length - 1];
          setMesSelecionado(mesPadrao);
        }
      } catch (error) {
        console.error("❌ Erro na inicialização:", error);
      } finally {
        setInicializado(true);
      }
    };

    inicializar();
  }, []);

  // Carregar dados por mês
  useEffect(() => {
    if (!inicializado || mesSelecionado === null || mesSelecionado === undefined) {
      return;
    }

    const carregarDadosMes = async () => {
      setLoading(true);
      
      try {
        const queryString = mesSelecionado ? `?mes=${mesSelecionado}` : '';
        
        const [receberRes, pagarRes, dfcRes] = await Promise.all([
          apiCache.fetchWithCache<SaldoData>(`${API_BASE_URL}/receber${queryString}`),
          apiCache.fetchWithCache<SaldoData>(`${API_BASE_URL}/pagar${queryString}`),
          apiCache.fetchWithCache<DFCData>(`${API_BASE_URL}/dfc`),
        ]);

        // Log apenas se houver problemas
        if (!dfcRes || !dfcRes.data || dfcRes.data.length === 0) {
          console.error("❌ DFC sem dados válidos:", dfcRes);
        } else {
          const custos = dfcRes.data.find(item => item.nome === "Custos");
          const movimentacoes = dfcRes.data.find(item => item.nome === "Movimentações");
          if (!custos) {
            console.warn("⚠️ Item 'Custos' não encontrado no DFC");
          }
          if (!movimentacoes) {
            console.warn("⚠️ Item 'Movimentações' não encontrado no DFC");
          }
        }

        setSaldoReceber(receberRes);
        setSaldoPagar(pagarRes);
        setDfc(dfcRes);

      } catch (error) {
        console.error("❌ Erro ao carregar dados:", error);
      } finally {
        setLoading(false);
      }
    };

    carregarDadosMes();
  }, [inicializado, mesSelecionado]);

  const handleMesSelecionado = (mes: string) => {
    if (!inicializado) return;
    setMesSelecionado(mes);
  };

  // Extrair dados dos estados
  const pmr = saldoReceber?.data?.pmr || null;
  const pmp = saldoPagar?.data?.pmp || null;
  const momReceber = saldoReceber?.data?.mom_analysis || [];
  const momPagar = saldoPagar?.data?.mom_analysis || [];
  
  // Extrair dados de movimentações do DFC
  const dfcData = dfc?.data;
  let movimentacoesValor = null;
  let momMovimentacoes: MoMData[] = [];

  if (dfcData && Array.isArray(dfcData)) {
    const movimentacoesItem = dfcData.find(item => item.nome === "Movimentações");
    
    if (movimentacoesItem) {
      if (!mesSelecionado) {
        // Todo o período - usar valor total
        movimentacoesValor = movimentacoesItem.valor;
      } else {
        // Mês específico - usar valores_mensais
        movimentacoesValor = movimentacoesItem.valores_mensais?.[mesSelecionado] || null;
      }

      // Converter horizontal_mensais para formato MoM
      if (movimentacoesItem.horizontal_mensais) {
        const mesesOrdenados = Object.keys(movimentacoesItem.valores_mensais || {}).sort();
        momMovimentacoes = mesesOrdenados.map((mes, idx) => {
          const valorAtual = movimentacoesItem.valores_mensais?.[mes] || 0;
          const valorAnterior = idx > 0 ? (movimentacoesItem.valores_mensais?.[mesesOrdenados[idx-1]] || null) : null;
          const horizontalStr = movimentacoesItem.horizontal_mensais?.[mes];
          
          let variacaoPercentual = null;
          let variacaoAbsoluta = null;
          
          if (horizontalStr && horizontalStr !== "–" && valorAnterior !== null) {
            const percentualMatch = horizontalStr.match(/([+-]?)(\d+\.?\d*)%/);
            if (percentualMatch) {
              const sinal = percentualMatch[1] === "-" ? -1 : 1;
              variacaoPercentual = parseFloat(percentualMatch[2]) * sinal;
              variacaoAbsoluta = valorAtual - valorAnterior;
            }
          }

          return {
            mes,
            valor_atual: valorAtual,
            valor_anterior: valorAnterior,
            variacao_absoluta: variacaoAbsoluta,
            variacao_percentual: variacaoPercentual
          };
        });
      }
    }
  }
  // Extrair dados de saldo final do DFC
  let saldoFinal = null;
  let saldoFinalMoM = null;
  let saldosEvolucaoChart: Array<{ mes: string, saldo_inicial: number, saldo_final: number }> = [];

  if (dfcData && Array.isArray(dfcData)) {
    // Encontrar itens "Saldo inicial" e "Saldo final"
    const saldoInicialItem = dfcData.find(item => item.nome === "Saldo inicial");
    const saldoFinalItem = dfcData.find(item => item.nome === "Saldo final");
    
    if (saldoFinalItem && saldoInicialItem) {
      // Calcular saldo final para o mês selecionado ou último disponível
      if (mesSelecionado && saldoFinalItem.valores_mensais[mesSelecionado] !== undefined) {
        saldoFinal = saldoFinalItem.valores_mensais[mesSelecionado];
        
        // Extrair MoM do horizontal_mensais do saldo final
        const momString = saldoFinalItem.horizontal_mensais?.[mesSelecionado];
        if (momString && momString !== "–") {
          // Parsing do formato "+12,5%" ou "-5,2%"
          const match = momString.match(/([+-]?\d+(?:,\d+)?)/);
          if (match) {
            const percentValue = parseFloat(match[1].replace(',', '.'));
            const valorAnterior = saldoFinal / (1 + percentValue / 100);
            saldoFinalMoM = {
              variacao_absoluta: saldoFinal - valorAnterior,
              variacao_percentual: percentValue
            };
          }
        }
      } else {
        // Usar último mês disponível
        const mesesDisponiveis = Object.keys(saldoFinalItem.valores_mensais).sort();
        if (mesesDisponiveis.length > 0) {
          const ultimoMes = mesesDisponiveis[mesesDisponiveis.length - 1];
          saldoFinal = saldoFinalItem.valores_mensais[ultimoMes];
          
          // Extrair MoM do último mês
          const momString = saldoFinalItem.horizontal_mensais?.[ultimoMes];
          if (momString && momString !== "–") {
            const match = momString.match(/([+-]?\d+(?:,\d+)?)/);
            if (match) {
              const percentValue = parseFloat(match[1].replace(',', '.'));
              const valorAnterior = saldoFinal / (1 + percentValue / 100);
              saldoFinalMoM = {
                variacao_absoluta: saldoFinal - valorAnterior,
                variacao_percentual: percentValue
              };
            }
          }
        }
      }

      // Criar dados para gráfico (últimos 12 meses)
      const mesesDisponiveis = Object.keys(saldoFinalItem.valores_mensais).sort();
      const ultimosMeses = mesesDisponiveis.slice(-12);
      
      saldosEvolucaoChart = ultimosMeses.map(mes => ({
        mes,
        saldo_inicial: saldoInicialItem.valores_mensais[mes] || 0,
        saldo_final: saldoFinalItem.valores_mensais[mes] || 0
      }));
    }
  }

  // Extrair dados de custos do DFC
  let custosValor = null;
  let custosMoM = null;
  let custosMesClass = {};

  if (dfcData && Array.isArray(dfcData)) {
    // Processar dados de custos
    // Primeiro, tentar encontrar "Custos" diretamente no nível principal
    let custosItem: DFCItem | DFCClassificacao | undefined = dfcData.find(item => item.nome === "Custos");
    
    // Se não encontrar, procurar dentro de "Movimentações" > "Operacional"
    if (!custosItem) {
      const movimentacoesItemCustos = dfcData.find(item => item.nome === "Movimentações");
      if (movimentacoesItemCustos && movimentacoesItemCustos.classificacoes) {
        const operacionalItem = movimentacoesItemCustos.classificacoes.find(item => item.nome === "Operacional");
        if (operacionalItem && operacionalItem.classificacoes) {
          custosItem = operacionalItem.classificacoes.find(item => item.nome === "Custos");
        }
      }
    }

    if (custosItem) {

      if (!mesSelecionado) {
        // Todo o período - usar valor total
        custosValor = custosItem.valor !== undefined && custosItem.valor !== null ? Math.abs(custosItem.valor) : null;
        
        // Classificações para todo o período
        if (custosItem.classificacoes && Array.isArray(custosItem.classificacoes)) {
          custosMesClass = Object.fromEntries(
            custosItem.classificacoes
              .filter(classificacao => 
                classificacao.valor !== undefined && 
                classificacao.valor !== null && 
                Math.abs(classificacao.valor) > 0
              )
              .map(classificacao => [
                classificacao.nome,
                Math.abs(classificacao.valor)
              ])
          );
        }
      } else {
        // Mês específico - usar valores_mensais
        const valorMes = custosItem.valores_mensais?.[mesSelecionado];
        custosValor = valorMes !== undefined && valorMes !== null ? Math.abs(valorMes) : null;
        
        // Classificações para o mês específico
        if (custosItem.classificacoes && Array.isArray(custosItem.classificacoes)) {
          custosMesClass = Object.fromEntries(
            custosItem.classificacoes
              .map(classificacao => {
                const valorClassificacao = classificacao.valores_mensais?.[mesSelecionado];
                return [
                  classificacao.nome,
                  valorClassificacao !== undefined && valorClassificacao !== null ? Math.abs(valorClassificacao) : 0
                ];
              })
              .filter(([, valor]) => (typeof valor === 'number' && valor > 0)) // Filtrar valores zero
          );
        }
        
        // Calcular MoM usando horizontal_mensais (equivalente ao MoM) - apenas para DFCItem
        const horizontalMensal = 'horizontal_mensais' in custosItem ? custosItem.horizontal_mensais?.[mesSelecionado] : undefined;
        if (horizontalMensal && horizontalMensal !== "–") {
          const percentualMatch = horizontalMensal.match(/([+-]?)(\d+\.?\d*)%/);
          if (percentualMatch) {
            const sinal = percentualMatch[1] === "-" ? -1 : 1;
            const percentual = parseFloat(percentualMatch[2]) * sinal;
            custosMoM = {
              variacao_absoluta: null, // Não temos valor absoluto no DFC
              variacao_percentual: percentual
            };
          }
        }
      }
    } else {
      
      // Debug adicional para mostrar a estrutura hierárquica
      const movimentacoesItemDebug = dfcData.find(item => item.nome === "Movimentações");
      if (movimentacoesItemDebug) {
        const operacionalItem = movimentacoesItemDebug.classificacoes?.find(item => item.nome === "Operacional");
        if (operacionalItem) {
        }
      }
    }

    // Processar dados de movimentações
    const movimentacoesItem = dfcData.find(item => item.nome === "Movimentações");
    
    if (movimentacoesItem) {
      if (!mesSelecionado) {
        // Todo o período - usar valor total
        movimentacoesValor = movimentacoesItem.valor;
      } else {
        // Mês específico - usar valores_mensais
        movimentacoesValor = movimentacoesItem.valores_mensais?.[mesSelecionado] || null;
      }

      // Converter horizontal_mensais para formato MoM
      if (movimentacoesItem.horizontal_mensais) {
        const mesesOrdenados = Object.keys(movimentacoesItem.valores_mensais || {}).sort();
        momMovimentacoes = mesesOrdenados.map((mes, idx) => {
          const valorAtual = movimentacoesItem.valores_mensais?.[mes] || 0;
          const valorAnterior = idx > 0 ? (movimentacoesItem.valores_mensais?.[mesesOrdenados[idx-1]] || null) : null;
          const horizontalStr = movimentacoesItem.horizontal_mensais?.[mes];
          
          let variacaoPercentual = null;
          let variacaoAbsoluta = null;
          
          if (horizontalStr && horizontalStr !== "–" && valorAnterior !== null) {
            const percentualMatch = horizontalStr.match(/([+-]?)(\d+\.?\d*)%/);
            if (percentualMatch) {
              const sinal = percentualMatch[1] === "-" ? -1 : 1;
              variacaoPercentual = parseFloat(percentualMatch[2]) * sinal;
              variacaoAbsoluta = valorAtual - valorAnterior;
            }
          }

          return {
            mes,
            valor_atual: valorAtual,
            valor_anterior: valorAnterior,
            variacao_absoluta: variacaoAbsoluta,
            variacao_percentual: variacaoPercentual
          };
        });
      }
    }
  } else {
  }

  const isLoading = !inicializado || loading;
  const hasCustosData = custosValor !== null && custosValor !== undefined;

  return (
    <main className="p-4">
      <section className="py-4 flex justify-between items-center">
        <FiltroMes 
          onSelect={handleMesSelecionado} 
          endpoint={`${API_BASE_URL}/receber`}
          value={mesSelecionado}
        />
      </section>
      
      <section className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {isLoading ? (
          <>
            <CardSkeleton />
            <CardSkeleton />
            <CardSkeleton />
            <CardSkeleton />
          </>
        ) : (
          <>
            {/* Contas Recebidas */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-center">
                  <CardTitle className="text-lg sm:text-xl select-none">
                    Contas recebidas
                  </CardTitle>
                  <PlusCircle className="ml-auto w-4 h-4" />
                </div>
              </CardHeader>

              <CardContent>
                <div className="sm:flex sm:justify-between sm:items-center">
                  <p className="text-lg sm:text-2xl">
                    {saldoReceber?.data?.saldo_total !== undefined ? (
                      formatCurrencyShort(saldoReceber.data.saldo_total)
                    ) : (
                      "--"
                    )}
                  </p>
                  <CardDescription>
                    {mesSelecionado === "" ? (
                      <p>vs período anterior <br />-- --</p>
                    ) : (() => {
                      const mom = getMoMIndicator(momReceber, mesSelecionado);
                      return mom && mom.hasValue ? (
                        <p>
                          vs {mom.mesAnterior} <br />
                          <span>
                            {mom.arrow} {mom.percentage?.toFixed(1)}%
                          </span>
                        </p>
                      ) : (
                        <p>vs mês anterior <br />-- --</p>
                      );
                    })()}
                  </CardDescription>
                </div>
              </CardContent>
            </Card>

            {/* Contas Pagas */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-center">
                  <CardTitle className="text-lg sm:text-xl select-none">
                    Contas pagas
                  </CardTitle>
                  <MinusCircle className="ml-auto w-4 h-4" />
                </div>
              </CardHeader>

              <CardContent>
                <div className="sm:flex sm:justify-between sm:items-center">
                  <p className="text-lg sm:text-2xl">
                    {saldoPagar?.data?.saldo_total !== undefined ? (
                      formatCurrencyShort(saldoPagar.data.saldo_total)
                    ) : (
                      "--"
                    )}
                  </p>
                  <CardDescription>
                    {mesSelecionado === "" ? (
                      <p>vs período anterior <br />-- --</p>
                    ) : (() => {
                      const mom = getMoMIndicator(momPagar, mesSelecionado);
                      return mom && mom.hasValue ? (
                        <p>
                          vs {mom.mesAnterior} <br />
                          <span>
                            {mom.arrow} {mom.percentage?.toFixed(1)}%
                          </span>
                        </p>
                      ) : (
                        <p>vs mês anterior <br />-- --</p>
                      );
                    })()}
                  </CardDescription>
                </div>
              </CardContent>
            </Card>

            {/* PMR */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-center">
                  <CardTitle className="text-lg sm:text-xl select-none">
                    PMR
                  </CardTitle>
                  <Hourglass className="ml-auto w-4 h-4" />
                </div>
                <CardDescription>
                  <p>prazo médio recebimento</p>
                  <p className="text-muted-foreground/50">Todo o período</p>
                </CardDescription>
              </CardHeader>

              <CardContent>
                <div>
                  <p className="text-lg sm:text-2xl">{pmr ?? "--"}</p>
                </div>
              </CardContent>
            </Card>

            {/* PMP */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-center">
                  <CardTitle className="text-lg sm:text-xl select-none">
                    PMP
                  </CardTitle>
                  <Hourglass className="ml-auto w-4 h-4" />
                </div>
                <CardDescription>
                  <p>prazo médio pagamento</p>
                  <p className="text-muted-foreground/50">Todo o período</p>
                </CardDescription>
              </CardHeader>

              <CardContent>
                <div>
                  <p className="text-lg sm:text-2xl">{pmp ?? "--"}</p>
                </div>
              </CardContent>
            </Card>
          </>
        )}
      </section>

      <section className="mt-4 flex flex-col lg:flex-row gap-4">
        {isLoading ? (
          <>
            <CardSkeletonLarge />
            <CardSkeletonLarge />
            <CardSkeletonLarge />
          </>
        ) : (
          <>
            {/* Card Movimentações Dinâmico */}
            <Card className="w-full">
              <CardHeader>
                <div className="flex items-center justify-center">
                  <CardTitle className="text-lg sm:text-xl select-none">
                    Movimentações
                  </CardTitle>
                  <ArrowUpDown className="ml-auto w-4 h-4" />
                </div>
              </CardHeader>

              <CardContent>
                <div className="sm:flex sm:justify-between sm:items-center">
                  <p className="text-lg sm:text-2xl">
                    {movimentacoesValor !== null ? (
                      formatCurrencyShort(movimentacoesValor)
                    ) : (
                      "--"
                    )}
                  </p>
                </div>

                <CardDescription>
                  <div className="flex items-center gap-2 mt-2 mb-10 leading-none font-medium">
                    {mesSelecionado === "" ? (
                      <>Sem variação</>
                    ) : (() => {
                      const mom = getMoMIndicator(momMovimentacoes, mesSelecionado);
                      return mom && mom.hasValue ? (
                        <>
                          {mom.isPositive === null ? "Sem variação" : mom.isPositive ? "Aumento" : "Queda"} de {mom.percentage?.toFixed(1)}% neste mês
                          {mom.isPositive === false ? (
                            <TrendingDown className="h-4 w-4" />
                          ) : (
                            <TrendingUp className="h-4 w-4" />
                          )}
                        </>
                      ) : (
                        <>Sem variação</>
                      );
                    })()}
                  </div>
                </CardDescription>

                <ChartMovimentacoes 
                  mesSelecionado={mesSelecionado}
                  momReceber={momReceber}
                  momPagar={momPagar}
                  momMovimentacoes={momMovimentacoes}
                />
              </CardContent>
              <CardFooter>
                <div className="flex w-full items-start gap-2 text-sm">
                  <div className="grid gap-2">
                    <CardDescription>
                      <p>Movimentações últimos 6M</p>
                    </CardDescription>
                    <div className="text-muted-foreground flex items-center gap-2 leading-none">
                      {formatarPeriodo({ mesSelecionado: "", saldosEvolucao: saldosEvolucaoChart })}
                    </div>
                  </div>
                </div>
              </CardFooter>
            </Card>
            
            {/* Card Saldo Final */}
            <Card className="w-full">
              <CardHeader>
                <div className="flex items-center justify-center">
                  <CardTitle className="text-lg sm:text-xl select-none">
                    Saldo Final
                  </CardTitle>
                  <Wallet className="ml-auto w-4 h-4" />
                </div>
              </CardHeader>

              <CardContent>
                <div className="sm:flex sm:justify-between sm:items-center">
                  <p className="text-lg sm:text-2xl">
                    {saldoFinal !== null ? (
                      formatCurrencyShort(saldoFinal)
                    ) : (
                      "--"
                    )}
                  </p>
                </div>

                <CardDescription>
                  <div className="flex items-center gap-2 mt-2 mb-10 leading-none font-medium">
                    {mesSelecionado === "" ? (
                      <>Sem variação</>
                    ) : saldoFinalMoM && saldoFinalMoM.variacao_percentual !== null && saldoFinalMoM.variacao_percentual !== undefined ? (
                      <>
                        {saldoFinalMoM.variacao_percentual > 0 ? "Aumento" : saldoFinalMoM.variacao_percentual < 0 ? "Queda" : "Sem variação"} de {Math.abs(saldoFinalMoM.variacao_percentual).toFixed(1)}% neste mês
                        {saldoFinalMoM.variacao_percentual < 0 ? (
                          <TrendingDown className="h-4 w-4" />
                        ) : (
                          <TrendingUp className="h-4 w-4" />
                        )}
                      </>
                    ) : (
                      <>Sem variação</>
                    )}
                  </div>
                </CardDescription>

                <ChartAreaSaldoFinal data={saldosEvolucaoChart} mesSelecionado={mesSelecionado} />
              </CardContent>
              <CardFooter>
                <div className="flex w-full items-start gap-2 text-sm">
                  <div className="grid gap-2">
                    <CardDescription>
                      <p>Saldo últimos 6M</p>
                    </CardDescription>
                    <div className="text-muted-foreground flex items-center gap-2 leading-none">
                      {formatarPeriodo({ mesSelecionado: "", saldosEvolucao: saldosEvolucaoChart })}
                    </div>
                  </div>
                </div>
              </CardFooter>
            </Card>

            {/* Card Custos */}
            <Card className="w-full">
              <CardHeader>
                <div className="flex items-center justify-center">
                  <CardTitle className="text-lg sm:text-xl select-none">
                    Custos
                  </CardTitle>
                  <Package className="ml-auto w-4 h-4" />
                </div>
              </CardHeader>

              <CardContent>
                <div className="sm:flex sm:justify-between sm:items-center">
                  <p className="text-lg sm:text-2xl">
                    {hasCustosData && custosValor !== null ? (
                      formatCurrencyShort(custosValor)
                    ) : (
                      "--"
                    )}
                  </p>
                </div>
                <CardDescription>
                  <div className="flex gap-2 mt-2 mb-10 leading-none font-medium">
                    {mesSelecionado === "" ? (
                      <>Sem variação</>
                    ) : custosMoM && custosMoM.variacao_percentual !== null ? (
                      <>
                        {custosMoM.variacao_percentual > 0 ? "Aumento" : custosMoM.variacao_percentual < 0 ? "Queda" : "Sem variação"} de {Math.abs(custosMoM.variacao_percentual).toFixed(1)}% neste mês
                        {custosMoM.variacao_percentual < 0 ? (
                          <TrendingDown className="h-4 w-4" />
                        ) : (
                          <TrendingUp className="h-4 w-4" />
                        )}
                      </>
                    ) : (
                      <>Sem variação</>
                    )}
                  </div>
                </CardDescription>

                <ChartCustosFinanceiro data={custosMesClass} />
              </CardContent>
              <CardFooter className="flex-col items-start gap-2 text-sm">
                <CardDescription>
                  <p>Custos por classificação</p>
                </CardDescription>
                <div className="text-muted-foreground flex items-center gap-2 leading-none">
                  {formatarPeriodo({ mesSelecionado, saldosEvolucao: saldosEvolucaoChart })}
                </div>
              </CardFooter>
            </Card>
          </>
        )}
      </section>
    </main>
  );
}