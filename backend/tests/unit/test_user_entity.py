"""
Testes unitários para User Entity
Testa regras de negócio e comportamentos da entidade User
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch

from app.domain.entities.user_entity import (
    User, Email, UserProfile, UserSubscription, UserStatus, SubscriptionType
)
from app.domain.entities.base import BusinessRuleViolationException, DomainEvent


@pytest.mark.unit
class TestEmail:
    """Testes para Value Object Email"""
    
    def test_valid_email_creation(self):
        """Testa criação de email válido"""
        email = Email("test@example.com")
        assert email.value == "test@example.com"
    
    def test_email_normalization(self):
        """Testa normalização de email (lowercase)"""
        email = Email("TEST@EXAMPLE.COM")
        assert email.value == "test@example.com"
    
    def test_invalid_email_raises_error(self):
        """Testa que email inválido gera erro"""
        with pytest.raises(ValueError, match="Invalid email format"):
            Email("invalid-email")
        
        with pytest.raises(ValueError, match="Invalid email format"):
            Email("@example.com")
        
        with pytest.raises(ValueError, match="Invalid email format"):
            Email("test@")
    
    def test_empty_email_raises_error(self):
        """Testa que email vazio gera erro"""
        with pytest.raises(ValueError, match="Email cannot be empty"):
            Email("")
        
        with pytest.raises(ValueError, match="Email cannot be empty"):
            Email(None)
    
    def test_email_immutability(self):
        """Testa que Email é imutável"""
        email = Email("test@example.com")
        
        # Não deve ser possível alterar
        with pytest.raises(AttributeError):
            email.value = "new@example.com"


@pytest.mark.unit
class TestUserProfile:
    """Testes para Value Object UserProfile"""
    
    def test_valid_profile_creation(self):
        """Testa criação de perfil válido"""
        profile = UserProfile(
            first_name="John",
            last_name="Doe",
            company="Test Corp",
            phone="+1234567890"
        )
        
        assert profile.first_name == "John"
        assert profile.last_name == "Doe"
        assert profile.company == "Test Corp"
        assert profile.phone == "+1234567890"
    
    def test_full_name_property(self):
        """Testa propriedade full_name"""
        profile = UserProfile(first_name="John", last_name="Doe")
        assert profile.full_name == "John Doe"
        
        # Teste com espaços extras
        profile2 = UserProfile(first_name="  John  ", last_name="  Doe  ")
        assert profile2.full_name.strip() == "John     Doe"
    
    def test_profile_immutability(self):
        """Testa que UserProfile é imutável"""
        profile = UserProfile(first_name="John", last_name="Doe")
        
        with pytest.raises(AttributeError):
            profile.first_name = "Jane"


@pytest.mark.unit
class TestUserSubscription:
    """Testes para Value Object UserSubscription"""
    
    def test_active_subscription_without_expiry(self):
        """Testa assinatura ativa sem data de expiração"""
        subscription = UserSubscription(
            type=SubscriptionType.PRO,
            started_at=datetime.utcnow()
        )
        
        assert subscription.is_active is True
        assert subscription.days_remaining is None
    
    def test_active_subscription_with_future_expiry(self):
        """Testa assinatura ativa com expiração futura"""
        future_date = datetime.utcnow() + timedelta(days=30)
        subscription = UserSubscription(
            type=SubscriptionType.BASIC,
            started_at=datetime.utcnow(),
            expires_at=future_date
        )
        
        assert subscription.is_active is True
        assert subscription.days_remaining == 30
    
    def test_expired_subscription(self):
        """Testa assinatura expirada"""
        past_date = datetime.utcnow() - timedelta(days=1)
        subscription = UserSubscription(
            type=SubscriptionType.BASIC,
            started_at=datetime.utcnow() - timedelta(days=31),
            expires_at=past_date
        )
        
        assert subscription.is_active is False
        assert subscription.days_remaining == 0


@pytest.mark.unit
class TestUser:
    """Testes para entidade User"""
    
    def test_user_creation_with_valid_data(self, sample_user_data):
        """Testa criação de usuário com dados válidos"""
        email = Email(sample_user_data["email"])
        profile = UserProfile(
            first_name=sample_user_data["first_name"],
            last_name=sample_user_data["last_name"]
        )
        
        user = User(email=email, profile=profile)
        
        assert user.email == email
        assert user.profile == profile
        assert user.status == UserStatus.PENDING_VERIFICATION
        assert user.subscription.type == SubscriptionType.FREE
        assert user.subscription.is_trial is True
        assert user.login_count == 0
        assert user.is_locked is False
    
    def test_user_creation_generates_domain_event(self, sample_user_data):
        """Testa que criação de usuário gera evento de domínio"""
        email = Email(sample_user_data["email"])
        profile = UserProfile(
            first_name=sample_user_data["first_name"],
            last_name=sample_user_data["last_name"]
        )
        
        user = User(email=email, profile=profile)
        
        events = user.domain_events
        assert len(events) == 1
        assert events[0].event_type == "user_created"
        assert events[0].data["email"] == sample_user_data["email"]
        assert events[0].data["full_name"] == f"{sample_user_data['first_name']} {sample_user_data['last_name']}"
    
    def test_user_creation_without_email_raises_error(self):
        """Testa que criação sem email gera erro"""
        profile = UserProfile(first_name="John", last_name="Doe")
        
        with pytest.raises(BusinessRuleViolationException, match="Email is required"):
            User(email=None, profile=profile)
    
    def test_user_creation_without_profile_raises_error(self):
        """Testa que criação sem perfil gera erro"""
        email = Email("test@example.com")
        
        with pytest.raises(BusinessRuleViolationException, match="Profile is required"):
            User(email=email, profile=None)
    
    def test_set_password(self, sample_user):
        """Testa definição de senha"""
        password_hash = "hashed_password_123"
        
        sample_user.set_password(password_hash)
        
        assert sample_user._password_hash == password_hash
        
        # Verifica evento gerado
        events = [e for e in sample_user.domain_events if e.event_type == "password_changed"]
        assert len(events) == 1
    
    def test_set_empty_password_raises_error(self, sample_user):
        """Testa que senha vazia gera erro"""
        with pytest.raises(BusinessRuleViolationException, match="Password hash cannot be empty"):
            sample_user.set_password("")
        
        with pytest.raises(BusinessRuleViolationException, match="Password hash cannot be empty"):
            sample_user.set_password(None)
    
    def test_verify_email(self, sample_user):
        """Testa verificação de email"""
        assert sample_user.status == UserStatus.PENDING_VERIFICATION
        
        sample_user.verify_email()
        
        assert sample_user.status == UserStatus.ACTIVE
        
        # Verifica evento gerado
        events = [e for e in sample_user.domain_events if e.event_type == "email_verified"]
        assert len(events) == 1
        assert events[0].data["email"] == sample_user.email.value
    
    def test_verify_already_verified_email_raises_error(self, sample_user):
        """Testa que verificar email já verificado gera erro"""
        sample_user.verify_email()  # Primeira verificação
        
        with pytest.raises(BusinessRuleViolationException, match="Email already verified"):
            sample_user.verify_email()  # Segunda verificação
    
    def test_successful_login(self, sample_user):
        """Testa login bem-sucedido"""
        sample_user.verify_email()  # Ativar usuário
        initial_count = sample_user.login_count
        
        sample_user.record_successful_login()
        
        assert sample_user.login_count == initial_count + 1
        assert sample_user.last_login is not None
        assert sample_user._failed_login_attempts == 0
        
        # Verifica evento gerado
        events = [e for e in sample_user.domain_events if e.event_type == "user_logged_in"]
        assert len(events) == 1
    
    def test_login_inactive_user_raises_error(self, sample_user):
        """Testa que login de usuário inativo gera erro"""
        # Usuário não verificado (inativo)
        with pytest.raises(BusinessRuleViolationException, match="User is not active"):
            sample_user.record_successful_login()
    
    def test_failed_login_attempts(self, sample_user):
        """Testa tentativas de login falhadas"""
        sample_user.verify_email()
        
        # 4 tentativas falhadas (não deve bloquear ainda)
        for i in range(4):
            sample_user.record_failed_login()
            assert sample_user.is_locked is False
        
        # 5ª tentativa deve bloquear
        sample_user.record_failed_login()
        assert sample_user.is_locked is True
        
        # Verifica evento de bloqueio
        events = [e for e in sample_user.domain_events if e.event_type == "account_locked"]
        assert len(events) == 1
    
    def test_login_locked_account_raises_error(self, sample_user):
        """Testa que login em conta bloqueada gera erro"""
        sample_user.verify_email()
        
        # Bloquear conta
        for _ in range(5):
            sample_user.record_failed_login()
        
        with pytest.raises(BusinessRuleViolationException, match="Account is locked"):
            sample_user.record_successful_login()
    
    def test_unlock_account(self, sample_user):
        """Testa desbloqueio de conta"""
        sample_user.verify_email()
        
        # Bloquear conta
        for _ in range(5):
            sample_user.record_failed_login()
        
        assert sample_user.is_locked is True
        
        # Desbloquear
        sample_user.unlock_account()
        
        assert sample_user.is_locked is False
        assert sample_user._failed_login_attempts == 0
        
        # Verifica evento gerado
        events = [e for e in sample_user.domain_events if e.event_type == "account_unlocked"]
        assert len(events) == 1
    
    def test_upgrade_subscription(self, sample_user):
        """Testa upgrade de assinatura"""
        assert sample_user.subscription.type == SubscriptionType.FREE
        
        expires_at = datetime.utcnow() + timedelta(days=365)
        sample_user.upgrade_subscription(SubscriptionType.PRO, expires_at)
        
        assert sample_user.subscription.type == SubscriptionType.PRO
        assert sample_user.subscription.expires_at == expires_at
        assert sample_user.subscription.is_trial is False
        
        # Verifica evento gerado
        events = [e for e in sample_user.domain_events if e.event_type == "subscription_upgraded"]
        assert len(events) == 1
        assert events[0].data["old_type"] == SubscriptionType.FREE.value
        assert events[0].data["new_type"] == SubscriptionType.PRO.value
    
    def test_upgrade_to_same_subscription_does_nothing(self, sample_user):
        """Testa que upgrade para mesma assinatura não faz nada"""
        initial_events_count = len(sample_user.domain_events)
        
        sample_user.upgrade_subscription(SubscriptionType.FREE)
        
        # Não deve gerar eventos adicionais
        assert len(sample_user.domain_events) == initial_events_count
    
    def test_suspend_user(self, sample_user):
        """Testa suspensão de usuário"""
        sample_user.verify_email()
        reason = "Violation of terms"
        
        sample_user.suspend(reason)
        
        assert sample_user.status == UserStatus.SUSPENDED
        
        # Verifica evento gerado
        events = [e for e in sample_user.domain_events if e.event_type == "user_suspended"]
        assert len(events) == 1
        assert events[0].data["reason"] == reason
        assert events[0].data["previous_status"] == UserStatus.ACTIVE.value
    
    def test_reactivate_suspended_user(self, sample_user):
        """Testa reativação de usuário suspenso"""
        sample_user.verify_email()
        sample_user.suspend("Test suspension")
        
        sample_user.reactivate()
        
        assert sample_user.status == UserStatus.ACTIVE
        
        # Verifica evento gerado
        events = [e for e in sample_user.domain_events if e.event_type == "user_reactivated"]
        assert len(events) == 1
    
    def test_reactivate_non_suspended_user_raises_error(self, sample_user):
        """Testa que reativar usuário não suspenso gera erro"""
        sample_user.verify_email()  # Usuário ativo
        
        with pytest.raises(BusinessRuleViolationException, match="User is not suspended"):
            sample_user.reactivate()
    
    def test_update_profile(self, sample_user):
        """Testa atualização de perfil"""
        new_profile = UserProfile(
            first_name="Jane",
            last_name="Smith",
            company="New Corp"
        )
        
        old_name = sample_user.profile.full_name
        sample_user.update_profile(new_profile)
        
        assert sample_user.profile == new_profile
        
        # Verifica evento gerado
        events = [e for e in sample_user.domain_events if e.event_type == "profile_updated"]
        assert len(events) == 1
        assert events[0].data["old_name"] == old_name
        assert events[0].data["new_name"] == new_profile.full_name
    
    def test_can_access_premium_features(self, sample_user):
        """Testa acesso a recursos premium"""
        # Usuário free não deve ter acesso
        assert sample_user.can_access_premium_features is False
        
        # Ativar e fazer upgrade
        sample_user.verify_email()
        sample_user.upgrade_subscription(SubscriptionType.PRO)
        
        assert sample_user.can_access_premium_features is True
        
        # Suspender usuário
        sample_user.suspend("Test")
        assert sample_user.can_access_premium_features is False
    
    def test_user_equality(self, sample_user_data):
        """Testa igualdade entre usuários"""
        email = Email(sample_user_data["email"])
        profile = UserProfile(
            first_name=sample_user_data["first_name"],
            last_name=sample_user_data["last_name"]
        )
        
        user1 = User(email=email, profile=profile, user_id="test-id")
        user2 = User(email=email, profile=profile, user_id="test-id")
        user3 = User(email=email, profile=profile, user_id="different-id")
        
        assert user1 == user2  # Mesmo ID
        assert user1 != user3  # IDs diferentes
        assert user1 != "not-a-user"  # Tipo diferente
