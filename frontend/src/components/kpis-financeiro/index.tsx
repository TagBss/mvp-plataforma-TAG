"use client";

import { ChartAreaSaldoFinal } from "@/components/chart-area-gradient-2";
import { ChartBarMixed } from "@/components/chart-bar-mixed";
import ChartOverview from "@/components/charts";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
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

// Função para extrair o MoM do mês selecionado (ou último)
const mesesAbreviados = [
  '', 'jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez'
];



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
  // ✅ Estados declarados apenas uma vez
  const [saldoReceber, setSaldoReceber] = useState<number | null>(null);
  const [saldoPagar, setSaldoPagar] = useState<number | null>(null);
  const [saldoMovimentacoes, setSaldoMovimentacoes] = useState<number | null>(null);
  const [saldoFinal, setSaldoFinal] = useState<number | null>(null);
  const [saldoFinalMoM, setSaldoFinalMoM] = useState<{ variacao_absoluta: number | null, variacao_percentual: number | null } | null>(null);
  const [mesSelecionado, setMesSelecionado] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [loadingSaldoFinal, setLoadingSaldoFinal] = useState(false);
  const [momReceber, setMomReceber] = useState<MoMData[]>([]);
  const [momPagar, setMomPagar] = useState<MoMData[]>([]);
  const [momMovimentacoes, setMomMovimentacoes] = useState<MoMData[]>([]);
  const [pmr, setPmr] = useState<string | null>(null);
  const [pmp, setPmp] = useState<string | null>(null);
  const [saldosEvolucao, setSaldosEvolucao] = useState<Array<{ mes: string; saldo_inicial: number; saldo_final: number }>>([]);


  // Carregar o último mês mais recente ao abrir a tela
  useEffect(() => {
    fetch(`http://localhost:8000/receber`).then(res => res.json()).then(data => {
      if (data.success && data.data?.meses_disponiveis?.length > 0) {
        const meses = data.data.meses_disponiveis;
        const mesPadrao = meses[meses.length - 1];
        setMesSelecionado(mesPadrao);
      }
      if (data.success && data.data?.pmr) {
        setPmr(data.data.pmr);
      }
    });
    fetch(`http://localhost:8000/pagar`).then(res => res.json()).then(data => {
      if (data.success && data.data?.pmp) {
        setPmp(data.data.pmp);
      }
    });
  }, []);


  const handleMesSelecionado = (mes: string) => {
    setSaldoReceber(null);
    setSaldoPagar(null);
    setSaldoMovimentacoes(null);
    setMesSelecionado(mes);
  };



  useEffect(() => {
    // Permitir busca mesmo quando mesSelecionado for string vazia (""),
    // só não busca se for null ou undefined
    if (mesSelecionado === null || mesSelecionado === undefined) return;
    setLoading(true);
    setLoadingSaldoFinal(true);
    const queryString = mesSelecionado ? `?mes=${mesSelecionado}` : "";
    Promise.all([
      fetch(`http://localhost:8000/receber${queryString}`).then(r => r.json()),
      fetch(`http://localhost:8000/pagar${queryString}`).then(r => r.json()),
      fetch(`http://localhost:8000/movimentacoes${queryString}`).then(r => r.json()),
      fetch(`http://localhost:8000/saldos-evolucao`).then(r => r.json())
    ]).then(([dataReceber, dataPagar, dataMovimentacoes, dataSaldosEvolucao]) => {
      if (dataReceber.success) {
        setSaldoReceber(dataReceber.data.saldo_total);
        setMomReceber(dataReceber.data.mom_analysis || []);
      }
      if (dataPagar.success) {
        setSaldoPagar(dataPagar.data.saldo_total);
        setMomPagar(dataPagar.data.mom_analysis || []);
      }
      if (dataMovimentacoes.success) {
        setSaldoMovimentacoes(dataMovimentacoes.data.saldo_total);
        setMomMovimentacoes(dataMovimentacoes.data.mom_analysis || []);
      }
      // Buscar saldo final do mês selecionado e MoM
      if (dataSaldosEvolucao.success && dataSaldosEvolucao.data?.evolucao?.length > 0) {
        let saldoFinal = null;
        let variacao_absoluta = null;
        let variacao_percentual = null;
        type SaldosEvolucaoItem = { mes: string; saldo_inicial: number; movimentacao: number; saldo_final: number; variacao_absoluta?: number | null; variacao_percentual?: number | null };
        const evolucaoArr = dataSaldosEvolucao.data.evolucao as SaldosEvolucaoItem[];
        // Salvar para o gráfico (últimos 12 meses)
        setSaldosEvolucao(evolucaoArr.slice(-12).map(({ mes, saldo_inicial, saldo_final }) => ({ mes, saldo_inicial, saldo_final })));
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
    }).catch(error => {
      console.error("Erro ao buscar saldos:", error);
      setSaldoFinal(null);
    }).finally(() => {
      setLoading(false);
      setLoadingSaldoFinal(false);
    });
  }, [mesSelecionado]);

  return (
    <main className="p-4">
      <section className="py-4 flex justify-between items-center">
        <FiltroMes 
          onSelect={handleMesSelecionado} 
          endpoint="http://localhost:8000/receber"
          value={mesSelecionado}
        />
      </section>
      
      <section className="grid grid-cols-2 lg:grid-cols-4 gap-4">
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
                {loading ? (
                  <Skeleton className="h-6 w-32" />
                ) : saldoReceber !== null ? (
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
                {loading ? (
                  <Skeleton className="h-6 w-32" />
                ) : saldoPagar !== null ? (
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
              <p className="text-lg sm:text-2xl">{pmr ?? <Skeleton className="h-6 w-20" />}</p>
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
              <p className="text-lg sm:text-2xl">{pmp ?? <Skeleton className="h-6 w-20" />}</p>
            </div>
          </CardContent>
        </Card>
      </section>

      <section className="mt-4 flex flex-col lg:flex-row gap-4">
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
                {loading ? (
                  <Skeleton className="h-6 w-32" />
                ) : saldoMovimentacoes !== null ? (
                  formatCurrencyShort(saldoMovimentacoes)
                ) : (
                  "--"
                )}
              </p>
              <CardDescription>
                {mesSelecionado === "" ? (
                  <p>vs período anterior <br />-- --</p>
                ) : (() => {
                  const mom = getMoMIndicator(momMovimentacoes, mesSelecionado);
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

            <CardDescription className="py-4">
              <p>Movimentações últimos 6M</p>
            </CardDescription>

            <ChartOverview />
          </CardContent>
          <CardFooter>
            <div className="flex w-full items-start gap-2 text-sm">
              <div className="grid gap-2">
                <div className="flex items-center gap-2 leading-none font-medium">
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
                {loadingSaldoFinal ? (
                  <Skeleton className="h-6 w-32" />
                ) : saldoFinal !== null ? (
                  formatCurrencyShort(saldoFinal)
                ) : (
                  "--"
                )}
              </p>
              <CardDescription>
                {mesSelecionado === "" ? (
                  <p>vs período anterior <br />-- --</p>
                ) : saldoFinalMoM && saldoFinalMoM.variacao_percentual !== null ? (
                  <p>
                    vs mês anterior <br />
                    <span>
                      {saldoFinalMoM.variacao_percentual > 0 ? "↗" : saldoFinalMoM.variacao_percentual < 0 ? "↙" : ""} {Math.abs(saldoFinalMoM.variacao_percentual).toFixed(1)}%
                    </span>
                  </p>
                ) : (
                  <p>vs mês anterior <br />-- --</p>
                )}
              </CardDescription>
            </div>

            <CardDescription className="py-4">
              <p>Saldo últimos 6M</p>
            </CardDescription>

            <ChartAreaSaldoFinal data={saldosEvolucao} />
          </CardContent>
          <CardFooter>
            <div className="flex w-full items-start gap-2 text-sm">
              <div className="grid gap-2">
                <div className="flex items-center gap-2 leading-none font-medium">
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
              <p className="text-lg sm:text-2xl">R$ -214,8 Mil</p>
              <CardDescription>
                <p>
                  vs abr/25 <br />↙ 17,6%
                </p>
              </CardDescription>
            </div>

            <CardDescription className="py-4">
              <p>Saldo últimos 6M</p>
            </CardDescription>

            <ChartBarMixed />
          </CardContent>
          <CardFooter className="flex-col items-start gap-2 text-sm">
            <div className="flex gap-2 leading-none font-medium">
              Trending up by 5.2% this month <TrendingUp className="h-4 w-4" />
            </div>
            <div className="text-muted-foreground leading-none">
              Showing total visitors for the last 6 months
            </div>
          </CardFooter>
        </Card>
      </section>
    </main>
  );
}