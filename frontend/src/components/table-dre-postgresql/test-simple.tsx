import { useEffect, useState } from "react"
import { api } from "../../services/api"

export default function TestSimpleDRE() {
  const [status, setStatus] = useState<string>("Clique em 'Testar DRE' para iniciar")
  const [data, setData] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const testarDRE = async () => {
    setLoading(true)
    setError(null)
    setData(null)
    setStatus("Testando...")
    
    console.log("🧪 TESTE SIMPLES DRE - Iniciando...")
    
    try {
      // Teste 1: Verificar se a API está acessível
      const healthRes = await api.get("/health")
      console.log("✅ Health check OK:", healthRes.status)
      setStatus("Health check OK - Testando DRE...")
      
      // Teste 2: Tentar o endpoint DRE
      const dreRes = await api.get("/dre-postgresql-views")
      console.log("✅ DRE endpoint OK:", dreRes.status)
      console.log("📊 Dados recebidos:", dreRes.data)
      setData(dreRes.data)
      setStatus("DRE carregado com sucesso!")
      
    } catch (err: any) {
      console.error("❌ ERRO NO TESTE:", err)
      console.error("❌ Detalhes:", {
        message: err.message,
        status: err.response?.status,
        data: err.response?.data,
        config: err.config
      })
      setError(`Erro: ${err.message}`)
      setStatus("Erro no teste")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-6 bg-white rounded-lg shadow">
      <h2 className="text-xl font-bold mb-4">🧪 Teste Simples DRE PostgreSQL</h2>
      
      <div className="space-y-4">
        <div className="flex gap-4 items-center">
          <button
            onClick={testarDRE}
            disabled={loading}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? "Testando..." : "🧪 Testar DRE"}
          </button>
          
          <div className="p-3 bg-blue-50 rounded flex-1">
            <strong>Status:</strong> {status}
          </div>
        </div>
        
        {error && (
          <div className="p-3 bg-red-50 rounded">
            <strong>Erro:</strong> {error}
          </div>
        )}
        
        {data && (
          <div className="p-3 bg-green-50 rounded">
            <strong>Dados:</strong>
            <pre className="mt-2 text-sm overflow-auto">
              {JSON.stringify(data, null, 2)}
            </pre>
          </div>
        )}
        
        <div className="p-3 bg-gray-50 rounded">
          <strong>Console:</strong> Abra o console do navegador (F12) para ver os logs detalhados
        </div>
      </div>
    </div>
  )
}
