"""
User Repository - DDD Implementation
Repositório para entidade User seguindo DDD
"""

from abc import abstractmethod
from typing import Optional, List
from datetime import datetime

from .base_repository import IRepository, QuerySpecification, PaginationResult
from ..entities.user_entity import User, Email, UserStatus, SubscriptionType


class IUserRepository(IRepository[User]):
    """
    Interface do repositório de usuários
    
    Define operações específicas do domínio User
    """
    
    @abstractmethod
    async def get_by_email(self, email: Email) -> Optional[User]:
        """Busca usuário por email"""
        pass
    
    @abstractmethod
    async def find_by_status(self, status: UserStatus) -> List[User]:
        """Busca usuários por status"""
        pass
    
    @abstractmethod
    async def find_by_subscription_type(self, subscription_type: SubscriptionType) -> List[User]:
        """Busca usuários por tipo de assinatura"""
        pass
    
    @abstractmethod
    async def find_expiring_subscriptions(self, days_ahead: int = 7) -> List[User]:
        """Busca usuários com assinatura expirando"""
        pass
    
    @abstractmethod
    async def find_locked_accounts(self) -> List[User]:
        """Busca contas bloqueadas"""
        pass
    
    @abstractmethod
    async def search_users(
        self, 
        query: str, 
        page: int = 1, 
        page_size: int = 20
    ) -> PaginationResult[User]:
        """Busca usuários com paginação"""
        pass
    
    @abstractmethod
    async def email_exists(self, email: Email) -> bool:
        """Verifica se email já existe"""
        pass


# Specifications para User
class UserByEmailSpecification(QuerySpecification):
    """Especificação para buscar por email"""
    
    def __init__(self, email: Email):
        self.email = email
    
    def to_sql_where(self) -> tuple[str, dict]:
        return "email = :email", {"email": self.email.value}


class UserByStatusSpecification(QuerySpecification):
    """Especificação para buscar por status"""
    
    def __init__(self, status: UserStatus):
        self.status = status
    
    def to_sql_where(self) -> tuple[str, dict]:
        return "status = :status", {"status": self.status.value}


class UserBySubscriptionTypeSpecification(QuerySpecification):
    """Especificação para buscar por tipo de assinatura"""
    
    def __init__(self, subscription_type: SubscriptionType):
        self.subscription_type = subscription_type
    
    def to_sql_where(self) -> tuple[str, dict]:
        return "subscription_type = :sub_type", {"sub_type": self.subscription_type.value}


class ActiveUsersSpecification(QuerySpecification):
    """Especificação para usuários ativos"""
    
    def to_sql_where(self) -> tuple[str, dict]:
        return "status = :status AND is_deleted = :deleted", {
            "status": UserStatus.ACTIVE.value,
            "deleted": False
        }


class ExpiringSubscriptionsSpecification(QuerySpecification):
    """Especificação para assinaturas expirando"""
    
    def __init__(self, days_ahead: int = 7):
        self.days_ahead = days_ahead
    
    def to_sql_where(self) -> tuple[str, dict]:
        return """
            subscription_expires_at IS NOT NULL 
            AND subscription_expires_at <= :expiry_date 
            AND subscription_expires_at > :now
        """, {
            "expiry_date": datetime.utcnow().replace(day=datetime.utcnow().day + self.days_ahead),
            "now": datetime.utcnow()
        }


class LockedAccountsSpecification(QuerySpecification):
    """Especificação para contas bloqueadas"""
    
    def to_sql_where(self) -> tuple[str, dict]:
        return "locked_until IS NOT NULL AND locked_until > :now", {
            "now": datetime.utcnow()
        }


class UserSearchSpecification(QuerySpecification):
    """Especificação para busca de usuários"""
    
    def __init__(self, query: str):
        self.query = f"%{query.lower()}%"
    
    def to_sql_where(self) -> tuple[str, dict]:
        return """
            (LOWER(first_name) LIKE :query 
             OR LOWER(last_name) LIKE :query 
             OR LOWER(email) LIKE :query 
             OR LOWER(company) LIKE :query)
        """, {"query": self.query}


# Domain Services
class UserDomainService:
    """
    Serviço de domínio para User
    
    Contém lógica de negócio que não pertence a uma entidade específica
    """
    
    def __init__(self, user_repository: IUserRepository):
        self._user_repository = user_repository
    
    async def is_email_unique(self, email: Email, exclude_user_id: Optional[str] = None) -> bool:
        """Verifica se email é único"""
        existing_user = await self._user_repository.get_by_email(email)
        
        if existing_user is None:
            return True
        
        # Se estamos excluindo um usuário específico (para updates)
        if exclude_user_id and existing_user.id == exclude_user_id:
            return True
        
        return False
    
    async def can_upgrade_subscription(
        self, 
        user: User, 
        target_type: SubscriptionType
    ) -> tuple[bool, Optional[str]]:
        """Verifica se usuário pode fazer upgrade da assinatura"""
        
        # Regras de negócio para upgrade
        if user.status != UserStatus.ACTIVE:
            return False, "User must be active to upgrade subscription"
        
        if user.is_locked:
            return False, "Cannot upgrade subscription for locked account"
        
        current_type = user.subscription.type
        
        # Hierarquia de assinaturas
        hierarchy = {
            SubscriptionType.FREE: 0,
            SubscriptionType.BASIC: 1,
            SubscriptionType.PRO: 2,
            SubscriptionType.ENTERPRISE: 3
        }
        
        if hierarchy[target_type] <= hierarchy[current_type]:
            return False, "Target subscription must be higher than current"
        
        return True, None
    
    async def calculate_subscription_metrics(self) -> dict:
        """Calcula métricas de assinatura"""
        
        metrics = {}
        
        for sub_type in SubscriptionType:
            users = await self._user_repository.find_by_subscription_type(sub_type)
            metrics[sub_type.value] = {
                "count": len(users),
                "active_count": len([u for u in users if u.status == UserStatus.ACTIVE])
            }
        
        # Assinaturas expirando
        expiring = await self._user_repository.find_expiring_subscriptions()
        metrics["expiring_soon"] = len(expiring)
        
        return metrics
    
    async def get_user_engagement_score(self, user: User) -> float:
        """Calcula score de engajamento do usuário"""
        
        score = 0.0
        
        # Pontos por login recente
        if user.last_login:
            days_since_login = (datetime.utcnow() - user.last_login).days
            if days_since_login <= 1:
                score += 30
            elif days_since_login <= 7:
                score += 20
            elif days_since_login <= 30:
                score += 10
        
        # Pontos por frequência de login
        if user.login_count > 100:
            score += 25
        elif user.login_count > 50:
            score += 15
        elif user.login_count > 10:
            score += 10
        
        # Pontos por tipo de assinatura
        if user.subscription.type == SubscriptionType.ENTERPRISE:
            score += 20
        elif user.subscription.type == SubscriptionType.PRO:
            score += 15
        elif user.subscription.type == SubscriptionType.BASIC:
            score += 10
        
        # Penalidade por conta inativa
        if user.status != UserStatus.ACTIVE:
            score *= 0.5
        
        return min(100.0, score)  # Máximo 100 pontos
