import * as React from "react"
import { useState, useEffect } from "react"
import { Link, useLocation } from "react-router-dom"
import {
  AudioWaveform,
  BookOpen,
  BotMessageSquare,
  ChevronLeft,
  ChevronRight,
  Command,
  Frame,
  GalleryVerticalEnd,
  Gauge,
  Home,
  LayoutDashboard,
  LayoutList,
  LogOut,
  Map,
  Menu,
  Package,
  PieChart,
  Settings2,
  TvMinimal,
  X,
} from "lucide-react"
import { cn } from "../lib/utils"
import { Button } from "./ui/button"
import { ModeToggle } from "./mode-toggle"
import { UserMenu } from "./UserMenu"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "./ui/tooltip"

interface MenuItem {
  title: string
  url: string
  icon: React.ComponentType<{ className?: string }>
  isActive?: boolean
  items?: { title: string; url: string }[]
}

const menuItems: MenuItem[] = [
  {
    title: "Dashboard",
    url: "/",
    icon: Gauge,
    items: [
      { title: "Financeiro", url: "/financeiro" },
      { title: "Competência", url: "/competencia" },
    ],
  },
  {
    title: "Demonstrativos",
    url: "#",
    icon: LayoutList,
    items: [
      { title: "DFC", url: "/demonstrativos/dfc" },
      { title: "DRE", url: "/demonstrativos/dre" },
    ],
  },
  {
    title: "TAG View",
    url: "#",
    icon: BotMessageSquare,
    items: [
      { title: "Relatório IA", url: "/relatorio-ia" },
    ],
  },
]

// Hook para detectar mobile
function useIsMobile() {
  const [isMobile, setIsMobile] = useState(false)

  useEffect(() => {
    const checkIsMobile = () => {
      setIsMobile(window.innerWidth < 768) // md breakpoint
    }

    checkIsMobile()
    window.addEventListener('resize', checkIsMobile)
    return () => window.removeEventListener('resize', checkIsMobile)
  }, [])

  return isMobile
}

interface SimpleSidebarProps {
  className?: string
}

export function SimpleSidebar({ className }: SimpleSidebarProps) {
  const [isExpanded, setIsExpanded] = useState(true)
  const [isMobileOpen, setIsMobileOpen] = useState(false)
  const location = useLocation()
  const isMobile = useIsMobile()

  // Fechar sidebar mobile quando mudar de rota
  useEffect(() => {
    if (isMobile) {
      setIsMobileOpen(false)
    }
  }, [location.pathname, isMobile])

  const toggleSidebar = () => {
    if (isMobile) {
      setIsMobileOpen(!isMobileOpen)
    } else {
      const newState = !isExpanded
      setIsExpanded(newState)
      // Emitir evento para sincronizar com o layout
      window.dispatchEvent(new CustomEvent('sidebar-toggle', { 
        detail: { expanded: newState } 
      }))
    }
  }

  const closeMobileSidebar = () => {
    if (isMobile) {
      setIsMobileOpen(false)
    }
  }

  // Mobile: Botão flutuante para abrir sidebar
  if (isMobile) {
    return (
      <TooltipProvider delayDuration={300}>
        {/* Botão toggle mobile */}
        <Button
          variant="outline"
          size="icon"
          className="fixed top-4 left-4 z-50 h-10 w-10 shadow-lg md:hidden"
          onClick={toggleSidebar}
        >
          <Menu className="h-5 w-5" />
        </Button>

        {/* Overlay */}
        {isMobileOpen && (
          <div 
            className="fixed inset-0 z-40 bg-black/50 md:hidden"
            onClick={closeMobileSidebar}
          />
        )}

        {/* Sidebar mobile */}
        <aside
          className={cn(
            "fixed inset-y-0 left-0 z-50 w-64 bg-background border-r transform transition-transform duration-300 ease-in-out md:hidden",
            isMobileOpen ? "translate-x-0" : "-translate-x-full",
            className
          )}
        >
          {/* Header mobile */}
          <div className="flex h-16 items-center justify-between px-4 border-b">
            <div className="flex items-center gap-2">
              <Package className="h-6 w-6 text-primary" />
              <span className="font-semibold text-lg">TAG BSS</span>
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={closeMobileSidebar}
              className="h-8 w-8"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>

          {/* Navigation mobile */}
          <nav className="flex-1 space-y-2 p-4 overflow-y-auto">
            {menuItems.map((item) => {
              const Icon = item.icon
              const isActiveSection = item.items?.some(subItem => 
                location.pathname === subItem.url
              ) || location.pathname === item.url

              return (
                <div key={item.title} className="space-y-1">
                  <div className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-muted-foreground">
                    <Icon className="h-4 w-4" />
                    {item.title}
                  </div>
                  {item.items && (
                    <div className="ml-7 space-y-1">
                      {item.items.map((subItem) => (
                        <Link
                          key={subItem.url}
                          to={subItem.url}
                          onClick={closeMobileSidebar}
                          className={cn(
                            "block rounded-md px-3 py-2 text-sm transition-colors",
                            location.pathname === subItem.url
                              ? "bg-primary text-primary-foreground"
                              : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                          )}
                        >
                          {subItem.title}
                        </Link>
                      ))}
                    </div>
                  )}
                </div>
              )
            })}
          </nav>

          {/* Footer mobile */}
          <div className="border-t p-4">
            <div className="flex items-center justify-center mb-4">
              <ModeToggle />
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-center">
                <UserMenu />
              </div>
            </div>
          </div>
        </aside>
      </TooltipProvider>
    )
  }

  // Desktop: Sidebar fixa

  // Desktop: Sidebar fixa
  return (
    <TooltipProvider delayDuration={300}>
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-30 hidden md:flex flex-col border-r bg-background transition-all duration-300 ease-in-out",
          isExpanded ? "w-64" : "w-16",
          className
        )}
      >
        {/* Header */}
        <div className="flex h-16 items-center justify-between px-4 border-b">
          {isExpanded && (
            <div className="flex items-center gap-2">
              <Package className="h-6 w-6 text-primary" />
              <span className="font-semibold text-lg">TAG BSS</span>
            </div>
          )}
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleSidebar}
            className="h-8 w-8"
          >
            {isExpanded ? (
              <ChevronLeft className="h-4 w-4" />
            ) : (
              <ChevronRight className="h-4 w-4" />
            )}
          </Button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 space-y-2 p-4 overflow-y-auto">
          {menuItems.map((item) => {
            const Icon = item.icon
            const isActiveSection = item.items?.some(subItem => 
              location.pathname === subItem.url
            ) || location.pathname === item.url

            return (
              <div key={item.title}>
                {isExpanded ? (
                  <div className="space-y-1">
                    <div className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-muted-foreground">
                      <Icon className="h-4 w-4" />
                      {item.title}
                    </div>
                    {item.items && (
                      <div className="ml-7 space-y-1">
                        {item.items.map((subItem) => (
                          <Link
                            key={subItem.url}
                            to={subItem.url}
                            className={cn(
                              "block rounded-md px-3 py-2 text-sm transition-colors",
                              location.pathname === subItem.url
                                ? "bg-primary text-primary-foreground"
                                : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                            )}
                          >
                            {subItem.title}
                          </Link>
                        ))}
                      </div>
                    )}
                  </div>
                ) : (
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <div
                        className={cn(
                          "flex h-10 w-10 items-center justify-center rounded-lg transition-colors cursor-pointer",
                          isActiveSection
                            ? "bg-primary text-primary-foreground"
                            : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                        )}
                      >
                        <Icon className="h-5 w-5" />
                      </div>
                    </TooltipTrigger>
                    <TooltipContent side="right" className="font-medium">
                      <div>
                        <div className="font-semibold">{item.title}</div>
                        {item.items && (
                          <div className="mt-1 space-y-1">
                            {item.items.map((subItem) => (
                              <Link
                                key={subItem.url}
                                to={subItem.url}
                                className="block text-xs hover:underline"
                              >
                                {subItem.title}
                              </Link>
                            ))}
                          </div>
                        )}
                      </div>
                    </TooltipContent>
                  </Tooltip>
                )}
              </div>
            )
          })}
        </nav>

        {/* Footer */}
        <div className="border-t p-4">
          <div className="flex items-center justify-center">
            <ModeToggle />
          </div>
          {isExpanded && (
            <div className="mt-4 space-y-2">
              <div className="flex items-center justify-center">
                <UserMenu />
              </div>
            </div>
          )}
        </div>
      </aside>
    </TooltipProvider>
  )
}

// Layout wrapper que adiciona a margem apropriada apenas no desktop
interface SimpleSidebarLayoutProps {
  children: React.ReactNode
  sidebarExpanded?: boolean
}

export function SimpleSidebarLayout({ 
  children, 
  sidebarExpanded = true 
}: SimpleSidebarLayoutProps) {
  const [isExpanded, setIsExpanded] = useState(sidebarExpanded)
  const isMobile = useIsMobile()

  // Sincronizar com o estado da sidebar no desktop
  React.useEffect(() => {
    if (!isMobile) {
      const handleSidebarToggle = (event: CustomEvent) => {
        setIsExpanded(event.detail.expanded)
      }

      window.addEventListener('sidebar-toggle', handleSidebarToggle as EventListener)
      return () => {
        window.removeEventListener('sidebar-toggle', handleSidebarToggle as EventListener)
      }
    }
  }, [isMobile])

  return (
    <div className="flex min-h-screen">
      <SimpleSidebar />
      <main 
        className={cn(
          "flex-1 transition-all duration-300 ease-in-out",
          // Margem apenas no desktop, no mobile o conteúdo ocupa tela toda
          !isMobile && (isExpanded ? "md:ml-64" : "md:ml-16")
        )}
      >
        {children}
      </main>
    </div>
  )
}
