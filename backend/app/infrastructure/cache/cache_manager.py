"""
Cache Manager - Redis Implementation
Sistema de cache distribuído com Redis
"""

import json
import pickle
from typing import Any, Optional, Union, Dict, List
from datetime import datetime, timedelta
from functools import wraps
import hashlib
import asyncio

import redis.asyncio as redis
from pydantic import BaseModel

from app.core.config import settings


class CacheConfig(BaseModel):
    """Configuração do cache"""
    default_ttl: int = 300  # 5 minutos
    max_connections: int = 20
    retry_on_timeout: bool = True
    socket_keepalive: bool = True
    socket_keepalive_options: Dict[str, int] = {
        1: 1,  # TCP_KEEPIDLE
        2: 3,  # TCP_KEEPINTVL  
        3: 5   # TCP_KEEPCNT
    }


class CacheManager:
    """
    Gerenciador de cache Redis
    
    Funcionalidades:
    - Cache com TTL configurável
    - Serialização automática
    - Invalidação por padrões
    - Métricas de cache
    - Connection pooling
    """
    
    def __init__(self, config: CacheConfig = None):
        self.config = config or CacheConfig()
        self._redis: Optional[redis.Redis] = None
        self._connection_pool: Optional[redis.ConnectionPool] = None
        self._metrics = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "errors": 0
        }
    
    async def initialize(self) -> None:
        """Inicializa conexão com Redis"""
        try:
            self._connection_pool = redis.ConnectionPool.from_url(
                settings.REDIS_URL,
                max_connections=self.config.max_connections,
                retry_on_timeout=self.config.retry_on_timeout,
                socket_keepalive=self.config.socket_keepalive,
                socket_keepalive_options=self.config.socket_keepalive_options,
                decode_responses=False  # Para suportar pickle
            )
            
            self._redis = redis.Redis(connection_pool=self._connection_pool)
            
            # Testar conexão
            await self._redis.ping()
            print("✅ Redis cache initialized successfully")
            
        except Exception as e:
            print(f"❌ Failed to initialize Redis cache: {e}")
            self._redis = None
    
    async def close(self) -> None:
        """Fecha conexões"""
        if self._redis:
            await self._redis.close()
        if self._connection_pool:
            await self._connection_pool.disconnect()
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Gera chave única para cache"""
        # Criar hash dos argumentos
        key_data = f"{prefix}:{args}:{sorted(kwargs.items())}"
        key_hash = hashlib.md5(key_data.encode()).hexdigest()
        return f"cache:{prefix}:{key_hash}"
    
    def _serialize_value(self, value: Any) -> bytes:
        """Serializa valor para cache"""
        try:
            # Tentar JSON primeiro (mais rápido)
            if isinstance(value, (str, int, float, bool, list, dict)):
                return json.dumps(value).encode()
            else:
                # Usar pickle para objetos complexos
                return pickle.dumps(value)
        except Exception:
            # Fallback para pickle
            return pickle.dumps(value)
    
    def _deserialize_value(self, data: bytes) -> Any:
        """Deserializa valor do cache"""
        try:
            # Tentar JSON primeiro
            return json.loads(data.decode())
        except (json.JSONDecodeError, UnicodeDecodeError):
            # Usar pickle
            return pickle.loads(data)
    
    async def get(self, key: str) -> Optional[Any]:
        """Recupera valor do cache"""
        if not self._redis:
            return None
        
        try:
            data = await self._redis.get(key)
            if data is None:
                self._metrics["misses"] += 1
                return None
            
            self._metrics["hits"] += 1
            return self._deserialize_value(data)
            
        except Exception as e:
            self._metrics["errors"] += 1
            print(f"Cache get error: {e}")
            return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None
    ) -> bool:
        """Armazena valor no cache"""
        if not self._redis:
            return False
        
        try:
            ttl = ttl or self.config.default_ttl
            data = self._serialize_value(value)
            
            await self._redis.setex(key, ttl, data)
            self._metrics["sets"] += 1
            return True
            
        except Exception as e:
            self._metrics["errors"] += 1
            print(f"Cache set error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Remove valor do cache"""
        if not self._redis:
            return False
        
        try:
            result = await self._redis.delete(key)
            self._metrics["deletes"] += 1
            return result > 0
            
        except Exception as e:
            self._metrics["errors"] += 1
            print(f"Cache delete error: {e}")
            return False
    
    async def delete_pattern(self, pattern: str) -> int:
        """Remove chaves por padrão"""
        if not self._redis:
            return 0
        
        try:
            keys = await self._redis.keys(pattern)
            if keys:
                deleted = await self._redis.delete(*keys)
                self._metrics["deletes"] += deleted
                return deleted
            return 0
            
        except Exception as e:
            self._metrics["errors"] += 1
            print(f"Cache delete pattern error: {e}")
            return 0
    
    async def exists(self, key: str) -> bool:
        """Verifica se chave existe"""
        if not self._redis:
            return False
        
        try:
            return await self._redis.exists(key) > 0
        except Exception:
            return False
    
    async def get_ttl(self, key: str) -> int:
        """Retorna TTL da chave"""
        if not self._redis:
            return -1
        
        try:
            return await self._redis.ttl(key)
        except Exception:
            return -1
    
    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Incrementa valor numérico"""
        if not self._redis:
            return None
        
        try:
            return await self._redis.incrby(key, amount)
        except Exception as e:
            self._metrics["errors"] += 1
            print(f"Cache increment error: {e}")
            return None
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Retorna métricas do cache"""
        metrics = self._metrics.copy()
        
        if self._redis:
            try:
                info = await self._redis.info()
                metrics.update({
                    "redis_memory_used": info.get("used_memory_human", "N/A"),
                    "redis_connected_clients": info.get("connected_clients", 0),
                    "redis_total_commands": info.get("total_commands_processed", 0),
                    "redis_keyspace_hits": info.get("keyspace_hits", 0),
                    "redis_keyspace_misses": info.get("keyspace_misses", 0)
                })
            except Exception:
                pass
        
        # Calcular hit rate
        total_requests = metrics["hits"] + metrics["misses"]
        metrics["hit_rate"] = (
            metrics["hits"] / total_requests * 100 
            if total_requests > 0 else 0
        )
        
        return metrics


# Instância global do cache
cache_manager = CacheManager()


def cache_result(
    prefix: str,
    ttl: Optional[int] = None,
    key_builder: Optional[callable] = None
):
    """
    Decorator para cache de resultados de funções
    
    Args:
        prefix: Prefixo da chave de cache
        ttl: Tempo de vida em segundos
        key_builder: Função customizada para gerar chave
    """
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Gerar chave de cache
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                cache_key = cache_manager._generate_key(prefix, *args, **kwargs)
            
            # Tentar recuperar do cache
            cached_result = await cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Executar função e cachear resultado
            result = await func(*args, **kwargs)
            if result is not None:
                await cache_manager.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


def invalidate_cache_pattern(pattern: str):
    """
    Decorator para invalidar cache por padrão após execução
    
    Args:
        pattern: Padrão das chaves a invalidar
    """
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            
            # Invalidar cache após sucesso
            await cache_manager.delete_pattern(pattern)
            
            return result
        
        return wrapper
    return decorator


# Cache específico para diferentes domínios
class UserCache:
    """Cache específico para usuários"""
    
    @staticmethod
    @cache_result("user_by_id", ttl=600)  # 10 minutos
    async def get_user_by_id(user_id: str):
        """Cache para usuário por ID"""
        pass
    
    @staticmethod
    @cache_result("user_by_email", ttl=600)
    async def get_user_by_email(email: str):
        """Cache para usuário por email"""
        pass
    
    @staticmethod
    async def invalidate_user(user_id: str):
        """Invalida cache de um usuário específico"""
        await cache_manager.delete_pattern(f"cache:user_*:{user_id}*")


class AgentCache:
    """Cache específico para agentes"""
    
    @staticmethod
    @cache_result("agent_stats", ttl=300)  # 5 minutos
    async def get_agent_stats(user_id: str):
        """Cache para estatísticas de agentes"""
        pass
    
    @staticmethod
    @cache_result("agent_performance", ttl=180)  # 3 minutos
    async def get_agent_performance(agent_id: str):
        """Cache para performance de agente"""
        pass


class LLMCache:
    """Cache específico para resultados de LLM"""
    
    @staticmethod
    @cache_result("llm_response", ttl=3600)  # 1 hora
    async def get_llm_response(prompt_hash: str):
        """Cache para respostas de LLM"""
        pass
