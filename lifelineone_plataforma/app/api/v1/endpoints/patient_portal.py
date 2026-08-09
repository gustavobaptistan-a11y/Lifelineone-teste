from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.patient import Patient
from app.models.journey import JourneyHistory
from app.models.lab_order import LabOrder
from app.models.user import User, UserRole
from app.core.auth_deps import get_current_user, require_roles

router = APIRouter()

@router.get("/my-dashboard")
async def get_patient_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retorna o painel personalizado do Portal do Paciente"""
    patient_id = current_user.patient_id or 1 # Fallback para demonstração

    patient_res = await db.execute(select(Patient).where(Patient.id == patient_id))
    patient = patient_res.scalars().first()
    if not patient:
        raise HTTPException(status_code=404, detail="Registro do paciente não encontrado.")

    # Buscar exames liberados no cofre
    lab_res = await db.execute(select(LabOrder).where(LabOrder.patient_id == patient_id))
    orders = lab_res.scalars().all()

    # Buscar histórico recente
    stages_res = await db.execute(select(JourneyHistory).where(JourneyHistory.patient_id == patient_id).order_by(JourneyHistory.created_at.desc()).limit(3))
    recent_stages = stages_res.scalars().all()

    return {
        "patient": {
            "id": patient.id,
            "name": patient.name,
            "phone": patient.phone,
            "current_stage": patient.current_stage.value if hasattr(patient.current_stage, 'value') else str(patient.current_stage)
        },
        "released_exams": [
            {
                "id": o.id,
                "exam_name": o.exam_name,
                "requesting_doctor": o.requesting_doctor,
                "status": o.status.value,
                "scheduled_date": o.scheduled_date,
                "findings": o.findings_summary if o.status == "liberado_cofre_segura" else "Aguardando liberação",
                "vault_hash": o.vault_file_hash
            } for o in orders
        ],
        "recent_activity": [
            {
                "stage": s.to_stage.value if hasattr(s.to_stage, 'value') else str(s.to_stage),
                "date": s.created_at.strftime("%d/%m/%Y %H:%M") if s.created_at else "-",
                "notes": s.notes
            } for s in recent_stages
        ]
    }
