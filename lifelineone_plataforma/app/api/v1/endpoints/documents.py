from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.patient import Patient
from app.models.journey import JourneyHistory
from app.services.pdf_generator_service import PDFGeneratorService
from app.core.auth_deps import get_current_user
from app.models.user import User

router = APIRouter()

class PrescriptionRequest(BaseModel):
    doctor_name: str
    patient_name: str
    prescription_text: str

@router.get("/pep-pdf/{patient_id}")
async def download_pep_pdf(
    patient_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Patient).where(Patient.id == patient_id))
    patient = result.scalars().first()
    if not patient:
        raise HTTPException(status_code=404, detail="Paciente não encontrado.")

    # Buscar histórico da jornada
    stages_res = await db.execute(select(JourneyHistory).where(JourneyHistory.patient_id == patient_id).order_by(JourneyHistory.created_at))
    stages = stages_res.scalars().all()

    history_events = []
    for s in stages:
        history_events.append({
            "timestamp": s.created_at.strftime("%d/%m/%Y %H:%M") if s.created_at else "-",
            "stage": s.to_stage.value if hasattr(s.to_stage, 'value') else str(s.to_stage),
            "description": f"Estágio da Jornada: {s.to_stage}. Observações: {s.notes or 'Em progresso'}",
            "actor": "Atendimento / IA"
        })

    if not history_events:
        history_events.append({
            "timestamp": "Hoje",
            "stage": "CADASTRO_INICIAL",
            "description": "Paciente cadastrado no PEP Master 360°.",
            "actor": "Sistema"
        })

    pdf_bytes = PDFGeneratorService.generate_unified_pep_pdf(
        patient_name=patient.name,
        patient_phone=patient.phone,
        history_events=history_events
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=PEP_Master_Paciente_{patient_id}.pdf"}
    )

@router.post("/prescription-pdf")
async def download_prescription_pdf(
    req: PrescriptionRequest,
    current_user: User = Depends(get_current_user)
):
    pdf_bytes = PDFGeneratorService.generate_prescription_pdf(
        doctor_name=req.doctor_name,
        patient_name=req.patient_name,
        prescription_text=req.prescription_text
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=Receituario_Medico_Lifeline.pdf"}
    )
