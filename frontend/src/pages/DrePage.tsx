import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card'
import DreTablePostgreSQL from '../components/table-dre-postgresql'

const DrePage = () => {
  console.log("🚀 DrePage renderizando...")
  
  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="space-y-2">
        <h1 className="text-2xl font-bold flex items-center gap-2">
          Demonstração do Resultado do Exercício (DRE)
        </h1>
      </div>

      <DreTablePostgreSQL />
    </div>
  )
}

export default DrePage
