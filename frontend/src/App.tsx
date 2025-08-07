import './App.css'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import Login from './pages/Login'
import Competencia from './pages/Competencia'
import DrePage from './pages/DrePage'
import DfcPage from './pages/DfcPage'
import RelatorioIA from './pages/RelatorioIA'
import { ThemeProvider } from './components/ThemeProvider'
import { SimpleSidebarLayout } from './components/simple-sidebar'
import TestConnection from './components/TestConnection'
import DebugPanel from './components/DebugPanel'
import DataStructureDebug from './components/DataStructureDebug'
import SimpleTest from './components/SimpleTest'
import TimeoutTest from './components/TimeoutTest'
import DashFinanceiro from './components/kpis-financeiro'
import { ErrorBoundary } from './components/error-boundary'
import { ToastProvider } from './components/toast'
import { DarkModeDemo } from './components/dark-mode-demo'
import { AuthProvider } from './contexts/AuthContext'
import { ProtectedRoute } from './components/ProtectedRoute'

// Layout component for pages with sidebar
function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <ErrorBoundary>
      <SimpleSidebarLayout>
        {children}
      </SimpleSidebarLayout>
    </ErrorBoundary>
  )
}

function App() {
  return (
    <ErrorBoundary>
      <ToastProvider>
        <AuthProvider>
          <ThemeProvider
            attribute="class"
            defaultTheme="system"
            enableSystem
            disableTransitionOnChange
          >
            <Router>
              <Routes>
                {/* Rotas públicas */}
                <Route path="/login" element={<Login />} />
                <Route path="/test" element={<TestConnection />} />
                <Route path="/debug" element={<DebugPanel />} />
                <Route path="/data-debug" element={<DataStructureDebug />} />
                <Route path="/simple-test" element={<SimpleTest />} />
                <Route path="/timeout-test" element={<TimeoutTest />} />
                <Route path="/dark-mode-demo" element={<DarkModeDemo />} />
                
                {/* Rotas protegidas */}
                <Route path="/financeiro" element={
                  <ProtectedRoute>
                    <AppLayout>
                      <DashFinanceiro />
                    </AppLayout>
                  </ProtectedRoute>
                } />
                <Route path="/" element={
                  <ProtectedRoute>
                    <AppLayout>
                      <Dashboard />
                    </AppLayout>
                  </ProtectedRoute>
                } />
                <Route path="/competencia" element={
                  <ProtectedRoute>
                    <AppLayout>
                      <Competencia />
                    </AppLayout>
                  </ProtectedRoute>
                } />
                <Route path="/demonstrativos/dre" element={
                  <ProtectedRoute requiredPermission="read:dre">
                    <AppLayout>
                      <DrePage />
                    </AppLayout>
                  </ProtectedRoute>
                } />
                <Route path="/demonstrativos/dfc" element={
                  <ProtectedRoute requiredPermission="read:dfc">
                    <AppLayout>
                      <DfcPage />
                    </AppLayout>
                  </ProtectedRoute>
                } />
                <Route path="/relatorio-ia" element={
                  <ProtectedRoute requiredPermission="read:reports">
                    <AppLayout>
                      <RelatorioIA />
                    </AppLayout>
                  </ProtectedRoute>
                } />
                
                {/* Redirecionamento padrão */}
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </Router>
          </ThemeProvider>
        </AuthProvider>
      </ToastProvider>
    </ErrorBoundary>
  )
}

export default App