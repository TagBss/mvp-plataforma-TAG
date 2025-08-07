"use client"

import { useState, useEffect } from "react"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "../ui/dropdown-menu"
import { Button } from "../ui/button"
import { api } from "../../services/api"

const mesesNomes = [
  "", "Janeiro", "Fevereiro", "Março",
  "Abril", "Maio", "Junho",
  "Julho", "Agosto", "Setembro",
  "Outubro", "Novembro", "Dezembro"
]


interface FiltroMesProps {
  onSelect: (mes: string) => void;
  endpoint: string;
  value: string; // mês selecionado controlado pelo pai
}


export function FiltroMes({ onSelect, endpoint, value }: FiltroMesProps) {
  const [mesesDisponiveis, setMesesDisponiveis] = useState<string[]>([])
  const [mesesAgrupados, setMesesAgrupados] = useState<Record<string, { value: string, label: string }[]>>({})

  useEffect(() => {
    const fetchMeses = async () => {
      try {
        const res = await api.get(endpoint)
        const data = res.data
        let meses: string[] = [];
        // Aceita tanto meses_disponiveis quanto meses
        if (data?.data?.meses_disponiveis && Array.isArray(data.data.meses_disponiveis)) {
          meses = data.data.meses_disponiveis;
        } else if (data?.meses_disponiveis && Array.isArray(data.meses_disponiveis)) {
          meses = data.meses_disponiveis;
        } else if (data?.meses && Array.isArray(data.meses)) {
          meses = data.meses;
        } else if (Array.isArray(data) && data.length > 0 && typeof data[0] === "string") {
          meses = data;
        }
        if (meses.length > 0) {
          setMesesDisponiveis(meses);
        } else {
          console.error("meses_disponiveis ou meses não encontrados!");
        }
      } catch (error) {
        console.error("Erro ao buscar meses:", error);
      }
    }
    fetchMeses()
  }, [endpoint])

  useEffect(() => {
    const agrupados: Record<string, { value: string, label: string }[]> = {}
    mesesDisponiveis.forEach((m) => {
      const [ano, mesNum] = m.split("-")
      if (!agrupados[ano]) agrupados[ano] = []
      agrupados[ano].push({ value: m, label: mesesNomes[parseInt(mesNum)] })
    })
    Object.keys(agrupados).forEach(ano => {
      agrupados[ano].sort((a, b) =>
        parseInt(a.value.split("-")[1]) - parseInt(b.value.split("-")[1])
      )
    })
    setMesesAgrupados(agrupados)
  }, [mesesDisponiveis])


  const handleSelect = (mes: { value: string, label: string } | null) => {
    // Atualiza imediatamente o filtro para 'Todo o período' ao clicar
    if (!mes) {
      onSelect("");
    } else {
      onSelect(mes.value);
    }
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline">
          {value === "" ? "Todo o período" : (() => {
            const [ano, mesNum] = value.split("-");
            if (!ano || !mesNum) return value;
            return `${mesesNomes[parseInt(mesNum)]}/${ano}`;
          })()}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent className="w-56 max-h-64 overflow-y-auto">
        <DropdownMenuItem onClick={() => handleSelect(null)}>
          Todo o período
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        {Object.keys(mesesAgrupados).sort().map(ano => (
          <div key={ano}>
            <DropdownMenuLabel>{ano}</DropdownMenuLabel>
            {mesesAgrupados[ano].map(mes => (
              <DropdownMenuItem
                key={mes.value}
                onClick={() => handleSelect(mes)}
              >
                {mes.label}
              </DropdownMenuItem>
            ))}
            <DropdownMenuSeparator />
          </div>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}