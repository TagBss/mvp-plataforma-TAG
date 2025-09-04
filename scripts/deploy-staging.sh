#!/bin/bash

# 🧪 DEPLOY STAGING ENVIRONMENT
# ===========================================

echo "🧪 Deploying to Staging Environment..."
echo "======================================"

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
if [ ! -f "docker-compose.staging.yml" ]; then
    print_error "docker-compose.staging.yml not found!"
    exit 1
fi

# Check if environment file exists
if [ ! -f "env.staging" ]; then
    print_warning "env.staging not found. Using default values."
else
    print_status "Loading staging environment variables..."
    export $(cat env.staging | grep -v '^#' | xargs)
fi

# Stop existing containers
print_status "Stopping existing staging containers..."
docker-compose -f docker-compose.staging.yml down

# Remove old images (optional)
read -p "Do you want to remove old images? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_status "Removing old images..."
    docker-compose -f docker-compose.staging.yml down --rmi all
fi

# Build and start containers
print_status "Building and starting staging containers..."
docker-compose -f docker-compose.staging.yml up -d --build

# Wait for services to be ready
print_status "Waiting for services to be ready..."
sleep 15

# Check health of services
print_status "Checking service health..."

# Check PostgreSQL
if docker-compose -f docker-compose.staging.yml exec -T postgres pg_isready -U postgres > /dev/null 2>&1; then
    print_success "PostgreSQL is ready"
else
    print_error "PostgreSQL is not ready"
fi

# Check Redis
if docker-compose -f docker-compose.staging.yml exec -T redis redis-cli ping > /dev/null 2>&1; then
    print_success "Redis is ready"
else
    print_error "Redis is not ready"
fi

# Check Backend
if curl -f http://localhost:8001/health > /dev/null 2>&1; then
    print_success "Backend is ready"
else
    print_warning "Backend health check failed, but it might still be starting..."
fi

# Check Frontend
if curl -f http://localhost:5174 > /dev/null 2>&1; then
    print_success "Frontend is ready"
else
    print_warning "Frontend health check failed, but it might still be starting..."
fi

# Show container status
print_status "Container status:"
docker-compose -f docker-compose.staging.yml ps

# Show access URLs
echo ""
print_success "🎉 Staging environment is ready!"
echo "======================================"
echo "📱 Frontend: http://localhost:5174"
echo "🐍 Backend:  http://localhost:8001"
echo "🗄️  Database: localhost:5433"
echo "🔴 Redis:    localhost:6380"
echo "🛠️  pgAdmin: http://localhost:5051"
echo ""
echo "📊 Health Check: http://localhost:8001/health"
echo "📚 API Docs:     http://localhost:8001/docs"
echo ""
print_status "To view logs: docker-compose -f docker-compose.staging.yml logs -f"
print_status "To stop:      docker-compose -f docker-compose.staging.yml down"
print_warning "Remember: This is a staging environment for testing before production!"
