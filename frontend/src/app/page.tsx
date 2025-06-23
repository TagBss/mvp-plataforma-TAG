import { ChartAreaGradient } from "@/components/chart-area-gradient";
import { ChartBarInteractive } from "@/components/chart-bar-interactive";
import ChartOverview from "@/components/charts";
import Sales from "@/components/sales";
import { TableDemo } from "@/components/table-demo";
import DreTable from "@/components/table-dre-roriz";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { DollarSign, ListOrdered, Percent, Users } from "lucide-react";

export default function Home() {
  return (
    <main className="sm:ml-14 p-4">
      <section className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader>
            <div className="flex items-center justify-center">
              <CardTitle className="text-lg sm:text-xl select-none">
                Total vendas
              </CardTitle>
              <DollarSign className="ml-auto w-4 h-4"/>
            </div>
            <CardDescription>
              Total vendas em 90 dias
            </CardDescription>
          </CardHeader>

          <CardContent>
            <p>R$ 40 mil</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center justify-center">
              <CardTitle className="text-lg sm:text-xl select-none">
                Novos clientes
              </CardTitle>
              <Users className="ml-auto w-4 h-4"/>
            </div>
            <CardDescription>
              Novos clientes em 90 dias
            </CardDescription>
          </CardHeader>

          <CardContent>
            <p>190</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center justify-center">
              <CardTitle className="text-lg sm:text-xl select-none">
                Pedidos
              </CardTitle>
              <ListOrdered className="ml-auto w-4 h-4"/>
            </div>
            <CardDescription>
              Total de pedidos em 90 dias
            </CardDescription>
          </CardHeader>

          <CardContent>
            <p>550</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center justify-center">
              <CardTitle className="text-lg sm:text-xl select-none">
                Ticket médio
              </CardTitle>
              <Percent className="ml-auto w-4 h-4"/>
            </div>
            <CardDescription>
              Ticket médio em 90 dias (Total Vendas / Pedidos)
            </CardDescription>
          </CardHeader>

          <CardContent>
            <p>R$ 72,7</p>
          </CardContent>
        </Card>
      </section>

      <section className="mt-4 flex flex-col md:flex-row gap-4">
        <ChartOverview/>
        <Sales/>
      </section>

      <section className="mt-4">
        <ChartBarInteractive/>
      </section>

      <section className="mt-4 flex flex-col md:flex-row gap-4">
        <ChartAreaGradient/>
      </section>

      <section className="mt-4 flex flex-col md:flex-row gap-4">
        <TableDemo/>
      </section>

      <section className="mt-4 flex flex-col md:flex-row gap-4">
        <DreTable/>
      </section>
    </main>
  );
}
