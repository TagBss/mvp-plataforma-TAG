#!/bin/bash
# 🚀 Script para configurar ambiente de desenvolvimento da Plataforma TAG

set -e  # Parar em caso de erro

echo "🐳 Configurando ambiente de desenvolvimento da Plataforma TAG..."
echo "================================================================"

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

# Verificar se Docker está instalado
print_status "Verificando se Docker está instalado..."
if ! command -v docker &> /dev/null; then
    print_error "Docker não está instalado. Instale o Docker primeiro."
    echo "📥 Instruções de instalação: https://docs.docker.com/get-docker/"
    exit 1
fi

# Verificar se Docker Compose está instalado
print_status "Verificando se Docker Compose está instalado..."
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose não está instalado. Instale o Docker Compose primeiro."
    echo "📥 Instruções de instalação: https://docs.docker.com/compose/install/"
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

# Criar arquivo .env se não existir
if [ ! -f .env ]; then
    print_status "Criando arquivo .env..."
    cp env.example .env
    print_success "Arquivo .env criado! Configure as variáveis conforme necessário."
    print_warning "IMPORTANTE: Altere as senhas padrão em produção!"
else
    print_status "Arquivo .env já existe."
fi

# Parar containers existentes
print_status "Parando containers existentes..."
docker-compose down --remove-orphans

# Limpar imagens antigas (opcional)
read -p "Deseja limpar imagens Docker antigas? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_status "Limpando imagens antigas..."
    docker system prune -f
fi

# Construir e iniciar containers
print_status "Construindo e iniciando containers..."
docker-compose up --build -d

# Aguardar banco estar pronto
print_status "Aguardando banco de dados estar pronto..."
sleep 15

# Verificar se os containers estão rodando
print_status "Verificando status dos containers..."
docker-compose ps

# Executar migrações do banco (se existirem)
if [ -f "backend/scripts/migrate_excel_data.py" ]; then
    print_status "Executando migrações do banco..."
    docker-compose exec backend python scripts/migrate_excel_data.py migrate || print_warning "Migrações não executadas (normal se não existirem)"
fi

# Verificar saúde dos serviços
print_status "Verificando saúde dos serviços..."
sleep 10

# Testar backend
if curl -f http://localhost:8000/health &> /dev/null; then
    print_success "Backend está funcionando!"
else
    print_warning "Backend pode não estar totalmente pronto ainda."
fi

# Testar frontend
if curl -f http://localhost:3000 &> /dev/null; then
    print_success "Frontend está funcionando!"
else
    print_warning "Frontend pode não estar totalmente pronto ainda."
fi

echo ""
echo "================================================================"
print_success "🎉 Ambiente de desenvolvimento configurado com sucesso!"
echo "================================================================"
echo ""
echo "🌐 Acesse a aplicação em:"
echo "   📱 Frontend:  http://localhost:3000"
echo "   🐍 Backend:   http://localhost:8000"
echo "   📚 Docs API:  http://localhost:8000/docs"
echo "   🗄️ PostgreSQL: localhost:5432"
echo "   🔴 Redis:     localhost:6379"
echo ""
echo "📋 Comandos úteis:"
echo "   📊 Ver logs:     docker-compose logs -f"
echo "   🛑 Parar:        docker-compose down"
echo "   🔄 Reiniciar:    docker-compose restart"
echo "   🧹 Limpar tudo:  docker-compose down -v --remove-orphans"
echo "   🔍 Status:       docker-compose ps"
echo ""
echo "🐛 Para debug:"
echo "   🐍 Backend:      docker-compose exec backend bash"
echo "   ⚛️ Frontend:     docker-compose exec frontend sh"
echo "   🗄️ PostgreSQL:   docker-compose exec postgres psql -U postgres -d tag_financeiro"
echo ""
print_warning "💡 Dica: Use 'docker-compose logs -f [serviço]' para ver logs específicos"

