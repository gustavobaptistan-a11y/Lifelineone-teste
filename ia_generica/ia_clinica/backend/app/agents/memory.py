import uuid
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.document import ClinicalNote

logger = logging.getLogger(__name__)


class MemoryAgent:
    """
    Agente Memória Clínica.
    Grava notas e históricos relevantes do paciente de forma longitudinal.
    """

    async def save_clinical_note(
        self,
        db: AsyncSession,
        patient_id: uuid.UUID,
        tipo_nota: str,
        descricao: str
    ) -> ClinicalNote | None:
        try:
            note = ClinicalNote(
                patient_id=patient_id,
                tipo_nota=tipo_nota,
                descricao=descricao
            )
            db.add(note)
            await db.flush()
            return note
        except Exception as e:
            await db.rollback()
            logger.info(f"Nota clínica não persistida: {e}")
            return None




memory_agent = MemoryAgent()
