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
  ChartColumnBig,
  MinusCircle,
  PlusCircle,
  TrendingUp,
  Wallet,
} from "lucide-react";
import { useEffect, useState } from "react";
import { FiltroMes } from "../filtro-mes"
import { ChartBarDre, WaterfallDataPoint } from "../charts-competencia/chart-bar-dre"
import { ChartBarCustos } from "../charts-competencia/chart-bar-custos"
import { ChartBarDespesas } from "../charts-competencia/chart-bar-despesas"
import { ChartCustosCompetencia as ChartAreaCustos } from "../charts-competencia/chart-area-custos"
import { ChartAreaDespesas } from "../charts-competencia/chart-area-despesas"
import { ChartBarCustosData } from "../charts-competencia/chart-bar-custos"
import { ChartBarDespesasData } from "../charts-competencia/chart-bar-despesas"
import { ChartAreaFaturamento } from "../charts-competencia/chart-area-faturamento"
import { api } from "../../services/api"

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
  classificacoes?: DreLinha[]; // Classificações (dre_n2) de um dre_n1
}

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

function getMoMIndicatorCustos(momData: MoMData[], mesSelecionado: string) {
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
  
  // Para custos, calculamos baseado nos valores absolutos
  const valorAtual = Math.abs(entry?.valor_atual ?? 0);
  const valorAnterior = Math.abs(entry?.valor_anterior ?? 0);
  
  let variacao = null;
  if (valorAnterior !== 0) {
    variacao = ((valorAtual - valorAnterior) / valorAnterior) * 100;
  }

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
    // Para custos: aumento de valor absoluto = seta para cima (ruim), diminuição = seta para baixo (bom)
    arrow: variacao !== null ? (variacao > 0 ? "↗" : "↙") : "",
    hasValue: variacao !== null
  };
}

export default function DashCompetencia() {
  // Estados principais
  const [mesSelecionado, setMesSelecionado] = useState<string>("");
  const [inicializando, setInicializando] = useState(true);
  const [loading, setLoading] = useState(false);
  // Estados dos KPIs
  const [faturamentoValor, setFaturamentoValor] = useState<number | null>(null);
  const [momFaturamento, setMomFaturamento] = useState<MoMData[]>([]);
  const [faturamentoEvolucao, setFaturamentoEvolucao] = useState<Array<{ mes: string; faturamento: number }>>([]);
  const [custosValor, setCustosValor] = useState<number | null>(null);
  const [momCustos, setMomCustos] = useState<MoMData[]>([]);
  const [custosEvolucao, setCustosEvolucao] = useState<Array<{ mes: string; custos: number }>>([]);
  const [despesasEvolucao, setDespesasEvolucao] = useState<Array<{ mes: string; despesas: number }>>([]);
  const [lucroLiquidoValor, setLucroLiquidoValor] = useState<number | null>(null);
  const [momLucroLiquido, setMomLucroLiquido] = useState<MoMData[]>([]);
  const [lucratividadeValor, setLucratividadeValor] = useState<number | null>(null);
  const [momLucratividade, setMomLucratividade] = useState<MoMData[]>([]);
  
  // Estados para custos e despesas dinâmicos
  const [custosNomes, setCustosNomes] = useState<string[]>([]);
  const [despesasNomes, setDespesasNomes] = useState<string[]>([]);
  
  // Handler para mudança de mês
  const handleMudancaMes = (novoMes: string) => {
    setMesSelecionado(novoMes);
  };
  // Estados para ranking de custos e despesas
  const [rankingCustos, setRankingCustos] = useState<ChartBarCustosData[]>([]);
  const [rankingDespesas, setRankingDespesas] = useState<ChartBarDespesasData[]>([]);
  // Estado para gráfico cascata DRE
  const [dreWaterfallData, setDreWaterfallData] = useState<WaterfallDataPoint[]>([]);

  // Função para carregar dados dos KPIs a partir do endpoint /dre
  const carregarDados = async (mes: string) => {
    setLoading(true);
     try {
       // SEMPRE buscar sem filtro de mês para ter dados históricos completos
       const response = await api.get('/dre');
       const data = response.data;
       // Aceita tanto data.data quanto data diretamente
       let linhas: DreLinha[] = [];
       if (Array.isArray(data?.data)) {
         linhas = data.data;
       } else if (Array.isArray(data)) {
         linhas = data;
       }
       
       // Obter custos e despesas do backend
       const custosBackend = data?.custos || [];
       const despesasBackend = data?.despesas || [];
       setCustosNomes(custosBackend);
       setDespesasNomes(despesasBackend);
       
       // Debug: log das linhas encontradas
       console.log("📊 Linhas DRE encontradas:", linhas.map(l => l.nome));
       console.log("💰 Custos identificados pelo backend:", custosBackend);
       console.log("💸 Despesas identificadas pelo backend:", despesasBackend);
       
       // Debug: log dos custos encontrados
       const custosEncontrados = linhas.filter((item) => 
         custosBackend.includes(item.nome)
       );
       console.log("💰 Custos encontrados:", custosEncontrados.map(c => ({ nome: c.nome, valor: c.valor })));
       
       // Debug: log das despesas encontradas
       const despesasEncontradas = linhas.filter((item) => 
         despesasBackend.includes(item.nome)
       );
       console.log("💸 Despesas encontradas:", despesasEncontradas.map(d => ({ nome: d.nome, valor: d.valor })));

       // Debug: log detalhado dos valores por mês para custos
       if (custosEncontrados.length > 0) {
         console.log("🔍 Debug Custos por mês:");
         custosEncontrados.forEach(custo => {
           console.log(`  ${custo.nome}:`, custo.valores_mensais);
         });
       }

       // Debug: log detalhado dos valores por mês para despesas
       if (despesasEncontradas.length > 0) {
         console.log("🔍 Debug Despesas por mês:");
         despesasEncontradas.forEach(despesa => {
           console.log(`  ${despesa.nome}:`, despesa.valores_mensais);
         });
       }

       // Gráfico cascata DRE (Waterfall)
       const sequenciaDre = [
         "Receita Bruta",
         "Receita Líquida",
         "Resultado Bruto",
         "EBITDA",
         "EBIT",
         "Resultado Financeiro",
         "Resultado Líquido"
       ];
       let valorAcumulado = 0;
       const waterfallData: WaterfallDataPoint[] = sequenciaDre.map((nome, index) => {
         const linha = linhas.find((item: DreLinha) => item.nome === nome);
         // Usar valor do mês selecionado ou valor total
         const valor = linha ? (
           mes && linha.valores_mensais?.[mes] !== undefined
             ? linha.valores_mensais[mes]
             : linha.valor ?? 0
         ) : 0;
         // Determinar o tipo baseado no valor
         let tipo: 'positivo' | 'negativo' | 'total' = 'positivo';
         if (index === 0) {
           tipo = 'total';
         } else if (valor < 0) {
           tipo = 'negativo';
         } else {
           tipo = 'positivo';
         }
         valorAcumulado += valor;
         // Determinar a cor baseada no tipo
         const fill = tipo === 'positivo' ? '#22c55e' : tipo === 'negativo' ? '#ef4444' : '#22c55e';
         return {
           nome,
           valor: Math.abs(valor),
           valorAcumulado,
           tipo,
           displayValue: formatCurrencyShort(valor, { noPrefix: false }),
           fill
         };
       });
       setDreWaterfallData(waterfallData);


             // Faturamento: buscar por diferentes nomes possíveis
       const fat = linhas.find((item) => 
         item.nome === "Faturamento" || 
         item.nome === "Receita Bruta" ||
         item.nome === "Receita Líquida"
       );

       // Usar valor específico do mês selecionado OU valor total
       const valorFaturamento = mes && fat?.valores_mensais?.[mes] !== undefined 
         ? fat.valores_mensais[mes] 
         : fat?.valor ?? null;
       setFaturamentoValor(valorFaturamento);
      // Processar evolução do faturamento (últimos 12 meses)
      if (fat && fat.valores_mensais) {
        const mesesOrdenados = Object.keys(fat.valores_mensais).sort();
        const evolucao = mesesOrdenados.slice(-12).map(mes => ({
          mes,
          faturamento: fat.valores_mensais[mes] || 0
        }));
        setFaturamentoEvolucao(evolucao);
      } else {
        setFaturamentoEvolucao([]);
      }
             // Custos: buscar itens que compõem o "Resultado Bruto"
       // Na nova estrutura, custos são itens com operador "-" que contribuem para o Resultado Bruto
       let custosLinhas: DreLinha[] = [];
       let totalCustos = 0;
       
       // Buscar custos diretamente na estrutura
       custosLinhas = linhas.filter((item) => 
         custosBackend.includes(item.nome)
       );
       
       // Calcular total de custos para o mês selecionado OU valor total
       custosLinhas.forEach(custo => {
         const valorCusto = mes && custo.valores_mensais?.[mes] !== undefined 
           ? custo.valores_mensais[mes] 
           : custo.valor ?? 0;
         // Para custos, sempre usar valor absoluto (pois são despesas)
         totalCustos += Math.abs(valorCusto);
         
         // Debug específico para maio
         if (mes === "2025-05") {
           console.log(`🔍 Custo ${custo.nome} em maio:`, valorCusto, "abs:", Math.abs(valorCusto));
         }
       });
       
       setCustosValor(totalCustos);
       
       // Debug específico para maio
       if (mes === "2025-05") {
         console.log("🔍 Total de custos em maio:", totalCustos);
       }
             const rankingCustosData: ChartBarCustosData[] = custosLinhas.map(linha => {
         const valorOriginal = mes && linha.valores_mensais?.[mes] !== undefined
           ? linha.valores_mensais[mes]
           : linha.valor ?? 0;
         return {
           categoria: linha.nome,
           valor: Math.abs(valorOriginal), // Custos são sempre positivos no ranking
           valorOriginal: valorOriginal
         };
       }).sort((a, b) => b.valor - a.valor);
       setRankingCustos(rankingCustosData);

             // Processar evolução dos custos (últimos 12 meses)
        if (custosLinhas.length > 0) {
          const todosMesesCustos = new Set<string>();
          custosLinhas.forEach(linha => {
            if (linha && linha.valores_mensais) {
              Object.keys(linha.valores_mensais).forEach(mes => todosMesesCustos.add(mes));
            }
          });
          
          const mesesOrdenadosCustos = Array.from(todosMesesCustos).sort();
          const evolucaoCustos = mesesOrdenadosCustos.slice(-12).map(mes => ({
            mes,
            custos: custosLinhas.reduce((total, linha) => {
              // Para custos, sempre usar valor absoluto
              return total + Math.abs(linha?.valores_mensais?.[mes] || 0);
            }, 0)
          }));
          
          // Debug específico para maio - evolução custos
          if (mes === "2025-05") {
            const custosMaio = evolucaoCustos.find(c => c.mes === "2025-05");
            console.log("🔍 Evolução custos em maio:", custosMaio);
          }
          
          setCustosEvolucao(evolucaoCustos);
        } else {
          setCustosEvolucao([]);
        }

             // Despesas: buscar itens que compõem o "EBITDA"
       // Na nova estrutura, despesas são itens com operador "-" que contribuem para o EBITDA
       let despesasLinhas: DreLinha[] = [];
       
       // Buscar despesas diretamente na estrutura
       despesasLinhas = linhas.filter((item) => 
         despesasBackend.includes(item.nome)
       );

       // Debug específico para maio - despesas
       if (mes === "2025-05") {
         console.log("🔍 Despesas encontradas em maio:");
         despesasLinhas.forEach(despesa => {
           const valorDespesa = despesa.valores_mensais?.[mes] || despesa.valor || 0;
           // Para despesas, sempre usar valor absoluto (pois são despesas)
           console.log(`  ${despesa.nome}:`, valorDespesa, "abs:", Math.abs(valorDespesa));
         });
       }

             // Ranking de despesas (para o gráfico de barras)
       const rankingDespesasData: ChartBarDespesasData[] = despesasLinhas.map(linha => {
         const valorOriginal = mes && linha.valores_mensais?.[mes] !== undefined
           ? linha.valores_mensais[mes]
           : linha.valor ?? 0;
         return {
           categoria: linha.nome,
           valor: Math.abs(valorOriginal), // Despesas são sempre positivas no ranking
           valorOriginal: valorOriginal
         };
       }).sort((a, b) => b.valor - a.valor);
       setRankingDespesas(rankingDespesasData);

       // Processar evolução das despesas (últimos 12 meses)
       if (despesasLinhas.length > 0) {
         const todosMesesDespesas = new Set<string>();
         despesasLinhas.forEach(linha => {
           if (linha && linha.valores_mensais) {
             Object.keys(linha.valores_mensais).forEach(mes => todosMesesDespesas.add(mes));
           }
         });
         
         const mesesOrdenadosDespesas = Array.from(todosMesesDespesas).sort();
         const evolucaoDespesas = mesesOrdenadosDespesas.slice(-12).map(mes => ({
           mes,
           despesas: despesasLinhas.reduce((total, linha) => {
             // Para despesas, sempre usar valor absoluto
             return total + Math.abs(linha?.valores_mensais?.[mes] || 0);
           }, 0)
         }));
         
         // Debug específico para maio - evolução despesas
         if (mes === "2025-05") {
           const despesasMaio = evolucaoDespesas.find(d => d.mes === "2025-05");
           console.log("🔍 Evolução despesas em maio:", despesasMaio);
         }
         
         setDespesasEvolucao(evolucaoDespesas);
       } else {
         setDespesasEvolucao([]);
       }

             // Lucro Líquido (Resultado Líquido)
       const lucro = linhas.find((item) => 
         item.nome === "Resultado Líquido" || 
         item.nome === "Lucro Líquido"
       );

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
      
             // Para custos, processar todos os custos do Resultado Bruto
       const momCustosCombinadoMap = new Map<string, MoMData>();
       
       if (custosLinhas.length > 0) {
         const todosMeses = new Set<string>();
         custosLinhas.forEach(linha => {
           if (linha.valores_mensais) {
             Object.keys(linha.valores_mensais).forEach(mes => todosMeses.add(mes));
           }
         });
         
         Array.from(todosMeses).sort().forEach(mes => {
           let valor_atual = 0;
           let valor_anterior = 0;
           
           custosLinhas.forEach(linha => {
             const valorCustoAtual = linha.valores_mensais?.[mes] || 0;
             // Para custos, sempre usar valor absoluto
             valor_atual += Math.abs(valorCustoAtual);
             
             // Para valor anterior, precisamos encontrar o mês anterior
             const mesesOrdenados = Object.keys(linha.valores_mensais || {}).sort();
             const indexMes = mesesOrdenados.indexOf(mes);
             if (indexMes > 0) {
               const mesAnterior = mesesOrdenados[indexMes - 1];
               const valorCustoAnterior = linha.valores_mensais?.[mesAnterior] || 0;
               // Para custos, sempre usar valor absoluto
               valor_anterior += Math.abs(valorCustoAnterior);
             }
           });
           
           let variacao_absoluta: number | null = null;
           let variacao_percentual: number | null = null;
           
           if (valor_anterior !== 0) {
             variacao_absoluta = valor_atual - valor_anterior;
             variacao_percentual = ((valor_atual - valor_anterior) / valor_anterior) * 100;
           }
           
           momCustosCombinadoMap.set(mes, {
             mes,
             valor_atual,
             valor_anterior,
             variacao_absoluta,
             variacao_percentual,
           });
         });
       }
       
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
        const response = await api.get('/dre');
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
    if (!inicializando) {
      carregarDados(mesSelecionado);
    }
  }, [mesSelecionado, inicializando]);

  return (
    <main className="p-4">
      <section className="py-4 flex justify-between items-center">
        <FiltroMes 
          onSelect={handleMudancaMes} 
          endpoint="/dre"
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
                      formatCurrencyShort(-custosValor)
                    ) : (
                      "--"
                    )}
                  </p>
                  <CardDescription>
                    {mesSelecionado === "" ? (
                      <p>vs período anterior <br />-- --</p>
                    ) : (() => {
                      const mom = getMoMIndicatorCustos(momCustos, mesSelecionado);
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
            {/* Gráfico cascata */}
            <Card className="w-full">
              <CardHeader>
                <div className="flex items-center justify-center">
                  <CardTitle className="text-lg sm:text-xl select-none">
                    Resultados por hierarquia DRE
                  </CardTitle>
                  <ChartColumnBig className="ml-auto w-4 h-4" />
                </div>
              </CardHeader>

              <CardContent>
                <div className="sm:flex sm:justify-between sm:items-center">
                  <CardDescription>
                    <div className="flex gap-2 mb-10 leading-none font-medium">
                      Evolução dos resultados financeiros
                      {mesSelecionado && ` - ${mesSelecionado}`}
                    </div>
                  </CardDescription>
                </div>

                <ChartBarDre data={dreWaterfallData} loading={inicializando || loading} error={undefined} />
              </CardContent>
              <CardFooter className="flex-col items-start gap-2 text-sm">
                <CardDescription>
                  <p>Análise por hierarquia DRE</p>
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
                    faturamentoEvolucao.length > 0 ? (
                      formatarPeriodo(faturamentoEvolucao)
                    ) : (
                      "Todo o período"
                    )
                  )}
                </div>
              </CardFooter>
            </Card>
            
            {/* Gráfico de faturamento */}
            <Card className="w-full">
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
                  <CardDescription>
                    <div className="flex gap-2 mb-10 leading-none font-medium">
                      Faturamento ao longo do tempo
                    </div>
                  </CardDescription>
                </div>

                <ChartAreaFaturamento data={faturamentoEvolucao} mesSelecionado={mesSelecionado} />
              </CardContent>
              <CardFooter className="flex-col items-start gap-2 text-sm">
                <CardDescription>
                  <p>Faturamento últimos 12M</p>
                </CardDescription>
                <div className="text-muted-foreground flex items-center gap-2 leading-none">
                  {faturamentoEvolucao.length > 0 ? (
                    formatarPeriodo(faturamentoEvolucao)
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
                <MinusCircle className="ml-auto w-4 h-4" />
              </div>
            </CardHeader>

            <CardContent>
              <div className="sm:flex sm:justify-between sm:items-center">
                <CardDescription>
                  <div className="flex gap-2 mb-10 leading-none font-medium">
                    Custos ao longo do tempo
                  </div>
                </CardDescription>
              </div>

              <ChartAreaCustos data={custosEvolucao} mesSelecionado={mesSelecionado} />
            </CardContent>
            <CardFooter className="flex-col items-start gap-2 text-sm">
              <CardDescription>
                <p>Custos últimos 12M</p>
              </CardDescription>
              <div className="text-muted-foreground flex items-center gap-2 leading-none">
                {custosEvolucao.length > 0 ? (
                  formatarPeriodo(custosEvolucao)
                ) : (
                  "Todo o período"
                )}
              </div>
            </CardFooter>
          </Card>
        )}

        {(inicializando || loading) ? (
          // Exibe skeleton enquanto carrega
          <CardSkeletonLarge />
        ) : (
          // Exibe o gráfico de ranking de custos
          <Card className="w-full">
            <CardHeader>
              <div className="flex items-center justify-center">
                <CardTitle className="text-lg sm:text-xl select-none">
                  Ranking de Custos
                </CardTitle>
                <MinusCircle className="ml-auto w-4 h-4" />
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

              <ChartBarCustos data={rankingCustos} loading={inicializando || loading} error={undefined} />
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

      <section className="mt-4 flex flex-col lg:flex-row gap-4">
        {(inicializando || loading) ? (
          // Exibe skeleton enquanto carrega
          <CardSkeletonLarge />
        ) : (
          // Exibe o gráfico de despesas
          <Card className="w-full">
            <CardHeader>
              <div className="flex items-center justify-center">
                <CardTitle className="text-lg sm:text-xl select-none">
                  Despesas
                </CardTitle>
                <MinusCircle className="ml-auto w-4 h-4" />
              </div>
            </CardHeader>

            <CardContent>
              <div className="sm:flex sm:justify-between sm:items-center">
                <CardDescription>
                  <div className="flex gap-2 mb-10 leading-none font-medium">
                    Despesas ao longo do tempo
                  </div>
                </CardDescription>
              </div>

              <ChartAreaDespesas data={despesasEvolucao} mesSelecionado={mesSelecionado} />
            </CardContent>
            <CardFooter className="flex-col items-start gap-2 text-sm">
              <CardDescription>
                <p>Despesas últimos 12M</p>
              </CardDescription>
              <div className="text-muted-foreground flex items-center gap-2 leading-none">
                {despesasEvolucao.length > 0 ? (
                  formatarPeriodo(despesasEvolucao)
                ) : (
                  "Todo o período"
                )}
              </div>
            </CardFooter>
          </Card>
        )}

        {(inicializando || loading) ? (
          // Exibe skeleton enquanto carrega
          <CardSkeletonLarge />
        ) : (
          // Exibe o gráfico de ranking de despesas
          <Card className="w-full">
            <CardHeader>
              <div className="flex items-center justify-center">
                <CardTitle className="text-lg sm:text-xl select-none">
                  Ranking de Despesas
                </CardTitle>
                <MinusCircle className="ml-auto w-4 h-4" />
              </div>
            </CardHeader>

            <CardContent>
              <div className="sm:flex sm:justify-between sm:items-center">
                <CardDescription>
                  <div className="flex gap-2 mb-10 leading-none font-medium">
                    Despesas por classificação
                  </div>
                </CardDescription>
              </div>

              <ChartBarDespesas data={rankingDespesas} loading={inicializando || loading} error={undefined} />
            </CardContent>
            <CardFooter className="flex-col items-start gap-2 text-sm">
              <CardDescription>
                <p>Classificação de despesas por valor</p>
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
          Dados atualizados em tempo real via endpoint unificado da DRE
        </p>
      </section>
    </main>
  );
}