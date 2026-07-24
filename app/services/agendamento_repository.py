import json
import os
from datetime import datetime

class AgendamentoRepository:
    def __init__(self, arquivo_db="agendamentos_db.json"):
        self.arquivo_db = arquivo_db
        self._inicializar()

    def _inicializar(self):
        if not os.path.exists(self.arquivo_db):
            with open(self.arquivo_db, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=4)

    def salvar_agendamento(self, remote_jid: str, dados_sessao: dict):
        """
        Salva o agendamento completo estruturado com todas as variáveis do fluxo.
        """
        try:
            with open(self.arquivo_db, "r", encoding="utf-8") as f:
                lista = json.load(f)
        except Exception:
            lista = []

        # Mapeamento completo e padronizado do registro clínico
        registro_completo = {
            "id_agendamento": f"AG-{int(datetime.now().timestamp())}",
            "whatsapp_jid": remote_jid,
            "data_criacao": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status_agendamento": "CONFIRMADO",
            "paciente": {
                "nome_completo": dados_sessao.get("nome", "Não informado"),
                "contato": remote_jid.split("@")[0]
            },
            "triagem": {
                "sintoma_principal": dados_sessao.get("sintoma", "Não informado"),
                "modalidade_atendimento": dados_sessao.get("convenio", "Não informado"),
                "tipo_consulta": (
                    "Primeira consulta" if dados_sessao.get("primeira_consulta") is True else
                    "Retorno" if dados_sessao.get("primeira_consulta") is False else
                    "Não informado"
                )
            },
            "agendamento": {
                "preferencia_periodo": dados_sessao.get("preferencia_horario", "Não informado"),
                "opcao_horario_escolhida": dados_sessao.get("horario", "Não informado")
            }
        }

        lista.append(registro_completo)

        with open(self.arquivo_db, "w", encoding="utf-8") as f:
            json.dump(lista, f, ensure_ascii=False, indent=4)
        
        print(f"💾 [BANCO DE DADOS] Agendamento estruturado de '{registro_completo['paciente']['nome_completo']}' salvo com ID: {registro_completo['id_agendamento']}")

agendamento_repository = AgendamentoRepository()
