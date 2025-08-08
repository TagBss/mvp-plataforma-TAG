"""
Configuração de conexão com PostgreSQL usando SQLAlchemy
"""
import os
from typing import Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configurações do banco de dados
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://postgres:postgres@localhost:5432/tag_financeiro"
)

# Engine com connection pooling
_engine: Optional[create_engine] = None
_SessionLocal: Optional[sessionmaker] = None

def get_engine():
    """Retorna engine do SQLAlchemy com pool de conexões"""
    global _engine
    
    if _engine is None:
        _engine = create_engine(
            DATABASE_URL,
            poolclass=QueuePool,
            pool_size=20,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=3600,
            echo=False  # Set to True for SQL logging
        )
    
    return _engine

def get_session():
    """Retorna session factory"""
    global _SessionLocal
    
    if _SessionLocal is None:
        engine = get_engine()
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    return _SessionLocal

def create_tables():
    """Cria todas as tabelas no banco"""
    from database.schema_sqlalchemy import Base
    
    engine = get_engine()
    Base.metadata.create_all(bind=engine)

# Context manager para sessões
class DatabaseSession:
    def __init__(self):
        self.SessionLocal = get_session()
    
    def __enter__(self):
        self.session = self.SessionLocal()
        return self.session
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.session.rollback()
        else:
            self.session.commit()
        self.session.close()
