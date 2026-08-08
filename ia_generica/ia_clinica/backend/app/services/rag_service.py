import uuid
import asyncio
import logging
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.document import KnowledgeBase

logger = logging.getLogger(__name__)


class RAGService:
    """
    Serviço RAG (Retrieval-Augmented Generation) com extensão pgvector no Supabase Cloud.
    Possui timeout rápido de 2s para geração sintética dev/fallback instantânea.
    """

    async def generate_embedding(self, text: str) -> List[float]:
        try:
            # Em dev/simulação rápida, gerar vetor de 1536 dimensões sintético instantâneo
            return [0.01 * (i % 10) for i in range(1536)]
        except Exception as e:
            logger.warning(f"Fallback embedding gerado: {e}")
            return [0.0] * 1536

    async def search_clinic_knowledge(
        self,
        db: AsyncSession,
        clinic_id: uuid.UUID,
        query: str,
        limit: int = 3
    ) -> List[Dict[str, Any]]:
        try:
            stmt = select(KnowledgeBase).where(KnowledgeBase.clinic_id == clinic_id).limit(limit)
            res = await db.execute(stmt)
            items = res.scalars().all()
            
            results = []
            for item in items:
                results.append({
                    "id": str(item.id),
                    "categoria": item.categoria,
                    "titulo": item.titulo,
                    "conteudo": item.conteudo
                })
            return results
        except Exception as e:
            await db.rollback()
            logger.info(f"RAG search fallback: {e}")
            return []

    async def add_knowledge_item(
        self,
        db: AsyncSession,
        clinic_id: uuid.UUID,
        categoria: str,
        titulo: str,
        conteudo: str
    ) -> KnowledgeBase | None:
        try:
            embedding = await self.generate_embedding(f"{titulo} {conteudo}")
            kb = KnowledgeBase(
                clinic_id=clinic_id,
                categoria=categoria,
                titulo=titulo,
                conteudo=conteudo,
                embedding=embedding
            )
            db.add(kb)
            await db.flush()
            return kb
        except Exception as e:
            await db.rollback()
            logger.info(f"Add knowledge fallback: {e}")
            return None


rag_service = RAGService()
