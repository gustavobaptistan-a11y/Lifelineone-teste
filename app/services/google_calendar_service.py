import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/calendar"]


class GoogleCalendarService:
    def __init__(self) -> None:
        self.enabled = settings.GOOGLE_CALENDAR_ENABLED
        self.calendar_id = settings.GOOGLE_CALENDAR_ID
        self.credentials_file = Path(settings.GOOGLE_CREDENTIALS_FILE)
        self.token_file = Path(settings.GOOGLE_TOKEN_FILE)
        self._service: Any | None = None

    def _build_service(self) -> Any:
        if self._service is not None:
            return self._service
        if not self.credentials_file.exists():
            raise FileNotFoundError(
                f"Credencial Google nao encontrada: {self.credentials_file}"
            )

        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build

        credentials = None
        if self.token_file.exists():
            credentials = Credentials.from_authorized_user_file(
                str(self.token_file), SCOPES
            )
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        if not credentials or not credentials.valid:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(self.credentials_file), SCOPES
            )
            credentials = flow.run_local_server(port=0)
        self.token_file.parent.mkdir(parents=True, exist_ok=True)
        self.token_file.write_text(credentials.to_json(), encoding="utf-8")
        self._service = build("calendar", "v3", credentials=credentials)
        return self._service

    def _ensure_enabled(self) -> None:
        if not self.enabled:
            raise RuntimeError("Google Calendar desabilitado")

    def listar_eventos(
        self, inicio: datetime, fim: datetime, limite: int = 100
    ) -> list[dict[str, Any]]:
        self._ensure_enabled()
        response = (
            self._build_service()
            .events()
            .list(
                calendarId=self.calendar_id,
                timeMin=inicio.isoformat(),
                timeMax=fim.isoformat(),
                singleEvents=True,
                orderBy="startTime",
                maxResults=limite,
            )
            .execute()
        )
        return response.get("items", [])

    def criar_evento(
        self,
        titulo: str,
        inicio: datetime,
        fim: datetime,
        descricao: str = "",
    ) -> dict[str, Any]:
        self._ensure_enabled()
        body = {
            "summary": titulo,
            "description": descricao,
            "start": {"dateTime": inicio.isoformat()},
            "end": {"dateTime": fim.isoformat()},
        }
        return (
            self._build_service()
            .events()
            .insert(calendarId=self.calendar_id, body=body)
            .execute()
        )


calendar_service = GoogleCalendarService()
