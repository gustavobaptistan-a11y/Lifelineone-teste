from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseWhatsAppProvider(ABC):
    """Interface abstrata para provedores de WhatsApp (Evolution API, Meta Cloud API, Z-API)."""

    @abstractmethod
    async def send_message(self, phone: str, text: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def send_media(self, phone: str, media_url: str, caption: Optional[str] = None) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def send_location(
        self, phone: str, latitude: float, longitude: float, address: str
    ) -> Dict[str, Any]:
        pass
