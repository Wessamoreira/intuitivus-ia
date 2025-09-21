"""
Testes de integração para Cache Manager
Testa integração real com Redis e performance
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import patch

from app.infrastructure.cache.cache_manager import (
    CacheManager, CacheConfig, cache_result, invalidate_cache_pattern,
    UserCache, AgentCache, LLMCache
)


@pytest.mark.integration
class TestCacheManagerIntegration:
    """Testes de integração do Cache Manager"""
    
    @pytest.mark.asyncio
    async def test_cache_initialization(self, test_cache_manager):
        """Testa inicialização do cache"""
        assert test_cache_manager._redis is not None
        
        # Testar ping
        result = await test_cache_manager._redis.ping()
        assert result is True
    
    @pytest.mark.asyncio
    async def test_basic_cache_operations(self, test_cache_manager):
        """Testa operações básicas de cache"""
        key = "test:basic:key"
        value = {"data": "test_value", "number": 42}
        
        # Set
        success = await test_cache_manager.set(key, value, ttl=60)
        assert success is True
        
        # Get
        cached_value = await test_cache_manager.get(key)
        assert cached_value == value
        
        # Exists
        exists = await test_cache_manager.exists(key)
        assert exists is True
        
        # TTL
        ttl = await test_cache_manager.get_ttl(key)
        assert 50 <= ttl <= 60  # Aproximadamente 60 segundos
        
        # Delete
        deleted = await test_cache_manager.delete(key)
        assert deleted is True
        
        # Verify deletion
        cached_value = await test_cache_manager.get(key)
        assert cached_value is None
    
    @pytest.mark.asyncio
    async def test_cache_serialization_types(self, test_cache_manager):
        """Testa serialização de diferentes tipos"""
        test_cases = [
            ("string", "simple string"),
            ("integer", 42),
            ("float", 3.14159),
            ("boolean", True),
            ("list", [1, 2, 3, "test"]),
            ("dict", {"key": "value", "nested": {"data": 123}}),
            ("complex_object", {
                "datetime": datetime.now().isoformat(),
                "list_of_dicts": [{"id": i, "name": f"item_{i}"} for i in range(3)]
            })
        ]
        
        for test_name, test_value in test_cases:
            key = f"test:serialization:{test_name}"
            
            # Set and get
            await test_cache_manager.set(key, test_value)
            cached_value = await test_cache_manager.get(key)
            
            assert cached_value == test_value, f"Failed for {test_name}"
    
    @pytest.mark.asyncio
    async def test_cache_expiration(self, test_cache_manager):
        """Testa expiração de cache"""
        key = "test:expiration:key"
        value = "expires_soon"
        
        # Set com TTL curto
        await test_cache_manager.set(key, value, ttl=1)
        
        # Verificar que existe
        cached_value = await test_cache_manager.get(key)
        assert cached_value == value
        
        # Esperar expirar
        await asyncio.sleep(1.1)
        
        # Verificar que expirou
        cached_value = await test_cache_manager.get(key)
        assert cached_value is None
    
    @pytest.mark.asyncio
    async def test_cache_pattern_deletion(self, test_cache_manager):
        """Testa deleção por padrão"""
        # Criar múltiplas chaves
        keys_data = [
            ("test:pattern:user:1", {"id": 1}),
            ("test:pattern:user:2", {"id": 2}),
            ("test:pattern:agent:1", {"id": 1}),
            ("test:other:key", {"id": 3})
        ]
        
        for key, value in keys_data:
            await test_cache_manager.set(key, value)
        
        # Verificar que todas existem
        for key, _ in keys_data:
            assert await test_cache_manager.exists(key)
        
        # Deletar apenas chaves de usuário
        deleted_count = await test_cache_manager.delete_pattern("test:pattern:user:*")
        assert deleted_count == 2
        
        # Verificar que apenas as corretas foram deletadas
        assert not await test_cache_manager.exists("test:pattern:user:1")
        assert not await test_cache_manager.exists("test:pattern:user:2")
        assert await test_cache_manager.exists("test:pattern:agent:1")
        assert await test_cache_manager.exists("test:other:key")
    
    @pytest.mark.asyncio
    async def test_cache_increment(self, test_cache_manager):
        """Testa incremento de valores"""
        key = "test:counter"
        
        # Incrementar valor inexistente
        result = await test_cache_manager.increment(key, 1)
        assert result == 1
        
        # Incrementar valor existente
        result = await test_cache_manager.increment(key, 5)
        assert result == 6
        
        # Verificar valor final
        value = await test_cache_manager.get(key)
        assert value == 6
    
    @pytest.mark.asyncio
    async def test_cache_metrics(self, test_cache_manager):
        """Testa coleta de métricas"""
        # Realizar algumas operações
        await test_cache_manager.set("test:metrics:1", "value1")
        await test_cache_manager.get("test:metrics:1")  # Hit
        await test_cache_manager.get("test:metrics:nonexistent")  # Miss
        
        metrics = await test_cache_manager.get_metrics()
        
        assert "hits" in metrics
        assert "misses" in metrics
        assert "sets" in metrics
        assert "hit_rate" in metrics
        assert metrics["hits"] >= 1
        assert metrics["misses"] >= 1
        assert metrics["sets"] >= 1


@pytest.mark.integration
class TestCacheDecorators:
    """Testes para decorators de cache"""
    
    @pytest.mark.asyncio
    async def test_cache_result_decorator(self, test_cache_manager):
        """Testa decorator cache_result"""
        call_count = 0
        
        @cache_result("test_function", ttl=60)
        async def expensive_function(param1: str, param2: int):
            nonlocal call_count
            call_count += 1
            return f"result_{param1}_{param2}_{call_count}"
        
        # Primeira chamada - deve executar função
        result1 = await expensive_function("test", 42)
        assert call_count == 1
        assert "result_test_42_1" in result1
        
        # Segunda chamada - deve usar cache
        result2 = await expensive_function("test", 42)
        assert call_count == 1  # Não deve incrementar
        assert result2 == result1
        
        # Chamada com parâmetros diferentes - deve executar função
        result3 = await expensive_function("other", 24)
        assert call_count == 2
        assert "result_other_24_2" in result3
    
    @pytest.mark.asyncio
    async def test_invalidate_cache_pattern_decorator(self, test_cache_manager):
        """Testa decorator invalidate_cache_pattern"""
        # Primeiro, cachear alguns dados
        await test_cache_manager.set("test:invalidate:user:1", {"id": 1})
        await test_cache_manager.set("test:invalidate:user:2", {"id": 2})
        
        @invalidate_cache_pattern("test:invalidate:user:*")
        async def update_user_data():
            return "updated"
        
        # Verificar que cache existe
        assert await test_cache_manager.exists("test:invalidate:user:1")
        assert await test_cache_manager.exists("test:invalidate:user:2")
        
        # Executar função que deve invalidar cache
        result = await update_user_data()
        assert result == "updated"
        
        # Verificar que cache foi invalidado
        assert not await test_cache_manager.exists("test:invalidate:user:1")
        assert not await test_cache_manager.exists("test:invalidate:user:2")


@pytest.mark.integration
class TestSpecificCaches:
    """Testes para caches específicos de domínio"""
    
    @pytest.mark.asyncio
    async def test_user_cache(self, test_cache_manager):
        """Testa UserCache"""
        user_id = "user_123"
        user_email = "test@example.com"
        
        # Mock das funções de cache
        with patch.object(UserCache, 'get_user_by_id') as mock_get_by_id, \
             patch.object(UserCache, 'get_user_by_email') as mock_get_by_email:
            
            # Configurar mocks
            mock_get_by_id.return_value = {"id": user_id, "email": user_email}
            mock_get_by_email.return_value = {"id": user_id, "email": user_email}
            
            # Testar invalidação
            await UserCache.invalidate_user(user_id)
            
            # Verificar que padrão correto foi usado
            # (Em implementação real, verificaríamos se as chaves foram deletadas)
    
    @pytest.mark.asyncio
    async def test_agent_cache(self, test_cache_manager):
        """Testa AgentCache"""
        user_id = "user_123"
        agent_id = "agent_456"
        
        # Simular cache de estatísticas
        stats_key = f"cache:agent_stats:{user_id}"
        performance_key = f"cache:agent_performance:{agent_id}"
        
        stats_data = {
            "total_agents": 5,
            "active_agents": 3,
            "total_tasks": 150
        }
        
        performance_data = {
            "success_rate": 95.5,
            "avg_execution_time": 1250,
            "total_executions": 100
        }
        
        # Cachear dados
        await test_cache_manager.set(stats_key, stats_data, ttl=300)
        await test_cache_manager.set(performance_key, performance_data, ttl=180)
        
        # Verificar que foram cacheados
        cached_stats = await test_cache_manager.get(stats_key)
        cached_performance = await test_cache_manager.get(performance_key)
        
        assert cached_stats == stats_data
        assert cached_performance == performance_data
    
    @pytest.mark.asyncio
    async def test_llm_cache(self, test_cache_manager):
        """Testa LLMCache"""
        import hashlib
        
        # Simular hash de prompt
        prompt = "Generate a marketing campaign for summer sale"
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()
        
        llm_response = {
            "response": "Here's a great summer sale campaign...",
            "tokens_used": 150,
            "model": "gpt-4",
            "timestamp": datetime.now().isoformat()
        }
        
        # Cachear resposta LLM (TTL longo para economizar tokens)
        cache_key = f"cache:llm_response:{prompt_hash}"
        await test_cache_manager.set(cache_key, llm_response, ttl=3600)
        
        # Verificar cache
        cached_response = await test_cache_manager.get(cache_key)
        assert cached_response == llm_response
        
        # Verificar TTL longo
        ttl = await test_cache_manager.get_ttl(cache_key)
        assert ttl > 3500  # Deve estar próximo de 3600


@pytest.mark.integration
@pytest.mark.performance
class TestCachePerformance:
    """Testes de performance do cache"""
    
    @pytest.mark.asyncio
    async def test_cache_performance_bulk_operations(self, test_cache_manager, performance_timer):
        """Testa performance de operações em massa"""
        num_operations = 1000
        
        # Teste de SET em massa
        performance_timer.start()
        
        tasks = []
        for i in range(num_operations):
            key = f"perf:test:{i}"
            value = {"id": i, "data": f"test_data_{i}"}
            tasks.append(test_cache_manager.set(key, value))
        
        await asyncio.gather(*tasks)
        performance_timer.stop()
        
        set_time = performance_timer.elapsed
        print(f"Bulk SET ({num_operations} ops): {set_time:.3f}s ({num_operations/set_time:.0f} ops/s)")
        
        # Teste de GET em massa
        performance_timer.start()
        
        tasks = []
        for i in range(num_operations):
            key = f"perf:test:{i}"
            tasks.append(test_cache_manager.get(key))
        
        results = await asyncio.gather(*tasks)
        performance_timer.stop()
        
        get_time = performance_timer.elapsed
        print(f"Bulk GET ({num_operations} ops): {get_time:.3f}s ({num_operations/get_time:.0f} ops/s)")
        
        # Verificar que todos os valores foram recuperados
        assert len(results) == num_operations
        assert all(result is not None for result in results)
        
        # Performance deve ser razoável (ajustar conforme ambiente)
        assert set_time < 10.0  # Menos de 10s para 1000 SETs
        assert get_time < 5.0   # Menos de 5s para 1000 GETs
    
    @pytest.mark.asyncio
    async def test_cache_hit_ratio_performance(self, test_cache_manager):
        """Testa hit ratio em cenário realista"""
        # Cachear dados iniciais
        for i in range(100):
            key = f"hit_ratio:user:{i}"
            value = {"id": i, "name": f"User {i}"}
            await test_cache_manager.set(key, value)
        
        # Simular padrão de acesso (80% hits, 20% misses)
        hits = 0
        misses = 0
        
        for _ in range(1000):
            if hits + misses < 800:  # 80% hits
                # Acessar dados existentes
                user_id = (hits + misses) % 100
                key = f"hit_ratio:user:{user_id}"
                result = await test_cache_manager.get(key)
                if result is not None:
                    hits += 1
                else:
                    misses += 1
            else:  # 20% misses
                # Acessar dados inexistentes
                key = f"hit_ratio:user:nonexistent_{misses}"
                result = await test_cache_manager.get(key)
                if result is None:
                    misses += 1
                else:
                    hits += 1
        
        hit_ratio = hits / (hits + misses) * 100
        print(f"Hit ratio: {hit_ratio:.1f}% (hits: {hits}, misses: {misses})")
        
        # Hit ratio deve ser próximo de 80%
        assert 75 <= hit_ratio <= 85
