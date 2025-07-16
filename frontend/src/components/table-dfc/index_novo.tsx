// "use client"

// import React, { useState, useEffect } from "react"
// import { ChevronDown } from "lucide-react"
// import ExcelJS from 'exceljs';
// import { saveAs } from 'file-saver';
// import { Button } from "@/components/ui/button"
// import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
// import { Skeleton } from "@/components/ui/skeleton"
// import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
// import { FiltroMes } from "@/components/filtro-mes"

// export interface DFCItem {
//   nome: string
//   tipo: string
//   valor: number
//   orcamento_total: number
  
//   valores_mensais: Record<string, number>
//   valores_trimestrais: Record<string, number>
//   valores_anuais: Record<string, number>
  
//   orcamentos_mensais: Record<string, number>
//   orcamentos_trimestrais: Record<string, number>
//   orcamentos_anuais: Record<string, number>
  
//   vertical_mensais?: Record<string, number>
//   vertical_trimestrais?: Record<string, number>
//   vertical_anuais?: Record<string, number>
//   vertical_total?: number
  
//   horizontal_mensais?: Record<string, number>
//   horizontal_trimestrais?: Record<string, number>
//   horizontal_anuais?: Record<string, number>
  
//   vertical_orcamentos_mensais?: Record<string, number>
//   vertical_orcamentos_trimestrais?: Record<string, number>
//   vertical_orcamentos_anuais?: Record<string, number>
//   vertical_orcamentos_total?: number
  
//   horizontal_orcamentos_mensais?: Record<string, number>
//   horizontal_orcamentos_trimestrais?: Record<string, number>
//   horizontal_orcamentos_anuais?: Record<string, number>
  
//   classificacoes?: DFCItem[]
// }

// interface DFCTableProps {
//   filtroMes: number
//   filtroAno: number
// }

// export default function DFCTable({ filtroMes, filtroAno }: DFCTableProps) {
//   const [data, setData] = useState<DFCItem[]>([])
//   const [loading, setLoading] = useState(true)
//   const [error, setError] = useState<string | null>(null)
//   const [openSections, setOpenSections] = useState<Record<string, boolean>>({})
//   const [periodo, setPeriodo] = useState<"mes" | "trimestre" | "ano">("mes")
//   const [showOrcado, setShowOrcado] = useState(false)
//   const [showDiferenca, setShowDiferenca] = useState(false)

//   const toggle = (section: string) => {
//     setOpenSections(prev => ({ ...prev, [section]: !prev[section] }))
//   }

//   useEffect(() => {
//     const fetchData = async () => {
//       if (!filtroAno) return
      
//       setLoading(true)
//       setError(null)
      
//       try {
//         const mes = filtroMes || new Date().getMonth() + 1
//         const response = await fetch(
//           `https://mvp-plataforma-tag-3s9u.onrender.com/dfc?filtro_mes=${mes}&filtro_ano=${filtroAno}`
//         )
        
//         if (!response.ok) {
//           throw new Error(`Erro ${response.status}: ${response.statusText}`)
//         }
        
//         const result = await response.json()
//         setData(result)
//       } catch (err) {
//         console.error("Erro ao buscar dados:", err)
//         setError(err instanceof Error ? err.message : "Erro desconhecido")
//       } finally {
//         setLoading(false)
//       }
//     }

//     fetchData()
//   }, [filtroMes, filtroAno])

//   const calcularValor = (item: DFCItem, periodo: string): number => {
//     const valores = item.valores_mensais || {}
//     return valores[periodo] || 0
//   }

//   const calcularOrcamento = (item: DFCItem, periodo: string): number => {
//     const orcamentos = item.orcamentos_mensais || {}
//     return orcamentos[periodo] || 0
//   }

//   const calcularTotal = (valores: Record<string, number> | undefined): number => {
//     if (!valores) return 0
//     return Object.values(valores).reduce((acc, val) => acc + (val || 0), 0)
//   }

//   const calcularTotalOrcamento = (orcamentos: Record<string, number> | undefined): number => {
//     if (!orcamentos) return 0
//     return Object.values(orcamentos).reduce((acc, val) => acc + (val || 0), 0)
//   }

//   const renderValor = (valor: number, vertical?: number, horizontal?: number): React.ReactNode => {
//     const formatCurrency = (value: number) => 
//       new Intl.NumberFormat("pt-BR", {
//         style: "currency",
//         currency: "BRL",
//         minimumFractionDigits: 0,
//         maximumFractionDigits: 0,
//       }).format(value)

//     const formatPercentage = (value: number) => 
//       `${value >= 0 ? '+' : ''}${value.toFixed(1)}%`

//     return (
//       <div className="text-right">
//         <div className="font-medium">{formatCurrency(valor)}</div>
//         {vertical !== undefined && (
//           <div className="text-xs text-muted-foreground">AV: {formatPercentage(vertical)}</div>
//         )}
//         {horizontal !== undefined && (
//           <div className="text-xs text-muted-foreground">AH: {formatPercentage(horizontal)}</div>
//         )}
//       </div>
//     )
//   }

//   const renderValorOrcamento = (valor: number, vertical?: number, horizontal?: number): React.ReactNode => {
//     const formatCurrency = (value: number) => 
//       new Intl.NumberFormat("pt-BR", {
//         style: "currency",
//         currency: "BRL",
//         minimumFractionDigits: 0,
//         maximumFractionDigits: 0,
//       }).format(value)

//     const formatPercentage = (value: number) => 
//       `${value >= 0 ? '+' : ''}${value.toFixed(1)}%`

//     return (
//       <div className="text-right">
//         <div className="font-medium text-blue-600">{formatCurrency(valor)}</div>
//         {vertical !== undefined && (
//           <div className="text-xs text-blue-500">AV: {formatPercentage(vertical)}</div>
//         )}
//         {horizontal !== undefined && (
//           <div className="text-xs text-blue-500">AH: {formatPercentage(horizontal)}</div>
//         )}
//       </div>
//     )
//   }

//   const renderValorDiferenca = (real: number, orcado: number): React.ReactNode => {
//     const diferenca = real - orcado
//     const formatCurrency = (value: number) => 
//       new Intl.NumberFormat("pt-BR", {
//         style: "currency",
//         currency: "BRL",
//         minimumFractionDigits: 0,
//         maximumFractionDigits: 0,
//       }).format(value)

//     return (
//       <div className="text-right">
//         <div className={`font-medium ${diferenca >= 0 ? 'text-green-600' : 'text-red-600'}`}>
//           {formatCurrency(diferenca)}
//         </div>
//       </div>
//     )
//   }

//   const periodosFiltrados = (() => {
//     if (periodo === "mes") {
//       return Array.from({ length: filtroMes }, (_, i) => {
//         const mes = String(i + 1).padStart(2, '0')
//         return `${filtroAno}-${mes}`
//       })
//     } else if (periodo === "trimestre") {
//       const trimestre = Math.ceil(filtroMes / 3)
//       return Array.from({ length: trimestre }, (_, i) => `${filtroAno}-T${i + 1}`)
//     } else {
//       return [`${filtroAno}`]
//     }
//   })()

//   const exportToExcel = async () => {
//     const wb = new ExcelJS.Workbook()
//     const ws = wb.addWorksheet('DFC')

//     // Cabeçalho
//     const headerRow = ["Conta"]
//     periodosFiltrados.forEach(p => {
//       headerRow.push(`Real ${p}`)
//       if (showOrcado) headerRow.push(`Orçado ${p}`)
//       if (showDiferenca) headerRow.push(`Diferença ${p}`)
//     })
//     headerRow.push("Total Real")
//     if (showOrcado) headerRow.push("Total Orçado")
//     if (showDiferenca) headerRow.push("Diferença Total")

//     ws.addRow(headerRow)

//     // Dados
//     data.forEach((item) => {
//       if (item.nome === "Movimentações" && item.classificacoes) {
//         // Linha principal das movimentações
//         const rowMovimentacoes: (string | number)[] = [item.nome]
//         periodosFiltrados.forEach(p => {
//           const real = calcularValor(item, p)
//           const orcado = calcularOrcamento(item, p)
//           rowMovimentacoes.push(real)
//           if (showOrcado) rowMovimentacoes.push(orcado)
//           if (showDiferenca) rowMovimentacoes.push(real - orcado)
//         })
//         rowMovimentacoes.push(item.valor)
//         if (showOrcado) rowMovimentacoes.push(item.orcamento_total)
//         if (showDiferenca) rowMovimentacoes.push(item.valor - item.orcamento_total)

//         ws.addRow(rowMovimentacoes)

//         // Totalizadores
//         item.classificacoes.forEach(totalizador => {
//           const totalTotalizador = calcularTotal(
//             periodo === "mes" ? totalizador.valores_mensais :
//             periodo === "trimestre" ? totalizador.valores_trimestrais :
//             totalizador.valores_anuais
//           )
//           const totalTotalizadorOrc = calcularTotalOrcamento(
//             periodo === "mes" ? totalizador.orcamentos_mensais :
//             periodo === "trimestre" ? totalizador.orcamentos_trimestrais :
//             totalizador.orcamentos_anuais
//           )

//           const rowTotalizador: (string | number)[] = ["  " + totalizador.nome]
//           periodosFiltrados.forEach(p => {
//             const real = calcularValor(totalizador, p)
//             const orcado = calcularOrcamento(totalizador, p)
//             rowTotalizador.push(real)
//             if (showOrcado) rowTotalizador.push(orcado)
//             if (showDiferenca) rowTotalizador.push(real - orcado)
//           })
//           rowTotalizador.push(totalTotalizador)
//           if (showOrcado) rowTotalizador.push(totalTotalizadorOrc)
//           if (showDiferenca) rowTotalizador.push(totalTotalizador - totalTotalizadorOrc)

//           ws.addRow(rowTotalizador)

//           // Contas
//           totalizador.classificacoes?.forEach(conta => {
//             const totalConta = calcularTotal(
//               periodo === "mes" ? conta.valores_mensais :
//               periodo === "trimestre" ? conta.valores_trimestrais :
//               conta.valores_anuais
//             )
//             const totalContaOrc = calcularTotalOrcamento(
//               periodo === "mes" ? conta.orcamentos_mensais :
//               periodo === "trimestre" ? conta.orcamentos_trimestrais :
//               conta.orcamentos_anuais
//             )

//             const rowConta: (string | number)[] = ["    " + conta.nome]
//             periodosFiltrados.forEach(p => {
//               const real = calcularValor(conta, p)
//               const orcado = calcularOrcamento(conta, p)
//               rowConta.push(real)
//               if (showOrcado) rowConta.push(orcado)
//               if (showDiferenca) rowConta.push(real - orcado)
//             })
//             rowConta.push(totalConta)
//             if (showOrcado) rowConta.push(totalContaOrc)
//             if (showDiferenca) rowConta.push(totalConta - totalContaOrc)

//             ws.addRow(rowConta)

//             // Classificações
//             conta.classificacoes?.forEach(classificacao => {
//               const totalClassificacao = calcularTotal(
//                 periodo === "mes" ? classificacao.valores_mensais :
//                 periodo === "trimestre" ? classificacao.valores_trimestrais :
//                 classificacao.valores_anuais
//               )
//               const totalClassificacaoOrc = calcularTotalOrcamento(
//                 periodo === "mes" ? classificacao.orcamentos_mensais :
//                 periodo === "trimestre" ? classificacao.orcamentos_trimestrais :
//                 classificacao.orcamentos_anuais
//               )

//               const rowClassificacao: (string | number)[] = ["      " + classificacao.nome]
//               periodosFiltrados.forEach(p => {
//                 const real = calcularValor(classificacao, p)
//                 const orcado = calcularOrcamento(classificacao, p)
//                 rowClassificacao.push(real)
//                 if (showOrcado) rowClassificacao.push(orcado)
//                 if (showDiferenca) rowClassificacao.push(real - orcado)
//               })
//               rowClassificacao.push(totalClassificacao)
//               if (showOrcado) rowClassificacao.push(totalClassificacaoOrc)
//               if (showDiferenca) rowClassificacao.push(totalClassificacao - totalClassificacaoOrc)

//               ws.addRow(rowClassificacao)
//             })
//           })
//         })
//       } else {
//         // Saldo inicial e final
//         const row: (string | number)[] = [item.nome]
//         periodosFiltrados.forEach(p => {
//           const real = calcularValor(item, p)
//           const orcado = calcularOrcamento(item, p)
//           row.push(real)
//           if (showOrcado) row.push(orcado)
//           if (showDiferenca) row.push(real - orcado)
//         })
//         row.push(item.valor)
//         if (showOrcado) row.push(item.orcamento_total)
//         if (showDiferenca) row.push(item.valor - item.orcamento_total)

//         ws.addRow(row)
//       }
//     })

//     wb.xlsx.writeBuffer().then(buffer => {
//       const blob = new Blob([buffer], { type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" })
//       saveAs(blob, "dfc.xlsx")
//     })
//   }

//   if (loading || !filtroAno) return (
//     <Card className="m-4">
//       <CardHeader>
//         <CardTitle>
//           <Skeleton className="h-6 w-40 mb-2" />
//         </CardTitle>
//       </CardHeader>
//       <CardContent>
//         <Skeleton className="h-8 w-full mb-2" />
//         <Skeleton className="h-8 w-3/4 mb-2" />
//         <Skeleton className="h-8 w-1/2" />
//       </CardContent>
//     </Card>
//   )

//   if (error) return (
//     <Card className="m-4">
//       <CardHeader>
//         <CardTitle>{error}</CardTitle>
//       </CardHeader>
//     </Card>
//   )

//   return (
//     <Card className="max-w-fit m-4">
//       <CardHeader>
//         <div className="flex flex-col lg:flex-row lg:flex-wrap lg:justify-between gap-2 lg:gap-4 overflow-x-auto">
//           <div>
//             <CardTitle>DFC - Roriz Instrumentos</CardTitle>
//             <CardDescription>
//               Demonstração do Fluxo de Caixa - {filtroMes}/{filtroAno}
//             </CardDescription>
//           </div>
          
//           <div className="flex flex-col lg:flex-row gap-2">
//             <FiltroMes 
//               periodo={periodo} 
//               onPeriodoChange={setPeriodo} 
//               showOrcado={showOrcado}
//               onShowOrcadoChange={setShowOrcado}
//               showDiferenca={showDiferenca}
//               onShowDiferencaChange={setShowDiferenca}
//             />
//             <Button onClick={exportToExcel} variant="outline" size="sm">
//               Exportar Excel
//             </Button>
//           </div>
//         </div>
//       </CardHeader>

//       <CardContent>
//         <div className="rounded-md border overflow-x-auto max-w-[95vw]">
//           <Table>
//             <TableHeader>
//               <TableRow>
//                 <TableHead className="min-w-[200px] sticky left-0 z-20 bg-background">
//                   Conta
//                 </TableHead>
//                 {periodosFiltrados.map((p) => (
//                   <React.Fragment key={p}>
//                     <TableHead className="text-center min-w-[120px]">
//                       Real {periodo === "mes" ? p.slice(-2) : periodo === "trimestre" ? p.slice(-2) : p}
//                     </TableHead>
//                     {showOrcado && (
//                       <TableHead className="text-center min-w-[120px] text-blue-600">
//                         Orçado {periodo === "mes" ? p.slice(-2) : periodo === "trimestre" ? p.slice(-2) : p}
//                       </TableHead>
//                     )}
//                     {showDiferenca && (
//                       <TableHead className="text-center min-w-[120px] text-green-600">
//                         Diferença {periodo === "mes" ? p.slice(-2) : periodo === "trimestre" ? p.slice(-2) : p}
//                       </TableHead>
//                     )}
//                   </React.Fragment>
//                 ))}
//                 <TableHead className="text-center min-w-[120px]">Total Real</TableHead>
//                 {showOrcado && (
//                   <TableHead className="text-center min-w-[120px] text-blue-600">Total Orçado</TableHead>
//                 )}
//                 {showDiferenca && (
//                   <TableHead className="text-center min-w-[120px] text-green-600">Diferença Total</TableHead>
//                 )}
//               </TableRow>
//             </TableHeader>

//             <TableBody>
//               {data.map((item) => {
//                 // Se for "Movimentações", renderizar seus totalizadores filhos
//                 if (item.nome === "Movimentações" && item.classificacoes) {
//                   return (
//                     <React.Fragment key={item.nome}>
//                       {/* LINHA PRINCIPAL DAS MOVIMENTAÇÕES */}
//                       <TableRow className="bg-primary/10 font-bold border-t-4 border-primary">
//                         <TableCell className="py-4 md:sticky md:left-0 md:z-20 bg-primary/10 font-bold">
//                           <div className="flex items-center gap-2">
//                             <span className="text-base font-bold text-primary">{item.nome}</span>
//                           </div>
//                         </TableCell>
                        
//                         {periodosFiltrados.map((p) => {
//                           const real = calcularValor(item, p);
//                           const orcado = calcularOrcamento(item, p);
//                           return (
//                             <React.Fragment key={p}>
//                               <TableCell className="font-bold">
//                                 {renderValor(real)}
//                               </TableCell>
//                               {showOrcado && (
//                                 <TableCell className="font-bold">
//                                   {renderValorOrcamento(orcado)}
//                                 </TableCell>
//                               )}
//                               {showDiferenca && (
//                                 <TableCell className="font-bold">
//                                   {renderValorDiferenca(real, orcado)}
//                                 </TableCell>
//                               )}
//                             </React.Fragment>
//                           );
//                         })}

//                         <TableCell className="py-4 text-right font-bold">
//                           {renderValor(item.valor)}
//                         </TableCell>
//                         {showOrcado && (
//                           <TableCell className="py-4 text-right font-bold">
//                             {renderValorOrcamento(item.orcamento_total)}
//                           </TableCell>
//                         )}
//                         {showDiferenca && (
//                           <TableCell className="py-4 text-right font-bold">
//                             {renderValorDiferenca(item.valor, item.orcamento_total)}
//                           </TableCell>
//                         )}
//                       </TableRow>

//                       {/* TOTALIZADORES (NÍVEL 1) */}
//                       {item.classificacoes.map((totalizador) => {
//                         const isOpen = openSections[totalizador.nome] ?? false;

//                         const totalTotalizador = calcularTotal(
//                           periodo === "mes"
//                             ? totalizador.valores_mensais
//                             : periodo === "trimestre"
//                             ? totalizador.valores_trimestrais
//                             : totalizador.valores_anuais
//                         );
//                         const totalTotalizadorOrc = calcularTotalOrcamento(
//                           periodo === "mes"
//                             ? totalizador.orcamentos_mensais
//                             : periodo === "trimestre"
//                             ? totalizador.orcamentos_trimestrais
//                             : totalizador.orcamentos_anuais
//                         );

//                         return (
//                           <React.Fragment key={totalizador.nome}>
//                             {/* LINHA DO TOTALIZADOR */}
//                             <TableRow
//                               className="cursor-pointer hover:bg-muted/50 bg-muted/80 font-bold border-t-2"
//                               onClick={() => toggle(totalizador.nome)}
//                             >
//                               <TableCell className="py-4 md:sticky md:left-0 md:z-20 bg-muted font-bold pl-4">
//                                 <div className="flex items-center gap-2">
//                                   <ChevronDown
//                                     size={18}
//                                     className={`transition-transform ${
//                                       isOpen ? "rotate-0" : "-rotate-90"
//                                     }`}
//                                   />
//                                   <span className="text-sm font-bold">{totalizador.tipo}</span>
//                                   <span className="text-base font-bold">{totalizador.nome}</span>
//                                 </div>
//                               </TableCell>

//                               {periodosFiltrados.map((p) => {
//                                 const real = calcularValor(totalizador, p);
//                                 const orcado = calcularOrcamento(totalizador, p);
//                                 return (
//                                   <React.Fragment key={p}>
//                                     <TableCell className="font-bold">
//                                       {renderValor(
//                                         real,
//                                         periodo === "mes"
//                                           ? totalizador.vertical_mensais?.[p]
//                                           : periodo === "trimestre"
//                                           ? totalizador.vertical_trimestrais?.[p]
//                                           : totalizador.vertical_anuais?.[p],
//                                         periodo === "mes"
//                                           ? totalizador.horizontal_mensais?.[p]
//                                           : periodo === "trimestre"
//                                           ? totalizador.horizontal_trimestrais?.[p]
//                                           : totalizador.horizontal_anuais?.[p]
//                                       )}
//                                     </TableCell>
//                                     {showOrcado && (
//                                       <TableCell className="font-bold">
//                                         {renderValorOrcamento(
//                                           orcado,
//                                           periodo === "mes"
//                                             ? totalizador.vertical_orcamentos_mensais?.[p]
//                                             : periodo === "trimestre"
//                                             ? totalizador.vertical_orcamentos_trimestrais?.[p]
//                                             : totalizador.vertical_orcamentos_anuais?.[p],
//                                           periodo === "mes"
//                                             ? totalizador.horizontal_orcamentos_mensais?.[p]
//                                             : periodo === "trimestre"
//                                             ? totalizador.horizontal_orcamentos_trimestrais?.[p]
//                                             : totalizador.horizontal_orcamentos_anuais?.[p]
//                                         )}
//                                       </TableCell>
//                                     )}
//                                     {showDiferenca && (
//                                       <TableCell className="font-bold">
//                                         {renderValorDiferenca(real, orcado)}
//                                       </TableCell>
//                                     )}
//                                   </React.Fragment>
//                                 );
//                               })}

//                               <TableCell className="py-4 text-right font-bold">
//                                 {renderValor(totalTotalizador, totalizador.vertical_total)}
//                               </TableCell>
//                               {showOrcado && (
//                                 <TableCell className="py-4 text-right font-bold">
//                                   {renderValorOrcamento(
//                                     totalTotalizadorOrc,
//                                     totalizador.vertical_orcamentos_total,
//                                     undefined
//                                   )}
//                                 </TableCell>
//                               )}
//                               {showDiferenca && (
//                                 <TableCell className="py-4 text-right font-bold">
//                                   {renderValorDiferenca(totalTotalizador, totalTotalizadorOrc)}
//                                 </TableCell>
//                               )}
//                             </TableRow>

//                             {/* CONTAS FILHAS DO TOTALIZADOR (NÍVEL 2) */}
//                             {isOpen &&
//                               totalizador.classificacoes?.map((conta) => {
//                                 const isContaExpandable = !!conta.classificacoes?.length;
//                                 const isContaOpen = openSections[`${totalizador.nome}-${conta.nome}`] ?? false;

//                                 const totalConta = calcularTotal(
//                                   periodo === "mes"
//                                     ? conta.valores_mensais
//                                     : periodo === "trimestre"
//                                     ? conta.valores_trimestrais
//                                     : conta.valores_anuais
//                                 );
//                                 const totalContaOrc = calcularTotalOrcamento(
//                                   periodo === "mes"
//                                     ? conta.orcamentos_mensais
//                                     : periodo === "trimestre"
//                                     ? conta.orcamentos_trimestrais
//                                     : conta.orcamentos_anuais
//                                 );

//                                 return (
//                                   <React.Fragment key={`${totalizador.nome}-${conta.nome}`}>
//                                     {/* LINHA DA CONTA */}
//                                     <TableRow
//                                       className={`${
//                                         isContaExpandable ? "cursor-pointer hover:bg-muted/30" : ""
//                                       } bg-muted/20`}
//                                       onClick={() => isContaExpandable && toggle(`${totalizador.nome}-${conta.nome}`)}
//                                     >
//                                       <TableCell className="sticky left-0 z-10 bg-muted/20 pl-8">
//                                         <div className="flex items-center gap-2">
//                                           {isContaExpandable && (
//                                             <ChevronDown
//                                               size={14}
//                                               className={`transition-transform ${
//                                                 isContaOpen ? "rotate-0" : "-rotate-90"
//                                               }`}
//                                             />
//                                           )}
//                                           <span className="text-sm">{conta.tipo}</span>
//                                           <span className="font-medium">{conta.nome}</span>
//                                         </div>
//                                       </TableCell>

//                                       {periodosFiltrados.map((p) => {
//                                         const real = calcularValor(conta, p);
//                                         const orcado = calcularOrcamento(conta, p);
//                                         return (
//                                           <React.Fragment key={p}>
//                                             <TableCell>
//                                               {renderValor(
//                                                 real,
//                                                 periodo === "mes"
//                                                   ? conta.vertical_mensais?.[p]
//                                                   : periodo === "trimestre"
//                                                   ? conta.vertical_trimestrais?.[p]
//                                                   : conta.vertical_anuais?.[p],
//                                                 periodo === "mes"
//                                                   ? conta.horizontal_mensais?.[p]
//                                                   : periodo === "trimestre"
//                                                   ? conta.horizontal_trimestrais?.[p]
//                                                   : conta.horizontal_anuais?.[p]
//                                               )}
//                                             </TableCell>
//                                             {showOrcado && (
//                                               <TableCell>
//                                                 {renderValorOrcamento(
//                                                   orcado,
//                                                   periodo === "mes"
//                                                     ? conta.vertical_orcamentos_mensais?.[p]
//                                                     : periodo === "trimestre"
//                                                     ? conta.vertical_orcamentos_trimestrais?.[p]
//                                                     : conta.vertical_orcamentos_anuais?.[p],
//                                                   periodo === "mes"
//                                                     ? conta.horizontal_orcamentos_mensais?.[p]
//                                                     : periodo === "trimestre"
//                                                     ? conta.horizontal_orcamentos_trimestrais?.[p]
//                                                     : conta.horizontal_orcamentos_anuais?.[p]
//                                                 )}
//                                               </TableCell>
//                                             )}
//                                             {showDiferenca && (
//                                               <TableCell>
//                                                 {renderValorDiferenca(real, orcado)}
//                                               </TableCell>
//                                             )}
//                                           </React.Fragment>
//                                         );
//                                       })}

//                                       <TableCell className="text-right">
//                                         {renderValor(totalConta, conta.vertical_total)}
//                                       </TableCell>
//                                       {showOrcado && (
//                                         <TableCell className="text-right">
//                                           {renderValorOrcamento(
//                                             totalContaOrc,
//                                             conta.vertical_orcamentos_total,
//                                             undefined
//                                           )}
//                                         </TableCell>
//                                       )}
//                                       {showDiferenca && (
//                                         <TableCell className="text-right">
//                                           {renderValorDiferenca(totalConta, totalContaOrc)}
//                                         </TableCell>
//                                       )}
//                                     </TableRow>

//                                     {/* CLASSIFICAÇÕES DA CONTA (NÍVEL 3) */}
//                                     {isContaOpen &&
//                                       conta.classificacoes?.map((classificacao) => {
//                                         const totalClassificacao = calcularTotal(
//                                           periodo === "mes"
//                                             ? classificacao.valores_mensais
//                                             : periodo === "trimestre"
//                                             ? classificacao.valores_trimestrais
//                                             : classificacao.valores_anuais
//                                         );
//                                         const totalClassificacaoOrc = calcularTotalOrcamento(
//                                           periodo === "mes"
//                                             ? classificacao.orcamentos_mensais
//                                             : periodo === "trimestre"
//                                             ? classificacao.orcamentos_trimestrais
//                                             : classificacao.orcamentos_anuais
//                                         );

//                                         return (
//                                           <TableRow 
//                                             key={`${totalizador.nome}-${conta.nome}-${classificacao.nome}`} 
//                                             className="bg-muted/10"
//                                           >
//                                             <TableCell className="sticky left-0 z-10 bg-muted/10 pl-16 text-sm">
//                                               <div className="flex items-center gap-2">
//                                                 <div className="w-2 h-2 rounded-full bg-muted-foreground/50" />
//                                                 <span className="text-muted-foreground">{classificacao.nome}</span>
//                                               </div>
//                                             </TableCell>

//                                             {periodosFiltrados.map((p) => {
//                                               const real = calcularValor(classificacao, p);
//                                               const orcado = calcularOrcamento(classificacao, p);
//                                               return (
//                                                 <React.Fragment key={p}>
//                                                   <TableCell className="text-sm">
//                                                     {renderValor(
//                                                       real,
//                                                       periodo === "mes"
//                                                         ? classificacao.vertical_mensais?.[p]
//                                                         : periodo === "trimestre"
//                                                         ? classificacao.vertical_trimestrais?.[p]
//                                                         : classificacao.vertical_anuais?.[p],
//                                                       periodo === "mes"
//                                                         ? classificacao.horizontal_mensais?.[p]
//                                                         : periodo === "trimestre"
//                                                         ? classificacao.horizontal_trimestrais?.[p]
//                                                         : classificacao.horizontal_anuais?.[p]
//                                                     )}
//                                                   </TableCell>
//                                                   {showOrcado && (
//                                                     <TableCell className="text-sm">
//                                                       {renderValorOrcamento(
//                                                         orcado,
//                                                         periodo === "mes"
//                                                           ? classificacao.vertical_orcamentos_mensais?.[p]
//                                                           : periodo === "trimestre"
//                                                           ? classificacao.vertical_orcamentos_trimestrais?.[p]
//                                                           : classificacao.vertical_orcamentos_anuais?.[p],
//                                                         periodo === "mes"
//                                                           ? classificacao.horizontal_orcamentos_mensais?.[p]
//                                                           : periodo === "trimestre"
//                                                           ? classificacao.horizontal_orcamentos_trimestrais?.[p]
//                                                           : classificacao.horizontal_orcamentos_anuais?.[p]
//                                                       )}
//                                                     </TableCell>
//                                                   )}
//                                                   {showDiferenca && (
//                                                     <TableCell className="text-sm">
//                                                       {renderValorDiferenca(real, orcado)}
//                                                     </TableCell>
//                                                   )}
//                                                 </React.Fragment>
//                                               );
//                                             })}

//                                             <TableCell className="text-right text-sm">
//                                               {renderValor(totalClassificacao, classificacao.vertical_total)}
//                                             </TableCell>
//                                             {showOrcado && (
//                                               <TableCell className="text-right text-sm">
//                                                 {renderValorOrcamento(
//                                                   totalClassificacaoOrc,
//                                                   classificacao.vertical_orcamentos_total,
//                                                   undefined
//                                                 )}
//                                               </TableCell>
//                                             )}
//                                             {showDiferenca && (
//                                               <TableCell className="text-right text-sm">
//                                                 {renderValorDiferenca(totalClassificacao, totalClassificacaoOrc)}
//                                               </TableCell>
//                                             )}
//                                           </TableRow>
//                                         );
//                                       })}
//                                   </React.Fragment>
//                                 );
//                               })}
//                           </React.Fragment>
//                         );
//                       })}
//                     </React.Fragment>
//                   );
//                 } else {
//                   // Para "Saldo inicial" e "Saldo final", renderizar diretamente
//                   return (
//                     <TableRow key={item.nome} className="bg-primary/5 font-bold border-t-2 border-primary">
//                       <TableCell className="py-4 md:sticky md:left-0 md:z-20 bg-primary/5 font-bold">
//                         <span className="text-base font-bold text-primary">{item.nome}</span>
//                       </TableCell>
                      
//                       {periodosFiltrados.map((p) => {
//                         const real = calcularValor(item, p);
//                         const orcado = calcularOrcamento(item, p);
//                         return (
//                           <React.Fragment key={p}>
//                             <TableCell className="font-bold">
//                               {renderValor(real)}
//                             </TableCell>
//                             {showOrcado && (
//                               <TableCell className="font-bold">
//                                 {renderValorOrcamento(orcado)}
//                               </TableCell>
//                             )}
//                             {showDiferenca && (
//                               <TableCell className="font-bold">
//                                 {renderValorDiferenca(real, orcado)}
//                               </TableCell>
//                             )}
//                           </React.Fragment>
//                         );
//                       })}

//                       <TableCell className="py-4 text-right font-bold">
//                         {renderValor(item.valor)}
//                       </TableCell>
//                       {showOrcado && (
//                         <TableCell className="py-4 text-right font-bold">
//                           {renderValorOrcamento(item.orcamento_total)}
//                         </TableCell>
//                       )}
//                       {showDiferenca && (
//                         <TableCell className="py-4 text-right font-bold">
//                           {renderValorDiferenca(item.valor, item.orcamento_total)}
//                         </TableCell>
//                       )}
//                     </TableRow>
//                   );
//                 }
//               })}
//             </TableBody>
//           </Table>
//         </div>
//       </CardContent>
//     </Card>
//   )
// }
