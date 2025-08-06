import { Skeleton } from "@/components/ui/skeleton"
import { Card, CardContent, CardHeader } from "@/components/ui/card"

// Loading Skeleton para KPIs Financeiros
export function KPIsSkeleton() {
  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {Array.from({ length: 4 }).map((_, i) => (
        <Card key={i}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <Skeleton className="h-4 w-[100px]" />
            <Skeleton className="h-4 w-4" />
          </CardHeader>
          <CardContent>
            <Skeleton className="h-8 w-[120px] mb-1" />
            <Skeleton className="h-3 w-[80px]" />
          </CardContent>
        </Card>
      ))}
    </div>
  )
}

// Loading Skeleton para Tabela Financeira
export function FinancialTableSkeleton() {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <Skeleton className="h-6 w-[200px]" />
          <div className="flex gap-2">
            <Skeleton className="h-9 w-[120px]" />
            <Skeleton className="h-9 w-[100px]" />
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {/* Header da tabela */}
          <div className="grid grid-cols-7 gap-4 p-3 border-b">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-full" />
          </div>
          
          {/* Linhas da tabela */}
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="grid grid-cols-7 gap-4 p-3">
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-full" />
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

// Loading Skeleton para Gráficos
export function ChartSkeleton({ height = "300px" }: { height?: string }) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <Skeleton className="h-6 w-[150px]" />
          <Skeleton className="h-4 w-[100px]" />
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Legenda */}
          <div className="flex gap-4">
            <div className="flex items-center gap-2">
              <Skeleton className="h-3 w-3 rounded-full" />
              <Skeleton className="h-3 w-[60px]" />
            </div>
            <div className="flex items-center gap-2">
              <Skeleton className="h-3 w-3 rounded-full" />
              <Skeleton className="h-3 w-[80px]" />
            </div>
          </div>
          
          {/* Área do gráfico */}
          <Skeleton className="w-full" style={{ height }} />
        </div>
      </CardContent>
    </Card>
  )
}

// Loading Skeleton para Dashboard Principal
export function DashboardSkeleton() {
  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <Skeleton className="h-8 w-[200px]" />
        <div className="flex gap-2">
          <Skeleton className="h-10 w-[120px]" />
          <Skeleton className="h-10 w-[100px]" />
        </div>
      </div>

      {/* KPIs */}
      <KPIsSkeleton />

      {/* Charts Row */}
      <div className="grid gap-6 md:grid-cols-2">
        <ChartSkeleton />
        <ChartSkeleton />
      </div>

      {/* Table */}
      <FinancialTableSkeleton />
    </div>
  )
}

// Loading Skeleton para Sidebar
export function SidebarSkeleton() {
  return (
    <div className="space-y-4 p-4">
      {/* User info */}
      <div className="flex items-center gap-3 pb-4 border-b">
        <Skeleton className="h-10 w-10 rounded-full" />
        <div className="space-y-1 flex-1">
          <Skeleton className="h-4 w-[100px]" />
          <Skeleton className="h-3 w-[120px]" />
        </div>
      </div>

      {/* Navigation items */}
      {Array.from({ length: 6 }).map((_, i) => (
        <div key={i} className="flex items-center gap-3 p-2">
          <Skeleton className="h-5 w-5" />
          <Skeleton className="h-4 w-[120px]" />
        </div>
      ))}
    </div>
  )
}

// Loading Skeleton para Lista de Transações
export function TransactionListSkeleton() {
  return (
    <Card>
      <CardHeader>
        <Skeleton className="h-6 w-[180px]" />
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="flex items-center justify-between p-3 border rounded-lg">
              <div className="flex items-center gap-3">
                <Skeleton className="h-10 w-10 rounded-lg" />
                <div className="space-y-1">
                  <Skeleton className="h-4 w-[150px]" />
                  <Skeleton className="h-3 w-[100px]" />
                </div>
              </div>
              <div className="text-right space-y-1">
                <Skeleton className="h-4 w-[80px]" />
                <Skeleton className="h-3 w-[60px]" />
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

// Loading Skeleton para Filtros
export function FiltersSkeleton() {
  return (
    <div className="flex gap-3 p-4 border rounded-lg">
      <Skeleton className="h-10 w-[120px]" />
      <Skeleton className="h-10 w-[100px]" />
      <Skeleton className="h-10 w-[140px]" />
      <Skeleton className="h-10 w-[80px]" />
    </div>
  )
}

// Loading Skeleton Genérico
export function LoadingSkeleton({ 
  lines = 3, 
  showHeader = true,
  className = ""
}: { 
  lines?: number
  showHeader?: boolean
  className?: string 
}) {
  return (
    <div className={`space-y-3 ${className}`}>
      {showHeader && <Skeleton className="h-6 w-[200px]" />}
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton 
          key={i} 
          className={`h-4 ${i === lines - 1 ? 'w-3/4' : 'w-full'}`} 
        />
      ))}
    </div>
  )
}

// Loading Skeleton com Pulse Effect (para dados em tempo real)
export function PulseSkeleton({ children }: { children: React.ReactNode }) {
  return (
    <div className="animate-pulse">
      {children}
    </div>
  )
}

// Loading Overlay para uso em componentes existentes
export function LoadingOverlay({ 
  isLoading, 
  children,
  skeleton 
}: { 
  isLoading: boolean
  children: React.ReactNode
  skeleton?: React.ReactNode
}) {
  if (isLoading) {
    return <>{skeleton || <LoadingSkeleton />}</>
  }
  
  return <>{children}</>
}
