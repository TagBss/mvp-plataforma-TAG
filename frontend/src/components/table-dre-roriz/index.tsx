"use client"

import { useEffect, useState } from "react"
import { ChevronDown } from "lucide-react"
import { Card } from "@/components/ui/card"
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table"

type DreItem = {
  tipo: string
  nome: string
  valor: number
}

export default function DreTable() {
  const [data, setData] = useState<DreItem[]>([])
  const [openSections, setOpenSections] = useState<Record<string, boolean>>({})

  useEffect(() => {
    fetch("https://dashboard-nextjs-and-fastapi.onrender.com/dre")
      .then(res => res.json())
      .then(setData)
  }, [])

  const toggle = (nome: string) => {
    setOpenSections(prev => ({ ...prev, [nome]: !prev[nome] }))
  }

  const rows = []
  let i = 0

  while (i < data.length) {
    const item = data[i]

    // É um totalizador (=): mostra direto
    if (item.tipo === "=") {
      rows.push(
        <TableRow key={i} className="bg-muted/40">
          <TableCell className="font-semibold">{item.nome}</TableCell>
          <TableCell className="text-right font-semibold">
            {item.valor.toLocaleString("pt-BR", {
              style: "currency",
              currency: "BRL",
            })}
          </TableCell>
        </TableRow>
      )
      i++
      continue
    }

    // É um agrupador (+, -, +/-): pode ter filhos
    const nomePai = item.nome
    const tipo = item.tipo
    const isOpen = openSections[nomePai] ?? true

    // Puxa os filhos (com o mesmo tipo e nome diferente)
    const children: DreItem[] = []
    let j = i + 1
    while (j < data.length && data[j].tipo === tipo && data[j].nome !== nomePai) {
      children.push(data[j])
      j++
    }

    rows.push(
      <TableRow
        key={i}
        onClick={() => toggle(nomePai)}
        className="cursor-pointer hover:bg-muted"
      >
        <TableCell className="font-bold flex items-center gap-2">
          <ChevronDown
            size={16}
            className={`transition-transform ${isOpen ? "rotate-0" : "-rotate-90"}`}
          />
          {nomePai}
        </TableCell>
        <TableCell className="text-right font-bold">
          {item.valor.toLocaleString("pt-BR", {
            style: "currency",
            currency: "BRL",
          })}
        </TableCell>
      </TableRow>
    )

    if (isOpen) {
      children.forEach((child, index) => {
        rows.push(
          <TableRow key={`${i}-child-${index}`}>
            <TableCell className="pl-8 text-muted-foreground">{child.nome}</TableCell>
            <TableCell className="text-right">
              {child.valor.toLocaleString("pt-BR", {
                style: "currency",
                currency: "BRL",
              })}
            </TableCell>
          </TableRow>
        )
      })
    }

    // Avança até depois dos filhos
    i = j
  }

  return (
    <Card className="p-4">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Descrição</TableHead>
            <TableHead className="text-right">Valor</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>{rows}</TableBody>
      </Table>
    </Card>
  )
}