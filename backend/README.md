# Backend - Plataforma TAG

## 📁 Estrutura do Projeto

```
backend/
├── main.py                 # Arquivo principal da aplicação
├── requirements.txt        # Dependências Python
├── env.example            # Exemplo de variáveis de ambiente
├── docs/                  # 📚 Documentação do projeto
├── scripts/               # 🔧 Scripts utilitários e migrações
├── tests/                 # 🧪 Arquivos de teste
├── utils/                 # ⚙️ Configurações e utilitários
├── endpoints/             # 🌐 Endpoints da API
├── helpers/               # 🛠️ Funções auxiliares
├── auth/                  # 🔐 Sistema de autenticação
├── database/              # 🗄️ Configurações de banco de dados
└── venv/                  # 🐍 Ambiente virtual Python
```

## 🚀 Como Executar

1. **Ativar ambiente virtual:**
   ```bash
   source venv/bin/activate
   ```

2. **Instalar dependências:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configurar variáveis de ambiente:**
   ```bash
   cp env.example .env
   # Editar .env com suas configurações
   ```

4. **Executar aplicação:**
   ```bash
   python main.py
   ```

## 📚 Documentação

Toda a documentação está organizada na pasta `docs/`:

- **Implementações:** Guias de implementação de funcionalidades
- **Migrações:** Documentação de migrações de banco
- **Refatorações:** Histórico de refatorações realizadas
- **Performance:** Otimizações e melhorias de performance

## 🔧 Scripts Utilitários

Scripts para migração, validação e manutenção na pasta `scripts/`:

- Migração de estruturas de banco
- Validação de dados financeiros
- Recriação de tabelas
- Análise de estruturas Excel

## 🧪 Testes

Arquivos de teste organizados na pasta `tests/`:

- Testes de endpoints
- Testes de conexão
- Validação de estruturas
- Testes de cálculos

## 🌐 Endpoints

API REST organizada na pasta `endpoints/`:

- Dados financeiros
- Autenticação
- Validações
- Relatórios

## 🗄️ Banco de Dados

Configurações e estruturas na pasta `database/`:

- Schemas
- Migrações
- Configurações de conexão

## 🔐 Autenticação

Sistema de autenticação na pasta `auth/`:

- Middleware de autenticação
- Controle de acesso
- Gerenciamento de sessões
