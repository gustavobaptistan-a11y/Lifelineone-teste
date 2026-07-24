import asyncio
from httpx import AsyncClient, ASGITransport
from main import app

async def executar_testes_modulares():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        
        print("==================================================")
        print("    AUDITORIA MODULAR DE TESTES - LIFELINE BOT    ")
        print("==================================================")
        
        problemas = []
        jid_teste = "5561911111111@s.whatsapp.net"

        # --- BLOCO 1: TESTE DE URGÊNCIA ---
        print("\n[BLOCO 1/6] Testando Interceptação de Urgência...")
        try:
            res = await ac.post("/webhook", json={
                "instance": "test",
                "data": {"key": {"remoteJid": jid_teste}, "message": {"conversation": "estou com dor no peito intensa"}}
            })
            data = res.json()
            if data.get("status") == "urgencia_detectada":
                print("  -> [SUCESSO] Urgência interceptada corretamente.")
            else:
                print("  -> [FALHA] O sistema não marcou como urgência.")
                problemas.append("Bloco 1: Falha na detecção de termos de urgência.")
        except Exception as e:
            print(f"  -> [ERRO] Falha de execução no Bloco 1: {e}")
            problemas.append(f"Bloco 1 Erro: {e}")

        # --- BLOCO 2: INÍCIO DO FLUXO (OLÁ) ---
        print("\n[BLOCO 2/6] Testando Início da Conversa...")
        jid_fluxo = "5561922222222@s.whatsapp.net"
        try:
            res = await ac.post("/webhook", json={
                "instance": "test",
                "data": {"key": {"remoteJid": jid_fluxo}, "message": {"conversation": "Olá"}}
            })
            data = res.json()
            if data.get("proximo_estado") == "aguardando_nome":
                print("  -> [SUCESSO] Transicionou para aguardando_nome.")
            else:
                print(f"  -> [FALHA] Estado incorreto: {data.get('proximo_estado')}")
                problemas.append("Bloco 2: Falha ao iniciar fluxo e solicitar nome.")
        except Exception as e:
            print(f"  -> [ERRO] Bloco 2: {e}")
            problemas.append(f"Bloco 2 Erro: {e}")

        # --- BLOCO 3: CAPTURA DE NOME E SINTOMA ---
        print("\n[BLOCO 3/6] Testando Captura de Nome e Sintoma...")
        try:
            await ac.post("/webhook", json={
                "instance": "test",
                "data": {"key": {"remoteJid": jid_fluxo}, "message": {"conversation": "Ana Paula"}}
            })
            res_sintoma = await ac.post("/webhook", json={
                "instance": "test",
                "data": {"key": {"remoteJid": jid_fluxo}, "message": {"conversation": "Dor de cabeça e febre alta"}}
            })
            data = res_sintoma.json()
            if data.get("proximo_estado") == "aguardando_convenio":
                print("  -> [SUCESSO] Nome e sintoma processados. Aguardando convênio.")
            else:
                print("  -> [FALHA] Erro na transição de sintoma para convênio.")
                problemas.append("Bloco 3: Falha na etapa de captura de sintomas.")
        except Exception as e:
            print(f"  -> [ERRO] Bloco 3: {e}")
            problemas.append(f"Bloco 3 Erro: {e}")

        # --- BLOCO 4: CONVÊNIO E PRIMEIRA CONSULTA ---
        print("\n[BLOCO 4/6] Testando Convênio e Primeira Consulta...")
        try:
            await ac.post("/webhook", json={
                "instance": "test",
                "data": {"key": {"remoteJid": jid_fluxo}, "message": {"conversation": "Particular"}}
            })
            res_pc = await ac.post("/webhook", json={
                "instance": "test",
                "data": {"key": {"remoteJid": jid_fluxo}, "message": {"conversation": "Sim"}}
            })
            data = res_pc.json()
            if data.get("proximo_estado") == "aguardando_horario":
                print("  -> [SUCESSO] Convênio e primeira consulta salvos. Aguardando horário.")
            else:
                print("  -> [FALHA] Erro ao validar primeira consulta.")
                problemas.append("Bloco 4: Falha na validação de convênio/primeira consulta.")
        except Exception as e:
            print(f"  -> [ERRO] Bloco 4: {e}")
            problemas.append(f"Bloco 4 Erro: {e}")

        # --- BLOCO 5: HORÁRIO E CONCLUSÃO ---
        print("\n[BLOCO 5/6] Testando Escolha de Horário e Conclusão...")
        try:
            res_fim = await ac.post("/webhook", json={
                "instance": "test",
                "data": {"key": {"remoteJid": jid_fluxo}, "message": {"conversation": "14:00"}}
            })
            data = res_fim.json()
            if data.get("proximo_estado") == "concluido":
                print("  -> [SUCESSO] Agendamento concluído com sucesso!")
            else:
                print("  -> [FALHA] O fluxo não concluiu corretamente.")
                problemas.append("Bloco 5: Falha na etapa de confirmação de horário.")
        except Exception as e:
            print(f"  -> [ERRO] Bloco 5: {e}")
            problemas.append(f"Bloco 5 Erro: {e}")

        # --- BLOCO 6: VERIFICAÇÃO DE PERSISTÊNCIA NO POSTGRES ---
        print("\n[BLOCO 6/6] Verificando Persistência no PostgreSQL...")
        try:
            from app.services.session_repository import obter_sessao
            sessao_db = obter_sessao(jid_fluxo)
            if sessao_db and sessao_db.get("nome") == "Ana Paula":
                print("  -> [SUCESSO] Dados recuperados corretamente do PostgreSQL!")
            else:
                print("  -> [FALHA] Os dados salvos não conferem com o banco.")
                problemas.append("Bloco 6: Falha na recuperação de dados do PostgreSQL.")
        except Exception as e:
            print(f"  -> [ERRO DE CONEXÃO COM BANCO]: {e}")
            problemas.append(f"Bloco 6 Erro (PostgreSQL): {e}")

        print("\n==================================================")
        print("               RELATÓRIO DE AUDITORIA             ")
        print("==================================================")
        if problemas:
            print(f"⚠️ ATENÇÃO: Foram identificados {len(problemas)} problema(s):")
            for p in problemas:
                print(f" - {p}")
        else:
            print("✨ PARABÉNS! Nenhum problema encontrado. Todos os blocos passaram perfeitamente!")
        print("==================================================")

if __name__ == "__main__":
    asyncio.run(executar_testes_modulares())
