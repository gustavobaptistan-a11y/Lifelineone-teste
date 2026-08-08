import uuid
import re
import logging
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.patient import Patient, Contact, PatientContact

logger = logging.getLogger(__name__)


class RegistrationAgent:
    """
    Agente de Cadastro (Paciente & Contato).
    Gerencia dados cadastrais e identificação do paciente com persistência assíncrona limpa.
    """

    def extract_name_from_text(self, text: str) -> str | None:
        if not text:
            return None
        
        patterns = [
            r"(?:meu nome [eé]|sou [oa]|chamo-me|me chamo|nome [eé])\s+([A-ZÀ-Ú][a-zà-ú]+(?:\s+[A-ZÀ-Ú][a-zà-ú]+)?)",
            r"(?:ol[aá]|oi|bom dia|boa tarde|boa noite)[,\s]+(?:eu sou [oa]\s+)?([A-ZÀ-Ú][a-zà-ú]+)",
        ]
        
        reserved_words = [
            "sim", "nao", "não", "gostaria", "quero", "doutor", "dra", "qual", "como",
            "onde", "quanto", "quando", "quem", "meu", "minha", "boa", "bom", "olá", "ola",
            "estou", "sou", "mae", "mãe", "pai", "vo", "vó", "já", "ja"
        ]
        
        for p in patterns:
            match = re.search(p, text, re.IGNORECASE)
            if match:
                extracted = match.group(1).strip()
                if extracted.lower() not in reserved_words and len(extracted) > 2:
                    return extracted.capitalize()
        return None

    async def get_or_create_contact(self, db: AsyncSession, clinic_id: uuid.UUID, phone: str, name: str | None = None) -> Contact:
        try:
            stmt = select(Contact).where(Contact.clinic_id == clinic_id, Contact.telefone == phone)
            res = await db.execute(stmt)
            contact = res.scalars().first()

            if not contact:
                contact = Contact(
                    clinic_id=clinic_id,
                    nome=name if name else "Paciente",
                    telefone=phone,
                    tipo_contato="proprio",
                    preferencias_comunicacao={"canal": "whatsapp"}
                )
                db.add(contact)
                await db.flush()
            elif name and name != "Paciente" and contact.nome != name:
                contact.nome = name
                await db.flush()

            return contact
        except Exception as e:
            await db.rollback()
            logger.info(f"Fallback no get_or_create_contact: {e}")
            c = Contact(id=uuid.uuid4(), clinic_id=clinic_id, nome=name or "Paciente", telefone=phone)
            return c

    async def update_contact_name(self, db: AsyncSession, contact_id_or_obj: Any, new_name: str) -> None:
        try:
            if isinstance(contact_id_or_obj, Contact):
                contact = contact_id_or_obj
            else:
                stmt = select(Contact).where(Contact.id == contact_id_or_obj)
                res = await db.execute(stmt)
                contact = res.scalars().first()

            if contact and contact.nome != new_name:
                contact.nome = new_name
                await db.flush()
        except Exception as e:
            await db.rollback()

    async def link_patient_to_contact(self, db: AsyncSession, clinic_id: uuid.UUID, contact_id: uuid.UUID, name: str) -> Patient:
        try:
            stmt = select(Patient).where(Patient.clinic_id == clinic_id, Patient.nome == name)
            res = await db.execute(stmt)
            patient = res.scalars().first()

            if not patient:
                patient = Patient(
                    clinic_id=clinic_id,
                    nome=name
                )
                db.add(patient)
                await db.flush()

                try:
                    # Tenta vincular via SQL direto ou ignora se permissao/duplicado
                    link = PatientContact(
                        patient_id=patient.id,
                        contact_id=contact_id,
                        parentesco="proprio",
                        responsavel_principal=True,
                        permissao="proprio"
                    )
                    db.add(link)
                    await db.flush()
                except Exception as e:
                    logger.info(f"Vínculo mantido/já existente: {e}")

            return patient
        except Exception as e:
            logger.error(f"Erro em link_patient_to_contact: {e}")
            return Patient(id=uuid.uuid4(), clinic_id=clinic_id, nome=name)


registration_agent = RegistrationAgent()
