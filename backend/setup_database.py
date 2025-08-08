"""
Script para configurar o banco de dados PostgreSQL
"""
import os
import sys
from pathlib import Path

def setup_database():
    """Configura o banco de dados PostgreSQL"""
    
    print("🚀 Configurando banco de dados PostgreSQL...")
    
    # Verificar se arquivo .env existe
    env_file = Path(".env")
    if not env_file.exists():
        print("📝 Criando arquivo .env...")
        with open(".env", "w") as f:
            f.write("""# Configurações do Banco de Dados PostgreSQL
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/tag_financeiro

# Configurações de Autenticação JWT
JWT_SECRET_KEY=sua_chave_secreta_aqui_muito_segura
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Configurações do Redis (para cache)
REDIS_URL=redis://localhost:6379

# Configurações da API
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True

# Configurações de Log
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
""")
        print("✅ Arquivo .env criado!")
    
    # Instalar dependências
    print("📦 Instalando dependências...")
    os.system("pip install -r requirements.txt")
    
    # Criar migrations
    print("🗄️ Criando migrations...")
    os.system("python database/migrations.py migrate")
    
    # Inserir dados iniciais
    print("🌱 Inserindo dados iniciais...")
    os.system("python database/migrations.py seed")
    
    print("✅ Configuração concluída!")
    print("\n📋 Próximos passos:")
    print("1. Configure o PostgreSQL localmente")
    print("2. Execute: python database/migrate_excel_data.py migrate")
    print("3. Execute: python database/migrate_excel_data.py validate")
    print("4. Inicie o servidor: uvicorn main:app --reload")

def setup_postgres_instructions():
    """Instruções para configurar PostgreSQL"""
    
    print("📋 INSTRUÇÕES PARA CONFIGURAR POSTGRESQL:")
    print("\n1. Instalar PostgreSQL:")
    print("   Ubuntu/Debian: sudo apt install postgresql postgresql-contrib")
    print("   macOS: brew install postgresql")
    print("   Windows: Baixar do site oficial")
    
    print("\n2. Iniciar PostgreSQL:")
    print("   Ubuntu/Debian: sudo systemctl start postgresql")
    print("   macOS: brew services start postgresql")
    
    print("\n3. Criar banco de dados:")
    print("   sudo -u postgres psql")
    print("   CREATE DATABASE tag_financeiro;")
    print("   CREATE USER postgres WITH PASSWORD 'postgres';")
    print("   GRANT ALL PRIVILEGES ON DATABASE tag_financeiro TO postgres;")
    print("   \\q")
    
    print("\n4. Ou usar Docker:")
    print("   docker run -d --name postgres-tag \\")
    print("     -e POSTGRES_DB=tag_financeiro \\")
    print("     -e POSTGRES_USER=postgres \\")
    print("     -e POSTGRES_PASSWORD=postgres \\")
    print("     -p 5432:5432 postgres:latest")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "setup":
            setup_database()
        elif command == "postgres-instructions":
            setup_postgres_instructions()
        else:
            print("Comandos: setup, postgres-instructions")
    else:
        print("Comandos: setup, postgres-instructions")
