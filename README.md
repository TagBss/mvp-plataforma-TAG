# 🚀 Plataforma TAG

Sistema completo de gestão financeira com backend Python e frontend React.

## 📁 Estrutura do Projeto

```
plataforma-tag/
├── 📚 docs/                    # Documentação geral do projeto
├── 🔧 backend/                 # API Python (FastAPI)
│   ├── 📚 docs/               # Documentação do backend
│   ├── 🔧 scripts/            # Scripts utilitários e migrações
│   ├── 🧪 tests/              # Arquivos de teste
│   ├── ⚙️ utils/              # Configurações e utilitários
│   ├── 🌐 endpoints/           # Endpoints da API
│   ├── 🛠️ helpers/            # Funções auxiliares
│   ├── 🔐 auth/               # Sistema de autenticação
│   └── 🗄️ database/           # Configurações de banco
├── 🎨 frontend/                # Aplicação React + TypeScript
│   ├── 📚 docs/               # Documentação do frontend
│   ├── 📝 src/                # Código fonte
│   └── 🌐 public/             # Arquivos estáticos
├── 🚀 frontend-nextjs/         # Versão Next.js (mantida como está)
├── 📦 node_modules/            # Dependências Node.js
└── 📋 .gitignore              # Arquivos ignorados pelo Git
```

## 🚀 Como Executar

### Backend (Python)

```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

### Frontend (React)

```bash
cd frontend
npm install
npm run dev
```

### Frontend Next.js

```bash
cd frontend-nextjs
npm install
npm run dev
```

## 🛠️ Tecnologias

### Backend
- **Python 3.8+**
- **FastAPI** - Framework web
- **SQLAlchemy** - ORM
- **PostgreSQL** - Banco de dados
- **Pandas** - Manipulação de dados

### Frontend
- **React 18** - Framework JavaScript
- **TypeScript** - Tipagem estática
- **Vite** - Build tool
- **Tailwind CSS** - Framework CSS
- **ESLint** - Linting

## 📚 Documentação

- **📚 docs/** - Documentação geral do projeto
- **🔧 backend/docs/** - Documentação específica do backend
- **🎨 frontend/docs/** - Documentação específica do frontend

## 🔧 Funcionalidades Principais

- 📊 **Gestão Financeira** - DRE, DFC, Cards KPIs e Gráficos
- 🔐 **Autenticação** - Sistema de login seguro
- 📈 **Relatórios** - Análises e dashboards
- 🗄️ **Migração de Dados** - Importação de Excel
- 🌙 **Dark Mode** - Interface adaptável
- 📱 **Responsivo** - Design mobile-first

## 🚀 Deploy

### Backend
```bash
cd backend
pip install -r requirements.txt
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### Frontend
```bash
cd frontend
npm run build
# Servir pasta dist/ com nginx ou similar
```

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 📞 Suporte

Para suporte e dúvidas, abra uma issue no repositório ou entre em contato com a equipe de desenvolvimento.