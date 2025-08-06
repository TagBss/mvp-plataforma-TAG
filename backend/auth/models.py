from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

# Schemas para requisições e respostas
class UserBase(BaseModel):
    email: str
    username: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool = True
    roles: List[str] = []
    permissions: List[str] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: User

class TokenData(BaseModel):
    email: Optional[str] = None

# Dados mockados para demonstração
DEMO_USERS = {
    "admin@tag.com": {
        "id": 1,
        "email": "admin@tag.com",
        "username": "Administrador",
        "hashed_password": "$2b$12$mUkK6WgsiuzslumB0yi61uNPTTXt0bFNQYdytrGGO23KQeR6z4wEa",  # admin123
        "is_active": True,
        "roles": ["admin"],
        "permissions": [
            "read:dre", "write:dre", 
            "read:dfc", "write:dfc", 
            "read:reports", "write:reports",
            "admin:all"
        ],
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    },
    "user@tag.com": {
        "id": 2,
        "email": "user@tag.com",
        "username": "Usuário Padrão",
        "hashed_password": "$2b$12$mUkK6WgsiuzslumB0yi61uNPTTXt0bFNQYdytrGGO23KQeR6z4wEa",  # admin123
        "is_active": True,
        "roles": ["user"],
        "permissions": [
            "read:dre", "read:dfc", "read:reports"
        ],
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
}

def get_password_hash(password: str) -> str:
    """Gera hash da senha para teste"""
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    return pwd_context.hash(password)

def get_user_by_email(email: str) -> Optional[dict]:
    """Busca usuário por email"""
    return DEMO_USERS.get(email)

def verify_user_credentials(email: str, password: str) -> Optional[dict]:
    """Verifica credenciais do usuário"""
    from passlib.context import CryptContext
    
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    user = get_user_by_email(email)
    if not user:
        return None
    
    if not pwd_context.verify(password, user["hashed_password"]):
        return None
    
    return user 