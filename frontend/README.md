# Frontend - Plataforma TAG

## 📁 Estrutura do Projeto

```
frontend/
├── src/                   # 📝 Código fonte da aplicação
├── public/                # 🌐 Arquivos públicos estáticos
├── dist/                  # 🚀 Build de produção
├── docs/                  # 📚 Documentação do projeto
├── package.json           # 📦 Dependências e scripts
├── package-lock.json      # 🔒 Lock das dependências
├── tsconfig.json          # ⚙️ Configuração TypeScript
├── vite.config.ts         # ⚡ Configuração Vite
├── tailwind.config.js     # 🎨 Configuração Tailwind CSS
├── postcss.config.js      # 🎭 Configuração PostCSS
├── eslint.config.js       # 🔍 Configuração ESLint
└── index.html             # 🏠 Página principal
```

## 🚀 Como Executar

1. **Instalar dependências:**
   ```bash
   npm install
   ```

2. **Executar em desenvolvimento:**
   ```bash
   npm run dev
   ```

3. **Build para produção:**
   ```bash
   npm run build
   ```

4. **Preview da build:**
   ```bash
   npm run preview
   ```

## 🛠️ Tecnologias

- **Framework:** React + TypeScript
- **Build Tool:** Vite
- **Styling:** Tailwind CSS
- **Linting:** ESLint
- **Package Manager:** npm

## 📚 Documentação

Toda a documentação está organizada na pasta `docs/`:

- **Implementações:** Guias de implementação de funcionalidades
- **Autenticação:** Sistema de autenticação
- **Dark Mode:** Implementação de tema escuro
- **Sidebar:** Melhorias na barra lateral
- **User Menu:** Menu do usuário

## 🎨 Componentes

Componentes organizados em `src/components/`:

- Interface de usuário
- Formulários
- Navegação
- Layouts

## 🌐 Páginas

Páginas da aplicação em `src/pages/`:

- Dashboard
- Relatórios
- Configurações
- Autenticação

## 🔧 Utilitários

Funções auxiliares em `src/utils/`:

- Validações
- Formatação
- APIs
- Helpers
