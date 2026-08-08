import uuid
import logging
from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.config import settings
from app.agents.admin_config import admin_config_agent

logger = logging.getLogger(__name__)

router = APIRouter()


class ConfigChatRequest(BaseModel):
    command_text: Optional[str] = None
    instruction: Optional[str] = None
    message: Optional[str] = None
    user_name: Optional[str] = "Dr. Gustav Baptista"


@router.post("/config-chat")
async def process_chatops_command(
    payload: ConfigChatRequest,
    db: AsyncSession = Depends(get_db)
):
    clinic_id = uuid.UUID(settings.DEFAULT_CLINIC_ID)
    cmd_text = payload.command_text or payload.instruction or payload.message or "resumo do projeto"
    user_name = payload.user_name or "Dr. Gustav Baptista"

    result = await admin_config_agent.process_config_command(
        db=db,
        clinic_id=clinic_id,
        command_text=cmd_text,
        user_name=user_name
    )
    return result
