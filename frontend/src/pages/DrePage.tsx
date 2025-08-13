import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card'
import { FileText } from 'lucide-react'
import DreTablePostgreSQL from '../components/table-dre-postgresql'

const DrePage = () => {
  console.log("🚀 DrePage renderizando...")
  
  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="space-y-2">
        <h1 className="text-3xl font-bold flex items-center gap-2">
          <FileText className="h-8 w-8" />
          Demonstração do Resultado do Exercício (DRE)
        </h1>
        <p className="text-muted-foreground">
          Análise detalhada das receitas, custos e despesas da empresa - Dados do PostgreSQL
        </p>
      </div>

      <DreTablePostgreSQL />
    </div>
  )
}

export default DrePage
