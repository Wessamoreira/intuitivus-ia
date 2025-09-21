"""
User Entity - DDD Implementation
Entidade User seguindo padrões Domain-Driven Design
"""

from datetime import datetime
from typing import Optional, List
from enum import Enum

from .base import AggregateRoot, ValueObject, DomainEvent, BusinessRuleViolationException


class UserStatus(str, Enum):
    """Status do usuário"""
    ACTIVE = "active"
    INACTIVE = "inactive" 
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"


class SubscriptionType(str, Enum):
    """Tipo de assinatura"""
    FREE = "free"
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class Email(ValueObject):
    """Value Object para email"""
    value: str
    
    def __init__(self, value: str):
        import re
        
        if not value or not isinstance(value, str):
            raise ValueError("Email cannot be empty")
        
        # Validação básica de email
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, value.lower()):
            raise ValueError(f"Invalid email format: {value}")
        
        super().__init__(value=value.lower())


class UserProfile(ValueObject):
    """Value Object para perfil do usuário"""
    first_name: str
    last_name: str
    company: Optional[str] = None
    phone: Optional[str] = None
    
    @property
    def full_name(self) -> str:
        """Nome completo do usuário"""
        return f"{self.first_name} {self.last_name}".strip()


class UserSubscription(ValueObject):
    """Value Object para assinatura"""
    type: SubscriptionType
    started_at: datetime
    expires_at: Optional[datetime] = None
    is_trial: bool = False
    
    @property
    def is_active(self) -> bool:
        """Verifica se a assinatura está ativa"""
        if self.expires_at is None:
            return True  # Assinatura vitalícia
        return datetime.utcnow() < self.expires_at
    
    @property
    def days_remaining(self) -> Optional[int]:
        """Dias restantes da assinatura"""
        if self.expires_at is None:
            return None
        
        remaining = self.expires_at - datetime.utcnow()
        return max(0, remaining.days)


class User(AggregateRoot):
    """
    Entidade User seguindo DDD
    
    Regras de negócio:
    - Email deve ser único
    - Usuário deve ter perfil completo para ativar
    - Assinatura controla funcionalidades
    - Histórico de login é mantido
    """
    
    def __init__(
        self,
        email: Email,
        profile: UserProfile,
        user_id: Optional[str] = None
    ):
        super().__init__(user_id)
        
        # Validações de negócio
        if not email:
            raise BusinessRuleViolationException("Email is required")
        if not profile:
            raise BusinessRuleViolationException("Profile is required")
        
        self._email = email
        self._profile = profile
        self._status = UserStatus.PENDING_VERIFICATION
        self._subscription = UserSubscription(
            type=SubscriptionType.FREE,
            started_at=datetime.utcnow(),
            is_trial=True
        )
        
        # Dados de autenticação
        self._password_hash: Optional[str] = None
        self._last_login: Optional[datetime] = None
        self._login_count = 0
        self._failed_login_attempts = 0
        self._locked_until: Optional[datetime] = None
        
        # Evento de criação
        self.add_domain_event(DomainEvent(
            event_type="user_created",
            aggregate_id=self.id,
            data={
                "email": self._email.value,
                "full_name": self._profile.full_name,
                "subscription_type": self._subscription.type.value
            }
        ))
    
    # Properties
    @property
    def email(self) -> Email:
        return self._email
    
    @property
    def profile(self) -> UserProfile:
        return self._profile
    
    @property
    def status(self) -> UserStatus:
        return self._status
    
    @property
    def subscription(self) -> UserSubscription:
        return self._subscription
    
    @property
    def last_login(self) -> Optional[datetime]:
        return self._last_login
    
    @property
    def login_count(self) -> int:
        return self._login_count
    
    @property
    def is_locked(self) -> bool:
        """Verifica se a conta está bloqueada"""
        if self._locked_until is None:
            return False
        return datetime.utcnow() < self._locked_until
    
    @property
    def can_access_premium_features(self) -> bool:
        """Verifica se pode acessar recursos premium"""
        return (
            self._status == UserStatus.ACTIVE and
            self._subscription.is_active and
            self._subscription.type in [SubscriptionType.PRO, SubscriptionType.ENTERPRISE]
        )
    
    # Métodos de negócio
    def set_password(self, password_hash: str) -> None:
        """Define hash da senha"""
        if not password_hash:
            raise BusinessRuleViolationException("Password hash cannot be empty")
        
        self._password_hash = password_hash
        self.mark_as_modified()
        
        self.add_domain_event(DomainEvent(
            event_type="password_changed",
            aggregate_id=self.id
        ))
    
    def verify_email(self) -> None:
        """Verifica o email do usuário"""
        if self._status != UserStatus.PENDING_VERIFICATION:
            raise BusinessRuleViolationException("Email already verified")
        
        self._status = UserStatus.ACTIVE
        self.mark_as_modified()
        
        self.add_domain_event(DomainEvent(
            event_type="email_verified",
            aggregate_id=self.id,
            data={"email": self._email.value}
        ))
    
    def record_successful_login(self) -> None:
        """Registra login bem-sucedido"""
        if self._status != UserStatus.ACTIVE:
            raise BusinessRuleViolationException("User is not active")
        
        if self.is_locked:
            raise BusinessRuleViolationException("Account is locked")
        
        self._last_login = datetime.utcnow()
        self._login_count += 1
        self._failed_login_attempts = 0  # Reset tentativas falhas
        self.mark_as_modified()
        
        self.add_domain_event(DomainEvent(
            event_type="user_logged_in",
            aggregate_id=self.id,
            data={"login_count": self._login_count}
        ))
    
    def record_failed_login(self) -> None:
        """Registra tentativa de login falhada"""
        self._failed_login_attempts += 1
        
        # Bloquear após 5 tentativas
        if self._failed_login_attempts >= 5:
            self._locked_until = datetime.utcnow().replace(
                hour=datetime.utcnow().hour + 1  # Bloquear por 1 hora
            )
            
            self.add_domain_event(DomainEvent(
                event_type="account_locked",
                aggregate_id=self.id,
                data={"failed_attempts": self._failed_login_attempts}
            ))
        
        self.mark_as_modified()
    
    def unlock_account(self) -> None:
        """Desbloqueia a conta"""
        if not self.is_locked:
            return
        
        self._locked_until = None
        self._failed_login_attempts = 0
        self.mark_as_modified()
        
        self.add_domain_event(DomainEvent(
            event_type="account_unlocked",
            aggregate_id=self.id
        ))
    
    def upgrade_subscription(
        self, 
        new_type: SubscriptionType,
        expires_at: Optional[datetime] = None
    ) -> None:
        """Atualiza assinatura"""
        if new_type == self._subscription.type:
            return
        
        old_subscription = self._subscription
        
        self._subscription = UserSubscription(
            type=new_type,
            started_at=datetime.utcnow(),
            expires_at=expires_at,
            is_trial=False
        )
        
        self.mark_as_modified()
        
        self.add_domain_event(DomainEvent(
            event_type="subscription_upgraded",
            aggregate_id=self.id,
            data={
                "old_type": old_subscription.type.value,
                "new_type": new_type.value,
                "expires_at": expires_at.isoformat() if expires_at else None
            }
        ))
    
    def suspend(self, reason: str) -> None:
        """Suspende o usuário"""
        if self._status == UserStatus.SUSPENDED:
            return
        
        old_status = self._status
        self._status = UserStatus.SUSPENDED
        self.mark_as_modified()
        
        self.add_domain_event(DomainEvent(
            event_type="user_suspended",
            aggregate_id=self.id,
            data={
                "reason": reason,
                "previous_status": old_status.value
            }
        ))
    
    def reactivate(self) -> None:
        """Reativa usuário suspenso"""
        if self._status != UserStatus.SUSPENDED:
            raise BusinessRuleViolationException("User is not suspended")
        
        self._status = UserStatus.ACTIVE
        self.mark_as_modified()
        
        self.add_domain_event(DomainEvent(
            event_type="user_reactivated",
            aggregate_id=self.id
        ))
    
    def update_profile(self, new_profile: UserProfile) -> None:
        """Atualiza perfil do usuário"""
        if new_profile == self._profile:
            return
        
        old_profile = self._profile
        self._profile = new_profile
        self.mark_as_modified()
        
        self.add_domain_event(DomainEvent(
            event_type="profile_updated",
            aggregate_id=self.id,
            data={
                "old_name": old_profile.full_name,
                "new_name": new_profile.full_name
            }
        ))
