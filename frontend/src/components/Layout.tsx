import React from 'react'

interface LayoutProps {
  children: React.ReactNode
}

export function Layout({ children }: LayoutProps) {
  return (
    <div className="min-h-screen bg-background">
      <div className="flex">
        {/* Sidebar simples temporário */}
        <aside className="w-64 bg-muted/40 border-r">
          <div className="p-4">
            <h2 className="text-lg font-semibold">Plataforma TAG</h2>
            <nav className="mt-4 space-y-2">
              <a href="/dashboard" className="block px-2 py-1 rounded hover:bg-muted">
                Dashboard
              </a>
              <a href="/dre" className="block px-2 py-1 rounded hover:bg-muted">
                DRE
              </a>
              <a href="/dfc" className="block px-2 py-1 rounded hover:bg-muted">
                DFC
              </a>
            </nav>
          </div>
        </aside>
        
        {/* Content */}
        <main className="flex-1">
          {children}
        </main>
      </div>
    </div>
  )
} 