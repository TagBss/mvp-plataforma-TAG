"use client";

import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "../ui/card";
import { CardSkeleton, CardSkeletonLarge } from "../ui/card-skeleton";
import {  
  TrendingUp,
  TrendingDown,
  ArrowUpDown,
  PlusCircle,
  MinusCircle,
  Package,
  Hourglass,
} from "lucide-react";
import { useEffect, useState } from "react";
import { FiltroMes } from "../filtro-mes";
import { ChartAreaSaldoFinal } from "../charts-financeiro/chart-area-saldo-final";
import { ChartCustosFinanceiro } from "../charts-financeiro/chart-bar-custos";
import ChartMovimentacoes from "../charts-financeiro/chart-movimentacoes";
import { api } from "../../services/api";

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

// Tipagem para MoM (análise horizontal)
type MoMData = {
  mes: string;
  valor_atual: number;
  valor_anterior: number | null;
  variacao_absoluta: number | null;
  variacao_percentual: number | null;
};

// Tipagem para dados de saldo
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

// Tipagem para dados DFC
type DFCItem = {
  tipo: string;
  nome: string;
  valor: number;
  valores_mensais: Record<string, number>;
  valores_trimestrais: Record<string, number>;
  valores_anuais: Record<string, number>;
  horizontal_mensais: Record<string, string>;
  horizontal_trimestrais: Record<string, string>;
  horizontal_anuais: Record<string, string>;
  classificacoes?: any[];
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

function formatarPeriodo(dados: Array<{ mes: string }>) {
  if (dados.length === 0) return "Todo o período";
  
  const primeiro = dados[0].mes;
  const ultimo = dados[dados.length - 1].mes;
  
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
    return null;
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

export default function DashFinanceiroPostgreSQL() {
  console.log("🔥 COMPONENTE FINANCEIRO POSTGRESQL INICIADO");
  
  // Estados principais
  const [mesSelecionado, setMesSelecionado] = useState<string>("");
  const [inicializando, setInicializando] = useState(true);
  const [loading, setLoading] = useState(false);
  
  // Estados dos KPIs
  const [saldoReceber, setSaldoReceber] = useState<SaldoData | null>(null);
  const [saldoPagar, setSaldoPagar] = useState<SaldoData | null>(null);
  const [dfcData, setDfcData] = useState<DFCData | null>(null);
  
  // Estados para gráficos
  const [saldoEvolucao, setSaldoEvolucao] = useState<Array<{ mes: string; saldo_final: number }>>([]);
  const [movimentacoesData, setMovimentacoesData] = useState<MoMData[]>([]);
  const [custosData, setCustosData] = useState<Record<string, number>>({});
  
  // Handler para mudança de mês
  const handleMudancaMes = (novoMes: string) => {
    console.log("🔄 Mudando para:", novoMes);
    setMesSelecionado(novoMes);
  };

  // Função para carregar dados dos KPIs a partir dos endpoints PostgreSQL
  const carregarDados = async (mes: string) => {
    setLoading(true);
    try {
      const queryString = mes ? `?mes=${mes}` : '';
      
      // Carregar dados dos endpoints PostgreSQL
      const [receberRes, pagarRes, dfcRes] = await Promise.all([
        api.get(`/financial-data/receber${queryString}`),
        api.get(`/financial-data/pagar${queryString}`),
        api.get('/financial-data/dfc')
      ]);

      setSaldoReceber(receberRes.data);
      setSaldoPagar(pagarRes.data);
      setDfcData(dfcRes.data);

      // Processar evolução do saldo (últimos 12 meses)
      if (dfcRes.data?.data) {
        // Encontrar itens "Saldo inicial" e "Saldo final" no DFC
        const saldoInicialItem = dfcRes.data.data.find((item: DFCItem) => item.nome === "Saldo inicial");
        const saldoFinalItem = dfcRes.data.data.find((item: DFCItem) => item.nome === "Saldo final");
        
        if (saldoFinalItem && saldoInicialItem) {
          // Criar dados para gráfico (últimos 12 meses)
          const mesesDisponiveis = Object.keys(saldoFinalItem.valores_mensais).sort();
          const ultimosMeses = mesesDisponiveis.slice(-12);
          
          const evolucao = ultimosMeses.map(mes => ({
            mes,
            saldo_final: saldoFinalItem.valores_mensais[mes] || 0
          }));
          setSaldoEvolucao(evolucao);
        } else {
          setSaldoEvolucao([]);
        }
      } else {
        setSaldoEvolucao([]);
      }

      // Processar dados de movimentações do DFC
      let movimentacoesData: MoMData[] = [];
      if (dfcRes.data?.data) {
        const movimentacoesItem = dfcRes.data.data.find((item: DFCItem) => item.nome === "Movimentações");
        
        if (movimentacoesItem && movimentacoesItem.horizontal_mensais) {
          const mesesOrdenados = Object.keys(movimentacoesItem.valores_mensais || {}).sort();
          movimentacoesData = mesesOrdenados.map((mes, idx) => {
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
      setMovimentacoesData(movimentacoesData);

      // Processar dados de custos do DFC
      if (dfcRes.data?.data) {
        // Primeiro, tentar encontrar "Custos" diretamente no nível principal
        let custosItem = dfcRes.data.data.find((item: DFCItem) => item.nome === "Custos");
        
        // Se não encontrar, procurar dentro de "Movimentações" > "Operacional"
        if (!custosItem) {
          const movimentacoesItemCustos = dfcRes.data.data.find((item: DFCItem) => item.nome === "Movimentações");
          
          if (movimentacoesItemCustos && movimentacoesItemCustos.classificacoes) {
            const operacionalItem = movimentacoesItemCustos.classificacoes.find((item: any) => item.nome === "Operacional");
            
            if (operacionalItem && operacionalItem.classificacoes) {
              custosItem = operacionalItem.classificacoes.find((item: any) => item.nome === "Custos");
            }
          }
        }

        if (custosItem) {
          const custosPorClassificacao: Record<string, number> = {};
          
          if (custosItem.classificacoes && Array.isArray(custosItem.classificacoes)) {
            custosItem.classificacoes.forEach((classificacao: any) => {
              const valor = mes && classificacao.valores_mensais?.[mes] !== undefined
                ? classificacao.valores_mensais[mes]
                : classificacao.valor || 0;
              
              if (Math.abs(valor) > 0) {
                custosPorClassificacao[classificacao.nome] = Math.abs(valor);
              }
            });
          }
          
          setCustosData(custosPorClassificacao);
        } else {
          setCustosData({});
        }
      } else {
        setCustosData({});
      }

    } catch (e) {
      console.error("❌ Erro ao carregar dados:", e);
    } finally {
      setLoading(false);
    }
  };

  // Inicialização: buscar meses disponíveis do endpoint /financial-data/receber
  useEffect(() => {
    const init = async () => {
      try {
        const response = await api.get('/financial-data/receber');
        const data = response.data;
        
        // Compatibilidade: aceita data.data.meses_disponiveis, data.meses, ou meses direto na raiz
        let meses: string[] = [];
        if (data?.data?.meses_disponiveis && Array.isArray(data.data.meses_disponiveis) && data.data.meses_disponiveis.length > 0) {
          meses = data.data.meses_disponiveis;
        } else if (data?.meses && Array.isArray(data.meses) && data.meses.length > 0) {
          meses = data.meses;
        } else if (Array.isArray(data) && data.length > 0 && typeof data[0] === "string") {
          meses = data;
        }
        
        if (meses.length > 0) {
          const ultimoMes = meses[meses.length - 1];
          setMesSelecionado(ultimoMes);
        }
        setInicializando(false);
      } catch {
        setInicializando(false);
      }
    };
    init();
  }, []);

  // Carregar dados quando mês muda OU "Todo o período"
  useEffect(() => {
    console.log("🔄 UseEffect de carregamento:", mesSelecionado, inicializando);
    if (!inicializando) {
      carregarDados(mesSelecionado);
    }
  }, [mesSelecionado, inicializando]);

  return (
    <main className="p-4">
      <section className="py-4 flex justify-between items-center">
        <FiltroMes 
          onSelect={handleMudancaMes} 
          endpoint="http://127.0.0.1:8000/financial-data/receber"
          value={mesSelecionado}
        />
      </section>
      
      <section className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {(inicializando || loading) ? (
          // Exibe skeletons enquanto carrega
          <>
            <CardSkeleton />
            <CardSkeleton />
            <CardSkeleton />
            <CardSkeleton />
          </>
        ) : (
          // Exibe os cards reais após carregar
          <>
            {/* Contas a Receber */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-center">
                  <CardTitle className="text-lg sm:text-xl select-none">
                    Contas a Receber
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
                      const mom = getMoMIndicator(saldoReceber?.data?.mom_analysis || [], mesSelecionado);
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

            {/* Contas a Pagar */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-center">
                  <CardTitle className="text-lg sm:text-xl select-none">
                    Contas a Pagar
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
                      const mom = getMoMIndicator(saldoPagar?.data?.mom_analysis || [], mesSelecionado);
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
                <CardDescription className="flex items-start">
                  <p className="text-xs text-muted-foreground opacity-70 select-none">Prazo médio de recebimento</p>
                </CardDescription>
              </CardHeader>

              <CardContent>
                <div className="sm:flex sm:justify-between sm:items-center">
                  <p className="text-lg sm:text-2xl">
                    {saldoReceber?.data?.pmr || "--"}
                  </p>
                  <CardDescription>
                    <p>Todo o período</p>
                  </CardDescription>
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
                <CardDescription className="flex items-start">
                  <p className="text-xs text-muted-foreground opacity-70 select-none">Prazo médio de pagamento</p>
                </CardDescription>
              </CardHeader>

              <CardContent>
                <div className="sm:flex sm:justify-between sm:items-center">
                  <p className="text-lg sm:text-2xl">
                    {saldoPagar?.data?.pmp || "--"}
                  </p>
                  <CardDescription>
                    <p>Todo o período</p>
                  </CardDescription>
                </div>
              </CardContent>
            </Card>
          </>
        )}
      </section>

      <section className="mt-4 flex flex-col lg:flex-row gap-4">
        {(inicializando || loading) ? (
          // Exibe skeletons enquanto carrega
          <>
            <CardSkeletonLarge />
            <CardSkeletonLarge />
          </>
        ) : (
          // Exibe os cards reais após carregar
          <>
            {/* Gráfico de Saldo */}
            <Card className="w-full">
              <CardHeader>
                <div className="flex items-center justify-center">
                  <CardTitle className="text-lg sm:text-xl select-none">
                    Evolução do Saldo
                  </CardTitle>
                  <TrendingUp className="ml-auto w-4 h-4" />
                </div>
              </CardHeader>

              <CardContent>
                <div className="sm:flex sm:justify-between sm:items-center">
                  <CardDescription>
                    <div className="flex gap-2 mb-10 leading-none font-medium">
                      Saldo ao longo do tempo
                      {mesSelecionado && ` - ${mesSelecionado}`}
                    </div>
                  </CardDescription>
                </div>

                <ChartAreaSaldoFinal 
                  data={saldoEvolucao} 
                  mesSelecionado={mesSelecionado} 
                />
              </CardContent>
              <CardFooter className="flex-col items-start gap-2 text-sm">
                <CardDescription>
                  <p>Evolução do saldo financeiro</p>
                </CardDescription>
                <div className="text-muted-foreground flex items-center gap-2 leading-none">
                  {saldoEvolucao.length > 0 ? (
                    formatarPeriodo(saldoEvolucao)
                  ) : (
                    "Todo o período"
                  )}
                </div>
              </CardFooter>
            </Card>
            
            {/* Gráfico de Movimentações */}
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
                  <CardDescription>
                    <div className="flex gap-2 mb-10 leading-none font-medium">
                      Entradas e saídas
                    </div>
                  </CardDescription>
                </div>

                <ChartMovimentacoes 
                  mesSelecionado={mesSelecionado}
                  momReceber={saldoReceber?.data?.mom_analysis || []}
                  momPagar={saldoPagar?.data?.mom_analysis || []}
                  momMovimentacoes={movimentacoesData}
                />
              </CardContent>
              <CardFooter className="flex-col items-start gap-2 text-sm">
                <CardDescription>
                  <p>Movimentações financeiras</p>
                </CardDescription>
                <div className="text-muted-foreground flex items-center gap-2 leading-none">
                  {mesSelecionado ? (
                    (() => {
                      const formatar = (mes: string) => {
                        if (!mes.match(/^\d{4}-\d{2}$/)) return mes;
                        const [ano, m] = mes.split("-");
                        const mesNum = parseInt(m, 10);
                        return `${mesesAbreviados[mesNum]}/${ano.slice(-2)}`;
                      };
                      return formatar(mesSelecionado);
                    })()
                  ) : (
                    "Todo o período"
                  )}
                </div>
              </CardFooter>
            </Card>
          </>
        )}
      </section>

      <section className="mt-4 flex flex-col lg:flex-row gap-4">
        {(inicializando || loading) ? (
          // Exibe skeleton enquanto carrega
          <CardSkeletonLarge />
        ) : (
          // Exibe o gráfico de custos
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
                <CardDescription>
                  <div className="flex gap-2 mb-10 leading-none font-medium">
                    Custos por classificação
                  </div>
                </CardDescription>
              </div>

              <ChartCustosFinanceiro data={custosData} />
            </CardContent>
            <CardFooter className="flex-col items-start gap-2 text-sm">
              <CardDescription>
                <p>Classificação de custos por valor</p>
              </CardDescription>
              <div className="text-muted-foreground flex items-center gap-2 leading-none">
                {mesSelecionado ? (
                  (() => {
                    const formatar = (mes: string) => {
                      if (!mes.match(/^\d{4}-\d{2}$/)) return mes;
                      const [ano, m] = mes.split("-");
                      const mesNum = parseInt(m, 10);
                      return `${mesesAbreviados[mesNum]}/${ano.slice(-2)}`;
                    };
                    return formatar(mesSelecionado);
                  })()
                ) : (
                  "Todo o período"
                )}
              </div>
            </CardFooter>
          </Card>
        )}
      </section>

      <section className="mt-8 text-center">
        <p className="text-sm text-gray-600">
          Dados atualizados em tempo real via PostgreSQL
        </p>
      </section>
    </main>
  );
}
