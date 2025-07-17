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
import { ChartBarLabelCustom } from "../chart-bar-label-custom";

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


// Função utilitária para formatar períodos de meses
const mesesAbreviados = ['', 'jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez'];

function formatarPeriodo({ mesSelecionado, saldosEvolucao }: { mesSelecionado: string, saldosEvolucao: { mes: string }[] }) {
  if (mesSelecionado === "") {
    if (saldosEvolucao.length > 0) {
      const primeiro = saldosEvolucao[0].mes;
      const ultimo = saldosEvolucao[saldosEvolucao.length - 1].mes;
      const formatar = (mes: string) => {
        if (!mes.match(/^\d{4}-\d{2}$/)) return mes;
        const [ano, m] = mes.split("-");
        const mesNum = parseInt(m, 10);
        return `${mesesAbreviados[mesNum]}/${ano.slice(-2)}`;
      };
      return `${formatar(primeiro)} - ${formatar(ultimo)}`;
    } else {
      return "--";
    }
  } else if (mesSelecionado.match(/^\d{4}-\d{2}$/)) {
    const [ano, m] = mesSelecionado.split("-");
    const mesNum = parseInt(m, 10);
    return `${mesesAbreviados[mesNum]}/${ano.slice(-2)}`;
  } else {
    return "--";
  }
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




export default function DashFinanceiro() {
  // Estados
  const [saldoReceber, setSaldoReceber] = useState<number | null>(null);
  const [saldoPagar, setSaldoPagar] = useState<number | null>(null);
  const [saldoMovimentacoes, setSaldoMovimentacoes] = useState<number | null>(null);
  const [saldoFinal, setSaldoFinal] = useState<number | null>(null);
  const [saldoFinalMoM, setSaldoFinalMoM] = useState<{ variacao_absoluta: number | null, variacao_percentual: number | null } | null>(null);
  const [mesSelecionado, setMesSelecionado] = useState<string>("");
  const [inicializando, setInicializando] = useState(true); // 🔥 NOVO: controla inicialização
  const [loading, setLoading] = useState(false);
  const [loadingSaldoFinal, setLoadingSaldoFinal] = useState(false);
  const [momReceber, setMomReceber] = useState<MoMData[]>([]);
  const [momPagar, setMomPagar] = useState<MoMData[]>([]);
  const [momMovimentacoes, setMomMovimentacoes] = useState<MoMData[]>([]);
  const [pmr, setPmr] = useState<string | null>(null);
  const [pmp, setPmp] = useState<string | null>(null);
  const [saldosEvolucao, setSaldosEvolucao] = useState<Array<{ mes: string; saldo_inicial: number; saldo_final: number }>>([]);
  // Custos
  const [custosValor, setCustosValor] = useState<number | null>(null);
  const [custosMoM, setCustosMoM] = useState<{ variacao_absoluta: number | null, variacao_percentual: number | null } | null>(null);
  // Removido: custosMoMArray não é necessário
  const [custosLoading, setCustosLoading] = useState(false);
  const [custosMesClass, setCustosMesClass] = useState<Record<string, number>>({});

  // 🔥 MODIFICADO: useEffect de inicialização com flag
  useEffect(() => {
    const inicializar = async () => {
      try {
        console.log("🚀 Iniciando carregamento dos dados...");
        const [receberRes, pagarRes] = await Promise.all([
          fetch(`http://127.0.0.1:8000/receber`).then(res => {
            console.log("📊 Resposta /receber:", res.status);
            return res.json();
          }),
          fetch(`http://127.0.0.1:8000/pagar`).then(res => {
            console.log("📊 Resposta /pagar:", res.status);
            return res.json();
          })
        ]);

        console.log("📋 Dados receber:", receberRes);
        console.log("📋 Dados pagar:", pagarRes);

        // Define PMR e PMP
        if (receberRes.success && receberRes.data?.pmr) {
          setPmr(receberRes.data.pmr);
          console.log("✅ PMR definido:", receberRes.data.pmr);
        }
        if (pagarRes.success && pagarRes.data?.pmp) {
          setPmp(pagarRes.data.pmp);
          console.log("✅ PMP definido:", pagarRes.data.pmp);
        }

        // Define o mês padrão apenas se houver meses disponíveis
        if (receberRes.success && receberRes.data?.meses_disponiveis?.length > 0) {
          const meses = receberRes.data.meses_disponiveis;
          const mesPadrao = meses[meses.length - 1];
          setMesSelecionado(mesPadrao);
          console.log("✅ Mês padrão definido:", mesPadrao);
          console.log("📅 Meses disponíveis:", meses);
        }
      } catch (error) {
        console.error("❌ Erro na inicialização:", error);
      } finally {
        setInicializando(false); // 🔥 NOVO: marca que inicialização terminou
        console.log("🏁 Inicialização concluída");
      }
    };

    inicializar();
  }, []);

  // Permite selecionar qualquer valor, inclusive "Todo o período" ("") após inicialização
  const handleMesSelecionado = (mes: string) => {
    if (inicializando) return;
    setSaldoReceber(null);
    setSaldoPagar(null);
    setSaldoMovimentacoes(null);
    setMesSelecionado(mes);
  };

  // 🔥 MODIFICADO: useEffect que só executa após inicialização
  useEffect(() => {
    // Não executa se ainda está inicializando
    if (inicializando) {
      console.log("⏳ Aguardando inicialização...");
      return;
    }
    
    // Não executa se mesSelecionado for null ou undefined
    if (mesSelecionado === null || mesSelecionado === undefined) {
      console.log("⏳ Aguardando seleção de mês...");
      return;
    }

    console.log("🔄 Carregando dados para o mês:", mesSelecionado);
    setLoading(true);
    setLoadingSaldoFinal(true);
    
    const queryString = mesSelecionado ? `?mes=${mesSelecionado}` : "";
    console.log("🔗 Query string:", queryString);
    
    setCustosLoading(true);
    Promise.all([
      fetch(`http://127.0.0.1:8000/receber${queryString}`).then(r => {
        console.log("📊 Status receber:", r.status);
        return r.json();
      }),
      fetch(`http://127.0.0.1:8000/pagar${queryString}`).then(r => {
        console.log("📊 Status pagar:", r.status);
        return r.json();
      }),
      fetch(`http://127.0.0.1:8000/movimentacoes${queryString}`).then(r => {
        console.log("📊 Status movimentacoes:", r.status);
        return r.json();
      }),
      fetch(`http://127.0.0.1:8000/saldos-evolucao`).then(r => {
        console.log("📊 Status saldos-evolucao:", r.status);
        return r.json();
      }),
      fetch(`http://127.0.0.1:8000/custos-visao-financeiro`).then(r => {
        console.log("📊 Status custos:", r.status);
        return r.json();
      })
    ]).then(([dataReceber, dataPagar, dataMovimentacoes, dataSaldosEvolucao, dataCustos]) => {
      console.log("📦 Dados recebidos:", {
        receber: dataReceber,
        pagar: dataPagar,
        movimentacoes: dataMovimentacoes,
        saldosEvolucao: dataSaldosEvolucao,
        custos: dataCustos
      });

      // Processa dados do receber
      if (dataReceber.success) {
        setSaldoReceber(dataReceber.data.saldo_total);
        setMomReceber(dataReceber.data.mom_analysis || []);
        console.log("✅ Saldo receber definido:", dataReceber.data.saldo_total);
      } else {
        console.log("❌ Erro nos dados receber:", dataReceber);
      }
      
      // Processa dados do pagar
      if (dataPagar.success) {
        setSaldoPagar(dataPagar.data.saldo_total);
        setMomPagar(dataPagar.data.mom_analysis || []);
        console.log("✅ Saldo pagar definido:", dataPagar.data.saldo_total);
      } else {
        console.log("❌ Erro nos dados pagar:", dataPagar);
      }
      
      // Processa dados das movimentações
      if (dataMovimentacoes.success) {
        setSaldoMovimentacoes(dataMovimentacoes.data.saldo_total);
        setMomMovimentacoes(dataMovimentacoes.data.mom_analysis || []);
        console.log("✅ Saldo movimentações definido:", dataMovimentacoes.data.saldo_total);
      } else {
        console.log("❌ Erro nos dados movimentações:", dataMovimentacoes);
      }
      
      // Processa saldo final e evolução
      if (dataSaldosEvolucao.success && dataSaldosEvolucao.data?.evolucao?.length > 0) {
        let saldoFinal = null;
        let variacao_absoluta = null;
        let variacao_percentual = null;
        
        type SaldosEvolucaoItem = { 
          mes: string; 
          saldo_inicial: number; 
          movimentacao: number; 
          saldo_final: number; 
          variacao_absoluta?: number | null; 
          variacao_percentual?: number | null 
        };
        
        const evolucaoArr = dataSaldosEvolucao.data.evolucao as SaldosEvolucaoItem[];
        
        // Salva dados para o gráfico (últimos 12 meses)
        setSaldosEvolucao(evolucaoArr.slice(-12).map(({ mes, saldo_inicial, saldo_final }) => ({ 
          mes, 
          saldo_inicial, 
          saldo_final 
        })));
        
        // Busca dados específicos do mês selecionado
        if (mesSelecionado) {
          const found = evolucaoArr.find((item) => item.mes === mesSelecionado);
          saldoFinal = found ? found.saldo_final : null;
          variacao_absoluta = found ? found.variacao_absoluta ?? null : null;
          variacao_percentual = found ? found.variacao_percentual ?? null : null;
        } else {
          // Se não houver mês selecionado, pega o último
          const last = evolucaoArr[evolucaoArr.length - 1];
          saldoFinal = last.saldo_final;
          variacao_absoluta = last.variacao_absoluta ?? null;
          variacao_percentual = last.variacao_percentual ?? null;
        }
        
        setSaldoFinal(saldoFinal);
        setSaldoFinalMoM({ variacao_absoluta, variacao_percentual });
      } else {
        setSaldoFinal(null);
        setSaldoFinalMoM(null);
        setSaldosEvolucao([]);
      }

      // Processa custos
      if (dataCustos.success && dataCustos.data) {
        // Se mesSelecionado vazio, pega total_geral
        if (!mesSelecionado) {
          setCustosValor(dataCustos.data.total_geral ?? null);
          setCustosMesClass(dataCustos.data.total_geral_classificacao ?? {});
          setCustosMoM(null);
        } else {
          // Soma todos os custos do mês selecionado
          const custosMes = dataCustos.data.custos_mes || {};
          setCustosValor(custosMes[mesSelecionado] ?? null);
          setCustosMesClass(
            Object.fromEntries(
              Object.entries(dataCustos.data.custos_mes_classificacao || {}).map(([classificacao, meses]) => {
                // Garante que meses é um objeto
                if (typeof meses === 'object' && meses !== null) {
                  return [classificacao, (meses as Record<string, number>)[mesSelecionado] ?? 0];
                }
                return [classificacao, 0];
              })
            )
          );
          // Consumir MoM do backend com tipagem
          const momArr: MoMData[] = dataCustos.data.mom_analysis || [];
          const momObj = momArr.find((item) => item.mes === mesSelecionado);
          if (momObj) {
            setCustosMoM({
              variacao_absoluta: momObj.variacao_absoluta,
              variacao_percentual: momObj.variacao_percentual
            });
          } else {
            setCustosMoM(null);
          }
        }
      } else {
        setCustosValor(null);
        setCustosMesClass({});
        setCustosMoM(null);
      }
      setCustosLoading(false);
    }).catch(error => {
      console.error("Erro ao buscar saldos:", error);
      setSaldoFinal(null);
      setSaldoFinalMoM(null);
    }).finally(() => {
      setLoading(false);
      setLoadingSaldoFinal(false);
    });
  }, [mesSelecionado, inicializando]); // 🔥 MODIFICADO: adiciona inicializando como dependência

  return (
    <main className="p-4">
      <section className="py-4 flex justify-between items-center">
        <FiltroMes 
          onSelect={handleMesSelecionado} 
          endpoint="http://127.0.0.1:8000/receber"
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
            {/* Contas Recebidas */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-center">
                  <CardTitle className="text-lg sm:text-xl select-none">
                    Faturamento
                  </CardTitle>
                  <PlusCircle className="ml-auto w-4 h-4" />
                </div>
              </CardHeader>

              <CardContent>
                <div className="sm:flex sm:justify-between sm:items-center">
                  <p className="text-lg sm:text-2xl">
                    {saldoReceber !== null ? (
                      formatCurrencyShort(saldoReceber)
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
                    {saldoPagar !== null ? (
                      formatCurrencyShort(saldoPagar)
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
        {(inicializando || loading || loadingSaldoFinal || custosLoading) ? (
          // Exibe skeletons enquanto carrega
          <>
            <CardSkeletonLarge />
            <CardSkeletonLarge />
            <CardSkeletonLarge />
          </>
        ) : (
          // Exibe os cards reais após carregar
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
                    {saldoMovimentacoes !== null ? (
                      formatCurrencyShort(saldoMovimentacoes)
                    ) : (
                      "--"
                    )}
                  </p>
                </div>

                <CardDescription>
                  <div className="flex items-center gap-2 mt-2 mb-10 leading-none font-medium">
                    {/* Footer dinâmico: mostra variação e período do gráfico */}
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

                <ChartMovimentacoes mesSelecionado={mesSelecionado} />
              </CardContent>
              <CardFooter>
                <div className="flex w-full items-start gap-2 text-sm">
                  <div className="grid gap-2">

                    <CardDescription>
                      <p>Movimentações últimos 6M</p>
                    </CardDescription>
                    <div className="text-muted-foreground flex items-center gap-2 leading-none">
                      {/* Período exibido no gráfico */}
                      {saldosEvolucao.length > 0 ? (
                        <>
                          {(() => {
                            const primeiro = saldosEvolucao[0].mes;
                            const ultimo = saldosEvolucao[saldosEvolucao.length - 1].mes;
                            // Formatar para "abr/25"
                            const formatar = (mes: string) => {
                              if (!mes.match(/^\d{4}-\d{2}$/)) return mes;
                              const [ano, m] = mes.split("-");
                              const meses = ["", "jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"];
                              const mesNum = parseInt(m, 10);
                              return `${meses[mesNum]}/${ano.slice(-2)}`;
                            };
                            return `${formatar(primeiro)} - ${formatar(ultimo)}`;
                          })()}
                        </>
                      ) : (
                        <>--</>
                      )}
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
                    {/* Footer dinâmico: mostra variação e período do gráfico */}
                    {mesSelecionado === "" ? (
                      <>Sem variação</>
                    ) : saldoFinalMoM && saldoFinalMoM.variacao_percentual !== null ? (
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

                <ChartAreaSaldoFinal data={saldosEvolucao} mesSelecionado={mesSelecionado} />
              </CardContent>
              <CardFooter>
                <div className="flex w-full items-start gap-2 text-sm">
                  <div className="grid gap-2">
                    <CardDescription>
                      <p>Saldo últimos 6M</p>
                    </CardDescription>

                    <div className="text-muted-foreground flex items-center gap-2 leading-none">
                      {/* Período exibido no gráfico */}
                      {saldosEvolucao.length > 0 ? (
                        <>
                          {(() => {
                            const primeiro = saldosEvolucao[0].mes;
                            const ultimo = saldosEvolucao[saldosEvolucao.length - 1].mes;
                            // Formatar para "abr/25"
                            const formatar = (mes: string) => {
                              if (!mes.match(/^\d{4}-\d{2}$/)) return mes;
                              const [ano, m] = mes.split("-");
                              const meses = ["", "jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"];
                              const mesNum = parseInt(m, 10);
                              return `${meses[mesNum]}/${ano.slice(-2)}`;
                            };
                            return `${formatar(primeiro)} - ${formatar(ultimo)}`;
                          })()}
                        </>
                      ) : (
                        <>--</>
                      )}
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
                    {custosValor !== null ? (
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

                <ChartBarLabelCustom data={custosMesClass} />
              </CardContent>
              <CardFooter className="flex-col items-start gap-2 text-sm">
                <CardDescription>
                  <p>Custos por classificação</p>
                </CardDescription>
                <div className="text-muted-foreground flex items-center gap-2 leading-none">
                  {/* Período exibido conforme filtro */}
                  {formatarPeriodo({ mesSelecionado, saldosEvolucao })}
                </div>
              </CardFooter>
            </Card>
          </>
        )}
      </section>

      <section className="py-4 flex justify-between items-center">
        
      </section>
    </main>
  );
}