import React from 'react'
import { useAuth } from '../contexts/AuthContext'
import { Button } from './ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from './ui/dropdown-menu'
import { Avatar, AvatarFallback } from './ui/avatar'
import { LogOut, User, Settings, Shield } from 'lucide-react'
import { useToast } from './toast'

export function UserMenu() {
  const { state, logout } = useAuth()
  const toast = useToast()

  const handleLogout = () => {
    logout()
    toast.success('Logout realizado com sucesso!')
  }

  if (!state.isAuthenticated || !state.user) {
    return null
  }

  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map(word => word.charAt(0))
      .join('')
      .toUpperCase()
      .slice(0, 2)
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" className="relative h-8 w-8 rounded-full">
          <Avatar className="h-8 w-8">
            <AvatarFallback>
              {getInitials(state.user.username)}
            </AvatarFallback>
          </Avatar>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent className="w-56" align="end" forceMount>
        <DropdownMenuLabel className="font-normal">
          <div className="flex flex-col space-y-1">
            <p className="text-sm font-medium leading-none">
              {state.user.username}
            </p>
            <p className="text-xs leading-none text-muted-foreground">
              {state.user.email}
            </p>
          </div>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        
        {/* Roles do usuário */}
        <DropdownMenuItem disabled>
          <Shield className="mr-2 h-4 w-4" />
          <span className="text-xs">
            {state.user.roles.join(', ')}
          </span>
        </DropdownMenuItem>
        
        <DropdownMenuSeparator />
        
        <DropdownMenuItem>
          <User className="mr-2 h-4 w-4" />
          <span>Perfil</span>
        </DropdownMenuItem>
        
        <DropdownMenuItem>
          <Settings className="mr-2 h-4 w-4" />
          <span>Configurações</span>
        </DropdownMenuItem>
        
        <DropdownMenuSeparator />
        
        <DropdownMenuItem onClick={handleLogout}>
          <LogOut className="mr-2 h-4 w-4" />
          <span>Sair</span>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

// Componente simples para mostrar apenas o nome do usuário
export function UserInfo() {
  const { state } = useAuth()

  if (!state.isAuthenticated || !state.user) {
    return null
  }

  return (
    <div className="flex items-center space-x-2 text-sm">
      <span className="text-muted-foreground">Olá,</span>
      <span className="font-medium">{state.user.username}</span>
    </div>
  )
} 