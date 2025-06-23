"use client"

import { useEffect, useState } from "react"
import { ChevronDown } from "lucide-react"
import { Card } from "@/components/ui/card"
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

  useEffect(() => {
    fetch("http://127.0.0.1:8000/dre")
      .then(res => res.json())
      .then(setData)
  }, [])

  const toggle = (nome: string) => {
    setOpenSections(prev => ({ ...prev, [nome]: !prev[nome] }))
  }

  return (
    <Card className="p-4">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Descrição</TableHead>
            <TableHead className="pl-4">Valor</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.map((item, idx) => {
            const isExpandable = item.classificacoes && item.classificacoes.length > 0
            const isOpen = openSections[item.nome] ?? true
            const isTotalizador = item.tipo === "="

            return (
              <>
                <TableRow
                  key={idx}
                  className={isExpandable ? "cursor-pointer hover:bg-muted" : ""}
                  onClick={() => isExpandable && toggle(item.nome)}
                >
                  <TableCell
                    className={`py-2 pr-16 ${isTotalizador ? "font-bold" : "text-foreground"} flex items-center gap-2`}
                  >
                    {isExpandable && (
                      <ChevronDown
                        className={`transition-transform ${isOpen ? "rotate-0" : "-rotate-90"}`}
                        size={16}
                      />
                    )}
                    <span className="text-muted-foreground">{item.tipo}</span>
                    <span>{item.nome}</span>
                  </TableCell>
                  <TableCell
                    className={`py-2 pl-4 ${isTotalizador ? "font-bold" : "text-foreground"}`}
                  >
                    {item.valor.toLocaleString("pt-BR", {
                      style: "currency",
                      currency: "BRL",
                    })}
                  </TableCell>
                </TableRow>

                {isOpen && isExpandable &&
                  item.classificacoes!.map((subItem, subIdx) => (
                    <TableRow key={`${idx}-${subIdx}`}>
                      <TableCell className="pl-10 text-muted-foreground">
                        {subItem.nome}
                      </TableCell>
                      <TableCell className="text-right text-muted-foreground">
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