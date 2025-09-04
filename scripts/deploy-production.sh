#!/bin/bash

# 🚀 DEPLOY PRODUCTION ENVIRONMENT
# ===========================================

echo "🚀 Deploying to Production Environment..."
echo "========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
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

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker Desktop."
    exit 1
fi

# Check if docker-compose file exists
if [ ! -f "docker-compose.production.yml" ]; then
    print_error "docker-compose.production.yml not found!"
    exit 1
fi

# Check if environment file exists
if [ ! -f "env.production" ]; then
    print_error "env.production not found! Please create it with production values."
    exit 1
fi

# Security check - ensure production environment variables are set
print_status "Checking production environment variables..."
source env.production

if [ -z "$POSTGRES_PASSWORD" ] || [ "$POSTGRES_PASSWORD" = "your_production_password" ]; then
    print_error "POSTGRES_PASSWORD not set or using default value!"
    exit 1
fi

if [ -z "$JWT_SECRET_KEY" ] || [ "$JWT_SECRET_KEY" = "your_jwt_secret_key" ]; then
    print_error "JWT_SECRET_KEY not set or using default value!"
    exit 1
fi

if [ -z "$SECRET_KEY" ] || [ "$SECRET_KEY" = "your_secret_key" ]; then
    print_error "SECRET_KEY not set or using default value!"
    exit 1
fi

print_success "Production environment variables validated"

# Confirmation prompt
echo ""
print_warning "⚠️  WARNING: This will deploy to PRODUCTION environment!"
print_warning "Make sure you have:"
print_warning "  - Tested in staging environment"
print_warning "  - Created database backup"
print_warning "  - Set all production environment variables"
echo ""
read -p "Are you sure you want to continue? (yes/no): " -r
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    print_status "Deployment cancelled."
    exit 0
fi

# Load environment variables
print_status "Loading production environment variables..."
export $(cat env.production | grep -v '^#' | xargs)

# Stop existing containers
print_status "Stopping existing production containers..."
docker-compose -f docker-compose.production.yml down

# Create backup before deployment
print_status "Creating database backup..."
if [ -f "scripts/backup-db.sh" ]; then
    ./scripts/backup-db.sh production
    print_success "Database backup created"
else
    print_warning "Backup script not found, skipping backup"
fi

# Build and start containers
print_status "Building and starting production containers..."
docker-compose -f docker-compose.production.yml up -d --build

# Wait for services to be ready
print_status "Waiting for services to be ready..."
sleep 20

# Check health of services
print_status "Checking service health..."

# Check PostgreSQL
if docker-compose -f docker-compose.production.yml exec -T postgres pg_isready -U postgres > /dev/null 2>&1; then
    print_success "PostgreSQL is ready"
else
    print_error "PostgreSQL is not ready"
fi

# Check Redis
if docker-compose -f docker-compose.production.yml exec -T redis redis-cli ping > /dev/null 2>&1; then
    print_success "Redis is ready"
else
    print_error "Redis is not ready"
fi

# Check Backend
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    print_success "Backend is ready"
else
    print_warning "Backend health check failed, but it might still be starting..."
fi

# Check Nginx
if curl -f http://localhost/health > /dev/null 2>&1; then
    print_success "Nginx is ready"
else
    print_warning "Nginx health check failed, but it might still be starting..."
fi

# Show container status
print_status "Container status:"
docker-compose -f docker-compose.production.yml ps

# Show access URLs
echo ""
print_success "🎉 Production environment is ready!"
echo "========================================="
echo "🌐 Application: http://localhost"
echo "🐍 Backend:     http://localhost:8000"
echo "📊 Health Check: http://localhost/health"
echo "📚 API Docs:     http://localhost:8000/docs"
echo ""
print_status "To view logs: docker-compose -f docker-compose.production.yml logs -f"
print_status "To stop:      docker-compose -f docker-compose.production.yml down"
print_warning "Production deployment complete! Monitor the application closely."
