"""
Configuração global para testes - Backend
Setup de fixtures e configurações compartilhadas
"""

import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

import asyncpg
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import Settings
from app.infrastructure.database.connection_manager import DatabaseManager
from app.infrastructure.cache.cache_manager import CacheManager
from app.domain.entities.user_entity import User, Email, UserProfile, UserSubscription, SubscriptionType
from app.domain.repositories.user_repository import IUserRepository


# Configurações de teste
class TestSettings(Settings):
    """Configurações específicas para testes"""
    database_url: str = "sqlite+aiosqlite:///:memory:"
    redis_url: str = "redis://localhost:6379/1"  # DB 1 para testes
    testing: bool = True
    log_level: str = "DEBUG"


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Event loop para testes assíncronos"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_settings() -> TestSettings:
    """Configurações de teste"""
    return TestSettings()


@pytest_asyncio.fixture(scope="session")
async def test_engine(test_settings: TestSettings):
    """Engine de banco para testes"""
    engine = create_async_engine(
        test_settings.database_url,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
        echo=False,
    )
    
    # Criar tabelas (em um projeto real, usar Alembic)
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    await engine.dispose()


@pytest_asyncio.fixture
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Sessão de banco para testes"""
    session_factory = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def test_cache_manager() -> AsyncGenerator[CacheManager, None]:
    """Cache manager para testes"""
    cache_manager = CacheManager()
    await cache_manager.initialize()
    
    yield cache_manager
    
    # Limpar cache de teste
    if cache_manager._redis:
        await cache_manager._redis.flushdb()
    await cache_manager.close()


@pytest_asyncio.fixture
async def test_db_manager(test_engine) -> AsyncGenerator[DatabaseManager, None]:
    """Database manager para testes"""
    db_manager = DatabaseManager()
    db_manager.engine = test_engine
    db_manager.session_factory = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    yield db_manager
    
    await db_manager.close()


# Fixtures de dados de teste
@pytest.fixture
def sample_user_data() -> dict:
    """Dados de usuário para testes"""
    return {
        "email": "test@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "company": "Test Corp",
        "phone": "+1234567890"
    }


@pytest.fixture
def sample_user(sample_user_data: dict) -> User:
    """Usuário de exemplo para testes"""
    email = Email(sample_user_data["email"])
    profile = UserProfile(
        first_name=sample_user_data["first_name"],
        last_name=sample_user_data["last_name"],
        company=sample_user_data["company"],
        phone=sample_user_data["phone"]
    )
    
    return User(email=email, profile=profile)


@pytest.fixture
def multiple_users() -> list[User]:
    """Múltiplos usuários para testes"""
    users = []
    
    for i in range(5):
        email = Email(f"user{i}@example.com")
        profile = UserProfile(
            first_name=f"User{i}",
            last_name="Test",
            company=f"Company{i}"
        )
        user = User(email=email, profile=profile)
        if i % 2 == 0:
            user.verify_email()  # Alguns verificados
        users.append(user)
    
    return users


# Mock repositories
@pytest.fixture
def mock_user_repository() -> AsyncMock:
    """Mock do repositório de usuários"""
    mock_repo = AsyncMock(spec=IUserRepository)
    
    # Configurar comportamentos padrão
    mock_repo.get_by_id.return_value = None
    mock_repo.get_by_email.return_value = None
    mock_repo.save.return_value = None
    mock_repo.delete.return_value = None
    mock_repo.exists.return_value = False
    
    return mock_repo


# Fixtures de performance
@pytest.fixture
def performance_timer():
    """Timer para medir performance em testes"""
    import time
    
    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        def start(self):
            self.start_time = time.perf_counter()
        
        def stop(self):
            self.end_time = time.perf_counter()
        
        @property
        def elapsed(self) -> float:
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return 0.0
    
    return Timer()


# Fixtures de integração
@pytest_asyncio.fixture
async def integration_setup(test_session, test_cache_manager):
    """Setup completo para testes de integração"""
    return {
        "session": test_session,
        "cache": test_cache_manager,
        "initialized": True
    }


# Markers personalizados
def pytest_configure(config):
    """Configuração de markers personalizados"""
    config.addinivalue_line(
        "markers", "unit: marca testes unitários"
    )
    config.addinivalue_line(
        "markers", "integration: marca testes de integração"
    )
    config.addinivalue_line(
        "markers", "e2e: marca testes end-to-end"
    )
    config.addinivalue_line(
        "markers", "performance: marca testes de performance"
    )
    config.addinivalue_line(
        "markers", "slow: marca testes lentos"
    )


# Helpers para testes
class TestHelpers:
    """Helpers úteis para testes"""
    
    @staticmethod
    def assert_user_equals(user1: User, user2: User):
        """Compara dois usuários"""
        assert user1.id == user2.id
        assert user1.email == user2.email
        assert user1.profile == user2.profile
        assert user1.status == user2.status
    
    @staticmethod
    def create_test_user(email: str = "test@example.com") -> User:
        """Cria usuário para teste"""
        return User(
            email=Email(email),
            profile=UserProfile(first_name="Test", last_name="User")
        )
    
    @staticmethod
    async def wait_for_condition(condition_func, timeout: float = 5.0, interval: float = 0.1):
        """Espera por uma condição em testes assíncronos"""
        import asyncio
        
        start_time = asyncio.get_event_loop().time()
        
        while True:
            if await condition_func():
                return True
            
            if asyncio.get_event_loop().time() - start_time > timeout:
                return False
            
            await asyncio.sleep(interval)


@pytest.fixture
def test_helpers() -> TestHelpers:
    """Helpers para testes"""
    return TestHelpers()


# Configuração de logging para testes
@pytest.fixture(autouse=True)
def configure_test_logging():
    """Configura logging para testes"""
    import logging
    
    # Reduzir verbosidade em testes
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    
    yield
    
    # Cleanup se necessário
