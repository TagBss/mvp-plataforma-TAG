# 🗄️ pgAdmin 4 - Configuração e Uso

## 🚀 Inicialização

### 1. Subir o pgAdmin
```bash
# Subir apenas o pgAdmin
docker-compose up -d pgadmin

# Ou subir todos os serviços
docker-compose up -d
```

### 2. Verificar se está rodando
```bash
# Verificar status
docker-compose ps pgadmin

# Ver logs se necessário
docker-compose logs pgadmin
```

## 🌐 Acesso

- **URL**: http://localhost:5050
- **Email**: admin@tag.com
- **Senha**: admin123
- **Master Password**: admin123

## ⚙️ Configuração do Servidor PostgreSQL

### 1. Primeiro Login
1. Acesse http://localhost:5050
2. **Faça login** com as credenciais acima
3. **Digite a Master Password**: `admin123`
4. Clique em "Add New Server"

### 2. Configuração do Servidor
**General Tab:**
- **Name**: `TAG Financeiro`

**Connection Tab:**
- **Host name/address**: `postgres` (nome do container)
- **Port**: `5432`
- **Database**: `tag_financeiro`
- **Username**: `postgres`
- **Password**: `postgres`

**Advanced Tab (opcional):**
- **DB restriction**: `tag_financeiro` (para mostrar apenas este banco)

### 3. Salvar Conexão
- Clique em "Save"
- O servidor aparecerá no painel esquerdo

## 📊 Funcionalidades Principais

### 1. Navegação
- **Servers** → **TAG Financeiro** → **Databases** → **tag_financeiro**
- **Schemas** → **public** → **Tables/Views**

### 2. Visualização de Dados
- Clique com botão direito em qualquer tabela
- Selecione "View/Edit Data" → "All Rows"
- Use filtros, ordenação e paginação

### 3. Editor de Queries
- Clique no ícone "Query Tool" (⚡)
- Digite suas consultas SQL
- Execute com F5 ou botão "Execute"

### 4. Estrutura do Banco
- **Tables**: Veja colunas, tipos, constraints
- **Views**: Visualize views criadas
- **Indexes**: Monitore performance
- **Functions**: Veja funções SQL

## 🔧 Queries Úteis para seu Projeto

### 1. Ver todas as tabelas
```sql
SELECT table_name, table_type 
FROM information_schema.tables 
WHERE table_schema = 'public'
ORDER BY table_type, table_name;
```

### 2. Ver estrutura da tabela financial_data
```sql
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns 
WHERE table_name = 'financial_data'
ORDER BY ordinal_position;
```

### 3. Estatísticas das tabelas
```sql
SELECT 
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation
FROM pg_stats 
WHERE schemaname = 'public'
ORDER BY tablename, attname;
```

### 4. Ver views existentes
```sql
SELECT viewname, definition
FROM pg_views 
WHERE schemaname = 'public'
ORDER BY viewname;
```

## 🎯 Comparação com sua Interface Atual

| Recurso | Interface Atual | pgAdmin 4 |
|---------|----------------|-----------|
| **Visualização de Dados** | ✅ Básica | ✅ Avançada com filtros |
| **Editor SQL** | ❌ Não | ✅ Completo com syntax highlighting |
| **Estrutura do BD** | ✅ Básica | ✅ Completa com índices |
| **Backup/Restore** | ❌ Manual | ✅ Interface gráfica |
| **Performance** | ❌ Limitada | ✅ Análise de performance |
| **Usuários/Permissões** | ❌ Não | ✅ Gerenciamento completo |
| **Relatórios** | ❌ Não | ✅ Dashboard integrado |
| **Exportação** | ❌ Não | ✅ Múltiplos formatos |

## 🔐 Configuração de Segurança

### **Autenticação Configurada**
O pgAdmin está configurado com:
- ✅ **Login obrigatório**: `admin@tag.com` / `admin123`
- ✅ **Master password**: `admin123` (para operações sensíveis)
- ✅ **Modo servidor**: Ativado para maior segurança
- ✅ **Configuração estável**: Sem erros

### **Credenciais Completas**
- **Email**: `admin@tag.com`
- **Senha**: `admin123`
- **Master Password**: `admin123`

### **Alterar Credenciais (Opcional)**
Para alterar as credenciais, edite o `docker-compose.yml`:
```yaml
environment:
  PGADMIN_DEFAULT_EMAIL: seu_email@tag.com
  PGADMIN_DEFAULT_PASSWORD: sua_senha_segura
  PGADMIN_CONFIG_MASTER_PASSWORD: "'sua_master_password'"
```

## 🚨 Troubleshooting

### 1. pgAdmin não inicia
```bash
# Verificar logs
docker-compose logs pgadmin

# Reiniciar serviço
docker-compose restart pgadmin
```

### 2. Não consegue conectar ao PostgreSQL
- Verifique se o container postgres está rodando: `docker-compose ps postgres`
- Use `postgres` como hostname (não `localhost`)
- Verifique as credenciais no arquivo `.env`

### 3. Erro de permissão
```bash
# Verificar permissões do volume
docker-compose exec pgadmin ls -la /var/lib/pgadmin
```

### 4. Login não funciona
- Limpe o cache do navegador
- Use modo incógnito
- Verifique se o container foi reiniciado após mudanças

### 5. Erro 'auth_source_manager' ou 'NameError'
```bash
# Limpar volume e reiniciar
docker-compose down pgadmin
docker volume rm plataforma-tag_pgadmin_data
docker-compose up -d pgadmin
```

### 6. Master Password não aceita
- Certifique-se de usar: `admin123`
- Se alterou, use a senha que definiu no docker-compose.yml

## 📱 Acesso Mobile
- pgAdmin 4 é responsivo
- Funciona bem em tablets
- Para mobile, considere apps como "Postico" ou "TablePlus"

## 🔒 Segurança
- **Desenvolvimento**: Senha simples está OK
- **Produção**: Altere as credenciais padrão
- **HTTPS**: Configure SSL em produção

## 💡 Dicas de Uso

1. **Favoritos**: Marque queries frequentes como favoritas
2. **Histórico**: Acesse queries anteriores no Query Tool
3. **Atalhos**: Use F5 para executar, Ctrl+Space para autocomplete
4. **Exportação**: Exporte dados em CSV, JSON, SQL
5. **Backup**: Use a interface gráfica para backups automáticos

## 🎉 Próximos Passos

1. ✅ Configure o servidor PostgreSQL
2. 🔍 Explore suas tabelas existentes
3. 📊 Teste queries na sua tabela `financial_data`
4. 🎨 Personalize o dashboard
5. 📚 Explore as views DRE/DFC que você já tem

---

**Agora você tem uma interface profissional e segura para gerenciar seu banco PostgreSQL!** 🚀