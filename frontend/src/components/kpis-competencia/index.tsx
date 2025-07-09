"use client";

import { ChartAreaGradientTwo } from "@/components/chart-area-gradient-2";
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
import {  
  ArrowUpDown,
  Hourglass,
  MinusCircle,
  Package,
  PlusCircle,
  TrendingUp,
  Wallet,
} from "lucide-react";
import { useEffect, useState } from "react";
import { FiltroMes } from "@/components/filtro-mes"

// Função para formatar no estilo curto (Mil / Mi)
function formatCurrencyShort(value: number): string {
  const absValue = Math.abs(value);
  let formatted = "";

  if (absValue >= 1_000_000) {
    formatted = `${(absValue / 1_000_000).toFixed(1)} Mi`;
  } else if (absValue >= 1_000) {
    formatted = `${(absValue / 1_000).toFixed(1)} Mil`;
  } else {
    formatted = absValue.toFixed(0);
  }

  return `R$ ${value < 0 ? "-" : ""}${formatted.replace(".", ",")}`;
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

export default function DashCompetencia() {
  // ✅ Estados declarados apenas uma vez
  const [saldoReceber, setSaldoReceber] = useState<number | null>(null);
  const [saldoPagar, setSaldoPagar] = useState<number | null>(null);
  const [mesSelecionado, setMesSelecionado] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [momReceber, setMomReceber] = useState<MoMData[]>([]);
  const [momPagar, setMomPagar] = useState<MoMData[]>([]);

  // Carregar o último mês mais recente ao abrir a tela
  useEffect(() => {
    fetch(`http://localhost:8000/receber`).then(res => res.json()).then(data => {
      if (data.success && data.data?.meses_disponiveis?.length > 0) {
        const meses = data.data.meses_disponiveis;
        const mesPadrao = meses[meses.length - 1];
        setMesSelecionado(mesPadrao);
      }
    });
  }, []);

  const handleMesSelecionado = (mes: string) => {
    setMesSelecionado(mes);
  };

  useEffect(() => {
    setLoading(true);
    const queryString = mesSelecionado ? `?mes=${mesSelecionado}` : "";
    Promise.all([
      fetch(`http://localhost:8000/receber${queryString}`).then(r => r.json()),
      fetch(`http://localhost:8000/pagar${queryString}`).then(r => r.json())
    ]).then(([dataReceber, dataPagar]) => {
      if (dataReceber.success) {
        setSaldoReceber(dataReceber.data.saldo_total);
        setMomReceber(dataReceber.data.mom_analysis || []);
      }
      if (dataPagar.success) {
        setSaldoPagar(dataPagar.data.saldo_total);
        setMomPagar(dataPagar.data.mom_analysis || []);
      }
    }).catch(error => {
      console.error("Erro ao buscar saldos:", error);
    }).finally(() => {
      setLoading(false);
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
                  <span className="inline-block h-6 w-32 rounded bg-muted animate-pulse"></span>
                ) : saldoReceber !== null ? (
                  formatCurrencyShort(saldoReceber)
                ) : (
                  <span className="inline-block h-6 w-32 rounded bg-muted animate-pulse"></span>
                )}
              </p>
              <CardDescription>
                {(() => {
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
            </CardDescription>
          </CardHeader>

          <CardContent>
            <div className="sm:flex sm:justify-between sm:items-center">
              <p className="text-lg sm:text-2xl">6 dias</p>
              <CardDescription>
                <p>Últimos 12M</p>
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
                  <span className="inline-block h-6 w-32 rounded bg-muted animate-pulse"></span>
                ) : saldoPagar !== null ? (
                  formatCurrencyShort(saldoPagar)
                ) : (
                  <span className="inline-block h-6 w-32 rounded bg-muted animate-pulse"></span>
                )}
              </p>
              <CardDescription>
                {(() => {
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
            </CardDescription>
          </CardHeader>

          <CardContent>
            <div className="sm:flex sm:justify-between sm:items-center">
              <p className="text-lg sm:text-2xl">8 dias</p>
              <CardDescription>
                <p>Últimos 12M</p>
              </CardDescription>
            </div>
          </CardContent>
        </Card>
      </section>

      <section className="mt-4 flex flex-col lg:flex-row gap-4">
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
              <p className="text-lg sm:text-2xl">R$ -515,2 Mil</p>
              <CardDescription>
                <p>
                  vs abr/25 <br />↗ 261,9%
                </p>
              </CardDescription>
            </div>

            <CardDescription className="py-4">
              <p>Movimentações últimos 6M</p>
            </CardDescription>

            <ChartOverview />
          </CardContent>
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
              <p className="text-lg sm:text-2xl">R$ -467,7 Mil</p>
              <CardDescription>
                <p>
                  vs abr/25 <br />↗ 1085,3%
                </p>
              </CardDescription>
            </div>

            <CardDescription className="py-4">
              <p>Saldo últimos 6M</p>
            </CardDescription>

            <ChartAreaGradientTwo />
          </CardContent>
          <CardFooter>
            <div className="flex w-full items-start gap-2 text-sm">
              <div className="grid gap-2">
                <div className="flex items-center gap-2 leading-none font-medium">
                  Trending up by 5.2% this month <TrendingUp className="h-4 w-4" />
                </div>
                <div className="text-muted-foreground flex items-center gap-2 leading-none">
                  January - June 2024
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