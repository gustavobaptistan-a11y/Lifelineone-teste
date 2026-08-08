from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, ConfigDict, Field
from app.models.journey import JourneyStage

class PatientCreate(BaseModel):
    name: str = Field(..., json_schema_extra={"example": "Gustavo Baptista"})
    phone: str = Field(..., json_schema_extra={"example": "5511999999999"})
    email: Optional[str] = None
    cpf: Optional[str] = None
    birth_date: Optional[str] = None
    insurance_name: Optional[str] = None
    insurance_card_number: Optional[str] = None
    insurance_plan: Optional[str] = None
    attending_doctor: Optional[str] = None
    doctor_crm: Optional[str] = None
    specialty: Optional[str] = None

class PatientUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    cpf: Optional[str] = None
    birth_date: Optional[str] = None
    insurance_name: Optional[str] = None
    insurance_card_number: Optional[str] = None
    insurance_plan: Optional[str] = None
    attending_doctor: Optional[str] = None
    doctor_crm: Optional[str] = None
    specialty: Optional[str] = None
    active_treatment: Optional[str] = None
    expected_return_date: Optional[datetime] = None
    pending_tasks: Optional[List[Any]] = None
    exams_data: Optional[List[Any]] = None
    active_ticket_id: Optional[str] = None
    current_intent: Optional[str] = None

class PersonalDataSchema(BaseModel):
    id: int
    name: str
    phone: str
    email: Optional[str] = None
    cpf: Optional[str] = None
    birth_date: Optional[str] = None

class InsuranceDataSchema(BaseModel):
    name: Optional[str] = None
    card_number: Optional[str] = None
    plan: Optional[str] = None

class MedicalInfoSchema(BaseModel):
    attending_doctor: Optional[str] = None
    doctor_crm: Optional[str] = None
    specialty: Optional[str] = None

class PatientStateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    patient_id: int
    personal_data: PersonalDataSchema
    insurance: InsuranceDataSchema
    medical_info: MedicalInfoSchema
    
    # Jornada e Status
    current_stage: JourneyStage
    active_treatment: Optional[str] = None
    expected_return_date: Optional[datetime] = None
    
    # Pendências, Exames e Tickets
    pending_tasks: List[Any] = []
    exams_data: List[Any] = []
    active_ticket_id: Optional[str] = None
    
    # Metadados de interação
    last_interaction: datetime
    current_intent: Optional[str] = None
