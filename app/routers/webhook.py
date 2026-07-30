import inspect
import logging
import uuid

from fastapi import APIRouter, Header, HTTPException
from app.config import settings
from app.models.schemas import WebhookPayload
from app.services.agendamento_repository import agendamento_repository
from app.services.evolution_service import evolution_service
from app.services.validador_fluxo import processar_fluxo_atendimento
from app.services import session_repository

router = APIRouter()
logger = logging.getLogger(__name__)

async def _salvar_sessao_compat(remote_jid: str, dados_sessao: dict, conversation_id: str | None) -> None:
    salvar = session_repository.salvar_sessao_async
    try:
        signature = inspect.signature(salvar)
    except (TypeError, ValueError):
        await salvar(remote_jid, dados_sessao, conversation_id)
        return

    params = signature.parameters.values()
    supports_varargs = any(param.kind == inspect.Parameter.VAR_POSITIONAL for param in params)
    supports_conversation_id = "conversation_id" in signature.parameters
    positional_params = [
        param
        for param in signature.parameters.values()
        if param.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
    ]

    if supports_varargs or supports_conversation_id or len(positional_params) >= 3:
        await salvar(remote_jid, dados_sessao, conversation_id)
    else:
        await salvar(remote_jid, dados_sessao)


@router.post("/webhook")
async def receber_webhook(
    payload: WebhookPayload,
    authorization: str | None = Header(None),
    x_webhook_secret: str | None = Header(None),
):
    try:
        if payload.event or payload.instance:
            logger.debug(
                "Webhook Evolution recebido: event=%s instance=%s",
                payload.event,
                payload.instance,
            )

        if settings.WEBHOOK_SECRET:
            token_candidates = []
            if x_webhook_secret:
                token_candidates.append(x_webhook_secret.strip())
            if authorization:
                auth_value = authorization.strip()
                if auth_value.lower().startswith("bearer "):
                    token_candidates.append(auth_value[7:].strip())
                else:
                    token_candidates.append(auth_value)

            if settings.WEBHOOK_SECRET not in token_candidates:
                logger.warning("Webhook nao autorizado: cabecalho inválido")
                raise HTTPException(status_code=401, detail="Webhook nao autorizado")

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

        message_id = data.key.id or str(uuid.uuid4())
        dados_sessao = await session_repository.obter_sessao_async(remote_jid)
        conversation_id = dados_sessao.get("conversation_id") or message_id
        estado_atual = dados_sessao.get("estado", "inicio")

        resposta, proximo_estado, dados_atualizados = await processar_fluxo_atendimento(
            estado_atual, texto_usuario, dados_sessao, remote_jid
        )

        dados_atualizados["estado"] = proximo_estado
        dados_atualizados["conversation_id"] = conversation_id
        dados_atualizados["last_message_id"] = message_id
        await _salvar_sessao_compat(remote_jid, dados_atualizados, None)

        if proximo_estado == "concluido":
            await agendamento_repository.salvar_agendamento_async(remote_jid, dados_atualizados)

        envio = await evolution_service.send_text_message(remote_jid, resposta)
        if envio.get("status") == "erro":
            logger.warning("Resposta processada, mas nao enviada pela Evolution")

        if proximo_estado == "urgencia_detectada":
            return {
                "status": "urgencia_detectada",
                "resposta": resposta,
                "resposta_enviada": resposta,
                "estado_anterior": estado_atual,
                "estado_final": proximo_estado,
                "proximo_estado": proximo_estado,
                "envio": envio,
            }

        return {
            "status": "sucesso",
            "estado_anterior": estado_atual,
            "estado_final": proximo_estado,
            "proximo_estado": proximo_estado,
            "resposta": resposta,
            "resposta_enviada": resposta,
            "envio": envio,
        }

    except HTTPException:
        raise
    except Exception:
        logger.exception("Erro interno ao processar webhook")
        raise HTTPException(status_code=500, detail="Erro interno ao processar webhook")
