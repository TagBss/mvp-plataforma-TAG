"""
Script para configurar banco de dados com SQLAlchemy
"""
import os
import sys
from pathlib import Path
from database.connection_sqlalchemy import create_tables, DatabaseSession
from database.schema_sqlalchemy import *
from database.repository_sqlalchemy import FinancialDataRepository, UserRepository

def setup_database():
    """Configura o banco de dados PostgreSQL com SQLAlchemy"""
    
    print("🚀 Configurando banco de dados PostgreSQL com SQLAlchemy...")
    
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
    
    # Criar tabelas
    print("🗄️ Criando tabelas...")
    create_tables()
    
    # Inserir dados iniciais
    print("🌱 Inserindo dados iniciais...")
    seed_initial_data()
    
    print("✅ Configuração concluída!")
    print("\n📋 Próximos passos:")
    print("1. Execute: python database/migrate_excel_data.py migrate")
    print("2. Execute: python database/migrate_excel_data.py validate")
    print("3. Inicie o servidor: uvicorn main:app --reload")

def seed_initial_data():
    """Insere dados iniciais no banco"""
    
    with DatabaseSession() as session:
        # Inserir roles básicos
        admin_role = Role(
            name="admin",
            description="Administrador do sistema"
        )
        session.add(admin_role)
        
        user_role = Role(
            name="user",
            description="Usuário padrão"
        )
        session.add(user_role)
        
        session.flush()  # Para obter os IDs
        
        # Inserir permissões básicas
        permissions_data = [
            ("financial_data:read", "Ler dados financeiros", "financial_data", "read"),
            ("financial_data:write", "Escrever dados financeiros", "financial_data", "write"),
            ("reports:read", "Ler relatórios", "reports", "read"),
            ("reports:write", "Criar relatórios", "reports", "write"),
            ("users:manage", "Gerenciar usuários", "users", "manage"),
        ]
        
        permissions = []
        for name, description, resource, action in permissions_data:
            perm = Permission(
                name=name,
                description=description,
                resource=resource,
                action=action
            )
            session.add(perm)
            permissions.append(perm)
        
        session.flush()
        
        # Associar permissões ao role admin
        admin_permissions = session.query(Permission).filter(
            Permission.name.in_([
                "financial_data:read", "financial_data:write",
                "reports:read", "reports:write", "users:manage"
            ])
        ).all()
        
        for perm in admin_permissions:
            user_role_perm = RolePermission(
                role_id=admin_role.id,
                permission_id=perm.id
            )
            session.add(user_role_perm)
        
        # Associar permissões básicas ao role user
        user_permissions = session.query(Permission).filter(
            Permission.name.in_([
                "financial_data:read", "reports:read"
            ])
        ).all()
        
        for perm in user_permissions:
            user_role_perm = RolePermission(
                role_id=user_role.id,
                permission_id=perm.id
            )
            session.add(user_role_perm)
    
    print("✅ Dados iniciais inseridos com sucesso!")

def test_connection():
    """Testa conexão com o banco"""
    
    try:
        with DatabaseSession() as session:
            # Testar query simples
            result = session.query(Role).first()
            print("✅ Conexão com banco de dados funcionando!")
            return True
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "setup":
            setup_database()
        elif command == "test":
            test_connection()
        else:
            print("Comandos: setup, test")
    else:
        print("Comandos: setup, test")
