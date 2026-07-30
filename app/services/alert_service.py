import logging
from typing import Any

logger = logging.getLogger(__name__)


def notificar_urgencia(
    remote_jid: str | None,
    texto_usuario: str,
    dados_sessao: dict[str, Any],
    *,
    origem: str,
) -> None:
    """Registra alerta interno de urgencia para acompanhamento humano."""
    logger.warning(
        "Urgencia medica detectada no atendimento",
        extra={
            "remote_jid": remote_jid,
            "origem": origem,
            "nome": dados_sessao.get("nome"),
            "estado": dados_sessao.get("estado"),
            "texto_usuario": texto_usuario,
        },
    )
