#!/bin/bash

# 🎯 MANAGE DSP ENVIRONMENTS
# ===========================================

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Function to print colored output
print_header() {
    echo -e "${PURPLE}===========================================${NC}"
    echo -e "${PURPLE}$1${NC}"
    echo -e "${PURPLE}===========================================${NC}"
}

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

# Function to show help
show_help() {
    print_header "🎯 DSP ENVIRONMENT MANAGER"
    echo ""
    echo "Usage: $0 [COMMAND] [ENVIRONMENT]"
    echo ""
    echo "Commands:"
    echo "  start     - Start environment"
    echo "  stop      - Stop environment"
    echo "  restart   - Restart environment"
    echo "  status    - Show environment status"
    echo "  logs      - Show environment logs"
    echo "  clean     - Clean environment (remove containers and volumes)"
    echo "  backup    - Backup environment database"
    echo "  restore   - Restore environment database"
    echo ""
    echo "Environments:"
    echo "  dev       - Development environment"
    echo "  staging   - Staging environment"
    echo "  prod      - Production environment"
    echo "  all       - All environments"
    echo ""
    echo "Examples:"
    echo "  $0 start dev"
    echo "  $0 stop staging"
    echo "  $0 logs prod"
    echo "  $0 clean all"
    echo ""
}

# Function to get compose file for environment
get_compose_file() {
    local env=$1
    case $env in
        "dev")
            echo "docker-compose.dev.yml"
            ;;
        "staging")
            echo "docker-compose.staging.yml"
            ;;
        "prod")
            echo "docker-compose.production.yml"
            ;;
        *)
            print_error "Invalid environment: $env"
            exit 1
            ;;
    esac
}

# Function to get environment name
get_env_name() {
    local env=$1
    case $env in
        "dev")
            echo "Development"
            ;;
        "staging")
            echo "Staging"
            ;;
        "prod")
            echo "Production"
            ;;
        *)
            echo "Unknown"
            ;;
    esac
}

# Function to start environment
start_environment() {
    local env=$1
    local compose_file=$(get_compose_file $env)
    local env_name=$(get_env_name $env)
    
    print_header "🚀 Starting $env_name Environment"
    
    if [ ! -f "$compose_file" ]; then
        print_error "$compose_file not found!"
        exit 1
    fi
    
    # Load environment variables if file exists
    local env_file="env.$env"
    if [ -f "$env_file" ]; then
        print_status "Loading environment variables from $env_file..."
        export $(cat $env_file | grep -v '^#' | xargs)
    fi
    
    print_status "Starting $env_name environment..."
    docker-compose -f $compose_file up -d --build
    
    if [ $? -eq 0 ]; then
        print_success "$env_name environment started successfully!"
        show_environment_urls $env
    else
        print_error "Failed to start $env_name environment!"
        exit 1
    fi
}

# Function to stop environment
stop_environment() {
    local env=$1
    local compose_file=$(get_compose_file $env)
    local env_name=$(get_env_name $env)
    
    print_header "🛑 Stopping $env_name Environment"
    
    print_status "Stopping $env_name environment..."
    docker-compose -f $compose_file down
    
    if [ $? -eq 0 ]; then
        print_success "$env_name environment stopped successfully!"
    else
        print_error "Failed to stop $env_name environment!"
        exit 1
    fi
}

# Function to restart environment
restart_environment() {
    local env=$1
    local env_name=$(get_env_name $env)
    
    print_header "🔄 Restarting $env_name Environment"
    
    stop_environment $env
    sleep 2
    start_environment $env
}

# Function to show environment status
show_environment_status() {
    local env=$1
    local compose_file=$(get_compose_file $env)
    local env_name=$(get_env_name $env)
    
    print_header "📊 $env_name Environment Status"
    
    if [ ! -f "$compose_file" ]; then
        print_error "$compose_file not found!"
        return 1
    fi
    
    docker-compose -f $compose_file ps
}

# Function to show environment logs
show_environment_logs() {
    local env=$1
    local compose_file=$(get_compose_file $env)
    local env_name=$(get_env_name $env)
    
    print_header "📋 $env_name Environment Logs"
    
    if [ ! -f "$compose_file" ]; then
        print_error "$compose_file not found!"
        return 1
    fi
    
    docker-compose -f $compose_file logs -f
}

# Function to clean environment
clean_environment() {
    local env=$1
    local compose_file=$(get_compose_file $env)
    local env_name=$(get_env_name $env)
    
    print_header "🧹 Cleaning $env_name Environment"
    
    print_warning "This will remove all containers, volumes, and images for $env_name environment!"
    read -p "Are you sure? (yes/no): " -r
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        print_status "Cleaning cancelled."
        return 0
    fi
    
    print_status "Stopping and removing containers..."
    docker-compose -f $compose_file down -v --rmi all
    
    print_status "Removing unused volumes..."
    docker volume prune -f
    
    print_success "$env_name environment cleaned successfully!"
}

# Function to show environment URLs
show_environment_urls() {
    local env=$1
    
    echo ""
    case $env in
        "dev")
            echo "🌐 Development Environment URLs:"
            echo "  📱 Frontend: http://localhost:5173"
            echo "  🐍 Backend:  http://localhost:8000"
            echo "  🗄️  Database: localhost:5432"
            echo "  🔴 Redis:    localhost:6379"
            echo "  🛠️  pgAdmin: http://localhost:5050"
            ;;
        "staging")
            echo "🌐 Staging Environment URLs:"
            echo "  📱 Frontend: http://localhost:5174"
            echo "  🐍 Backend:  http://localhost:8001"
            echo "  🗄️  Database: localhost:5433"
            echo "  🔴 Redis:    localhost:6380"
            echo "  🛠️  pgAdmin: http://localhost:5051"
            ;;
        "prod")
            echo "🌐 Production Environment URLs:"
            echo "  🌐 Application: http://localhost"
            echo "  🐍 Backend:     http://localhost:8000"
            echo "  📊 Health:      http://localhost/health"
            ;;
    esac
    echo ""
}

# Main script logic
if [ $# -eq 0 ]; then
    show_help
    exit 0
fi

COMMAND=$1
ENVIRONMENT=$2

case $COMMAND in
    "start")
        if [ -z "$ENVIRONMENT" ]; then
            print_error "Environment not specified!"
            show_help
            exit 1
        fi
        
        if [ "$ENVIRONMENT" = "all" ]; then
            start_environment "dev"
            start_environment "staging"
            start_environment "prod"
        else
            start_environment $ENVIRONMENT
        fi
        ;;
    "stop")
        if [ -z "$ENVIRONMENT" ]; then
            print_error "Environment not specified!"
            show_help
            exit 1
        fi
        
        if [ "$ENVIRONMENT" = "all" ]; then
            stop_environment "dev"
            stop_environment "staging"
            stop_environment "prod"
        else
            stop_environment $ENVIRONMENT
        fi
        ;;
    "restart")
        if [ -z "$ENVIRONMENT" ]; then
            print_error "Environment not specified!"
            show_help
            exit 1
        fi
        
        if [ "$ENVIRONMENT" = "all" ]; then
            restart_environment "dev"
            restart_environment "staging"
            restart_environment "prod"
        else
            restart_environment $ENVIRONMENT
        fi
        ;;
    "status")
        if [ -z "$ENVIRONMENT" ]; then
            print_error "Environment not specified!"
            show_help
            exit 1
        fi
        
        if [ "$ENVIRONMENT" = "all" ]; then
            show_environment_status "dev"
            show_environment_status "staging"
            show_environment_status "prod"
        else
            show_environment_status $ENVIRONMENT
        fi
        ;;
    "logs")
        if [ -z "$ENVIRONMENT" ]; then
            print_error "Environment not specified!"
            show_help
            exit 1
        fi
        
        show_environment_logs $ENVIRONMENT
        ;;
    "clean")
        if [ -z "$ENVIRONMENT" ]; then
            print_error "Environment not specified!"
            show_help
            exit 1
        fi
        
        if [ "$ENVIRONMENT" = "all" ]; then
            clean_environment "dev"
            clean_environment "staging"
            clean_environment "prod"
        else
            clean_environment $ENVIRONMENT
        fi
        ;;
    "help"|"-h"|"--help")
        show_help
        ;;
    *)
        print_error "Unknown command: $COMMAND"
        show_help
        exit 1
        ;;
esac
