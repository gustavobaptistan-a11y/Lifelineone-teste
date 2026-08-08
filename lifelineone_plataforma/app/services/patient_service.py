from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException

from app.models.patient import Patient
from app.models.journey import JourneyStage, JourneyHistory
from app.schemas.patient import (
    PatientCreate, PatientUpdate, PatientStateResponse,
    PersonalDataSchema, InsuranceDataSchema, MedicalInfoSchema
)

class PatientService:
    @staticmethod
    async def create_patient(db: AsyncSession, patient_in: PatientCreate) -> Patient:
        # Verifica se telefone já existe
        result = await db.execute(select(Patient).where(Patient.phone == patient_in.phone))
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Paciente com este telefone já está cadastrado")

        patient = Patient(
            name=patient_in.name,
            phone=patient_in.phone,
            email=patient_in.email,
            cpf=patient_in.cpf,
            birth_date=patient_in.birth_date,
            insurance_name=patient_in.insurance_name,
            insurance_card_number=patient_in.insurance_card_number,
            insurance_plan=patient_in.insurance_plan,
            attending_doctor=patient_in.attending_doctor,
            doctor_crm=patient_in.doctor_crm,
            specialty=patient_in.specialty,
            current_stage=JourneyStage.LEAD_CRIADO
        )
        db.add(patient)
        await db.flush()

        # Registra primeira entrada no histórico de jornada
        initial_history = JourneyHistory(
            patient_id=patient.id,
            from_stage=None,
            to_stage=JourneyStage.LEAD_CRIADO,
            trigger_event="lead_created",
            notes="Lead criado na plataforma Lifeline One"
        )
        db.add(initial_history)
        await db.flush()

        return patient

    @staticmethod
    async def get_by_id(db: AsyncSession, patient_id: int) -> Optional[Patient]:
        result = await db.execute(select(Patient).where(Patient.id == patient_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_phone(db: AsyncSession, phone: str) -> Optional[Patient]:
        result = await db.execute(select(Patient).where(Patient.phone == phone))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_patient_state(db: AsyncSession, patient_identifier: str) -> PatientStateResponse:
        """
        Retorna o estado consolidado do paciente conforme a visão da Lifeline One.
        Pode receber o ID (int como str) ou o telefone do paciente.
        """
        patient: Optional[Patient] = None
        if patient_identifier.isdigit():
            patient = await PatientService.get_by_id(db, int(patient_identifier))
        
        if not patient:
            patient = await PatientService.get_by_phone(db, patient_identifier)

        if not patient:
            raise HTTPException(status_code=404, detail=f"Paciente '{patient_identifier}' não foi encontrado na plataforma.")

        return PatientStateResponse(
            patient_id=patient.id,
            personal_data=PersonalDataSchema(
                id=patient.id,
                name=patient.name,
                phone=patient.phone,
                email=patient.email,
                cpf=patient.cpf,
                birth_date=patient.birth_date
            ),
            insurance=InsuranceDataSchema(
                name=patient.insurance_name,
                card_number=patient.insurance_card_number,
                plan=patient.insurance_plan
            ),
            medical_info=MedicalInfoSchema(
                attending_doctor=patient.attending_doctor,
                doctor_crm=patient.doctor_crm,
                specialty=patient.specialty
            ),
            current_stage=patient.current_stage,
            active_treatment=patient.active_treatment,
            expected_return_date=patient.expected_return_date,
            pending_tasks=patient.pending_tasks or [],
            exams_data=patient.exams_data or [],
            active_ticket_id=patient.active_ticket_id,
            last_interaction=patient.last_interaction,
            current_intent=patient.current_intent
        )

    @staticmethod
    async def update_patient(db: AsyncSession, patient_id: int, update_in: PatientUpdate) -> Patient:
        patient = await PatientService.get_by_id(db, patient_id)
        if not patient:
            raise HTTPException(status_code=404, detail="Paciente não encontrado")

        update_data = update_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(patient, field, value)

        patient.last_interaction = datetime.now(timezone.utc)
        await db.flush()
        return patient
