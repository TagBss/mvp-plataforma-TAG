"""
Helper para cache Redis com TTL e invalidação inteligente
"""
import json
import hashlib
from typing import Any, Optional, Union
import redis.asyncio as redis
from datetime import datetime, timedelta

class RedisCache:
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis: Optional[redis.Redis] = None
        
    async def connect(self):
        """Conecta ao Redis"""
        if not self.redis:
            self.redis = redis.from_url(self.redis_url, encoding="utf-8", decode_responses=True)
            await self.redis.ping()
            print("✅ Redis conectado com sucesso")
    
    async def disconnect(self):
        """Desconecta do Redis"""
        if self.redis:
            await self.redis.close()
            self.redis = None
            print("🔌 Redis desconectado")
    
    def _generate_key(self, prefix: str, **kwargs) -> str:
        """Gera chave de cache baseada em parâmetros"""
        # Ordenar kwargs para garantir consistência na chave
        sorted_kwargs = sorted(kwargs.items())
        params_str = "&".join([f"{k}={v}" for k, v in sorted_kwargs])
        
        # Hash dos parâmetros para chave mais curta
        params_hash = hashlib.md5(params_str.encode()).hexdigest()[:8]
        return f"{prefix}:{params_hash}"
    
    async def get(self, key: str) -> Optional[Any]:
        """Busca valor no cache"""
        if not self.redis:
            return None
            
        try:
            value = await self.redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            print(f"❌ Erro ao buscar cache: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Define valor no cache com TTL (padrão: 5 minutos)"""
        if not self.redis:
            return False
            
        try:
            await self.redis.setex(key, ttl, json.dumps(value))
            return True
        except Exception as e:
            print(f"❌ Erro ao definir cache: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Remove valor do cache"""
        if not self.redis:
            return False
            
        try:
            await self.redis.delete(key)
            return True
        except Exception as e:
            print(f"❌ Erro ao deletar cache: {e}")
            return False
    
    async def delete_pattern(self, pattern: str) -> bool:
        """Remove múltiplos valores por padrão"""
        if not self.redis:
            return False
            
        try:
            keys = await self.redis.keys(pattern)
            if keys:
                await self.redis.delete(*keys)
                print(f"🗑️ Cache limpo: {len(keys)} chaves removidas")
            return True
        except Exception as e:
            print(f"❌ Erro ao limpar cache por padrão: {e}")
            return False
    
    async def invalidate_dre_cache(self):
        """Invalida todo o cache relacionado ao DRE"""
        await self.delete_pattern("dre_n0:*")
        await self.delete_pattern("classificacoes:*")
        print("🔄 Cache DRE invalidado")
    
    async def get_dre_n0_cache(self, periodo: str, filtro_ano: str) -> Optional[dict]:
        """Busca cache específico do DRE N0"""
        key = self._generate_key("dre_n0", periodo=periodo, ano=filtro_ano)
        return await self.get(key)
    
    async def set_dre_n0_cache(self, periodo: str, filtro_ano: str, data: dict, ttl: int = 300) -> bool:
        """Define cache específico do DRE N0"""
        key = self._generate_key("dre_n0", periodo=periodo, ano=filtro_ano)
        return await self.set(key, data, ttl)
    
    async def get_classificacoes_cache(self, dre_n2_name: str) -> Optional[dict]:
        """Busca cache específico de classificações"""
        key = self._generate_key("classificacoes", dre_n2_name=dre_n2_name)
        return await self.get(key)
    
    async def set_classificacoes_cache(self, dre_n2_name: str, data: dict, ttl: int = 300) -> bool:
        """Define cache específico de classificações"""
        key = self._generate_key("classificacoes", dre_n2_name=dre_n2_name)
        return await self.set(key, data, ttl)

# Instância global do cache
cache = RedisCache()

async def get_cache() -> RedisCache:
    """Retorna instância do cache, conectando se necessário"""
    if not cache.redis:
        await cache.connect()
    return cache
