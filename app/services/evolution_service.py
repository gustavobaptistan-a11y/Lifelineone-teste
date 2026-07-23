import requests
from app.config import settings

class EvolutionService:
    def __init__(self):
        self.base_url = settings.EVOLUTION_API_URL.rstrip("/")
        self.api_key = settings.EVOLUTION_API_KEY
        self.instance = settings.EVOLUTION_INSTANCE

    def enviar_mensagem(self, remote_jid: str, texto: str) -> bool:
        """
        Envia mensagem de texto utilizando o endpoint /send/text com autenticação dupla para Evolution GO.
        """
        url = f"{self.base_url}/send/text"
        
        # Envia os dois padrões comuns de autenticação para evitar falhas de chave
        headers = {
            "Content-Type": "application/json",
            "apikey": self.api_key,
            "Authorization": f"Bearer {self.api_key}"
        }
        
        number = remote_jid.split("@")[0]

        payload = {
            "instance": self.instance,
            "number": number,
            "text": texto
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            if response.status_code in [200, 201]:
                print(f"📤 [EVOLUTION GO] Mensagem enviada com sucesso para {number}")
                return True
            else:
                print(f"❌ [EVOLUTION GO] Erro ao enviar ({response.status_code}): {response.text}")
                return False
        except Exception as e:
            print(f"❌ [EVOLUTION GO] Falha de conexão: {e}")
            return False

evolution_service = EvolutionService()
