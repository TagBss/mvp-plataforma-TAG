#!/bin/bash
# 💾 Script para backup do banco de dados PostgreSQL

set -e  # Parar em caso de erro

echo "💾 Fazendo backup do banco de dados PostgreSQL..."
echo "================================================"

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

# Verificar se Docker está rodando
if ! docker info &> /dev/null; then
    print_error "Docker não está rodando. Inicie o Docker primeiro."
    exit 1
fi

# Verificar se o container PostgreSQL está rodando
if ! docker-compose ps postgres | grep -q "Up"; then
    print_error "Container PostgreSQL não está rodando!"
    print_status "Inicie os containers primeiro: docker-compose up -d"
    exit 1
fi

# Criar diretório de backups se não existir
mkdir -p backups

# Gerar timestamp para o backup
timestamp=$(date +"%Y%m%d_%H%M%S")
backup_file="backups/plataforma_tag_backup_${timestamp}.sql"

print_status "Criando backup: $backup_file"

# Fazer backup do banco de dados
if docker-compose exec -T postgres pg_dump -U postgres -d tag_financeiro > "$backup_file"; then
    print_success "Backup criado com sucesso!"
    
    # Verificar tamanho do arquivo
    file_size=$(du -h "$backup_file" | cut -f1)
    print_status "Tamanho do backup: $file_size"
    
    # Comprimir o backup
    print_status "Comprimindo backup..."
    gzip "$backup_file"
    compressed_file="${backup_file}.gz"
    compressed_size=$(du -h "$compressed_file" | cut -f1)
    print_success "Backup comprimido: $compressed_size"
    
    # Manter apenas os últimos 10 backups
    print_status "Limpando backups antigos (mantendo últimos 10)..."
    cd backups
    ls -t plataforma_tag_backup_*.sql.gz | tail -n +11 | xargs -r rm
    cd ..
    
    print_success "✅ Backup concluído: $compressed_file"
    
else
    print_error "Falha ao criar backup!"
    exit 1
fi

echo ""
echo "📋 Comandos úteis:"
echo "   📁 Listar backups: ls -la backups/"
echo "   🔄 Restaurar backup: ./scripts/restore-db.sh [arquivo]"
echo "   🗑️ Limpar backups: rm backups/*.sql.gz"

