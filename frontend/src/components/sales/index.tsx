import { CircleDollarSign } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../ui/card";
import { Avatar, AvatarFallback, AvatarImage } from "../ui/avatar";

export default function Sales() {
    return (
        <Card className="flex-1">
            <CardHeader>
                <div className="flex items-center justify-center">
                    <CardTitle className="text-lg sm:text-xl text-gray-800">
                        Últimos clientes
                    </CardTitle>
                    <CircleDollarSign className="ml-auto w-4 h-4"/>
                </div>
                <CardDescription>
                    Novos clientes nas últimas 24h
                </CardDescription>
            </CardHeader>

            <CardContent>
                <article className="flex items-center gap-2 border-b py-2">
                    <Avatar className="w-8 h-8">
                    <AvatarImage src="https://github.com/igormatheusf.png"/>
                    <AvatarFallback>if</AvatarFallback>
                    </Avatar>
                    <div>
                        <p className="tex-sm sm:tex-base font-semibold">Igor Fonseca</p>
                        <span className="text-[12px] sm:text-sm text-gray-500">email@email.com</span>
                    </div>
                </article>

                <article className="flex items-center gap-2 border-b py-2">
                    <Avatar className="w-8 h-8">
                    <AvatarImage src=""/>
                    <AvatarFallback>cs</AvatarFallback>
                    </Avatar>
                    <div>
                        <p className="tex-sm sm:tex-base font-semibold">Cristina Silva</p>
                        <span className="text-[12px] sm:text-sm text-gray-500">email@email.com</span>
                    </div>
                </article>

                <article className="flex items-center gap-2 border-b py-2">
                    <Avatar className="w-8 h-8">
                    <AvatarImage src=""/>
                    <AvatarFallback>tp</AvatarFallback>
                    </Avatar>
                    <div>
                        <p className="tex-sm sm:tex-base font-semibold">Tiago Pereira</p>
                        <span className="text-[12px] sm:text-sm text-gray-500">email@email.com</span>
                    </div>
                </article>
            </CardContent>
        </Card>
    )
}