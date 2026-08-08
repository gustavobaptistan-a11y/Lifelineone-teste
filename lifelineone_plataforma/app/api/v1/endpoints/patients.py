from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.patient import PatientCreate, PatientUpdate, PatientStateResponse
from app.services.patient_service import PatientService

router = APIRouter()

@router.post("/", response_model=PatientStateResponse, status_code=201)
async def create_patient(
    patient_in: PatientCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Cria um novo Lead/Paciente na plataforma Lifeline One.
    """
    patient = await PatientService.create_patient(db, patient_in)
    return await PatientService.get_patient_state(db, str(patient.id))

@router.get("/{identifier}/state", response_model=PatientStateResponse)
async def get_patient_state(
    identifier: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Consulta o **Estado do Paciente** em tempo real.
    A IA ou a plataforma utiliza este endpoint para saber a fonte da verdade antes de responder.
    O `identifier` pode ser o ID do paciente (ex: '1') ou o telefone (ex: '5511999999999').
    """
    return await PatientService.get_patient_state(db, identifier)

@router.patch("/{patient_id}", response_model=PatientStateResponse)
async def update_patient(
    patient_id: int,
    update_in: PatientUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Atualiza informações do paciente (convênio, médico, tratamento, intenção atual, pendências, exames).
    """
    await PatientService.update_patient(db, patient_id, update_in)
    return await PatientService.get_patient_state(db, str(patient_id))
