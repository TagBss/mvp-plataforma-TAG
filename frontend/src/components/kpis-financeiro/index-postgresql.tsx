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
import { useFinancialDataContext } from "../../contexts/FinancialDataContext";
import { transformToKPIs, transformToDFCData, groupDataByPeriod } from "../../utils/postgresql-transformers";

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
  horizontal_mensais: Record<string, string>;
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
  
  // Usar o contexto PostgreSQL
  const { 
    financialData, 
    summary, 
    dataLoading, 
    summaryLoading,
    currentFilters,
    updateFilters 
  } = useFinancialDataContext();
  

  
  // Estados principais
  const [mesSelecionado, setMesSelecionado] = useState<string>("");
  const [inicializando, setInicializando] = useState(true);
  
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
    
    // Atualizar filtros do contexto PostgreSQL
    if (novoMes) {
      const [ano, mes] = novoMes.split("-");
      const startDate = `${ano}-${mes}-01`;
      const endDate = new Date(parseInt(ano), parseInt(mes), 0).toISOString().split('T')[0];
      updateFilters({ start_date: startDate, end_date: endDate });
    } else {
      // Todo o período
      const currentYear = new Date().getFullYear();
      updateFilters({ 
        start_date: `${currentYear}-01-01`, 
        end_date: new Date().toISOString().split('T')[0] 
      });
    }
  };

  // Processar dados PostgreSQL quando mudarem
  useEffect(() => {
    if (!financialData || financialData.length === 0) return;

    console.log("🔄 Processando dados PostgreSQL:", financialData.length, "registros");

    // Transformar dados para formato DFC
    const dfcTransformed = transformToDFCData(financialData);
    
    // Criar estrutura de dados compatível com o componente original
    const dfcCompatible: DFCData = {
      success: true,
      meses: dfcTransformed.meses_unicos,
      trimestres: dfcTransformed.trimestres_unicos,
      anos: dfcTransformed.anos_unicos,
      data: []
    };

    // Processar saldo receber (receitas)
    const receitas = financialData.filter(item => item.type === 'receita');
    const receitasPorMes = groupDataByPeriod(receitas, 'month');
    const saldoReceberTotal = receitas.reduce((sum, item) => sum + item.value, 0);
    
    const saldoReceberData: SaldoData = {
      success: true,
      data: {
        saldo_total: saldoReceberTotal,
        mom_analysis: Object.keys(receitasPorMes).map((mes, idx, meses) => {
          // Calcular total do mês somando todas as categorias
          const valorAtual = Object.values(receitasPorMes[mes] || {}).reduce((sum, val) => sum + val, 0);
          const valorAnterior = idx > 0 ? Object.values(receitasPorMes[meses[idx-1]] || {}).reduce((sum, val) => sum + val, 0) : null;
          const variacaoAbsoluta = valorAnterior !== null ? valorAtual - valorAnterior : null;
          const variacaoPercentual = valorAnterior !== null && valorAnterior !== 0 
            ? ((valorAtual - valorAnterior) / valorAnterior) * 100 
            : null;

          return {
            mes,
            valor_atual: valorAtual,
            valor_anterior: valorAnterior,
            variacao_absoluta: variacaoAbsoluta,
            variacao_percentual: variacaoPercentual
          };
        }),
        pmr: "30 dias" // Placeholder
      }
    };

    // Processar saldo pagar (despesas)
    const despesas = financialData.filter(item => item.type === 'despesa');
    const despesasPorMes = groupDataByPeriod(despesas, 'month');
    const saldoPagarTotal = despesas.reduce((sum, item) => sum + item.value, 0);
    
    const saldoPagarData: SaldoData = {
      success: true,
      data: {
        saldo_total: saldoPagarTotal,
        mom_analysis: Object.keys(despesasPorMes).map((mes, idx, meses) => {
          // Calcular total do mês somando todas as categorias
          const valorAtual = Object.values(despesasPorMes[mes] || {}).reduce((sum, val) => sum + val, 0);
          const valorAnterior = idx > 0 ? Object.values(despesasPorMes[meses[idx-1]] || {}).reduce((sum, val) => sum + val, 0) : null;
          const variacaoAbsoluta = valorAnterior !== null ? valorAtual - valorAnterior : null;
          const variacaoPercentual = valorAnterior !== null && valorAnterior !== 0 
            ? ((valorAtual - valorAnterior) / valorAnterior) * 100 
            : null;

          return {
            mes,
            valor_atual: valorAtual,
            valor_anterior: valorAnterior,
            variacao_absoluta: variacaoAbsoluta,
            variacao_percentual: variacaoPercentual
          };
        }),
        pmp: "30 dias" // Placeholder
      }
    };

    // Processar evolução do saldo
    const mesesOrdenados = Object.keys(receitasPorMes).sort();
    const evolucaoSaldo = mesesOrdenados.map(mes => {
      const receitasMes = Object.values(receitasPorMes[mes] || {}).reduce((sum, val) => sum + val, 0);
      const despesasMes = Object.values(despesasPorMes[mes] || {}).reduce((sum, val) => sum + val, 0);
      return {
        mes,
        saldo_final: receitasMes - despesasMes
      };
    });

    // Processar movimentações
    const movimentacoesData: MoMData[] = mesesOrdenados.map((mes, idx) => {
      const receitasMes = Object.values(receitasPorMes[mes] || {}).reduce((sum, val) => sum + val, 0);
      const despesasMes = Object.values(despesasPorMes[mes] || {}).reduce((sum, val) => sum + val, 0);
      const valorAtual = receitasMes - despesasMes;
      
      const valorAnterior = idx > 0 ? (() => {
        const mesAnterior = mesesOrdenados[idx-1];
        const receitasAnterior = Object.values(receitasPorMes[mesAnterior] || {}).reduce((sum, val) => sum + val, 0);
        const despesasAnterior = Object.values(despesasPorMes[mesAnterior] || {}).reduce((sum, val) => sum + val, 0);
        return receitasAnterior - despesasAnterior;
      })() : null;

      const variacaoAbsoluta = valorAnterior !== null ? valorAtual - valorAnterior : null;
      const variacaoPercentual = valorAnterior !== null && valorAnterior !== 0 
        ? ((valorAtual - valorAnterior) / valorAnterior) * 100 
        : null;

      return {
        mes,
        valor_atual: valorAtual,
        valor_anterior: valorAnterior,
        variacao_absoluta: variacaoAbsoluta,
        variacao_percentual: variacaoPercentual
      };
    });

    // Processar custos por categoria
    const custosPorCategoria: Record<string, number> = {};
    despesas.forEach(item => {
      const categoria = item.category;
      custosPorCategoria[categoria] = (custosPorCategoria[categoria] || 0) + item.value;
    });

    // Atualizar estados
    setSaldoReceber(saldoReceberData);
    setSaldoPagar(saldoPagarData);
    setDfcData(dfcCompatible);
    setSaldoEvolucao(evolucaoSaldo);
    setMovimentacoesData(movimentacoesData);
    setCustosData(custosPorCategoria);

  }, [financialData]);

  // Inicialização: definir período padrão
  useEffect(() => {
    if (!inicializando) return;
    
    const currentYear = new Date().getFullYear();
    const currentMonth = new Date().getMonth() + 1;
    const mesAtual = `${currentYear}-${String(currentMonth).padStart(2, '0')}`;
    
    setMesSelecionado(mesAtual);
    updateFilters({ 
      start_date: `${currentYear}-01-01`, 
      end_date: new Date().toISOString().split('T')[0] 
    });
    setInicializando(false);
  }, [inicializando, updateFilters]);

  const loading = dataLoading || summaryLoading || inicializando;

  return (
    <main className="p-4">
      <section className="py-4 flex justify-between items-center">
        <FiltroMes 
          onSelect={handleMudancaMes} 
          endpoint="http://127.0.0.1:8000/financial-data/months"
          value={mesSelecionado}
        />
      </section>
      
      <section className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {loading ? (
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
        {loading ? (
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
        {loading ? (
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
