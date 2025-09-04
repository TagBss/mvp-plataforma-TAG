"""
Sistema de migrations para Drizzle ORM
"""
import os
import sys
from pathlib import Path
from drizzle_orm.drizzle import PostgresDrizzle
from drizzle_orm.drizzle import migrate
from database.connection import get_database
from database.schema import *

def create_migrations():
    """Cria as migrations baseadas no schema"""
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
    """Insere dados iniciais no banco"""
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
        
        if command == "migrate":
            create_migrations()
        elif command == "seed":
            seed_initial_data()
        else:
            print("Comandos disponíveis: migrate, seed")
    else:
        print("Comandos disponíveis: migrate, seed")
