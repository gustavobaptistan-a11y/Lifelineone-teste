from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.medical_record import ExamDocument
from app.services.exam_analysis_service import ExamAnalysisService

router = APIRouter()

class ExamUploadRequest(BaseModel):
    file_name: str = Field(..., json_schema_extra={"example": "espirometria_gustavo.pdf"})
    exam_type: str = Field("Espirometria", json_schema_extra={"example": "Espirometria"})

class ExamDocumentResponse(BaseModel):
    document_id: int
    patient_id: int
    file_name: str
    exam_type: str
    extracted_findings: Optional[str]
    analysis_status: str

@router.post("/upload/{patient_id}")
async def upload_and_analyze_exam(
    patient_id: int,
    payload: ExamUploadRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Realiza o envio e análise de exames por IA Multimodal / OCR (PEP).
    Dispara automaticamente o evento 'exame_disponivel' e atualiza a jornada.
    """
    result = await ExamAnalysisService.process_exam_upload(
        db=db,
        patient_id=patient_id,
        file_name=payload.file_name,
        exam_type=payload.exam_type
    )
    return result

@router.get("/patient/{patient_id}")
async def get_patient_exam_history(
    patient_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Retorna todo o histórico de exames e laudos analisados do Prontuário Eletrônico do Paciente.
    """
    res = await db.execute(
        select(ExamDocument)
        .where(ExamDocument.patient_id == patient_id)
        .order_by(ExamDocument.uploaded_at.desc())
    )
    docs = res.scalars().all()
    return [
        {
            "id": d.id,
            "patient_id": d.patient_id,
            "file_name": d.file_name,
            "exam_type": d.exam_type,
            "extracted_findings": d.extracted_findings,
            "status": d.analysis_status,
            "uploaded_at": d.uploaded_at
        } for d in docs
    ]
