from typing import Optional
from pydantic import BaseModel, Field

class DadosExtraidos(BaseModel):
    nome: Optional[str] = Field(default=None, description="Nome completo do paciente extraído da mensagem")
    sintoma: Optional[str] = Field(default=None, description="Motivo da consulta ou sintoma relatado")
    convenio: Optional[str] = Field(default=None, description="Nome do convênio ou se é particular")
    primeira_consulta: Optional[bool] = Field(default=None, description="True se for primeira vez, False se for retorno")
    preferencia_horario: Optional[str] = Field(default=None, description="Período de preferência (manhã/tarde)")
    opcao_escolhida_id: Optional[int] = Field(default=None, description="Número da opção de horário escolhida pelo paciente")

class RespostaAgente(BaseModel):
    resposta_paciente: str = Field(..., description="Texto humanizado que será enviado ao WhatsApp do paciente")
    proximo_estado: str = Field(..., description="Próximo estado obrigatório da máquina de estados")
    dados_extraidos: DadosExtraidos = Field(default_factory=DadosExtraidos, description="Dados estruturados coletados nesta interação")
