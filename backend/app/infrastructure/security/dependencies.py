from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional

from app.infrastructure.db.database import get_db
from app.infrastructure.security.auth import AuthService
from app.domain.models.user import User
from app.infrastructure.repositories.user_repository import UserRepository

# Configurar esquema de autenticação
security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency para obter o usuário atual autenticado.
    Verifica o token JWT e retorna o usuário correspondente.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Verificar token
        payload = AuthService.verify_token(credentials.credentials)
        if payload is None:
            raise credentials_exception
        
        # Extrair dados do token
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        
        # Buscar usuário no banco
        user_repo = UserRepository(db)
        user = user_repo.get_by_id(user_id)
        
        if user is None:
            raise credentials_exception
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
        
        return user
        
    except Exception as e:
        raise credentials_exception

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency para obter usuário ativo.
    Verifica se o usuário está ativo e tem licença válida.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Verificar se tem licença válida
    if not current_user.license or not current_user.license.is_valid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or expired license"
        )
    
    return current_user

async def get_current_superuser(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency para obter superusuário.
    Verifica se o usuário tem privilégios de administrador.
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return current_user

def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Dependency para obter usuário atual opcional.
    Retorna None se não autenticado, não levanta exceção.
    """
    if not credentials:
        return None
    
    try:
        payload = AuthService.verify_token(credentials.credentials)
        if payload is None:
            return None
        
        user_id: int = payload.get("sub")
        if user_id is None:
            return None
        
        user_repo = UserRepository(db)
        user = user_repo.get_by_id(user_id)
        
        return user if user and user.is_active else None
        
    except Exception:
        return None
