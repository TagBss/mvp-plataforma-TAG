import React from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { ModeToggle } from './mode-toggle'
import { useThemeAdvanced } from '../hooks/use-theme'

export function DarkModeDemo() {
  const { isDark, theme } = useThemeAdvanced()

  return (
    <div className="p-6 space-y-6">
      {/* Header com toggle */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Dark Mode Demo</h1>
          <p className="text-muted-foreground">
            Tema atual: <span className="font-medium">{theme}</span>
            {isDark && <span className="ml-2">🌙</span>}
            {!isDark && <span className="ml-2">☀️</span>}
          </p>
        </div>
        <ModeToggle showLabel />
      </div>

      {/* Cards de demonstração */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* KPI Card */}
        <Card className="kpi-card">
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              Receita Total
              <span className="text-2xl">💰</span>
            </CardTitle>
            <CardDescription>
              Período: Janeiro - Dezembro 2024
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-600 dark:text-green-400">
              R$ 2.450.000
            </div>
            <p className="text-sm text-muted-foreground mt-2">
              +12.5% vs período anterior
            </p>
          </CardContent>
        </Card>

        {/* Financial Card */}
        <Card className="financial-card">
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              Margem de Lucro
              <span className="text-2xl">📊</span>
            </CardTitle>
            <CardDescription>
              Indicador de rentabilidade
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-blue-600 dark:text-blue-400">
              23.4%
            </div>
            <p className="text-sm text-muted-foreground mt-2">
              +2.1% vs meta
            </p>
          </CardContent>
        </Card>

        {/* Chart Container */}
        <Card className="chart-container">
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              Gráfico de Vendas
              <span className="text-2xl">📈</span>
            </CardTitle>
            <CardDescription>
              Evolução mensal
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-32 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center text-white font-bold">
              Gráfico Interativo
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tabela Financeira */}
      <Card>
        <CardHeader>
          <CardTitle>Tabela Financeira</CardTitle>
          <CardDescription>
            Dados detalhados por período
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full financial-table">
              <thead>
                <tr>
                  <th className="text-left p-3 border-b">Período</th>
                  <th className="text-left p-3 border-b">Receita</th>
                  <th className="text-left p-3 border-b">Custos</th>
                  <th className="text-left p-3 border-b">Lucro</th>
                  <th className="text-left p-3 border-b">Margem</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td className="p-3">Q1 2024</td>
                  <td className="p-3">R$ 580.000</td>
                  <td className="p-3">R$ 420.000</td>
                  <td className="p-3 text-green-600 dark:text-green-400">R$ 160.000</td>
                  <td className="p-3">27.6%</td>
                </tr>
                <tr>
                  <td className="p-3">Q2 2024</td>
                  <td className="p-3">R$ 620.000</td>
                  <td className="p-3">R$ 440.000</td>
                  <td className="p-3 text-green-600 dark:text-green-400">R$ 180.000</td>
                  <td className="p-3">29.0%</td>
                </tr>
                <tr>
                  <td className="p-3">Q3 2024</td>
                  <td className="p-3">R$ 650.000</td>
                  <td className="p-3">R$ 460.000</td>
                  <td className="p-3 text-green-600 dark:text-green-400">R$ 190.000</td>
                  <td className="p-3">29.2%</td>
                </tr>
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Loading Skeleton Demo */}
      <Card>
        <CardHeader>
          <CardTitle>Loading States</CardTitle>
          <CardDescription>
            Skeleton loading em diferentes temas
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="skeleton h-20 rounded-lg"></div>
            <div className="skeleton h-20 rounded-lg"></div>
            <div className="skeleton h-20 rounded-lg"></div>
          </div>
        </CardContent>
      </Card>

      {/* Informações do tema */}
      <Card>
        <CardHeader>
          <CardTitle>Informações do Tema</CardTitle>
          <CardDescription>
            Detalhes sobre a implementação do dark mode
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <strong>Tema Atual:</strong> {theme}
            </div>
            <div>
              <strong>Modo Escuro:</strong> {isDark ? 'Sim' : 'Não'}
            </div>
            <div>
              <strong>Preferência Sistema:</strong> {window.matchMedia('(prefers-color-scheme: dark)').matches ? 'Escuro' : 'Claro'}
            </div>
            <div>
              <strong>Transições:</strong> Ativadas
            </div>
          </div>
          
          <div className="p-4 bg-muted rounded-lg">
            <h4 className="font-semibold mb-2">Classes CSS Disponíveis:</h4>
            <ul className="text-sm space-y-1">
              <li><code>.financial-card</code> - Cards financeiros com gradiente</li>
              <li><code>.kpi-card</code> - Cards de KPIs com sombras</li>
              <li><code>.chart-container</code> - Containers de gráficos</li>
              <li><code>.financial-table</code> - Tabelas financeiras</li>
              <li><code>.skeleton</code> - Estados de loading</li>
            </ul>
          </div>
        </CardContent>
      </Card>
    </div>
  )
} 