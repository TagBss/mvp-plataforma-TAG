import { ChartAreaGradientTwo } from "@/components/chart-area-gradient-2";
import { ChartBarMixed } from "@/components/chart-bar-mixed";
import ChartOverview from "@/components/charts";
import DreTable from "@/components/table-dre-roriz";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { ArrowUpDown, Hourglass, MinusCircle, Package, PlusCircle, TrendingUp, Wallet } from "lucide-react";

export default function Home() {
  return (
    <main className="sm:ml-14 p-4">
      <section className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader>
            <div className="flex items-center justify-center">
              <CardTitle className="text-lg sm:text-xl select-none">
                Contas recebidas
              </CardTitle>
              <PlusCircle className="ml-auto w-4 h-4"/>
            </div>
          </CardHeader>

          <CardContent>
            <div className="sm:flex sm:justify-between sm:items-center">
              <p className="text-lg sm:text-2xl">R$ 342,1 Mil</p>
              <CardDescription>
                <p>vs abr/25 <br/>↙ 63,9%</p>
              </CardDescription>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center justify-center">
              <CardTitle className="text-lg sm:text-xl select-none">
                PMR
              </CardTitle>
              <Hourglass className="ml-auto w-4 h-4"/>
            </div>
            <CardDescription>
              <p>prazo médio recebimento</p>
            </CardDescription>
          </CardHeader>

          <CardContent>
            <div className="sm:flex sm:justify-between sm:items-center">
              <p className="text-lg sm:text-2xl">6 dias</p>
              <CardDescription>
                <p>Últimos 12M</p>
              </CardDescription>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center justify-center">
              <CardTitle className="text-lg sm:text-xl select-none">
                Contas pagas
              </CardTitle>
              <MinusCircle className="ml-auto w-4 h-4"/>
            </div>
          </CardHeader>

          <CardContent>
            <div className="sm:flex sm:justify-between sm:items-center">
              <p className="text-lg sm:text-2xl">R$ -857,2 Mil</p>
              <CardDescription>
                <p>vs abr/25 <br/>↙ 21,4%</p>
              </CardDescription>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center justify-center">
              <CardTitle className="text-lg sm:text-xl select-none">
                PMP
              </CardTitle>
              <Hourglass className="ml-auto w-4 h-4"/>
            </div>
            <CardDescription>
              <p>prazo médio pagamento</p>
            </CardDescription>
          </CardHeader>

          <CardContent>
            <div className="sm:flex sm:justify-between sm:items-center">
              <p className="text-lg sm:text-2xl">8 dias</p>
              <CardDescription>
                <p>Últimos 12M</p>
              </CardDescription>
            </div>
          </CardContent>
        </Card>
      </section>

      <section className="mt-4 flex flex-col md:flex-row gap-4">
        <Card className="w-full">
          <CardHeader>
            <div className="flex items-center justify-center">
              <CardTitle className="text-lg sm:text-xl select-none">
                Movimentações
              </CardTitle>
              <ArrowUpDown className="ml-auto w-4 h-4"/>
            </div>
          </CardHeader>

          <CardContent>
            <div className="sm:flex sm:justify-between sm:items-center">
              <p className="text-lg sm:text-2xl">R$ -515,2 Mil</p>
              <CardDescription>
                <p>vs abr/25 <br/>↗ 261,9%</p>
              </CardDescription>
            </div>

            <CardDescription className="py-4">
              <p>Movimentações últimos 6M</p>
            </CardDescription>

            <ChartOverview/>
          </CardContent>
        </Card>

        <Card className="w-full">
          <CardHeader>
            <div className="flex items-center justify-center">
              <CardTitle className="text-lg sm:text-xl select-none">
                Saldo Final
              </CardTitle>
              <Wallet className="ml-auto w-4 h-4"/>
            </div>
          </CardHeader>

          <CardContent>
            <div className="sm:flex sm:justify-between sm:items-center">
              <p className="text-lg sm:text-2xl">R$ -467,7 Mil</p>
              <CardDescription>
                <p>vs abr/25 <br/>↗ 1085,3%</p>
              </CardDescription>
            </div>

            <CardDescription className="py-4">
              <p>Saldo últimos 6M</p>
            </CardDescription>
            
            <ChartAreaGradientTwo/>
          </CardContent>
          <CardFooter>
            <div className="flex w-full items-start gap-2 text-sm">
              <div className="grid gap-2">
                <div className="flex items-center gap-2 leading-none font-medium">
                  Trending up by 5.2% this month <TrendingUp className="h-4 w-4" />
                </div>
                <div className="text-muted-foreground flex items-center gap-2 leading-none">
                  January - June 2024
                </div>
              </div>
            </div>
          </CardFooter>
        </Card>

        <Card className="w-full">
          <CardHeader>
            <div className="flex items-center justify-center">
              <CardTitle className="text-lg sm:text-xl select-none">
                Custos
              </CardTitle>
              <Package className="ml-auto w-4 h-4"/>
            </div>
          </CardHeader>

          <CardContent>
            <div className="sm:flex sm:justify-between sm:items-center">
              <p className="text-lg sm:text-2xl">R$ -214,8 Mil</p>
              <CardDescription>
                <p>vs abr/25 <br/>↙ 17,6%</p>
              </CardDescription>
            </div>

            <CardDescription className="py-4">
              <p>Saldo últimos 6M</p>
            </CardDescription>
            
            <ChartBarMixed/>
          </CardContent>
          <CardFooter className="flex-col items-start gap-2 text-sm">
            <div className="flex gap-2 leading-none font-medium">
              Trending up by 5.2% this month <TrendingUp className="h-4 w-4" />
            </div>
            <div className="text-muted-foreground leading-none">
              Showing total visitors for the last 6 months
            </div>
          </CardFooter>
        </Card>
      </section>

      <section className="mt-4 flex flex-col md:flex-row gap-4">
        <DreTable/>
      </section>
    </main>
  );
}