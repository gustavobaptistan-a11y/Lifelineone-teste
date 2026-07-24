import httpx
import os
import json
from dotenv import load_dotenv

load_dotenv()

class EvolutionService:
    def __init__(self):
        self.base_url = os.getenv("EVOLUTION_API_URL", "http://localhost:8080")
        self.api_key = os.getenv("EVOLUTION_API_KEY", "")
        self.instance = os.getenv("EVOLUTION_INSTANCE", "minha_instancia")

    async def send_text_message(self, phone: str, text: str):
        # Endpoint padrão do ecossistema Evolution / EvolutionGO para envio de texto
        url = f"{self.base_url}/message/sendText/{self.instance}"
        headers = {
            "Content-Type": "application/json",
            "apikey": self.api_key
        }
        payload = {
            "number": phone,
            "text": text
        }
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                
                # Log opcional para debug do status retornado pelo EvolutionGO
                if response.status_code >= 400:
                    print(f"[EvolutionGO] Erro HTTP {response.status_code}: {response.text}")
                
                # Tenta interpretar como JSON, caso contrário retorna o texto puro da resposta
                try:
                    return response.json()
                except Exception:
                    return {"status": "success", "raw_response": response.text}
                    
        except Exception as e:
            print(f"Erro de conexão com EvolutionGO: {str(e)}")
            return {"error": str(e)}

evolution_service = EvolutionService()
