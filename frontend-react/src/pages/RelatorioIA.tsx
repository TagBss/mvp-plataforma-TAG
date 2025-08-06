import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card'
import { Button } from '../components/ui/button'
import { Separator } from '../components/ui/separator'
import { Badge } from '../components/ui/badge'
import { Alert, AlertDescription } from '../components/ui/alert'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs'
import { Textarea } from '../components/ui/textarea'
import { Input } from '../components/ui/input'
import { Label } from '../components/ui/label'
import { Brain, Sparkles, Download, Send, FileText } from 'lucide-react'
import { useHealthCheck } from '../hooks/useFinancialData'
import LoadingSpinner from '../components/LoadingSpinner'
import { useState } from 'react'

const RelatorioIA = () => {
  const { health, loading, error } = useHealthCheck()
  const [prompt, setPrompt] = useState('')
  const [generatingReport, setGeneratingReport] = useState(false)

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner />
      </div>
    )
  }

  if (error) {
    return (
      <div className="container mx-auto p-6">
        <Alert variant="destructive">
          <AlertDescription>
            Erro ao conectar com o servidor: {error}
          </AlertDescription>
        </Alert>
      </div>
    )
  }

  const handleGenerateReport = () => {
    setGeneratingReport(true)
    // Aqui será implementada a lógica de geração do relatório com IA
    setTimeout(() => {
      setGeneratingReport(false)
    }, 3000) // Simular tempo de processamento
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="space-y-2">
        <h1 className="text-3xl font-bold flex items-center gap-2">
          <Brain className="h-8 w-8 text-purple-600" />
          Relatório Personalizado com IA
        </h1>
        <p className="text-muted-foreground">
          Gere relatórios financeiros personalizados usando inteligência artificial
        </p>
      </div>

      <Separator />

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-purple-600" />
              Configuração do Relatório
            </CardTitle>
            <CardDescription>
              Descreva o tipo de relatório que você deseja gerar
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="report-title">Título do Relatório</Label>
              <Input 
                id="report-title" 
                placeholder="Ex: Análise de Performance Q4 2024"
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="report-prompt">Descrição e Requisitos</Label>
              <Textarea
                id="report-prompt"
                placeholder="Descreva detalhadamente o que você gostaria que o relatório contenha. Por exemplo: 'Preciso de uma análise comparativa das receitas do último trimestre, incluindo gráficos de tendência e identificação dos principais fatores que impactaram o crescimento...'"
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                className="min-h-[120px]"
              />
            </div>

            <Button 
              onClick={handleGenerateReport}
              disabled={!prompt.trim() || generatingReport}
              className="w-full"
            >
              {generatingReport ? (
                <>
                  <LoadingSpinner />
                  Gerando Relatório...
                </>
              ) : (
                <>
                  <Send className="h-4 w-4 mr-2" />
                  Gerar Relatório
                </>
              )}
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              Prévia do Relatório
            </CardTitle>
            <CardDescription>
              O relatório gerado aparecerá aqui
            </CardDescription>
          </CardHeader>
          <CardContent>
            {generatingReport ? (
              <div className="flex items-center justify-center h-40">
                <div className="text-center space-y-2">
                  <LoadingSpinner />
                  <p className="text-sm text-muted-foreground">
                    A IA está analisando seus dados...
                  </p>
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-center h-40 bg-muted rounded-md">
                <p className="text-muted-foreground text-center">
                  Configure e gere um relatório para ver a prévia aqui
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Modelos de Relatórios</CardTitle>
          <CardDescription>
            Selecione um modelo pré-configurado para começar rapidamente
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-3">
            <Card className="cursor-pointer hover:bg-accent">
              <CardContent className="p-4">
                <h3 className="font-medium mb-2">Análise de Performance</h3>
                <p className="text-sm text-muted-foreground">
                  Relatório completo de performance financeira com KPIs principais
                </p>
              </CardContent>
            </Card>
            
            <Card className="cursor-pointer hover:bg-accent">
              <CardContent className="p-4">
                <h3 className="font-medium mb-2">Comparativo Mensal</h3>
                <p className="text-sm text-muted-foreground">
                  Comparação mês a mês com análise de tendências
                </p>
              </CardContent>
            </Card>
            
            <Card className="cursor-pointer hover:bg-accent">
              <CardContent className="p-4">
                <h3 className="font-medium mb-2">Relatório Executivo</h3>
                <p className="text-sm text-muted-foreground">
                  Resumo executivo com insights e recomendações
                </p>
              </CardContent>
            </Card>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default RelatorioIA
