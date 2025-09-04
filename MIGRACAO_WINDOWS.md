# 🪟 Guia de Migração para Windows

Este guia contém todas as informações necessárias para migrar o projeto **Plataforma TAG** do Linux/WSL2 para Windows.

## 📋 Pré-requisitos

### 1. **Node.js** (para Frontend)
- **Download**: https://nodejs.org/
- **Versão recomendada**: Node.js 18.x ou superior
- **Verificar instalação**: `node --version` e `npm --version`

### 2. **Python** (para Backend)
- **Download**: https://www.python.org/downloads/
- **Versão recomendada**: Python 3.8 ou superior
- **Verificar instalação**: `python --version` e `pip --version`

### 3. **PostgreSQL** (para Banco de Dados)
- **Download**: https://www.postgresql.org/download/windows/
- **Versão recomendada**: PostgreSQL 14 ou superior
- **Configurar**: Criar banco de dados e usuário conforme configurações do projeto

### 4. **Git** (opcional, mas recomendado)
- **Download**: https://git-scm.com/download/win
- **Para clonar o repositório**: `git clone <url-do-repositorio>`

## 🚀 Instalação e Configuração

### **Frontend React (Vite)**

1. **Navegar para a pasta frontend**:
   ```cmd
   cd frontend
   ```

2. **Instalar dependências**:
   ```cmd
   npm install
   ```

3. **Executar em modo desenvolvimento**:
   ```cmd
   npm run dev
   ```

4. **Acessar**: http://localhost:5173

### **Backend Python (FastAPI)**

1. **Navegar para a pasta backend**:
   ```cmd
   cd backend
   ```

2. **Criar ambiente virtual**:
   ```cmd
   python -m venv venv
   ```

3. **Ativar ambiente virtual**:
   ```cmd
   # Windows CMD
   venv\Scripts\activate
   
   # Windows PowerShell
   venv\Scripts\Activate.ps1
   ```

4. **Instalar dependências**:
   ```cmd
   pip install -r requirements.txt
   ```

5. **Configurar variáveis de ambiente**:
   - Copiar `.env.example` para `.env`
   - Configurar conexão com PostgreSQL
   - Configurar outras variáveis necessárias

6. **Executar servidor**:
   ```cmd
   python main.py
   # ou
   uvicorn main:app --reload
   ```

7. **Acessar**: http://localhost:8000

## 📁 Estrutura de Arquivos

```
plataforma-tag/
├── frontend/                 # Frontend React (Vite)
│   ├── package.json         # Dependências Node.js
│   ├── requirements.txt     # Guia de instalação
│   └── ...
├── backend/                 # Backend Python (FastAPI)
│   ├── requirements.txt     # Dependências Python
│   ├── main.py             # Arquivo principal
│   └── ...
└── MIGRACAO_WINDOWS.md     # Este arquivo
```

## 🔧 Comandos Úteis

### **Frontend**
```cmd
# Instalar dependências
npm install

# Executar em desenvolvimento
npm run dev

# Gerar build de produção
npm run build

# Visualizar build
npm run preview

# Executar linter
npm run lint
```

### **Backend**
```cmd
# Ativar ambiente virtual
venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt

# Executar servidor
python main.py

# Executar com hot reload
uvicorn main:app --reload

# Desativar ambiente virtual
deactivate
```

## 🗄️ Configuração do Banco de Dados

1. **Instalar PostgreSQL** no Windows
2. **Criar banco de dados**:
   ```sql
   CREATE DATABASE plataforma_tag;
   ```
3. **Configurar usuário**:
   ```sql
   CREATE USER tag_user WITH PASSWORD 'sua_senha';
   GRANT ALL PRIVILEGES ON DATABASE plataforma_tag TO tag_user;
   ```
4. **Atualizar arquivo `.env`** no backend com as credenciais

## ⚠️ Possíveis Problemas e Soluções

### **1. Erro de Permissão no PowerShell**
```powershell
# Executar como administrador ou alterar política de execução
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### **2. Porta já em uso**
```cmd
# Verificar processos usando a porta
netstat -ano | findstr :8000
netstat -ano | findstr :5173

# Finalizar processo (substituir PID)
taskkill /PID <numero_do_pid> /F
```

### **3. Problemas com psycopg2**
```cmd
# Instalar dependências do PostgreSQL
pip install psycopg2-binary
```

### **4. Problemas com Node.js**
```cmd
# Limpar cache do npm
npm cache clean --force

# Deletar node_modules e reinstalar
rmdir /s node_modules
npm install
```

## 📝 Checklist de Migração

- [ ] Instalar Node.js
- [ ] Instalar Python
- [ ] Instalar PostgreSQL
- [ ] Clonar/copiar projeto
- [ ] Configurar banco de dados
- [ ] Instalar dependências do frontend (`npm install`)
- [ ] Instalar dependências do backend (`pip install -r requirements.txt`)
- [ ] Configurar variáveis de ambiente
- [ ] Testar frontend (http://localhost:5173)
- [ ] Testar backend (http://localhost:8000)
- [ ] Verificar conexão com banco de dados

## 🆘 Suporte

Em caso de problemas:
1. Verificar logs de erro
2. Confirmar se todas as dependências estão instaladas
3. Verificar configurações de banco de dados
4. Consultar documentação específica de cada tecnologia

---

**✅ Projeto migrado com sucesso para Windows!**
