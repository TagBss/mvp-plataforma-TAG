"use client"

import { useEffect, useState } from "react"
import { ChevronDown } from "lucide-react"
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow
} from "@/components/ui/table"

type DreItem = {
  tipo: string
  nome: string
  valor: number
  valores_mensais?: Record<string, number>
  classificacoes?: {
    nome: string
    valor: number
    valores_mensais?: Record<string, number>
  }[]
}

type DreResponse = {
  meses: string[]
  data: DreItem[]
}

export default function DreTable() {
  const [data, setData] = useState<DreItem[]>([])
  const [meses, setMeses] = useState<string[]>([])
  const [openSections, setOpenSections] = useState<Record<string, boolean>>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filtroAno, setFiltroAno] = useState<string>("2025")

  useEffect(() => {
    fetch("http://127.0.0.1:8000/dre")
      .then(res => res.json())
      .then((result: DreResponse | { error: string }) => {
        if ("error" in result) {
          setError(result.error)
        } else {
          setData(result.data)
          setMeses(result.meses || [])
        }
      })
      .catch(err => {
        setError(`Erro ao carregar dados: ${err.message}`)
      })
      .finally(() => {
        setLoading(false)
      })
  }, [])

  const toggle = (nome: string) => {
    setOpenSections((prev) => ({ ...prev, [nome]: !prev[nome] }))
  }

  const anosDisponiveis = Array.from(new Set(meses.map(m => m.split("-")[0])))

  // Meses filtrados
  const mesesFiltrados = filtroAno === "todos"
    ? meses
    : meses.filter(m => m.startsWith(filtroAno))

  if (loading) {
    return (
      <Card className="p-4">
        <CardHeader>
          <CardTitle>DRE - Roriz Instrumentos</CardTitle>
          <CardDescription>Carregando...</CardDescription>
        </CardHeader>
      </Card>
    )
  }

  if (error) {
    return (
      <Card className="p-4">
        <CardHeader>
          <CardTitle>DRE - Roriz Instrumentos</CardTitle>
          <CardDescription className="text-red-500">{error}</CardDescription>
        </CardHeader>
      </Card>
    )
  }

  return (
    <Card className="p-4 max-w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>DRE - Roriz Instrumentos</CardTitle>
            <CardDescription>
              {filtroAno === "todos" ? "Todo o período" : `Ano: ${filtroAno}`}
            </CardDescription>
          </div>
          <select
            className="text-sm border rounded px-2 py-1"
            value={filtroAno}
            onChange={(e) => setFiltroAno(e.target.value)}
          >
            <option value="todos">Todo o período</option>
            {anosDisponiveis.map((ano) => (
              <option key={ano} value={ano}>
                {ano}
              </option>
            ))}
          </select>
        </div>
      </CardHeader>

      <div className="relative overflow-auto max-w-full max-h-[80vh]">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="min-w-[300px] font-bold bg-muted md:sticky md:left-0 md:top-0 md:z-20 ">Descrição</TableHead>
                {mesesFiltrados.map((mes) => (
                  <TableHead key={mes} className="font-bold bg-muted/30 text-right min-w-[120px]">
                    {mes}
                  </TableHead>
                ))}
                <TableHead className="text-right min-w-[120px] font-bold bg-muted/30">Total</TableHead>
              </TableRow>
            </TableHeader>

            <TableBody>
              {data.map((item, idx) => {
                const isExpandable = item.classificacoes && item.classificacoes.length > 0
                const isOpen = openSections[item.nome] ?? false
                const isTotalizador = item.tipo === "="

                return (
                  <>
                    <TableRow
                      key={idx}
                      className={`${isExpandable ? "cursor-pointer hover:bg-muted/50" : ""} ${
                        isTotalizador ? "bg-muted/30" : ""
                      }`}
                      onClick={() => isExpandable && toggle(item.nome)}
                    >
                      <TableCell
                        className={`py-3 md:sticky md:left-0 md:z-20 ${
                          isTotalizador ? "font-bold bg-muted" : "text-foreground bg-background"
                        } flex items-center gap-2`}
                      >
                        {isExpandable && (
                          <ChevronDown
                            className={`transition-transform duration-200 ${
                              isOpen ? "rotate-0" : "-rotate-90"
                            }`}
                            size={16}
                          />
                        )}
                        <span className="text-muted-foreground text-sm w-4 flex-shrink-0">{item.tipo}</span>
                        <span>{item.nome}</span>
                      </TableCell>

                      {mesesFiltrados.map((mes) => (
                        <TableCell
                          key={mes}
                          className={`py-3 text-right ${isTotalizador ? "font-bold" : "text-foreground"}`}
                        >
                          {item.valores_mensais?.[mes]?.toLocaleString("pt-BR", {
                            style: "currency",
                            currency: "BRL",
                          }) || "R$ 0,00"}
                        </TableCell>
                      ))}

                      <TableCell className={`py-3 text-right ${isTotalizador ? "font-bold" : "text-foreground"} bg-muted/20`}>
                        {item.valor.toLocaleString("pt-BR", {
                          style: "currency",
                          currency: "BRL",
                        })}
                      </TableCell>
                    </TableRow>

                    {isOpen &&
                      isExpandable &&
                      item.classificacoes!.map((subItem, subIdx) => (
                        <TableRow key={`${idx}-${subIdx}`} className="bg-muted/20">
                          <TableCell className="pl-12 py-2 text-muted-foreground text-sm bg-muted md:sticky md:left-0  md:z-20">
                            <span className="flex items-center gap-2">
                              <span className="w-2 h-2 bg-muted-foreground/30 rounded-full"></span>
                              {subItem.nome}
                            </span>
                          </TableCell>

                          {mesesFiltrados.map((mes) => (
                            <TableCell key={mes} className="py-2 text-right text-muted-foreground text-sm">
                              {(subItem.valores_mensais?.[mes] ?? 0).toLocaleString("pt-BR", {
                                style: "currency",
                                currency: "BRL",
                              })}
                            </TableCell>
                          ))}

                          <TableCell className="py-2 text-right text-muted-foreground text-sm bg-muted/20">
                            {subItem.valor.toLocaleString("pt-BR", {
                              style: "currency",
                              currency: "BRL",
                            })}
                          </TableCell>
                        </TableRow>
                      ))}
                  </>
                )
              })}
            </TableBody>
          </Table>
      </div>
    </Card>
  )
}