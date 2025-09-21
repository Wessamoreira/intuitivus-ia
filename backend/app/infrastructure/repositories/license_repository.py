from typing import Optional, List
from sqlalchemy.orm import Session
from datetime import datetime

from app.domain.models.license import License, LicenseStatus
from app.infrastructure.security.auth import generate_license_key

class LicenseRepository:
    """Repository para operações com licenças"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, license_data: dict) -> License:
        """Cria uma nova licença"""
        # Gerar chave se não fornecida
        if 'license_key' not in license_data:
            license_data['license_key'] = generate_license_key()
        
        license = License(**license_data)
        self.db.add(license)
        self.db.commit()
        self.db.refresh(license)
        return license
    
    def get_by_id(self, license_id: int) -> Optional[License]:
        """Busca licença por ID"""
        return self.db.query(License).filter(License.id == license_id).first()
    
    def get_by_key(self, license_key: str) -> Optional[License]:
        """Busca licença por chave"""
        return self.db.query(License).filter(License.license_key == license_key).first()
    
    def get_by_user_id(self, user_id: int) -> Optional[License]:
        """Busca licença por usuário"""
        return self.db.query(License).filter(License.user_id == user_id).first()
    
    def get_available_licenses(self, limit: int = 100) -> List[License]:
        """Lista licenças disponíveis"""
        return self.db.query(License).filter(
            License.status == LicenseStatus.AVAILABLE
        ).limit(limit).all()
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[License]:
        """Lista todas as licenças com paginação"""
        return self.db.query(License).offset(skip).limit(limit).all()
    
    def update(self, license_id: int, license_data: dict) -> Optional[License]:
        """Atualiza uma licença"""
        license = self.get_by_id(license_id)
        if not license:
            return None
        
        for field, value in license_data.items():
            setattr(license, field, value)
        
        self.db.commit()
        self.db.refresh(license)
        return license
    
    def activate_license(self, license_key: str, user_id: int) -> Optional[License]:
        """Ativa uma licença para um usuário"""
        license = self.get_by_key(license_key)
        if not license:
            return None
        
        if license.status != LicenseStatus.AVAILABLE:
            return None
        
        # Ativar licença
        license.status = LicenseStatus.ACTIVE
        license.user_id = user_id
        license.activated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(license)
        return license
    
    def revoke_license(self, license_id: int) -> Optional[License]:
        """Revoga uma licença"""
        return self.update(license_id, {"status": LicenseStatus.REVOKED})
    
    def expire_license(self, license_id: int) -> Optional[License]:
        """Marca licença como expirada"""
        return self.update(license_id, {"status": LicenseStatus.EXPIRED})
    
    def validate_license_key(self, license_key: str) -> bool:
        """Valida se uma chave de licença existe e está disponível"""
        license = self.get_by_key(license_key)
        return license is not None and license.status == LicenseStatus.AVAILABLE
    
    def create_from_webhook(self, webhook_data: dict) -> License:
        """Cria licença a partir de dados de webhook"""
        license_data = {
            'purchase_email': webhook_data.get('email'),
            'purchase_platform': webhook_data.get('platform'),
            'purchase_transaction_id': webhook_data.get('transaction_id'),
            'license_type': webhook_data.get('license_type', 'pro'),
        }
        
        # Definir data de expiração se fornecida
        if 'expires_at' in webhook_data:
            license_data['expires_at'] = webhook_data['expires_at']
        
        return self.create(license_data)
