#!/bin/bash
# 🚀 Script para configurar ambiente de produção da Plataforma TAG

set -e  # Parar em caso de erro

echo "🐳 Configurando ambiente de produção da Plataforma TAG..."
echo "=========================================================="

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para imprimir mensagens coloridas
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verificar se estamos em produção
if [ "$ENVIRONMENT" != "production" ]; then
    print_warning "Este script é para PRODUÇÃO. Tem certeza que deseja continuar?"
    read -p "Digite 'PRODUCTION' para confirmar: " -r
    if [ "$REPLY" != "PRODUCTION" ]; then
        print_error "Deploy cancelado."
        exit 1
    fi
fi

# Verificar se Docker está instalado
print_status "Verificando se Docker está instalado..."
if ! command -v docker &> /dev/null; then
    print_error "Docker não está instalado. Instale o Docker primeiro."
    exit 1
fi

# Verificar se Docker Compose está instalado
print_status "Verificando se Docker Compose está instalado..."
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose não está instalado. Instale o Docker Compose primeiro."
    exit 1
fi

print_success "Docker e Docker Compose estão instalados!"

# Verificar se Docker está rodando
print_status "Verificando se Docker está rodando..."
if ! docker info &> /dev/null; then
    print_error "Docker não está rodando. Inicie o Docker primeiro."
    exit 1
fi

print_success "Docker está rodando!"

# Verificar arquivo .env de produção
if [ ! -f .env.production ]; then
    print_error "Arquivo .env.production não encontrado!"
    print_status "Crie o arquivo .env.production com as configurações de produção."
    exit 1
fi

# Backup do banco de dados (se existir)
if docker-compose ps postgres | grep -q "Up"; then
    print_status "Fazendo backup do banco de dados..."
    timestamp=$(date +"%Y%m%d_%H%M%S")
    docker-compose exec postgres pg_dump -U postgres tag_financeiro > "backup_${timestamp}.sql"
    print_success "Backup criado: backup_${timestamp}.sql"
fi

# Parar containers existentes
print_status "Parando containers existentes..."
docker-compose down

# Construir imagens de produção
print_status "Construindo imagens de produção..."
docker-compose -f docker-compose.yml -f docker-compose.prod.yml build --no-cache

# Iniciar containers de produção
print_status "Iniciando containers de produção..."
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Aguardar serviços estarem prontos
print_status "Aguardando serviços estarem prontos..."
sleep 30

# Verificar saúde dos serviços
print_status "Verificando saúde dos serviços..."

# Testar backend
max_attempts=10
attempt=1
while [ $attempt -le $max_attempts ]; do
    if curl -f http://localhost:8000/health &> /dev/null; then
        print_success "Backend está funcionando!"
        break
    else
        print_status "Tentativa $attempt/$max_attempts - Aguardando backend..."
        sleep 10
        ((attempt++))
    fi
done

if [ $attempt -gt $max_attempts ]; then
    print_error "Backend não respondeu após $max_attempts tentativas!"
    print_status "Verificando logs do backend..."
    docker-compose logs backend
    exit 1
fi

# Testar frontend
max_attempts=10
attempt=1
while [ $attempt -le $max_attempts ]; do
    if curl -f http://localhost:3000 &> /dev/null; then
        print_success "Frontend está funcionando!"
        break
    else
        print_status "Tentativa $attempt/$max_attempts - Aguardando frontend..."
        sleep 10
        ((attempt++))
    fi
done

if [ $attempt -gt $max_attempts ]; then
    print_error "Frontend não respondeu após $max_attempts tentativas!"
    print_status "Verificando logs do frontend..."
    docker-compose logs frontend
    exit 1
fi

# Verificar status final
print_status "Verificando status final dos containers..."
docker-compose ps

echo ""
echo "=========================================================="
print_success "🎉 Ambiente de produção configurado com sucesso!"
echo "=========================================================="
echo ""
echo "🌐 Aplicação disponível em:"
echo "   📱 Frontend:  http://localhost:3000"
echo "   🐍 Backend:   http://localhost:8000"
echo "   📚 Docs API:  http://localhost:8000/docs"
echo ""
echo "📋 Comandos úteis para produção:"
echo "   📊 Ver logs:     docker-compose logs -f"
echo "   🔍 Status:       docker-compose ps"
echo "   🔄 Reiniciar:    docker-compose restart"
echo "   🛑 Parar:        docker-compose down"
echo ""
echo "🔒 Configurações de segurança aplicadas:"
echo "   ✅ Usuários não-root nos containers"
echo "   ✅ Health checks configurados"
echo "   ✅ Volumes persistentes para dados"
echo "   ✅ Network isolada"
echo ""
print_warning "💡 IMPORTANTE: Configure SSL/HTTPS em produção!"
print_warning "💡 Configure backup automático do banco de dados!"

