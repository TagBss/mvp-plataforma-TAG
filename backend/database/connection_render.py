"""
Configuração de conexão para Render (Backend + Redis)
Data: 2025-09-05
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import redis

# Carregar variáveis de ambiente
load_dotenv()

def get_render_engine():
    """Cria engine do Render PostgreSQL com configurações otimizadas"""
    
    DATABASE_URL = os.getenv('DATABASE_URL')
    
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL não configurada no arquivo .env")
    
    # Configurações otimizadas para Render PostgreSQL
    engine = create_engine(
        DATABASE_URL,
        pool_size=5,  # Render Basic tem limite menor
        max_overflow=10,  # Conexões extras permitidas
        pool_pre_ping=True,  # Verificar conexões antes de usar
        pool_recycle=1800,  # Reciclar conexões a cada 30 min
        echo=False,  # Mudar para True para debug SQL
        connect_args={
            "connect_timeout": 10,
            "application_name": "plataforma-tag-backend"
        }
    )
    
    return engine

def get_render_redis():
    """Cria conexão Redis do Render"""
    
    REDIS_URL = os.getenv('REDIS_URL')
    
    if not REDIS_URL:
        raise ValueError("REDIS_URL não configurada no arquivo .env")
    
    # Configurações otimizadas para Render Redis
    redis_client = redis.from_url(
        REDIS_URL,
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5,
        retry_on_timeout=True,
        health_check_interval=30
    )
    
    return redis_client

# Criar instâncias globais
engine = get_render_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
redis_client = get_render_redis()

def get_db():
    """Dependency para FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_redis():
    """Dependency para FastAPI"""
    return redis_client

def test_connection():
    """Testa conexões com Render"""
    try:
        # Testar PostgreSQL
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            print("✅ PostgreSQL Render conectado!")
        
        # Testar Redis
        redis_client.ping()
        print("✅ Redis Render conectado!")
        
        return True
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
        return False
