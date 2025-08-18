// import React, { useState, useEffect } from 'react';
// import { useFinancialDataContext } from '../../contexts/FinancialDataContext';
// import { transformToDREData } from '../../utils/postgresql-transformers';
// import { formatCurrency } from '../../services/financial-api';

// // Tipos para DRE
// type DreItem = {
//   tipo: string;
//   nome: string;
//   valor?: number;
//   orcamento_total?: number;
  
//   valores_mensais?: Record<string, number>;
//   valores_trimestrais?: Record<string, number>;
//   valores_anuais?: Record<string, number>;
//   vertical_mensais?: Record<string, string>;
//   vertical_trimestrais?: Record<string, string>;
//   vertical_anuais?: Record<string, string>;
//   vertical_total?: string;
//   horizontal_mensais?: Record<string, string>;
//   horizontal_trimestrais?: Record<string, string>;
//   horizontal_anuais?: Record<string, string>;

//   vertical_orcamentos_mensais?: Record<string, string>;
//   vertical_orcamentos_trimestrais?: Record<string, string>;
//   vertical_orcamentos_anuais?: Record<string, string>;
//   vertical_orcamentos_total?: string;
//   horizontal_orcamentos_mensais?: Record<string, string>;
//   horizontal_orcamentos_trimestrais?: Record<string, string>;
//   horizontal_orcamentos_anuais?: Record<string, string>;

//   orcamentos_mensais?: Record<string, number>;
//   orcamentos_trimestrais?: Record<string, number>;
//   orcamentos_anuais?: Record<string, number>;

//   classificacoes?: DreItem[];
// };

// type DreResponse = {
//   meses: string[];
//   trimestres: string[];
//   anos: number[];
//   data: DreItem[];
// };

// export default function DreTablePostgreSQL() {
//   const { financialData, dataLoading, dataError, currentFilters } = useFinancialDataContext();
  
//   const [data, setData] = useState<DreItem[]>([]);
//   const [meses, setMeses] = useState<string[]>([]);
//   const [trimestres, setTrimestres] = useState<string[]>([]);
//   const [anos, setAnos] = useState<number[]>([]);
//   const [loading, setLoading] = useState(true);
//   const [error, setError] = useState<string | null>(null);
//   const [filtroAno, setFiltroAno] = useState<string>("todos");
//   const [openSections, setOpenSections] = useState<Record<string, boolean>>({});
//   const [showHorizontal, setShowHorizontal] = useState(true);
//   const [showOrcado, setShowOrcado] = useState(false);
//   const [showDiferenca, setShowDiferenca] = useState(false);
//   const [allExpanded, setAllExpanded] = useState(false);
//   const [periodo, setPeriodo] = useState<"mes" | "trimestre" | "ano">("mes");

//   useEffect(() => {
//     if (!dataLoading && financialData.length > 0) {
//       try {
//         // Transformar dados PostgreSQL em formato DRE
//         const dreData = transformToDREData(financialData);
        
//         // Converter para formato esperado pelo componente
//         const dreResponse: DreResponse = {
//           meses: dreData.meses_unicos,
//           trimestres: dreData.trimestres_unicos,
//           anos: dreData.anos_unicos,
//           data: dreData.contas_dre.map(([nome, sinal]) => ({
//             tipo: sinal === '+' ? 'receita' : 'despesa',
//             nome,
//             valores_mensais: dreData.total_real_por_mes,
//             valores_trimestrais: dreData.total_real_por_tri,
//             valores_anuais: dreData.total_real_por_ano,
//             orcamentos_mensais: dreData.total_orc_por_mes,
//             orcamentos_trimestrais: dreData.total_orc_por_tri,
//             orcamentos_anuais: dreData.total_orc_por_ano,
//           }))
//         };

//         setData(dreResponse.data);
//         setMeses(dreResponse.meses);
//         setTrimestres(dreResponse.trimestres);
//         setAnos(dreResponse.anos);
        
//         if (dreResponse.anos.length > 0) {
//           const ultimoAno = Math.max(...dreResponse.anos);
//           setFiltroAno(String(ultimoAno));
//         }
        
//         setError(null);
//       } catch (err) {
//         console.error('Erro ao transformar dados DRE:', err);
//         setError(`Erro ao processar dados: ${err instanceof Error ? err.message : 'Erro desconhecido'}`);
//       }
//     } else if (dataError) {
//       setError(dataError);
//     }
    
//     setLoading(false);
//   }, [financialData, dataLoading, dataError]);

//   const toggle = (nome: string) => {
//     setOpenSections(prev => ({ ...prev, [nome]: !prev[nome] }));
//   };

//   const toggleAll = () => {
//     const novoEstado = !allExpanded;
//     const novasSecoes: Record<string, boolean> = {};
//     const marcar = (itens: DreItem[]) => {
//       itens.forEach(item => {
//         if (item.classificacoes?.length) {
//           novasSecoes[item.nome] = novoEstado;
//           marcar(item.classificacoes);
//         }
//       });
//     };
//     marcar(data);
//     setOpenSections(novasSecoes);
//     setAllExpanded(novoEstado);
//   };

//   // Determinar períodos baseado no tipo selecionado
//   let periodosFiltrados: string[] = [];
  
//   if (periodo === "mes") {
//     periodosFiltrados = meses.filter(m => filtroAno === "todos" ? true : m.startsWith(filtroAno)).sort();
//     console.log("🔍 DEBUG periodosFiltrados (mes):", periodosFiltrados);
//   } else if (periodo === "trimestre") {
//     periodosFiltrados = trimestres.filter(t => {
//       const ano = t.split('-')[0];
//       return filtroAno === "todos" ? true : ano === filtroAno;
//     }).sort();
//     console.log("🔍 DEBUG periodosFiltrados (trimestre):", periodosFiltrados);
//   } else if (periodo === "ano") {
//     periodosFiltrados = filtroAno === "todos" ? anos.map(String).sort() : [filtroAno];
//     console.log("🔍 DEBUG periodosFiltrados (ano):", periodosFiltrados);
//   }

//   const calcularValor = (item: DreItem, periodoLabel: string): number => {
//     if (periodo === "mes") return item.valores_mensais?.[periodoLabel] ?? 0;
//     if (periodo === "trimestre") return item.valores_trimestrais?.[periodoLabel] ?? 0;
//     if (periodo === "ano") return item.valores_anuais?.[periodoLabel] ?? item.valores_anuais?.[`${periodoLabel}.0`] ?? 0;
//     return 0;
//   };

//   const calcularOrcamento = (item: DreItem, periodoLabel: string): number => {
//     if (periodo === "mes") return item.orcamentos_mensais?.[periodoLabel] ?? 0;
//     if (periodo === "trimestre") return item.orcamentos_trimestrais?.[periodoLabel] ?? 0;
//     if (periodo === "ano") return item.orcamentos_anuais?.[periodoLabel] ?? item.orcamentos_anuais?.[`${periodoLabel}.0`] ?? 0;
//     return 0;
//   };

//   const calcularTotal = (valores: Record<string, number> | undefined): number => {
//     console.log("🔍 DEBUG calcularTotal:");
//     console.log("  - Valores recebidos:", valores);
//     console.log("  - Periodos filtrados:", periodosFiltrados);
    
//     const resultado = periodosFiltrados.reduce((total, p) => {
//       const valor = valores?.[p] ?? valores?.[`${p}.0`] ?? 0;
//       console.log(`  - Período ${p}: valor = ${valor}`);
//       return total + valor;
//     }, 0);
    
//     console.log("  - Total calculado:", resultado);
//     return resultado;
//   };

//   const calcularTotalOrcamento = (orcamentos: Record<string, number> | undefined): number => {
//     return periodosFiltrados.reduce((total, p) => total + (orcamentos?.[p] ?? orcamentos?.[`${p}.0`] ?? 0), 0);
//   };

//   const calcularDiffPct = (real: number, orcado: number): string | undefined => {
//     if (orcado === 0) return undefined;
//     const diff = ((real - orcado) / orcado) * 100;
//     return `${diff.toFixed(1)}%`;
//   };

//   // Função para calcular análise vertical dinâmica do total
//   const calcularVerticalTotalDinamica = (): number => {
//     // CORREÇÃO: Usar apenas o Faturamento como base, não a soma de todas as contas
//     const faturamentoItem = data.find(item => item.nome === "( + ) Faturamento");
    
//     console.log("🔍 DEBUG calcularVerticalTotalDinamica:");
//     console.log("  - Total de itens:", data.length);
//     console.log("  - Faturamento encontrado:", faturamentoItem);
//     console.log("  - Filtro ano atual:", filtroAno);
    
//     if (!faturamentoItem) {
//       console.log("❌ Faturamento não encontrado!");
//       return 0;
//     }
    
//     // CORREÇÃO: Calcular base apenas para o ano selecionado, não para todos os períodos
//     let baseFaturamento = 0;
    
//     if (periodo === "mes") {
//       // Filtrar apenas meses do ano selecionado
//       const mesesAno = meses.filter(m => filtroAno === "todos" ? true : m.startsWith(filtroAno));
//       baseFaturamento = mesesAno.reduce((total, mes) => total + (faturamentoItem.valores_mensais?.[mes] ?? 0), 0);
//       console.log("  - Meses do ano:", mesesAno);
//     } else if (periodo === "trimestre") {
//       // Filtrar apenas trimestres do ano selecionado
//       const trimestresAno = trimestres.filter(t => {
//         const ano = t.split('-')[0];
//         return filtroAno === "todos" ? true : ano === filtroAno;
//       });
//       baseFaturamento = trimestresAno.reduce((total, tri) => total + (faturamentoItem.valores_trimestrais?.[tri] ?? 0), 0);
//       console.log("  - Trimestres do ano:", trimestresAno);
//     } else if (periodo === "ano") {
//       // Usar apenas o ano selecionado
//       if (filtroAno === "todos") {
//         baseFaturamento = Object.values(faturamentoItem.valores_anuais || {}).reduce((total, valor) => total + valor, 0);
//       } else {
//         baseFaturamento = faturamentoItem.valores_anuais?.[filtroAno] ?? 0;
//       }
//       console.log("  - Ano selecionado:", filtroAno);
//     }
    
//     console.log("  - Período atual:", periodo);
//     console.log("  - Valores do faturamento:", {
//       mensais: faturamentoItem.valores_mensais,
//       trimestrais: faturamentoItem.valores_trimestrais,
//       anuais: faturamentoItem.valores_anuais
//     });
//     console.log("  - Base calculada:", baseFaturamento);
//     console.log("  - Base final (abs):", Math.abs(baseFaturamento));
    
//     return Math.abs(baseFaturamento);
//   };

//   // Função para calcular AV% dinâmica do total
//   const calcularAVTotalDinamica = (valorTotal: number): string | undefined => {
//     const totalGeral = calcularVerticalTotalDinamica();
    
//     console.log("🔍 DEBUG calcularAVTotalDinamica:");
//     console.log("  - Valor total recebido:", valorTotal);
//     console.log("  - Total geral (base):", totalGeral);
    
//     if (totalGeral === 0) {
//       console.log("❌ Base é zero, retornando undefined");
//       return undefined;
//     }
    
//     const percentual = (Math.abs(valorTotal) / totalGeral) * 100;
//     const resultado = `${percentual.toFixed(1)}%`;
    
//     console.log("  - Cálculo:", `|${valorTotal}| / ${totalGeral} * 100 = ${percentual.toFixed(2)}%`);
//     console.log("  - Resultado final:", resultado);
    
//     return resultado;
//   };

//   const renderValorDiferenca = (real: number, orcado: number) => {
//     const diff = real - orcado;
//     const diffPct = calcularDiffPct(real, orcado);
//     const isPositive = diff >= 0;
    
//     return (
//       <div className="text-right">
//         <div className={`font-medium ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
//           {formatCurrency(diff)}
//         </div>
//         {diffPct && (
//           <div className={`text-xs ${isPositive ? 'text-green-500' : 'text-red-500'}`}>
//             {diffPct}
//           </div>
//         )}
//       </div>
//     );
//   };

//   const renderValor = (
//     valor: number,
//     verticalPct?: string,
//     horizontalPct?: string
//   ) => (
//     <div className="text-right">
//       <div className="font-medium">{formatCurrency(valor)}</div>
//       {verticalPct && <div className="text-xs text-gray-500">AV: {verticalPct}</div>}
//       {horizontalPct && <div className="text-xs text-gray-500">AH: {horizontalPct}</div>}
//     </div>
//   );

//   const renderValorOrcamento = (
//     valor: number,
//     verticalPct?: string,
//     horizontalPct?: string
//   ) => (
//     <div className="text-right">
//       <div className="font-medium text-blue-600">{formatCurrency(valor)}</div>
//       {verticalPct && <div className="text-xs text-blue-500">AV: {verticalPct}</div>}
//       {horizontalPct && <div className="text-xs text-blue-500">AH: {horizontalPct}</div>}
//     </div>
//   );

//   if (loading) {
//     return (
//       <div className="flex items-center justify-center p-8">
//         <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
//         <span className="ml-2">Carregando dados DRE...</span>
//       </div>
//     );
//   }

//   if (error) {
//     return (
//       <div className="bg-red-50 border border-red-200 rounded-md p-4">
//         <div className="flex">
//           <div className="flex-shrink-0">
//             <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
//               <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
//             </svg>
//           </div>
//           <div className="ml-3">
//             <h3 className="text-sm font-medium text-red-800">Erro ao carregar dados DRE</h3>
//             <div className="mt-2 text-sm text-red-700">{error}</div>
//           </div>
//         </div>
//       </div>
//     );
//   }

//   return (
//     <div className="space-y-6">
//       {/* Controles */}
//       <div className="bg-white p-4 rounded-lg shadow">
//         <div className="flex flex-wrap items-center gap-4">
//           <div>
//             <label className="block text-sm font-medium text-gray-700">Ano</label>
//             <select
//               value={filtroAno}
//               onChange={(e) => setFiltroAno(e.target.value)}
//               className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
//             >
//               <option value="todos">Todos</option>
//               {anos.map(ano => (
//                 <option key={ano} value={String(ano)}>{ano}</option>
//               ))}
//             </select>
//           </div>
          
//           <div>
//             <label className="block text-sm font-medium text-gray-700">Período</label>
//             <select
//               value={periodo}
//               onChange={(e) => setPeriodo(e.target.value as "mes" | "trimestre" | "ano")}
//               className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
//             >
//               <option value="mes">Mensal</option>
//               <option value="trimestre">Trimestral</option>
//               <option value="ano">Anual</option>
//             </select>
//           </div>

//           <div className="flex items-center space-x-4">
//             <label className="flex items-center">
//               <input
//                 type="checkbox"
//                 checked={showHorizontal}
//                 onChange={(e) => setShowHorizontal(e.target.checked)}
//                 className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
//               />
//               <span className="ml-2 text-sm text-gray-700">Análise Horizontal</span>
//             </label>
            
//             <label className="flex items-center">
//               <input
//                 type="checkbox"
//                 checked={showOrcado}
//                 onChange={(e) => setShowOrcado(e.target.checked)}
//                 className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
//               />
//               <span className="ml-2 text-sm text-gray-700">Orçado</span>
//             </label>
            
//             <label className="flex items-center">
//               <input
//                 type="checkbox"
//                 checked={showDiferenca}
//                 onChange={(e) => setShowDiferenca(e.target.checked)}
//                 className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
//               />
//               <span className="ml-2 text-sm text-gray-700">Diferença</span>
//             </label>
//           </div>

//           <button
//             onClick={toggleAll}
//             className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
//           >
//             {allExpanded ? 'Recolher Tudo' : 'Expandir Tudo'}
//           </button>
//         </div>
//       </div>

//       {/* Tabela */}
//       <div className="bg-white shadow rounded-lg overflow-hidden">
//         <div className="overflow-x-auto">
//           <table className="min-w-full divide-y divide-gray-200">
//             <thead className="bg-gray-50">
//               <tr>
//                 <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
//                   Conta
//                 </th>
//                 {periodosFiltrados.map(periodo => (
//                   <th key={periodo} className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
//                     {periodo}
//                   </th>
//                 ))}
//                 <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
//                   Total
//                 </th>
//                 {showOrcado && (
//                   <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
//                     Orçado
//                   </th>
//                 )}
//                 {showDiferenca && (
//                   <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
//                     Diferença
//                   </th>
//                 )}
//               </tr>
//             </thead>
//             <tbody className="bg-white divide-y divide-gray-200">
//               {data.map((item) => {
//                 const totalReal = calcularTotal(
//                   periodo === "mes" ? item.valores_mensais :
//                   periodo === "trimestre" ? item.valores_trimestrais :
//                   item.valores_anuais
//                 );
//                 const totalOrcado = calcularTotalOrcamento(
//                   periodo === "mes" ? item.orcamentos_mensais :
//                   periodo === "trimestre" ? item.orcamentos_trimestrais :
//                   item.orcamentos_anuais
//                 );

//                 return (
//                   <tr key={item.nome} className="hover:bg-gray-50">
//                     <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
//                       {item.nome}
//                     </td>
//                     {periodosFiltrados.map(periodo => (
//                       <td key={periodo} className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
//                         {renderValor(calcularValor(item, periodo))}
//                       </td>
//                     ))}
//                     <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
//                       {renderValor(totalReal, calcularAVTotalDinamica(totalReal))}
//                     </td>
//                     {showOrcado && (
//                       <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
//                         {renderValorOrcamento(totalOrcado)}
//                       </td>
//                     )}
//                     {showDiferenca && (
//                       <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
//                         {renderValorDiferenca(totalReal, totalOrcado)}
//                       </td>
//                     )}
//                   </tr>
//                 );
//               })}
//             </tbody>
//           </table>
//         </div>
//       </div>
//     </div>
//   );
// }
