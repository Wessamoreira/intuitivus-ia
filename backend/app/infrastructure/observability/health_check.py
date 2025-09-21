"""
Health Check System
Sistema completo de health checks para monitoramento
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from dataclasses import dataclass, asdict
import psutil

from sqlalchemy import text
from redis import Redis

from .logger import logger
from .metrics_collector import MetricsCollector


class HealthStatus(Enum):
    """Status de saúde dos componentes"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """Resultado de um health check"""
    name: str
    status: HealthStatus
    message: str
    duration_ms: float
    timestamp: datetime
    details: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        result = asdict(self)
        result['status'] = self.status.value
        result['timestamp'] = self.timestamp.isoformat()
        return result


class HealthChecker:
    """
    Sistema de health checks
    
    Funcionalidades:
    - Health checks de componentes individuais
    - Health check agregado do sistema
    - Monitoramento contínuo
    - Alertas baseados em saúde
    - Métricas de disponibilidade
    """
    
    def __init__(self, metrics_collector: MetricsCollector = None):
        self.metrics_collector = metrics_collector
        self.checks: Dict[str, Callable] = {}
        self.last_results: Dict[str, HealthCheckResult] = {}
        self.thresholds = {
            'response_time_ms': 5000,  # 5 segundos
            'cpu_usage_percent': 80,
            'memory_usage_percent': 85,
            'disk_usage_percent': 90,
            'database_connections': 80  # % do pool
        }
    
    def register_check(self, name: str, check_func: Callable):
        """Registra um health check"""
        self.checks[name] = check_func
        logger.info(f"Health check registrado: {name}")
    
    async def run_check(self, name: str) -> HealthCheckResult:
        """Executa um health check específico"""
        if name not in self.checks:
            return HealthCheckResult(
                name=name,
                status=HealthStatus.UNKNOWN,
                message=f"Health check '{name}' não encontrado",
                duration_ms=0,
                timestamp=datetime.utcnow()
            )
        
        start_time = time.time()
        
        try:
            check_func = self.checks[name]
            
            # Executar check com timeout
            if asyncio.iscoroutinefunction(check_func):
                result = await asyncio.wait_for(check_func(), timeout=10.0)
            else:
                result = check_func()
            
            duration_ms = (time.time() - start_time) * 1000
            
            # Se retornou apenas status
            if isinstance(result, HealthStatus):
                result = HealthCheckResult(
                    name=name,
                    status=result,
                    message="OK",
                    duration_ms=duration_ms,
                    timestamp=datetime.utcnow()
                )
            
            # Se retornou tupla (status, message, details)
            elif isinstance(result, tuple):
                status, message, details = result if len(result) == 3 else (*result, {})
                result = HealthCheckResult(
                    name=name,
                    status=status,
                    message=message,
                    duration_ms=duration_ms,
                    timestamp=datetime.utcnow(),
                    details=details
                )
            
            # Se já é HealthCheckResult
            elif isinstance(result, HealthCheckResult):
                result.duration_ms = duration_ms
                result.timestamp = datetime.utcnow()
            
            else:
                result = HealthCheckResult(
                    name=name,
                    status=HealthStatus.HEALTHY,
                    message=str(result),
                    duration_ms=duration_ms,
                    timestamp=datetime.utcnow()
                )
            
        except asyncio.TimeoutError:
            duration_ms = (time.time() - start_time) * 1000
            result = HealthCheckResult(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message="Health check timeout",
                duration_ms=duration_ms,
                timestamp=datetime.utcnow()
            )
        
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            result = HealthCheckResult(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=f"Health check falhou: {str(e)}",
                duration_ms=duration_ms,
                timestamp=datetime.utcnow()
            )
            
            logger.error(f"Health check falhou: {name}", error=str(e))
        
        # Armazenar resultado
        self.last_results[name] = result
        
        # Coletar métricas
        if self.metrics_collector:
            self.metrics_collector.record_health_check(
                name, result.status.value, result.duration_ms
            )
        
        return result
    
    async def run_all_checks(self) -> Dict[str, HealthCheckResult]:
        """Executa todos os health checks"""
        results = {}
        
        # Executar checks em paralelo
        tasks = [self.run_check(name) for name in self.checks.keys()]
        check_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(check_results):
            name = list(self.checks.keys())[i]
            
            if isinstance(result, Exception):
                results[name] = HealthCheckResult(
                    name=name,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Erro ao executar check: {str(result)}",
                    duration_ms=0,
                    timestamp=datetime.utcnow()
                )
            else:
                results[name] = result
        
        return results
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Obtém saúde geral do sistema"""
        results = await self.run_all_checks()
        
        # Calcular status geral
        statuses = [result.status for result in results.values()]
        
        if all(status == HealthStatus.HEALTHY for status in statuses):
            overall_status = HealthStatus.HEALTHY
        elif any(status == HealthStatus.UNHEALTHY for status in statuses):
            overall_status = HealthStatus.UNHEALTHY
        else:
            overall_status = HealthStatus.DEGRADED
        
        # Calcular métricas
        total_checks = len(results)
        healthy_checks = sum(1 for r in results.values() if r.status == HealthStatus.HEALTHY)
        unhealthy_checks = sum(1 for r in results.values() if r.status == HealthStatus.UNHEALTHY)
        
        return {
            "status": overall_status.value,
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {name: result.to_dict() for name, result in results.items()},
            "summary": {
                "total": total_checks,
                "healthy": healthy_checks,
                "unhealthy": unhealthy_checks,
                "availability_percent": (healthy_checks / total_checks * 100) if total_checks > 0 else 0
            }
        }
    
    def get_last_results(self) -> Dict[str, HealthCheckResult]:
        """Obtém últimos resultados dos checks"""
        return self.last_results.copy()


# Health checks específicos
class SystemHealthChecks:
    """Implementações de health checks do sistema"""
    
    def __init__(self, db_engine=None, redis_client=None):
        self.db_engine = db_engine
        self.redis_client = redis_client
    
    async def check_database(self) -> tuple[HealthStatus, str, Dict[str, Any]]:
        """Verifica saúde do banco de dados"""
        if not self.db_engine:
            return HealthStatus.UNKNOWN, "Engine do banco não configurado", {}
        
        try:
            # Testar conexão
            async with self.db_engine.connect() as conn:
                result = await conn.execute(text("SELECT 1"))
                await result.fetchone()
            
            # Verificar pool de conexões
            pool = self.db_engine.pool
            pool_size = pool.size()
            checked_out = pool.checkedout()
            usage_percent = (checked_out / pool_size * 100) if pool_size > 0 else 0
            
            details = {
                "pool_size": pool_size,
                "checked_out": checked_out,
                "usage_percent": usage_percent
            }
            
            if usage_percent > 80:
                return HealthStatus.DEGRADED, f"Pool de conexões em {usage_percent:.1f}%", details
            
            return HealthStatus.HEALTHY, "Banco de dados operacional", details
            
        except Exception as e:
            return HealthStatus.UNHEALTHY, f"Erro no banco: {str(e)}", {}
    
    async def check_redis(self) -> tuple[HealthStatus, str, Dict[str, Any]]:
        """Verifica saúde do Redis"""
        if not self.redis_client:
            return HealthStatus.UNKNOWN, "Cliente Redis não configurado", {}
        
        try:
            # Testar ping
            pong = await self.redis_client.ping()
            if not pong:
                return HealthStatus.UNHEALTHY, "Redis não respondeu ao ping", {}
            
            # Obter informações
            info = await self.redis_client.info()
            
            details = {
                "version": info.get("redis_version"),
                "connected_clients": info.get("connected_clients"),
                "used_memory": info.get("used_memory"),
                "used_memory_human": info.get("used_memory_human")
            }
            
            return HealthStatus.HEALTHY, "Redis operacional", details
            
        except Exception as e:
            return HealthStatus.UNHEALTHY, f"Erro no Redis: {str(e)}", {}
    
    def check_system_resources(self) -> tuple[HealthStatus, str, Dict[str, Any]]:
        """Verifica recursos do sistema"""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memória
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Disco
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            
            details = {
                "cpu_percent": cpu_percent,
                "memory_percent": memory_percent,
                "disk_percent": disk_percent,
                "memory_available_gb": memory.available / (1024**3),
                "disk_free_gb": disk.free / (1024**3)
            }
            
            # Verificar thresholds
            if (cpu_percent > 90 or memory_percent > 95 or disk_percent > 95):
                return HealthStatus.UNHEALTHY, "Recursos do sistema críticos", details
            elif (cpu_percent > 80 or memory_percent > 85 or disk_percent > 90):
                return HealthStatus.DEGRADED, "Recursos do sistema sob pressão", details
            
            return HealthStatus.HEALTHY, "Recursos do sistema normais", details
            
        except Exception as e:
            return HealthStatus.UNHEALTHY, f"Erro ao verificar recursos: {str(e)}", {}
    
    def check_disk_space(self) -> tuple[HealthStatus, str, Dict[str, Any]]:
        """Verifica espaço em disco"""
        try:
            disk = psutil.disk_usage('/')
            usage_percent = disk.percent
            free_gb = disk.free / (1024**3)
            
            details = {
                "usage_percent": usage_percent,
                "free_gb": round(free_gb, 2),
                "total_gb": round(disk.total / (1024**3), 2)
            }
            
            if usage_percent > 95:
                return HealthStatus.UNHEALTHY, f"Disco quase cheio: {usage_percent:.1f}%", details
            elif usage_percent > 90:
                return HealthStatus.DEGRADED, f"Pouco espaço em disco: {usage_percent:.1f}%", details
            
            return HealthStatus.HEALTHY, f"Espaço em disco adequado: {usage_percent:.1f}%", details
            
        except Exception as e:
            return HealthStatus.UNHEALTHY, f"Erro ao verificar disco: {str(e)}", {}
    
    async def check_external_services(self) -> tuple[HealthStatus, str, Dict[str, Any]]:
        """Verifica serviços externos"""
        import aiohttp
        
        services = [
            ("OpenAI API", "https://api.openai.com/v1/models"),
            ("Google Ads API", "https://googleads.googleapis.com/"),
        ]
        
        results = {}
        overall_status = HealthStatus.HEALTHY
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
            for name, url in services:
                try:
                    async with session.get(url) as response:
                        if response.status < 400:
                            results[name] = "OK"
                        else:
                            results[name] = f"HTTP {response.status}"
                            overall_status = HealthStatus.DEGRADED
                            
                except Exception as e:
                    results[name] = f"Erro: {str(e)}"
                    overall_status = HealthStatus.DEGRADED
        
        message = "Todos os serviços externos operacionais"
        if overall_status == HealthStatus.DEGRADED:
            message = "Alguns serviços externos com problemas"
        
        return overall_status, message, results


# Instância global
health_checker = HealthChecker()


# Configuração automática
def setup_health_checks(db_engine=None, redis_client=None, metrics_collector=None):
    """Configura health checks padrão"""
    
    global health_checker
    health_checker = HealthChecker(metrics_collector)
    
    # Registrar checks do sistema
    system_checks = SystemHealthChecks(db_engine, redis_client)
    
    health_checker.register_check("database", system_checks.check_database)
    health_checker.register_check("redis", system_checks.check_redis)
    health_checker.register_check("system_resources", system_checks.check_system_resources)
    health_checker.register_check("disk_space", system_checks.check_disk_space)
    health_checker.register_check("external_services", system_checks.check_external_services)
    
    logger.info("Health checks configurados")


# Endpoint para FastAPI
async def health_endpoint():
    """Endpoint de health check para FastAPI"""
    return await health_checker.get_system_health()


async def readiness_endpoint():
    """Endpoint de readiness para Kubernetes"""
    results = await health_checker.run_all_checks()
    
    # Verificar apenas componentes críticos
    critical_checks = ["database", "redis"]
    critical_results = {k: v for k, v in results.items() if k in critical_checks}
    
    if all(result.status == HealthStatus.HEALTHY for result in critical_results.values()):
        return {"status": "ready", "checks": {k: v.to_dict() for k, v in critical_results.items()}}
    else:
        return {"status": "not_ready", "checks": {k: v.to_dict() for k, v in critical_results.items()}}


async def liveness_endpoint():
    """Endpoint de liveness para Kubernetes"""
    # Check básico - aplicação está respondendo
    return {"status": "alive", "timestamp": datetime.utcnow().isoformat()}
