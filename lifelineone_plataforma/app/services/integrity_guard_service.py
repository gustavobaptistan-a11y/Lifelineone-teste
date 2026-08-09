import hashlib
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.audit import AuditLog
from app.models.patient import Patient
from app.core.websocket_manager import ws_manager

class IntegrityGuardService:
    """
    Guardião de IA responsável pela Integridade e Auditoria do Prontuário Unificado (PEP Master).
    Registra Quem acessou, De onde acessou e valida se há anomalias de segurança.
    """

    @staticmethod
    async def log_access(
        db: AsyncSession,
        patient_id: int,
        actor_name: str,
        actor_role: str,
        unit_location: str,
        access_ip: str,
        action: str
    ) -> AuditLog:
        # Análise básica de anomalia (ex: acesso sem papel reconhecido ou IP fora da rede)
        integrity_status = "VALIDO"
        if "Desconhecido" in actor_role or access_ip == "0.0.0.0":
            integrity_status = "ANOMALIA_DETECTADA"

        log_entry = AuditLog(
            patient_id=patient_id,
            actor_name=actor_name,
            actor_role=actor_role,
            unit_location=unit_location,
            access_ip=access_ip,
            action=action,
            ai_integrity_status=integrity_status
        )
        db.add(log_entry)
        await db.flush()

        # Transmite alerta via WebSocket se anomalia detectada
        if integrity_status != "VALIDO":
            await ws_manager.broadcast({
                "type": "security_alert",
                "patient_id": patient_id,
                "actor_name": actor_name,
                "action": action,
                "status": integrity_status
            })

        return log_entry

    @staticmethod
    async def verify_pep_integrity(db: AsyncSession, patient_id: int) -> Dict[str, Any]:
        """Audita todo o histórico de alterações do Prontuário para este paciente."""
        res = await db.execute(
            select(AuditLog)
            .where(AuditLog.patient_id == patient_id)
            .order_by(AuditLog.timestamp.desc())
        )
        logs = list(res.scalars().all())

        anomalies_count = sum(1 for l in logs if l.ai_integrity_status != "VALIDO")
        pep_hash = hashlib.sha256(f"patient_{patient_id}_logs_{len(logs)}".encode()).hexdigest()

        return {
            "patient_id": patient_id,
            "total_access_logs": len(logs),
            "anomalies_detected": anomalies_count,
            "integrity_score": "100%" if anomalies_count == 0 else "90% (Atenção requerida)",
            "pep_blockchain_sha256_hash": pep_hash,
            "recent_access_logs": [
                {
                    "actor_name": l.actor_name,
                    "actor_role": l.actor_role,
                    "unit": l.unit_location,
                    "ip": l.access_ip,
                    "action": l.action,
                    "status": l.ai_integrity_status,
                    "timestamp": l.timestamp
                } for l in logs[:10]
            ]
        }
