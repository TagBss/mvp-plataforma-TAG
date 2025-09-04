# 🐳 Plataforma TAG - Docker Setup

Este documento explica como configurar e executar a Plataforma TAG usando Docker.

## 📋 **Pré-requisitos**

- **Docker** 20.10+ instalado
- **Docker Compose** 2.0+ instalado
- **Git** para clonar o repositório
- **8GB RAM** mínimo recomendado
- **10GB** espaço em disco livre

## 🚀 **Configuração Rápida**

### **1. Primeira Execução**

```bash
# Clone o repositório
git clone <seu-repositorio>
cd plataforma-tag

# Torne os scripts executáveis
chmod +x scripts/*.sh

# Configure o ambiente de desenvolvimento
./scripts/setup-dev.sh
```

### **2. Acessar a Aplicação**

Após a configuração, acesse:

- **📱 Frontend**: http://localhost:3000
- **🐍 Backend**: http://localhost:8000
- **📚 API Docs**: http://localhost:8000/docs
- **🗄️ PostgreSQL**: localhost:5432
- **🔴 Redis**: localhost:6379

## 🏗️ **Arquitetura dos Containers**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   PostgreSQL    │
│   (React)       │◄──►│   (FastAPI)     │◄──►│   (Database)    │
│   Port: 3000    │    │   Port: 8000    │    │   Port: 5432    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │     Redis       │
                    │    (Cache)      │
                    │   Port: 6379    │
                    └─────────────────┘
```

## 📁 **Estrutura de Arquivos Docker**

```
plataforma-tag/
├── 🐳 docker-compose.yml          # Orquestração principal
├── 📝 env.example                 # Exemplo de variáveis
├── 📝 .env                        # Suas variáveis (criado automaticamente)
├── 📁 backend/
│   ├── 🐳 Dockerfile              # Container do backend
│   └── 📝 .dockerignore           # Arquivos ignorados
├── 📁 frontend/
│   ├── 🐳 Dockerfile              # Container do frontend
│   └── 📝 .dockerignore           # Arquivos ignorados
├── 📁 nginx/
│   └── 🌐 nginx.conf              # Configuração do proxy
└── 📁 scripts/
    ├── 🚀 setup-dev.sh            # Setup desenvolvimento
    ├── 🚀 setup-prod.sh           # Setup produção
    └── 💾 backup-db.sh            # Backup do banco
```

## 🛠️ **Comandos Úteis**

### **Desenvolvimento**

```bash
# Iniciar todos os serviços
docker-compose up -d

# Ver logs em tempo real
docker-compose logs -f

# Ver logs de um serviço específico
docker-compose logs -f backend
docker-compose logs -f frontend

# Parar todos os serviços
docker-compose down

# Reiniciar um serviço
docker-compose restart backend

# Reconstruir e iniciar
docker-compose up --build -d
```

### **Debug e Manutenção**

```bash
# Acessar container do backend
docker-compose exec backend bash

# Acessar container do frontend
docker-compose exec frontend sh

# Acessar banco PostgreSQL
docker-compose exec postgres psql -U postgres -d tag_financeiro

# Ver status dos containers
docker-compose ps

# Ver uso de recursos
docker stats
```

### **Backup e Restore**

```bash
# Fazer backup do banco
./scripts/backup-db.sh

# Listar backups
ls -la backups/

# Restaurar backup (manual)
docker-compose exec -T postgres psql -U postgres -d tag_financeiro < backup.sql
```

## 🔧 **Configurações de Ambiente**

### **Variáveis Importantes**

Edite o arquivo `.env` para configurar:

```env
# Banco de dados
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/tag_financeiro

# Redis
REDIS_URL=redis://redis:6379

# API
VITE_API_URL=http://localhost:8000

# Segurança (IMPORTANTE em produção)
JWT_SECRET_KEY=sua_chave_secreta_muito_segura
```

### **Portas Personalizadas**

Para alterar as portas, edite o `docker-compose.yml`:

```yaml
services:
  backend:
    ports:
      - "8080:8000"  # Backend na porta 8080
  frontend:
    ports:
      - "3001:3000"  # Frontend na porta 3001
```

## 🚀 **Deploy em Produção**

### **1. Preparar Ambiente**

```bash
# Criar arquivo de produção
cp env.example .env.production

# Editar variáveis de produção
nano .env.production
```

### **2. Deploy**

```bash
# Executar script de produção
./scripts/setup-prod.sh
```

### **3. Configurações de Produção**

- ✅ Configure SSL/HTTPS
- ✅ Use senhas seguras
- ✅ Configure backup automático
- ✅ Configure monitoramento
- ✅ Use domínio personalizado

## 🐛 **Solução de Problemas**

### **Container não inicia**

```bash
# Ver logs detalhados
docker-compose logs [nome-do-serviço]

# Verificar status
docker-compose ps

# Reconstruir container
docker-compose build --no-cache [nome-do-serviço]
```

### **Banco de dados não conecta**

```bash
# Verificar se PostgreSQL está rodando
docker-compose exec postgres pg_isready -U postgres

# Verificar logs do banco
docker-compose logs postgres

# Reiniciar banco
docker-compose restart postgres
```

### **Frontend não carrega**

```bash
# Verificar logs do frontend
docker-compose logs frontend

# Verificar se backend está respondendo
curl http://localhost:8000/health

# Reinstalar dependências
docker-compose exec frontend npm install
```

### **Problemas de permissão**

```bash
# Corrigir permissões dos volumes
sudo chown -R $USER:$USER .

# Limpar volumes
docker-compose down -v
```

## 📊 **Monitoramento**

### **Health Checks**

Todos os serviços têm health checks configurados:

```bash
# Verificar saúde dos serviços
docker-compose ps

# Status detalhado
docker inspect [container-name] | grep Health -A 10
```

### **Logs**

```bash
# Logs em tempo real
docker-compose logs -f

# Logs com timestamp
docker-compose logs -f -t

# Logs de erro apenas
docker-compose logs --tail=100 | grep ERROR
```

## 🔒 **Segurança**

### **Configurações Aplicadas**

- ✅ Usuários não-root nos containers
- ✅ Network isolada
- ✅ Volumes persistentes
- ✅ Health checks
- ✅ Rate limiting (nginx)
- ✅ Headers de segurança

### **Recomendações para Produção**

- 🔐 Use senhas fortes
- 🔐 Configure SSL/HTTPS
- 🔐 Atualize dependências regularmente
- 🔐 Configure firewall
- 🔐 Monitore logs de segurança

## 📈 **Performance**

### **Otimizações Incluídas**

- 🚀 Multi-stage builds
- 🚀 Cache de dependências
- 🚀 Compressão gzip
- 🚀 Cache de arquivos estáticos
- 🚀 Connection pooling

### **Monitoramento de Recursos**

```bash
# Ver uso de CPU e memória
docker stats

# Ver uso de disco
docker system df

# Limpar recursos não utilizados
docker system prune -f
```

## 🤝 **Contribuição**

### **Para Desenvolvedores**

1. Clone o repositório
2. Execute `./scripts/setup-dev.sh`
3. Faça suas alterações
4. Teste com `docker-compose up --build`
5. Commit suas alterações

### **Estrutura de Branches**

- `main`: Produção
- `develop`: Desenvolvimento
- `feature/*`: Novas funcionalidades
- `hotfix/*`: Correções urgentes

## 📞 **Suporte**

### **Comandos de Emergência**

```bash
# Parar tudo e limpar
docker-compose down -v --remove-orphans
docker system prune -af

# Restaurar do backup
./scripts/backup-db.sh
```

### **Contatos**

- 📧 Email: suporte@plataforma-tag.com
- 💬 Slack: #plataforma-tag
- 🐛 Issues: GitHub Issues

---

## 📚 **Recursos Adicionais**

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Reference](https://docs.docker.com/compose/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://reactjs.org/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

---

**🎉 Parabéns! Sua aplicação está virtualizada e pronta para a equipe!**

