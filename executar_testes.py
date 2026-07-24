import httpx
import asyncio

URL_WEBHOOK = "http://localhost:8000/webhook"

async def testar_fluxos():
    async with httpx.AsyncClient() as client:
        print("=== TESTE 1: CASO DE URGÊNCIA ===")
        payload_urgencia = {
            "instance": "test_instance",
            "data": {
                "key": {"remoteJid": "5561999999999@s.whatsapp.net"},
                "message": {"conversation": "Estou com muita falta de ar e dor no peito"}
            }
        }
        try:
            resp = await client.post(URL_WEBHOOK, json=payload_urgencia, timeout=5.0)
            print(f"Status: {resp.status_code} | Resposta: {resp.json()}")
        except Exception as e:
            print(f"Erro: {e}")

        print("\n=== TESTE 2: FLUXO NORMAL ===")
        payload_normal = {
            "instance": "test_instance",
            "data": {
                "key": {"remoteJid": "5561888888888@s.whatsapp.net"},
                "message": {"conversation": "Olá, gostaria de marcar uma consulta"}
            }
        }
        try:
            resp = await client.post(URL_WEBHOOK, json=payload_normal, timeout=5.0)
            print(f"Status: {resp.status_code} | Resposta: {resp.json() if resp.headers.get('content-type', '').startswith('application/json') else resp.text}")
        except Exception as e:
            print(f"Erro: {e}")

if __name__ == "__main__":
    asyncio.run(testar_fluxos())
