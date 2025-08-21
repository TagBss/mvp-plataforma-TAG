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
    from sqlalchemy import text
    
    engine = get_engine()
    
    # Dropar apenas as tabelas específicas que precisamos recriar
    print("🗑️ Dropando tabelas específicas...")
    with engine.connect() as conn:
        # Desabilitar foreign key checks temporariamente
        conn.execute(text("SET session_replication_role = replica"))
        
        # Dropar apenas as tabelas que precisamos recriar
        tables_to_drop = [
            'de_para',
            'plano_de_contas', 
            'categorias',
            'empresas',
            'grupos_empresa'
        ]
        
        for table in tables_to_drop:
            try:
                conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
                print(f"✅ Tabela {table} dropada")
            except Exception as e:
                print(f"⚠️ Erro ao dropar {table}: {e}")
        
        # Reabilitar foreign key checks
        conn.execute(text("SET session_replication_role = DEFAULT"))
        conn.commit()
    
    print("✅ Tabelas específicas dropadas!")
    
    # Criar todas as tabelas novamente
    print("📋 Criando tabelas...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tabelas criadas!")

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
