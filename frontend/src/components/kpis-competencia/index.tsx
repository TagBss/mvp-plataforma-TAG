"use client";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { CardSkeleton } from "@/components/ui/card-skeleton";
import {  
  MinusCircle,
  PlusCircle,
  TrendingUp,
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

// Tipagem para MoM (análise horizontal)
type MoMData = {
  mes: string;
  valor_atual: number;
  valor_anterior: number | null;
  variacao_absoluta: number | null;
  variacao_percentual: number | null;
};

// Tipagem para linha da DRE
interface DreLinha {
  nome: string;
  valor: number;
  valores_mensais: Record<string, number>;
  horizontal_mensais: Record<string, string>; // Strings como "+35.2%", "-100.0%"
}

// Função utilitária para formatar períodos de meses
const mesesAbreviados = ['', 'jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez'];

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

export default function DashCompetencia() {
  console.log("🔥 COMPONENTE INICIADO");
  
  // Estados principais
  const [mesSelecionado, setMesSelecionado] = useState<string>("");
  const [inicializando, setInicializando] = useState(true);
  const [loading, setLoading] = useState(false);
  
  // Estados dos KPIs
  const [faturamentoValor, setFaturamentoValor] = useState<number | null>(null);
  const [momFaturamento, setMomFaturamento] = useState<MoMData[]>([]);
  const [custosValor, setCustosValor] = useState<number | null>(null);
  const [momCustos, setMomCustos] = useState<MoMData[]>([]);
  const [lucroLiquidoValor, setLucroLiquidoValor] = useState<number | null>(null);
  const [momLucroLiquido, setMomLucroLiquido] = useState<MoMData[]>([]);
  const [lucratividadeValor, setLucratividadeValor] = useState<number | null>(null);
  const [momLucratividade, setMomLucratividade] = useState<MoMData[]>([]);

  console.log("🔍 Estados atuais - mesSelecionado:", mesSelecionado, "inicializando:", inicializando);

  // Handler para mudança de mês
  const handleMudancaMes = (novoMes: string) => {
    console.log("🔄 Mudando para:", novoMes);
    setMesSelecionado(novoMes);
  };

  // Função para carregar dados dos KPIs a partir do endpoint /dre
  const carregarDados = async (mes: string) => {
    setLoading(true);
    try {
      // SEMPRE buscar sem filtro de mês para ter dados históricos completos
      const response = await fetch(`http://127.0.0.1:8000/dre`);
      const data = await response.json();
      // Aceita tanto data.data quanto data diretamente
      let linhas: DreLinha[] = [];
      if (Array.isArray(data?.data)) {
        linhas = data.data;
      } else if (Array.isArray(data)) {
        linhas = data;
      }
      // Faturamento
      const fat = linhas.find((item) => item.nome === "Faturamento");
      
      // Usar valor específico do mês selecionado OU valor total
      const valorFaturamento = mes && fat?.valores_mensais?.[mes] !== undefined 
        ? fat.valores_mensais[mes] 
        : fat?.valor ?? null;
      setFaturamentoValor(valorFaturamento);
      // Custos (Custo com Importação + Custo com Mercadoria Interna)
      const custoImport = linhas.find((item) => item.nome === "Custo com Importação");
      const custoMerc = linhas.find((item) => item.nome === "Custo com Mercadoria Interna");
      
      // Calcular custos para o mês selecionado OU valor total
      const valorCustoImport = mes && custoImport?.valores_mensais?.[mes] !== undefined 
        ? custoImport.valores_mensais[mes] 
        : custoImport?.valor ?? 0;
      const valorCustoMerc = mes && custoMerc?.valores_mensais?.[mes] !== undefined 
        ? custoMerc.valores_mensais[mes] 
        : custoMerc?.valor ?? 0;
      setCustosValor(valorCustoImport + valorCustoMerc);
      // Lucro Líquido (Resultado Líquido)
      const lucro = linhas.find((item) => item.nome === "Resultado Líquido");
      const valorLucro = mes && lucro?.valores_mensais?.[mes] !== undefined 
        ? lucro.valores_mensais[mes] 
        : lucro?.valor ?? null;
      setLucroLiquidoValor(valorLucro);
      
      // Lucratividade (Lucro Líquido / Faturamento * 100)
      const lucratividade = valorFaturamento && valorLucro && valorFaturamento !== 0 
        ? (valorLucro / valorFaturamento) * 100 
        : null;
      setLucratividadeValor(lucratividade);

      // MoM (análise horizontal)
      // Helper para converter horizontal_mensais em array de MoMData
      function getMoMArray(linha?: DreLinha): MoMData[] {
        if (!linha || !linha.horizontal_mensais || !linha.valores_mensais) return [];
        
        const meses = Object.keys(linha.valores_mensais).sort();
        
        return meses.map((mes, index) => {
          const valor_atual = linha.valores_mensais[mes] || 0;
          const valor_anterior = index > 0 ? linha.valores_mensais[meses[index - 1]] || 0 : null;
          
          // Pegar a string de análise horizontal do backend (ex: "+35.2%", "-100.0%")
          const horizontalString = linha.horizontal_mensais[mes];
          
          let variacao_percentual: number | null = null;
          let variacao_absoluta: number | null = null;
          
          if (horizontalString && typeof horizontalString === "string" && horizontalString !== "–") {
            // Simplificar: remover % e converter
            const numericString = horizontalString.replace('%', '');
            const numericValue = parseFloat(numericString);
            
            if (!isNaN(numericValue)) {
              variacao_percentual = numericValue;
            }
          }
          
          // Calcular variação absoluta se temos os valores
          if (valor_anterior !== null && variacao_percentual !== null) {
            variacao_absoluta = valor_atual - valor_anterior;
          }
          
          return {
            mes,
            valor_atual,
            valor_anterior,
            variacao_absoluta,
            variacao_percentual,
          };
        });
      }
      const momFatData = getMoMArray(fat);
      setMomFaturamento(momFatData);
      
      // Para custos, processar os dois tipos de custos separadamente e depois combinar
      const momCustoImport = getMoMArray(custoImport);
      const momCustoMerc = getMoMArray(custoMerc);
      
      // Combinar os MoM dos dois custos
      const todosMeses = new Set([
        ...momCustoImport.map(item => item.mes),
        ...momCustoMerc.map(item => item.mes)
      ]);
      
      const momCustosCombinadoMap = new Map<string, MoMData>();
      
      Array.from(todosMeses).sort().forEach(mes => {
        const importData = momCustoImport.find(item => item.mes === mes);
        const mercData = momCustoMerc.find(item => item.mes === mes);
        
        const valor_atual = (importData?.valor_atual || 0) + (mercData?.valor_atual || 0);
        const valor_anterior = (importData?.valor_anterior || 0) + (mercData?.valor_anterior || 0);
        
        let variacao_absoluta: number | null = null;
        let variacao_percentual: number | null = null;
        
        if (valor_anterior !== null && valor_anterior !== 0) {
          variacao_absoluta = valor_atual - valor_anterior;
          variacao_percentual = ((valor_atual - valor_anterior) / Math.abs(valor_anterior)) * 100;
        }
        
        momCustosCombinadoMap.set(mes, {
          mes,
          valor_atual,
          valor_anterior,
          variacao_absoluta,
          variacao_percentual,
        });
      });
      
      setMomCustos(Array.from(momCustosCombinadoMap.values()));
      setMomLucroLiquido(getMoMArray(lucro));
      // Lucratividade MoM: calcular a partir de lucro/faturamento mês a mês
      if (fat && lucro) {
        const meses = Object.keys(fat.valores_mensais || {});
        const momLucratividade: MoMData[] = meses.map((mes, idx) => {
          const fatAtual = fat.valores_mensais[mes] ?? 0;
          const lucroAtual = lucro.valores_mensais[mes] ?? 0;
          const valor_atual = fatAtual !== 0 ? (lucroAtual / fatAtual) * 100 : 0;
          let valor_anterior = null;
          if (idx > 0) {
            const mesAnterior = meses[idx - 1];
            const fatAnt = fat.valores_mensais[mesAnterior] ?? 0;
            const lucroAnt = lucro.valores_mensais[mesAnterior] ?? 0;
            valor_anterior = fatAnt !== 0 ? (lucroAnt / fatAnt) * 100 : 0;
          }
          let variacao_absoluta = null;
          let variacao_percentual = null;
          if (valor_anterior !== null) {
            variacao_absoluta = valor_atual - valor_anterior;
            variacao_percentual = valor_anterior !== 0 ? ((valor_atual - valor_anterior) / valor_anterior) * 100 : null;
          }
          return { mes, valor_atual, valor_anterior, variacao_absoluta, variacao_percentual };
        });
        setMomLucratividade(momLucratividade);
      } else {
        setMomLucratividade([]);
      }
    } catch (e) {
      console.error("❌ Erro ao carregar dados:", e);
    } finally {
      setLoading(false);
    }
  };

  // Inicialização: buscar meses disponíveis do endpoint /dre
  useEffect(() => {
    const init = async () => {
      try {
        const response = await fetch(`http://127.0.0.1:8000/dre`);
        const data = await response.json();
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
          endpoint="http://127.0.0.1:8000/dre"
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
            {/* Faturamento */}
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
                    {faturamentoValor !== null ? (
                      formatCurrencyShort(faturamentoValor)
                    ) : (
                      "--"
                    )}
                  </p>
                  <CardDescription>
                    {mesSelecionado === "" ? (
                      <p>vs período anterior <br />-- --</p>
                    ) : (() => {
                      const mom = getMoMIndicator(momFaturamento, mesSelecionado);
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

            {/* Custos */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-center">
                  <CardTitle className="text-lg sm:text-xl select-none">
                    Custos
                  </CardTitle>
                  <MinusCircle className="ml-auto w-4 h-4" />
                </div>
              </CardHeader>

              <CardContent>
                <div className="sm:flex sm:justify-between sm:items-center">
                  <p className="text-lg sm:text-2xl">
                    {custosValor !== null ? (
                      formatCurrencyShort(Math.abs(custosValor))
                    ) : (
                      "--"
                    )}
                  </p>
                  <CardDescription>
                    {mesSelecionado === "" ? (
                      <p>vs período anterior <br />-- --</p>
                    ) : (() => {
                      const mom = getMoMIndicator(momCustos, mesSelecionado);
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

            {/* Lucro Líquido */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-center">
                  <CardTitle className="text-lg sm:text-xl select-none">
                    Lucro Líquido
                  </CardTitle>
                  <Wallet className="ml-auto w-4 h-4" />
                </div>
              </CardHeader>

              <CardContent>
                <div className="sm:flex sm:justify-between sm:items-center">
                  <p className="text-lg sm:text-2xl">
                    {lucroLiquidoValor !== null ? (
                      formatCurrencyShort(lucroLiquidoValor)
                    ) : (
                      "--"
                    )}
                  </p>
                  <CardDescription>
                    {mesSelecionado === "" ? (
                      <p>vs período anterior <br />-- --</p>
                    ) : (() => {
                      const mom = getMoMIndicator(momLucroLiquido, mesSelecionado);
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

            {/* Lucratividade */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-center">
                  <CardTitle className="text-lg sm:text-xl select-none">
                    Lucratividade
                  </CardTitle>
                  <TrendingUp className="ml-auto w-4 h-4" />
                </div>
              </CardHeader>

              <CardContent>
                <div className="sm:flex sm:justify-between sm:items-center">
                  <p className="text-lg sm:text-2xl">
                    {lucratividadeValor !== null ? (
                      `${lucratividadeValor.toFixed(1)}%`
                    ) : (
                      "--"
                    )}
                  </p>
                  <CardDescription>
                    {mesSelecionado === "" ? (
                      <p>vs período anterior <br />-- --</p>
                    ) : (() => {
                      const mom = getMoMIndicator(momLucratividade, mesSelecionado);
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
          </>
        )}
      </section>

      <section className="mt-8 text-center">
        <p className="text-sm text-gray-600">
          Dados atualizados em tempo real via endpoint unificado da DRE
        </p>
      </section>
    </main>
  );
}
