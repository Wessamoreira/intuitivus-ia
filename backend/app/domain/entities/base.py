"""
Base Entity - DDD Pattern
Entidade base com comportamentos comuns
"""

from abc import ABC
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class DomainEvent(BaseModel):
    """Evento de domínio base"""
    event_id: UUID = Field(default_factory=uuid4)
    event_type: str
    aggregate_id: str
    occurred_at: datetime = Field(default_factory=datetime.utcnow)
    data: Dict[str, Any] = Field(default_factory=dict)
    version: int = 1


class BaseEntity(ABC):
    """
    Entidade base seguindo padrões DDD
    
    Características:
    - Identidade única
    - Eventos de domínio
    - Validações de negócio
    - Imutabilidade controlada
    """
    
    def __init__(self, entity_id: Optional[str] = None):
        self._id = entity_id or str(uuid4())
        self._domain_events: List[DomainEvent] = []
        self._created_at = datetime.utcnow()
        self._updated_at = datetime.utcnow()
        self._version = 1
    
    @property
    def id(self) -> str:
        """Identificador único da entidade"""
        return self._id
    
    @property
    def created_at(self) -> datetime:
        """Data de criação"""
        return self._created_at
    
    @property
    def updated_at(self) -> datetime:
        """Data da última atualização"""
        return self._updated_at
    
    @property
    def version(self) -> int:
        """Versão para controle de concorrência otimista"""
        return self._version
    
    @property
    def domain_events(self) -> List[DomainEvent]:
        """Eventos de domínio pendentes"""
        return self._domain_events.copy()
    
    def add_domain_event(self, event: DomainEvent) -> None:
        """Adiciona um evento de domínio"""
        self._domain_events.append(event)
    
    def clear_domain_events(self) -> None:
        """Limpa eventos de domínio após processamento"""
        self._domain_events.clear()
    
    def mark_as_modified(self) -> None:
        """Marca entidade como modificada"""
        self._updated_at = datetime.utcnow()
        self._version += 1
    
    def __eq__(self, other: object) -> bool:
        """Igualdade baseada no ID"""
        if not isinstance(other, BaseEntity):
            return False
        return self._id == other._id
    
    def __hash__(self) -> int:
        """Hash baseado no ID"""
        return hash(self._id)


class AggregateRoot(BaseEntity):
    """
    Raiz de agregado DDD
    
    Responsabilidades:
    - Garantir consistência do agregado
    - Coordenar mudanças
    - Publicar eventos de domínio
    """
    
    def __init__(self, entity_id: Optional[str] = None):
        super().__init__(entity_id)
        self._is_deleted = False
    
    @property
    def is_deleted(self) -> bool:
        """Indica se o agregado foi marcado para exclusão"""
        return self._is_deleted
    
    def mark_as_deleted(self) -> None:
        """Marca agregado como excluído (soft delete)"""
        if self._is_deleted:
            raise ValueError("Aggregate is already deleted")
        
        self._is_deleted = True
        self.mark_as_modified()
        
        # Evento de exclusão
        self.add_domain_event(DomainEvent(
            event_type="aggregate_deleted",
            aggregate_id=self._id,
            data={"entity_type": self.__class__.__name__}
        ))


class ValueObject(BaseModel):
    """
    Objeto de valor DDD
    
    Características:
    - Imutável
    - Sem identidade
    - Igualdade baseada em valor
    """
    
    class Config:
        frozen = True  # Imutável
        validate_assignment = True
    
    def __hash__(self) -> int:
        """Hash baseado nos valores"""
        return hash(tuple(self.__dict__.values()))


# Exceções de domínio
class DomainException(Exception):
    """Exceção base do domínio"""
    
    def __init__(self, message: str, error_code: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code


class BusinessRuleViolationException(DomainException):
    """Violação de regra de negócio"""
    pass


class EntityNotFoundException(DomainException):
    """Entidade não encontrada"""
    pass


class ConcurrencyException(DomainException):
    """Conflito de concorrência"""
    pass
