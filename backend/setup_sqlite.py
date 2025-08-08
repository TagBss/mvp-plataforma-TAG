"""
Script para configurar SQLite temporariamente para testes
"""
import os
import sys
from pathlib import Path
from database.connection_sqlite import get_database
from database.schema_sqlite import *
from drizzle_orm.drizzle import migrate

def setup_sqlite_database():
    """Configura o banco de dados SQLite"""
    
    print("🚀 Configurando banco de dados SQLite...")
    
    # Verificar se arquivo .env existe
    env_file = Path(".env")
    if not env_file.exists():
        print("📝 Criando arquivo .env...")
        with open(".env", "w") as f:
            f.write("""# Configurações do Banco de Dados SQLite
DATABASE_URL=sqlite:///./tag_financeiro.db

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
    create_migrations()
    
    # Inserir dados iniciais
    print("🌱 Inserindo dados iniciais...")
    seed_initial_data()
    
    print("✅ Configuração concluída!")
    print("\n📋 Próximos passos:")
    print("1. Execute: python database/migrate_excel_data.py migrate")
    print("2. Execute: python database/migrate_excel_data.py validate")
    print("3. Inicie o servidor: uvicorn main:app --reload")

def create_migrations():
    """Cria as migrations baseadas no schema SQLite"""
    db = get_database()
    
    # Criar todas as tabelas
    with db.connect() as conn:
        # Executar migrations
        migrate(conn, [
            financial_data,
            categories,
            periods,
            users,
            roles,
            permissions,
            user_roles,
            role_permissions,
            # Índices
            financial_data_date_idx,
            financial_data_category_idx,
            financial_data_type_idx,
            financial_data_period_idx,
            categories_parent_idx,
            categories_level_idx,
            periods_type_idx,
            periods_date_range_idx,
            users_email_idx,
        ])
    
    print("✅ Migrations criadas com sucesso!")

def seed_initial_data():
    """Insere dados iniciais no banco SQLite"""
    db = get_database()
    
    with db.connect() as conn:
        # Inserir roles básicos
        admin_role = conn.execute(
            roles.insert().values(
                name="admin",
                description="Administrador do sistema"
            )
        )
        
        user_role = conn.execute(
            roles.insert().values(
                name="user",
                description="Usuário padrão"
            )
        )
        
        # Inserir permissões básicas
        permissions_data = [
            ("financial_data:read", "Ler dados financeiros", "financial_data", "read"),
            ("financial_data:write", "Escrever dados financeiros", "financial_data", "write"),
            ("reports:read", "Ler relatórios", "reports", "read"),
            ("reports:write", "Criar relatórios", "reports", "write"),
            ("users:manage", "Gerenciar usuários", "users", "manage"),
        ]
        
        for name, description, resource, action in permissions_data:
            conn.execute(
                permissions.insert().values(
                    name=name,
                    description=description,
                    resource=resource,
                    action=action
                )
            )
        
        # Associar permissões ao role admin
        admin_permissions = conn.execute(
            permissions.select().where(permissions.name.in_([
                "financial_data:read", "financial_data:write",
                "reports:read", "reports:write", "users:manage"
            ]))
        ).fetchall()
        
        for perm in admin_permissions:
            conn.execute(
                role_permissions.insert().values(
                    role_id=admin_role.inserted_primary_key[0],
                    permission_id=perm[0]
                )
            )
        
        # Associar permissões básicas ao role user
        user_permissions = conn.execute(
            permissions.select().where(permissions.name.in_([
                "financial_data:read", "reports:read"
            ]))
        ).fetchall()
        
        for perm in user_permissions:
            conn.execute(
                role_permissions.insert().values(
                    role_id=user_role.inserted_primary_key[0],
                    permission_id=perm[0]
                )
            )
    
    print("✅ Dados iniciais inseridos com sucesso!")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "setup":
            setup_sqlite_database()
        else:
            print("Comandos: setup")
    else:
        print("Comandos: setup")
