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
  classificacoes?: {
    nome: string
    valor: number
  }[]
}

export default function DreTable() {
  const [data, setData] = useState<DreItem[]>([])
  const [openSections, setOpenSections] = useState<Record<string, boolean>>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetch("http://127.0.0.1:8000/dre")
      .then(res => res.json())
      .then(result => {
        if (result.error) {
          setError(result.error)
        } else {
          setData(result)
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
    setOpenSections(prev => ({ ...prev, [nome]: !prev[nome] }))
  }

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
    <Card className="p-4">
      <CardHeader>
        <CardTitle>DRE - Roriz Instrumentos</CardTitle>
        <CardDescription>Todo o período</CardDescription>
      </CardHeader>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Descrição</TableHead>
            <TableHead>Valor</TableHead>
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
                    className={`py-3 pr-16 ${isTotalizador ? "font-bold" : "text-foreground"} flex items-center gap-2`}
                  >
                    {isExpandable && (
                      <ChevronDown
                        className={`transition-transform duration-200 ${
                          isOpen ? "rotate-0" : "-rotate-90"
                        }`}
                        size={16}
                      />
                    )}
                    <span className="text-muted-foreground font-mono text-sm w-4 flex-shrink-0">
                      {item.tipo}
                    </span>
                    <span>{item.nome}</span>
                  </TableCell>
                  <TableCell
                    className={`py-3 ${isTotalizador ? "font-bold" : "text-foreground"}`}
                  >
                    {item.valor.toLocaleString("pt-BR", {
                      style: "currency",
                      currency: "BRL",
                    })}
                  </TableCell>
                </TableRow>

                {isOpen && isExpandable &&
                  item.classificacoes!.map((subItem, subIdx) => (
                    <TableRow key={`${idx}-${subIdx}`} className="bg-muted/20">
                      <TableCell className="pl-12 py-2 text-muted-foreground text-sm">
                        <span className="flex items-center gap-2">
                          <span className="w-2 h-2 bg-muted-foreground/30 rounded-full"></span>
                          {subItem.nome}
                        </span>
                      </TableCell>
                      <TableCell className="py-2 text-muted-foreground text-sm">
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
    </Card>
  )
}