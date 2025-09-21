"""
User Repository Implementation
Implementação básica para corrigir erro de importação
"""

from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.user import User


class UserRepository:
    """Repository básico para usuários"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        """Busca usuário por ID"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Busca usuário por email"""
        return self.db.query(User).filter(User.email == email).first()
    
    def get_all(self) -> List[User]:
        """Lista todos os usuários"""
        return self.db.query(User).all()
    
    def create(self, user_data: dict) -> User:
        """Cria novo usuário"""
        user = User(**user_data)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def update(self, user_id: int, user_data: dict) -> Optional[User]:
        """Atualiza usuário"""
        user = self.get_by_id(user_id)
        if user:
            for key, value in user_data.items():
                setattr(user, key, value)
            self.db.commit()
            self.db.refresh(user)
        return user
    
    def delete(self, user_id: int) -> bool:
        """Remove usuário"""
        user = self.get_by_id(user_id)
        if user:
            self.db.delete(user)
            self.db.commit()
            return True
        return False
