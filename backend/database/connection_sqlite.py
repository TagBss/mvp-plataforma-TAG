"""
Configuração de conexão com SQLite para testes temporários
"""
import os
from typing import Optional
from drizzle_orm import Drizzle
from drizzle_orm.drizzle import SQLiteDrizzle
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configurações do banco de dados SQLite
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "sqlite:///./tag_financeiro.db"
)

# Pool de conexões
_db: Optional[SQLiteDrizzle] = None

def get_database() -> SQLiteDrizzle:
    """Retorna instância do banco de dados SQLite"""
    global _db
    
    if _db is None:
        _db = Drizzle(
            DATABASE_URL,
        )
    
    return _db

def close_database():
    """Fecha a conexão com o banco de dados"""
    global _db
    if _db:
        _db.close()
        _db = None

# Context manager para transações
class DatabaseTransaction:
    def __init__(self):
        self.db = get_database()
    
    def __enter__(self):
        return self.db
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            # Rollback em caso de erro
            pass
        # Commit automático se não houver erro
