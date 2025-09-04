# 🎯 DSP + Deploy Guide - Plataforma TAG

## 📋 **Visão Geral**

Este guia implementa a estrutura **DSP (Development, Staging, Production)** com deploy automatizado para a Plataforma TAG.

## 🏗️ **Estrutura de Ambientes**

### **1. 🏠 Development (Local)**
- **Objetivo**: Desenvolvimento local
- **Dados**: Mock/Teste
- **Debug**: Ativo
- **Portas**: 
  - Frontend: 5173
  - Backend: 8000
  - Database: 5432
  - Redis: 6379
  - pgAdmin: 5050

### **2. 🧪 Staging (Teste)**
- **Objetivo**: Teste antes da produção
- **Dados**: Cópia da produção
- **Debug**: Desativado
- **Portas**:
  - Frontend: 5174
  - Backend: 8001
  - Database: 5433
  - Redis: 6380
  - pgAdmin: 5051

### **3. 🚀 Production (Vercel + Render)**
- **Objetivo**: Ambiente de produção
- **Dados**: Dados reais
- **Debug**: Desativado
- **Deploy**: Automático via GitHub

## 🚀 **Como Usar**

### **Gerenciamento de Ambientes**

```bash
# Ver ajuda
./scripts/manage-environments.sh help

# Iniciar ambiente de desenvolvimento
./scripts/manage-environments.sh start dev

# Iniciar ambiente de staging
./scripts/manage-environments.sh start staging

# Iniciar ambiente de produção
./scripts/manage-environments.sh start prod

# Ver status de todos os ambientes
./scripts/manage-environments.sh status all

# Ver logs de um ambiente
./scripts/manage-environments.sh logs dev

# Parar ambiente
./scripts/manage-environments.sh stop dev

# Limpar ambiente (remove containers e volumes)
./scripts/manage-environments.sh clean dev
```

### **Deploy Individual**

```bash
# Deploy para desenvolvimento
./scripts/deploy-dev.sh

# Deploy para staging
./scripts/deploy-staging.sh

# Deploy para produção
./scripts/deploy-production.sh
```

## 🔧 **Configuração de Ambientes**

### **Variáveis de Ambiente**

Cada ambiente tem seu arquivo de configuração:

- **Development**: `env.development`
- **Staging**: `env.staging`
- **Production**: `env.production`

### **Docker Compose**

- **Development**: `docker-compose.dev.yml`
- **Staging**: `docker-compose.staging.yml`
- **Production**: `docker-compose.production.yml`

## 🌐 **URLs de Acesso**

### **Development**
- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs
- pgAdmin: http://localhost:5050

### **Staging**
- Frontend: http://localhost:5174
- Backend: http://localhost:8001
- API Docs: http://localhost:8001/docs
- pgAdmin: http://localhost:5051

### **Production**
- Frontend: https://seu-frontend.vercel.app
- Backend: https://seu-backend.onrender.com
- API Docs: https://seu-backend.onrender.com/docs

## 🔄 **Fluxo de Deploy**

### **1. Desenvolvimento**
```bash
# Desenvolvedor trabalha localmente
git checkout -b feature/nova-funcionalidade
./scripts/manage-environments.sh start dev
# Desenvolve e testa
```

### **2. Staging**
```bash
# Merge para branch main
git checkout main
git merge feature/nova-funcionalidade
./scripts/manage-environments.sh start staging
# Testa em ambiente similar à produção
```

### **3. Production**
```bash
# Deploy automático via GitHub
git tag v1.2.0
git push origin v1.2.0
# Vercel + Render fazem deploy automático
```

## 🔐 **Configuração de Segurança**

### **Development**
- Senhas padrão (não seguras)
- CORS liberado para localhost
- Debug ativo

### **Staging**
- Senhas intermediárias
- CORS limitado
- Debug desativado

### **Production**
- Senhas fortes obrigatórias
- CORS restrito aos domínios de produção
- Debug desativado
- SSL obrigatório

## 📊 **Monitoramento**

### **Health Checks**
- Backend: `/health`
- Frontend: `/`
- Database: `pg_isready`
- Redis: `ping`

### **Logs**
```bash
# Ver logs de um ambiente
./scripts/manage-environments.sh logs dev

# Ver logs específicos
docker-compose -f docker-compose.dev.yml logs -f backend
```

## 🗄️ **Backup e Restore**

### **Backup**
```bash
# Backup do banco de dados
./scripts/backup-db.sh production
```

### **Restore**
```bash
# Restore do banco de dados
docker-compose exec -T postgres psql -U postgres -d tag_financeiro < backup.sql
```

## 🚨 **Troubleshooting**

### **Problemas Comuns**

1. **Container não inicia**
   ```bash
   # Ver logs
   ./scripts/manage-environments.sh logs dev
   
   # Verificar status
   ./scripts/manage-environments.sh status dev
   ```

2. **Porta já em uso**
   ```bash
   # Parar ambiente
   ./scripts/manage-environments.sh stop dev
   
   # Verificar processos
   lsof -i :8000
   ```

3. **Banco de dados não conecta**
   ```bash
   # Verificar se PostgreSQL está rodando
   docker-compose -f docker-compose.dev.yml exec postgres pg_isready -U postgres
   ```

### **Limpeza Completa**
```bash
# Limpar todos os ambientes
./scripts/manage-environments.sh clean all

# Limpar Docker completamente
docker system prune -a --volumes
```

## 📝 **Checklist de Deploy**

### **Antes do Deploy**
- [ ] Código testado localmente
- [ ] Testes passando
- [ ] Variáveis de ambiente configuradas
- [ ] Backup do banco criado

### **Deploy para Staging**
- [ ] Merge para branch main
- [ ] Deploy para staging
- [ ] Testes em staging
- [ ] Validação completa

### **Deploy para Production**
- [ ] Aprovação dos testes de staging
- [ ] Tag de versão criada
- [ ] Deploy automático via GitHub
- [ ] Monitoramento pós-deploy

## 🎯 **Próximos Passos**

1. **CI/CD**: Configurar GitHub Actions
2. **Monitoramento**: Implementar Sentry/LogRocket
3. **SSL**: Configurar certificados
4. **CDN**: Otimizar performance
5. **Backup**: Automatizar backups

## 📞 **Suporte**

Para dúvidas ou problemas:
1. Verificar logs: `./scripts/manage-environments.sh logs [env]`
2. Verificar status: `./scripts/manage-environments.sh status [env]`
3. Limpar ambiente: `./scripts/manage-environments.sh clean [env]`
4. Reiniciar: `./scripts/manage-environments.sh restart [env]`
