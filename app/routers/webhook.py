from fastapi import APIRouter, Request, HTTPException
from app.services.llm_service import llm_service
from app.services.session_repository import session_repository
from app.services.validador_fluxo import processar_fluxo_atendimento
from app.services.agendamento_repository import agendamento_repository
from app.services.evolution_service import evolution_service

router = APIRouter()

@router.post("/webhook")
async def webhook_handler(request: Request):
    try:
        body = await request.json()
        data = body.get("data", {})
        key = data.get("key", {})
        remote_jid = key.get("remoteJid")
        
        # Ignora mensagens enviadas pelo próprio bot para evitar loop infinito
        if key.get("fromMe", False):
            return {"status": "ignored", "reason": "outgoing message"}
        
        message_obj = data.get("message", {})
        texto_usuario = message_obj.get("conversation") or message_obj.get("extendedTextMessage", {}).get("text", "")
        
        if not remote_jid or not texto_usuario:
            return {"status": "ignored", "reason": "invalid payload"}
            
        # 1. Verifica urgência médica
        if llm_service.verificar_urgencia(texto_usuario):
            resposta_urgencia = "🚨 **ATENÇÃO: Identificamos sintomas que podem indicar urgência médica.** Por favor, dirija-se imediatamente ao pronto-socorro mais próximo ou ligue para o SAMU (192)."
            evolution_service.enviar_mensagem(remote_jid, resposta_urgencia)
            return {"status": "success", "estado_final": "urgencia_detectada", "resposta_enviada": resposta_urgencia}
            
        # 2. Recupera sessão atual do paciente
        sessao = session_repository.obter_sessao(remote_jid)
        estado_atual = sessao.get("estado", "inicio")
        dados_paciente = sessao.get("dados", {})
        historico = sessao.get("historico", [])
        
        # 3. Processa o fluxo de atendimento
        novo_estado, resposta_bot = processar_fluxo_atendimento(estado_atual, texto_usuario, dados_paciente)
        
        # 4. Se o fluxo acabou de ser finalizado, persiste no banco de dados
        if novo_estado == "finalizado" and estado_atual != "finalizado":
            agendamento_repository.salvar_agendamento(remote_jid, dados_paciente)
            
        # 5. Atualiza o histórico e salva a sessão completa
        historico.append({"autor": "usuario", "texto": texto_usuario})
        historico.append({"autor": "bot", "texto": resposta_bot})
        session_repository.salvar_sessao(remote_jid, {
            "estado": novo_estado, 
            "dados": dados_paciente,
            "historico": historico
        })
        
        # 6. Dispara a resposta de volta para o WhatsApp via Evolution API
        evolution_service.enviar_mensagem(remote_jid, resposta_bot)
        
        return {
            "status": "success",
            "estado_final": novo_estado,
            "resposta_enviada": resposta_bot
        }
    except Exception as e:
        print(f"Erro crítico no webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))
