import { useState, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card'
import { Button } from '../components/ui/button'
import { Input } from '../components/ui/input'
import { Label } from '../components/ui/label'
import { Alert, AlertDescription } from '../components/ui/alert'
import { Loader2, Eye, EyeOff } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import { useToast } from '../components/toast'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  
  const { login, state } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const toast = useToast()

  // Redirecionar se já estiver autenticado
  useEffect(() => {
    if (state.isAuthenticated) {
      const from = location.state?.from?.pathname || '/'
      navigate(from, { replace: true })
    }
  }, [state.isAuthenticated, navigate, location])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!email || !password) {
      toast.error('Por favor, preencha todos os campos')
      return
    }

    try {
      setIsSubmitting(true)
      await login({ email, password })
      toast.success('Login realizado com sucesso!')
      
      // Redirecionar para a página que tentou acessar ou dashboard
      const from = location.state?.from?.pathname || '/'
      navigate(from, { replace: true })
    } catch (error: any) {
      toast.error(error.message || 'Erro ao fazer login')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl text-center">🔐 Login</CardTitle>
          <CardDescription className="text-center">
            Entre com suas credenciais para acessar o sistema
          </CardDescription>
        </CardHeader>
        <CardContent>
          {/* Mensagem de erro */}
          {state.error && (
            <Alert className="mb-4" variant="destructive">
              <AlertDescription>{state.error}</AlertDescription>
            </Alert>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="seu@email.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled={isSubmitting}
                required
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="password">Senha</Label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  disabled={isSubmitting}
                  required
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                  onClick={() => setShowPassword(!showPassword)}
                  disabled={isSubmitting}
                >
                  {showPassword ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </Button>
              </div>
            </div>

            <Button 
              type="submit" 
              className="w-full" 
              disabled={isSubmitting || state.isLoading}
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Entrando...
                </>
              ) : (
                'Entrar'
              )}
            </Button>
          </form>

          {/* Informações adicionais */}
          <div className="mt-6 text-center text-sm text-muted-foreground">
            <p>Demo: admin@tag.com / admin123</p>
            <p className="mt-2">
              Não tem conta?{' '}
              <Button variant="link" className="p-0 h-auto">
                Solicitar acesso
              </Button>
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
} 