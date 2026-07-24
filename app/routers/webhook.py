import logging

from fastapi import APIRouter, HTTPException
from app.models.schemas import WebhookPayload
from app.services.agendamento_repository import agendamento_repository
from app.services.evolution_service import evolution_service
from app.services.validador_fluxo import processar_fluxo_atendimento
from app.services.session_repository import obter_sessao, salvar_sessao

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/webhook")
async def receber_webhook(payload: WebhookPayload):
    try:
        data = payload.data
        if data.key.from_me:
            return {"status": "ignorado", "motivo": "mensagem enviada pelo proprio bot"}

        texto_usuario = (
            data.message.conversation
            or (
                data.message.extended_text_message.text
                if data.message.extended_text_message
                else None
            )
            or ""
        )

        remote_jid = data.key.remote_jid
        texto_usuario = texto_usuario.strip()
        if not texto_usuario:
            return {"status": "ignorado", "motivo": "mensagem sem texto ou formato incompatível"}

        dados_sessao = obter_sessao(remote_jid)
        estado_atual = dados_sessao.get("estado", "inicio")

        resposta, proximo_estado, dados_atualizados = await processar_fluxo_atendimento(
            estado_atual, texto_usuario, dados_sessao
        )

        dados_atualizados["estado"] = proximo_estado
        salvar_sessao(remote_jid, dados_atualizados)

        if proximo_estado == "concluido":
            agendamento_repository.salvar_agendamento(remote_jid, dados_atualizados)

        envio = await evolution_service.send_text_message(remote_jid, resposta)
        if envio.get("status") == "erro":
            logger.warning("Resposta processada, mas nao enviada pela Evolution")

        if proximo_estado == "urgencia_detectada":
            return {"status": "urgencia_detectada", "resposta": resposta, "envio": envio}

        return {
            "status": "sucesso",
            "estado_anterior": estado_atual,
            "proximo_estado": proximo_estado,
            "resposta": resposta,
            "envio": envio,
        }

    except Exception:
        logger.exception("Erro interno ao processar webhook")
        raise HTTPException(status_code=500, detail="Erro interno ao processar webhook")
