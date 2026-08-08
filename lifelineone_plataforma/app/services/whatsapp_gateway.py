from typing import Dict, Any, Optional
from app.services.whatsapp.base import BaseWhatsAppProvider
from app.services.whatsapp.evolution_provider import EvolutionAPIProvider

class WhatsAppGatewayService:
    """
    Gateway de abstração para o WhatsApp.
    Permite trocar entre Evolution API (gratuito) e Meta Cloud API (oficial pago) via configuração.
    """

    def __init__(self, provider: Optional[BaseWhatsAppProvider] = None):
        self.provider = provider or EvolutionAPIProvider()

    async def dispatch_ai_response(
        self, phone: str, response_text: str, tool_outputs: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Envia a resposta gerada pelo Lifeline AI Orchestrator para o paciente no WhatsApp.
        Se houve chamada de ferramenta de localização, envia a localização gráfica em seguida!
        """
        res = await self.provider.send_message(phone=phone, text=response_text)

        # Se a IA enviou localização via tool
        if tool_outputs and "localizacao" in tool_outputs:
            loc = tool_outputs["localizacao"]
            await self.provider.send_location(
                phone=phone,
                latitude=-23.5615,
                longitude=-46.6559,
                address=loc.get("address", "Av. Paulista, 1000")
            )

        return res

whatsapp_gateway = WhatsAppGatewayService()
