from fastapi import APIRouter, Request, HTTPException
from app.services.validador_fluxo import processar_fluxo_atendimento
from app.services.session_repository import obter_sessao, salvar_sessao

router = APIRouter()

@router.post("/webhook")
async def receber_webhook(request: Request):
    try:
        body = await request.json()
        
        data = body.get("data", {})
        remote_jid = data.get("key", {}).get("remoteJid", "default_user")
        
        message_obj = data.get("message", {})
        texto_usuario = (
            message_obj.get("conversation") or 
            message_obj.get("extendedTextMessage", {}).get("text") or 
            ""
        )
        
        if not texto_usuario:
            return {"status": "ignorado", "motivo": "mensagem sem texto ou formato incompatível"}

        dados_sessao = obter_sessao(remote_jid)
        estado_atual = dados_sessao.get("estado", "inicio")

        resposta, proximo_estado, dados_atualizados = processar_fluxo_atendimento(
            estado_atual, texto_usuario, dados_sessao
        )

        dados_atualizados["estado"] = proximo_estado
        salvar_sessao(remote_jid, dados_atualizados)

        if proximo_estado == "urgencia_detectada":
            return {"status": "urgencia_detectada", "resposta": resposta}

        return {
            "status": "sucesso",
            "estado_anterior": estado_atual,
            "proximo_estado": proximo_estado,
            "resposta": resposta
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno no webhook: {str(e)}")
