"use client"

import { useEffect, useState } from "react"
import { ChevronDown } from "lucide-react"
import { Card } from "@/components/ui/card"
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow
} from "@/components/ui/table"

type DreItem = {
  DRE_n1: string
  DRE_n2: string
  valor_original: number
}

export default function DreTable() {
  const [data, setData] = useState<DreItem[]>([])
  const [openSections, setOpenSections] = useState<Record<string, boolean>>({})

  useEffect(() => {
    fetch("https://dashboard-nextjs-and-fastapi.onrender.com/dre")
      .then(res => res.json())
      .then(setData)
  }, [])

  const grouped = data.reduce((acc, item) => {
    if (!acc[item.DRE_n1]) {
      acc[item.DRE_n1] = []
    }
    acc[item.DRE_n1].push(item)
    return acc
  }, {} as Record<string, DreItem[]>)

  const toggle = (section: string) => {
    setOpenSections(prev => ({ ...prev, [section]: !prev[section] }))
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
        <TableBody>
          {Object.entries(grouped).map(([dre_n1, items]) => {
            const total = items.reduce((sum, i) => sum + i.valor_original, 0)
            const isOpen = openSections[dre_n1] ?? true
            return (
              <div key={dre_n1}>
                <TableRow
                  className="cursor-pointer hover:bg-muted"
                  onClick={() => toggle(dre_n1)}
                >
                  <TableCell className="font-bold flex items-center gap-2">
                    <ChevronDown
                      className={`transition-transform ${isOpen ? "rotate-0" : "-rotate-90"}`}
                      size={16}
                    />
                    {dre_n1}
                  </TableCell>
                  <TableCell className="text-right font-bold">
                    {total.toLocaleString("pt-BR", {
                      style: "currency",
                      currency: "BRL",
                    })}
                  </TableCell>
                </TableRow>
                {isOpen &&
                  items.map((item, i) => (
                    <TableRow key={i}>
                      <TableCell className="pl-8 text-muted-foreground">
                        {item.DRE_n2}
                      </TableCell>
                      <TableCell className="text-right">
                        {item.valor_original.toLocaleString("pt-BR", {
                          style: "currency",
                          currency: "BRL",
                        })}
                      </TableCell>
                    </TableRow>
                  ))}
              </div>
            )
          })}
        </TableBody>
      </Table>
    </Card>
  )
}