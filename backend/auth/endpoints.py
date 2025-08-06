from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import timedelta
from .models import UserLogin, Token, User, verify_user_credentials, get_user_by_email
from .security import create_access_token, get_current_user_email

router = APIRouter(prefix="/auth", tags=["authentication"])

# Security scheme
security = HTTPBearer()

@router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin):
    """Endpoint para login do usuário"""
    
    # Verificar credenciais
    user = verify_user_credentials(user_credentials.email, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verificar se usuário está ativo
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuário inativo"
        )
    
    # Criar token de acesso
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user["email"]}, expires_delta=access_token_expires
    )
    
    # Retornar token e dados do usuário
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "email": user["email"],
            "username": user["username"],
            "is_active": user["is_active"],
            "roles": user["roles"],
            "permissions": user["permissions"],
            "created_at": user["created_at"],
            "updated_at": user["updated_at"]
        }
    }

@router.get("/me", response_model=User)
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Endpoint para obter dados do usuário atual"""
    
    # Verificar token
    email = get_current_user_email(credentials.credentials)
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Buscar usuário
    user = get_user_by_email(email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
    
    # Verificar se usuário está ativo
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuário inativo"
        )
    
    return {
        "id": user["id"],
        "email": user["email"],
        "username": user["username"],
        "is_active": user["is_active"],
        "roles": user["roles"],
        "permissions": user["permissions"],
        "created_at": user["created_at"],
        "updated_at": user["updated_at"]
    }

@router.post("/logout")
async def logout():
    """Endpoint para logout (token será invalidado no frontend)"""
    return {"message": "Logout realizado com sucesso"}

# Função para verificar se usuário tem permissão
def check_permission(required_permission: str):
    """Dependency para verificar permissão do usuário"""
    def permission_checker(credentials: HTTPAuthorizationCredentials = Depends(security)):
        email = get_current_user_email(credentials.credentials)
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido"
            )
        
        user = get_user_by_email(email)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado"
            )
        
        # Verificar se tem permissão ou é admin
        if required_permission not in user["permissions"] and "admin" not in user["roles"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permissão insuficiente"
            )
        
        return user
    
    return permission_checker 