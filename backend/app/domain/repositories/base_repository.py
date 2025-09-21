"""
Base Repository - DDD Pattern
Interface base para repositórios seguindo DDD
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List, Dict, Any
from uuid import UUID

from ..entities.base import AggregateRoot

# Type variable para o agregado
T = TypeVar('T', bound=AggregateRoot)


class IRepository(ABC, Generic[T]):
    """
    Interface base para repositórios DDD
    
    Responsabilidades:
    - Persistência de agregados
    - Recuperação por ID
    - Queries específicas do domínio
    - Unit of Work pattern
    """
    
    @abstractmethod
    async def get_by_id(self, entity_id: str) -> Optional[T]:
        """Recupera entidade por ID"""
        pass
    
    @abstractmethod
    async def save(self, entity: T) -> None:
        """Salva ou atualiza entidade"""
        pass
    
    @abstractmethod
    async def delete(self, entity: T) -> None:
        """Remove entidade"""
        pass
    
    @abstractmethod
    async def exists(self, entity_id: str) -> bool:
        """Verifica se entidade existe"""
        pass


class IUnitOfWork(ABC):
    """
    Interface para Unit of Work pattern
    
    Garante consistência transacional entre agregados
    """
    
    @abstractmethod
    async def begin(self) -> None:
        """Inicia transação"""
        pass
    
    @abstractmethod
    async def commit(self) -> None:
        """Confirma transação"""
        pass
    
    @abstractmethod
    async def rollback(self) -> None:
        """Desfaz transação"""
        pass
    
    @abstractmethod
    async def __aenter__(self):
        """Context manager entry"""
        await self.begin()
        return self
    
    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if exc_type is not None:
            await self.rollback()
        else:
            await self.commit()


class BaseRepository(IRepository[T], ABC):
    """
    Implementação base do repositório
    
    Fornece funcionalidades comuns:
    - Cache de entidades
    - Tracking de mudanças
    - Eventos de domínio
    """
    
    def __init__(self):
        self._identity_map: Dict[str, T] = {}
        self._new_entities: List[T] = []
        self._dirty_entities: List[T] = []
        self._removed_entities: List[T] = []
    
    def add_to_identity_map(self, entity: T) -> None:
        """Adiciona entidade ao mapa de identidade"""
        self._identity_map[entity.id] = entity
    
    def get_from_identity_map(self, entity_id: str) -> Optional[T]:
        """Recupera entidade do mapa de identidade"""
        return self._identity_map.get(entity_id)
    
    def track_new(self, entity: T) -> None:
        """Marca entidade como nova"""
        if entity not in self._new_entities:
            self._new_entities.append(entity)
        self.add_to_identity_map(entity)
    
    def track_dirty(self, entity: T) -> None:
        """Marca entidade como modificada"""
        if entity not in self._dirty_entities and entity not in self._new_entities:
            self._dirty_entities.append(entity)
    
    def track_removed(self, entity: T) -> None:
        """Marca entidade para remoção"""
        if entity in self._new_entities:
            self._new_entities.remove(entity)
        elif entity in self._dirty_entities:
            self._dirty_entities.remove(entity)
        
        if entity not in self._removed_entities:
            self._removed_entities.append(entity)
    
    async def save_changes(self) -> None:
        """Persiste todas as mudanças pendentes"""
        # Salvar novas entidades
        for entity in self._new_entities:
            await self._persist_new(entity)
        
        # Atualizar entidades modificadas
        for entity in self._dirty_entities:
            await self._persist_update(entity)
        
        # Remover entidades
        for entity in self._removed_entities:
            await self._persist_delete(entity)
        
        # Limpar tracking
        self._new_entities.clear()
        self._dirty_entities.clear()
        self._removed_entities.clear()
    
    @abstractmethod
    async def _persist_new(self, entity: T) -> None:
        """Persiste nova entidade"""
        pass
    
    @abstractmethod
    async def _persist_update(self, entity: T) -> None:
        """Atualiza entidade existente"""
        pass
    
    @abstractmethod
    async def _persist_delete(self, entity: T) -> None:
        """Remove entidade"""
        pass
    
    async def save(self, entity: T) -> None:
        """Salva entidade (implementação padrão)"""
        existing = self.get_from_identity_map(entity.id)
        
        if existing is None:
            # Nova entidade
            self.track_new(entity)
        elif existing != entity:
            # Entidade modificada
            self.track_dirty(entity)
            self.add_to_identity_map(entity)
    
    async def delete(self, entity: T) -> None:
        """Remove entidade (implementação padrão)"""
        self.track_removed(entity)
        
        # Remover do mapa de identidade
        if entity.id in self._identity_map:
            del self._identity_map[entity.id]


class QuerySpecification(ABC):
    """
    Specification pattern para queries complexas
    
    Permite composição de critérios de busca
    """
    
    @abstractmethod
    def to_sql_where(self) -> tuple[str, Dict[str, Any]]:
        """Converte para cláusula WHERE SQL"""
        pass
    
    def and_(self, other: 'QuerySpecification') -> 'AndSpecification':
        """Combina com AND"""
        return AndSpecification(self, other)
    
    def or_(self, other: 'QuerySpecification') -> 'OrSpecification':
        """Combina com OR"""
        return OrSpecification(self, other)


class AndSpecification(QuerySpecification):
    """Especificação AND"""
    
    def __init__(self, left: QuerySpecification, right: QuerySpecification):
        self.left = left
        self.right = right
    
    def to_sql_where(self) -> tuple[str, Dict[str, Any]]:
        left_sql, left_params = self.left.to_sql_where()
        right_sql, right_params = self.right.to_sql_where()
        
        combined_params = {**left_params, **right_params}
        combined_sql = f"({left_sql}) AND ({right_sql})"
        
        return combined_sql, combined_params


class OrSpecification(QuerySpecification):
    """Especificação OR"""
    
    def __init__(self, left: QuerySpecification, right: QuerySpecification):
        self.left = left
        self.right = right
    
    def to_sql_where(self) -> tuple[str, Dict[str, Any]]:
        left_sql, left_params = self.left.to_sql_where()
        right_sql, right_params = self.right.to_sql_where()
        
        combined_params = {**left_params, **right_params}
        combined_sql = f"({left_sql}) OR ({right_sql})"
        
        return combined_sql, combined_params


class PaginationResult(Generic[T]):
    """Resultado paginado"""
    
    def __init__(
        self,
        items: List[T],
        total_count: int,
        page: int,
        page_size: int
    ):
        self.items = items
        self.total_count = total_count
        self.page = page
        self.page_size = page_size
        self.total_pages = (total_count + page_size - 1) // page_size
        self.has_next = page < self.total_pages
        self.has_previous = page > 1
