from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_password_hash, verify_password, create_access_token
from app.models.user import User, UserRole
from app.core.auth_deps import get_current_user

router = APIRouter()

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: UserRole = UserRole.RECEPCAO
    unit_location: str = "Unidade Jardins - SP"
    patient_id: Optional[int] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    full_name: str
    role: str
    unit_location: str
    patient_id: Optional[int] = None

@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalars().first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="E-mail ou senha incorretos.")

    token = create_access_token({"sub": str(user.id), "role": user.role.value})
    return TokenResponse(
        access_token=token,
        user_id=user.id,
        full_name=user.full_name,
        role=user.role.value,
        unit_location=user.unit_location,
        patient_id=user.patient_id
    )

@router.post("/register", response_model=TokenResponse)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == req.email))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Este e-mail já está cadastrado.")

    user = User(
        email=req.email,
        hashed_password=get_password_hash(req.password),
        full_name=req.full_name,
        role=req.role,
        unit_location=req.unit_location,
        patient_id=req.patient_id
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_access_token({"sub": str(user.id), "role": user.role.value})
    return TokenResponse(
        access_token=token,
        user_id=user.id,
        full_name=user.full_name,
        role=user.role.value,
        unit_location=user.unit_location,
        patient_id=user.patient_id
    )

@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role.value,
        "unit_location": current_user.unit_location,
        "patient_id": current_user.patient_id
    }

@router.post("/seed-users")
async def seed_users(db: AsyncSession = Depends(get_db)):
    """Cria os usuários padrão para teste dos perfis (Médico, Laboratório, Recepção, Paciente)"""
    users_data = [
        {"email": "medico@lifeline.com", "password": "123", "full_name": "Dr. Carlos Pneumologia", "role": UserRole.MEDICO, "unit": "Unidade Jardins - SP"},
        {"email": "lab@lifeline.com", "password": "123", "full_name": "Bioquímico Dr. Silva", "role": UserRole.LABORATORIO, "unit": "Laboratório Central"},
        {"email": "recepcao@lifeline.com", "password": "123", "full_name": "Mariana Recepção", "role": UserRole.RECEPCAO, "unit": "Unidade Jardins - SP"},
        {"email": "paciente@lifeline.com", "password": "123", "full_name": "Paciente João Silva", "role": UserRole.PACIENTE, "unit": "Domiciliar", "patient_id": 1},
    ]
    created = []
    for u in users_data:
        res = await db.execute(select(User).where(User.email == u["email"]))
        if not res.scalars().first():
            usr = User(
                email=u["email"],
                hashed_password=get_password_hash(u["password"]),
                full_name=u["full_name"],
                role=u["role"],
                unit_location=u["unit"],
                patient_id=u.get("patient_id")
            )
            db.add(usr)
            created.append(u["email"])
    await db.commit()
    return {"message": "Usuários de teste criados com sucesso!", "created_emails": created}
