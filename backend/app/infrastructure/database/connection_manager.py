"""
Database Connection Manager - Optimized Pooling
Sistema otimizado de connection pooling para PostgreSQL
"""

import asyncio
from typing import Optional, Dict, Any, AsyncGenerator
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
import logging

import asyncpg
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import QueuePool
from sqlalchemy import text, event
from sqlalchemy.engine import Engine

from app.core.config import settings

logger = logging.getLogger(__name__)


class DatabaseConfig:
    """Configuração otimizada do banco de dados"""
    
    # Connection Pool Settings
    POOL_SIZE = 20  # Conexões simultâneas
    MAX_OVERFLOW = 30  # Conexões extras em pico
    POOL_TIMEOUT = 30  # Timeout para obter conexão
    POOL_RECYCLE = 3600  # Reciclar conexões a cada 1h
    POOL_PRE_PING = True  # Verificar conexões antes de usar
    
    # Query Optimization
    STATEMENT_CACHE_SIZE = 1000  # Cache de prepared statements
    QUERY_TIMEOUT = 30  # Timeout para queries
    
    # Connection Settings
    CONNECT_TIMEOUT = 10
    COMMAND_TIMEOUT = 60
    SERVER_SETTINGS = {
        'application_name': 'ai_agents_platform',
        'tcp_keepalives_idle': '600',
        'tcp_keepalives_interval': '30',
        'tcp_keepalives_count': '3',
    }


class ConnectionMetrics:
    """Métricas de conexão"""
    
    def __init__(self):
        self.total_connections = 0
        self.active_connections = 0
        self.pool_hits = 0
        self.pool_misses = 0
        self.slow_queries = 0
        self.failed_connections = 0
        self.query_times = []
        self.last_reset = datetime.utcnow()
    
    def record_connection_acquired(self):
        self.active_connections += 1
        self.pool_hits += 1
    
    def record_connection_released(self):
        self.active_connections = max(0, self.active_connections - 1)
    
    def record_connection_created(self):
        self.total_connections += 1
        self.pool_misses += 1
    
    def record_connection_failed(self):
        self.failed_connections += 1
    
    def record_query_time(self, duration: float):
        self.query_times.append(duration)
        if duration > 1.0:  # Queries > 1s são consideradas lentas
            self.slow_queries += 1
        
        # Manter apenas últimas 1000 queries
        if len(self.query_times) > 1000:
            self.query_times = self.query_times[-1000:]
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas"""
        avg_query_time = (
            sum(self.query_times) / len(self.query_times)
            if self.query_times else 0
        )
        
        return {
            "total_connections": self.total_connections,
            "active_connections": self.active_connections,
            "pool_efficiency": (
                self.pool_hits / (self.pool_hits + self.pool_misses) * 100
                if (self.pool_hits + self.pool_misses) > 0 else 0
            ),
            "slow_queries": self.slow_queries,
            "failed_connections": self.failed_connections,
            "avg_query_time": round(avg_query_time, 3),
            "uptime_hours": (datetime.utcnow() - self.last_reset).total_seconds() / 3600
        }
    
    def reset(self):
        """Reset das métricas"""
        self.__init__()


class DatabaseManager:
    """
    Gerenciador de conexões de banco otimizado
    
    Funcionalidades:
    - Connection pooling inteligente
    - Métricas detalhadas
    - Query optimization
    - Health checks automáticos
    - Retry logic
    """
    
    def __init__(self):
        self.engine: Optional[Engine] = None
        self.session_factory: Optional[async_sessionmaker] = None
        self.raw_pool: Optional[asyncpg.Pool] = None
        self.metrics = ConnectionMetrics()
        self._health_check_task: Optional[asyncio.Task] = None
        self._is_healthy = False
    
    async def initialize(self) -> None:
        """Inicializa conexões com o banco"""
        try:
            # SQLAlchemy Engine com pool otimizado
            self.engine = create_async_engine(
                settings.database_url.replace('postgresql://', 'postgresql+asyncpg://'),
                
                # Pool Configuration
                poolclass=QueuePool,
                pool_size=DatabaseConfig.POOL_SIZE,
                max_overflow=DatabaseConfig.MAX_OVERFLOW,
                pool_timeout=DatabaseConfig.POOL_TIMEOUT,
                pool_recycle=DatabaseConfig.POOL_RECYCLE,
                pool_pre_ping=DatabaseConfig.POOL_PRE_PING,
                
                # Connection Arguments
                connect_args={
                    "server_settings": DatabaseConfig.SERVER_SETTINGS,
                    "command_timeout": DatabaseConfig.COMMAND_TIMEOUT,
                    "statement_cache_size": DatabaseConfig.STATEMENT_CACHE_SIZE,
                },
                
                # Engine Options
                echo=settings.DEBUG,  # Log queries em desenvolvimento
                future=True,
            )
            
            # Session Factory
            self.session_factory = async_sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=True,
                autocommit=False
            )
            
            # Raw AsyncPG Pool para queries de alta performance
            self.raw_pool = await asyncpg.create_pool(
                settings.database_url,
                min_size=5,
                max_size=DatabaseConfig.POOL_SIZE,
                timeout=DatabaseConfig.CONNECT_TIMEOUT,
                command_timeout=DatabaseConfig.QUERY_TIMEOUT,
                server_settings=DatabaseConfig.SERVER_SETTINGS
            )
            
            # Event listeners para métricas
            self._setup_event_listeners()
            
            # Testar conexão
            await self._test_connection()
            
            # Iniciar health checks
            self._health_check_task = asyncio.create_task(self._health_check_loop())
            
            self._is_healthy = True
            logger.info("✅ Database connections initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize database: {e}")
            raise
    
    def _setup_event_listeners(self):
        """Configura listeners para métricas"""
        
        @event.listens_for(self.engine.sync_engine, "connect")
        def on_connect(dbapi_connection, connection_record):
            self.metrics.record_connection_created()
        
        @event.listens_for(self.engine.sync_engine, "checkout")
        def on_checkout(dbapi_connection, connection_record, connection_proxy):
            self.metrics.record_connection_acquired()
        
        @event.listens_for(self.engine.sync_engine, "checkin")
        def on_checkin(dbapi_connection, connection_record):
            self.metrics.record_connection_released()
    
    async def _test_connection(self):
        """Testa conexão com o banco"""
        async with self.get_session() as session:
            result = await session.execute(text("SELECT 1"))
            assert result.scalar() == 1
    
    async def _health_check_loop(self):
        """Loop de health check"""
        while True:
            try:
                await asyncio.sleep(30)  # Check a cada 30s
                await self._test_connection()
                self._is_healthy = True
            except Exception as e:
                logger.warning(f"Database health check failed: {e}")
                self._is_healthy = False
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Context manager para sessões SQLAlchemy"""
        if not self.session_factory:
            raise RuntimeError("Database not initialized")
        
        session = self.session_factory()
        start_time = datetime.utcnow()
        
        try:
            yield session
            await session.commit()
            
        except Exception as e:
            await session.rollback()
            self.metrics.record_connection_failed()
            logger.error(f"Database session error: {e}")
            raise
            
        finally:
            await session.close()
            
            # Registrar tempo da transação
            duration = (datetime.utcnow() - start_time).total_seconds()
            self.metrics.record_query_time(duration)
    
    @asynccontextmanager
    async def get_raw_connection(self) -> AsyncGenerator[asyncpg.Connection, None]:
        """Context manager para conexões raw AsyncPG (alta performance)"""
        if not self.raw_pool:
            raise RuntimeError("Raw pool not initialized")
        
        start_time = datetime.utcnow()
        
        async with self.raw_pool.acquire() as connection:
            try:
                yield connection
                
            except Exception as e:
                self.metrics.record_connection_failed()
                logger.error(f"Raw connection error: {e}")
                raise
                
            finally:
                # Registrar tempo
                duration = (datetime.utcnow() - start_time).total_seconds()
                self.metrics.record_query_time(duration)
    
    async def execute_raw_query(
        self, 
        query: str, 
        *args, 
        fetch_mode: str = "all"
    ) -> Any:
        """
        Executa query raw de alta performance
        
        Args:
            query: SQL query
            *args: Parâmetros da query
            fetch_mode: 'all', 'one', 'val', 'none'
        """
        async with self.get_raw_connection() as conn:
            if fetch_mode == "all":
                return await conn.fetch(query, *args)
            elif fetch_mode == "one":
                return await conn.fetchrow(query, *args)
            elif fetch_mode == "val":
                return await conn.fetchval(query, *args)
            elif fetch_mode == "none":
                return await conn.execute(query, *args)
            else:
                raise ValueError(f"Invalid fetch_mode: {fetch_mode}")
    
    async def execute_batch(self, query: str, args_list: list) -> None:
        """Executa batch de queries para alta performance"""
        async with self.get_raw_connection() as conn:
            await conn.executemany(query, args_list)
    
    async def get_pool_status(self) -> Dict[str, Any]:
        """Retorna status do pool de conexões"""
        if not self.engine:
            return {"status": "not_initialized"}
        
        pool = self.engine.pool
        
        return {
            "pool_size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "invalid": pool.invalid(),
            "is_healthy": self._is_healthy,
            "metrics": self.metrics.get_stats()
        }
    
    async def close(self):
        """Fecha todas as conexões"""
        if self._health_check_task:
            self._health_check_task.cancel()
        
        if self.raw_pool:
            await self.raw_pool.close()
        
        if self.engine:
            await self.engine.dispose()
        
        logger.info("Database connections closed")


# Instância global
db_manager = DatabaseManager()


# Decorators para otimização
def with_db_session(func):
    """Decorator para injetar sessão de banco"""
    async def wrapper(*args, **kwargs):
        async with db_manager.get_session() as session:
            return await func(session, *args, **kwargs)
    return wrapper


def with_raw_connection(func):
    """Decorator para injetar conexão raw"""
    async def wrapper(*args, **kwargs):
        async with db_manager.get_raw_connection() as conn:
            return await func(conn, *args, **kwargs)
    return wrapper


# Query Builders otimizados
class OptimizedQueries:
    """Queries otimizadas para operações comuns"""
    
    @staticmethod
    async def get_user_with_stats(user_id: str) -> Optional[Dict]:
        """Query otimizada para usuário com estatísticas"""
        query = """
        SELECT 
            u.*,
            COUNT(a.id) as agent_count,
            COUNT(CASE WHEN a.status = 'active' THEN 1 END) as active_agents,
            COALESCE(SUM(a.tasks_completed), 0) as total_tasks
        FROM users u
        LEFT JOIN agents a ON u.id = a.user_id
        WHERE u.id = $1 AND u.is_deleted = false
        GROUP BY u.id
        """
        
        return await db_manager.execute_raw_query(query, user_id, fetch_mode="one")
    
    @staticmethod
    async def get_agent_performance_batch(agent_ids: list) -> list:
        """Query em batch para performance de agentes"""
        query = """
        SELECT 
            a.id,
            a.name,
            a.status,
            COUNT(t.id) as total_tasks,
            COUNT(CASE WHEN t.status = 'completed' THEN 1 END) as completed_tasks,
            AVG(CASE WHEN t.status = 'completed' THEN t.execution_time END) as avg_execution_time
        FROM agents a
        LEFT JOIN tasks t ON a.id = t.agent_id
        WHERE a.id = ANY($1)
        GROUP BY a.id, a.name, a.status
        """
        
        return await db_manager.execute_raw_query(query, agent_ids, fetch_mode="all")
    
    @staticmethod
    async def update_user_last_login_batch(user_login_data: list):
        """Update em batch para último login"""
        query = """
        UPDATE users 
        SET last_login = $2, login_count = login_count + 1
        WHERE id = $1
        """
        
        await db_manager.execute_batch(query, user_login_data)
