import json
import os
import time
import requests
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

# --- Configuração ---
# Use variáveis de ambiente para flexibilidade, com valores padrão para conveniência.
URL_WEBHOOK = os.getenv("LIFELINE_WEBHOOK_URL", "http://127.0.0.1:8000/webhook")
REMOTE_JID = os.getenv("LIFELINE_TEST_JID", "5561999999999@s.whatsapp.net")

# Usar uma estrutura de dados mais rica para os testes.
# Isso permite adicionar o estado esperado para validação futura.
MENSAGENS_TESTE = [
    {"texto": "Olá, gostaria de agendar uma consulta médica.", "estado_esperado": "coletando_nome"},
    {"texto": "Meu nome é Carlos Eduardo", "estado_esperado": "coletando_motivo"},
    {"texto": "Estou com muitas dores de cabeça e tontura", "estado_esperado": "coletando_convenio"},
    {"texto": "Tenho convênio Bradesco Saúde", "estado_esperado": "coletando_status_paciente"},
    {"texto": "Já sou paciente da clínica", "estado_esperado": "coletando_preferencia_horario"},
    {"texto": "Prefiro no período da manhã", "estado_esperado": "confirmando_horario"},
    {"texto": "Opção 1", "estado_esperado": "agendamento_confirmado"},
]

console = Console()


def enviar_mensagem(texto: str):
    """Envia uma mensagem para o webhook e retorna a resposta e o estado."""
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    payload = {
        "data": {
            "key": {
                "remoteJid": REMOTE_JID
            },
            "message": {
                "conversation": texto
            }
        }
    }
    
    try:
        # Timeout de 30 segundos para cobrir oscilações na API da OpenAI.
        response = requests.post(URL_WEBHOOK, json=payload, headers=headers, timeout=30)
        response.raise_for_status()  # Lança uma exceção para erros HTTP (4xx ou 5xx).

        if response.status_code == 200:
            dados = response.json()
            if dados.get("status") == "sucesso":
                resposta_ia = dados.get("resposta_enviada", "")
                json_llm = dados.get("json_interno_llm", {})
                proximo_estado = json_llm.get("proximo_estado", "Desconhecido")
                dados_extraidos = json.dumps(json_llm.get("dados_extraidos", {}), ensure_ascii=False)
                return resposta_ia, proximo_estado, dados_extraidos
            else:
                return f"Erro no Backend: {dados.get('detalhes')}", "Erro", {}
    except requests.exceptions.RequestException as e:
        return f"Erro na conexão com o servidor: {str(e)}", "Erro", {}
    except json.JSONDecodeError:
        return "Erro: A resposta do servidor não é um JSON válido.", "Erro", {}


def main():
    """Executa a simulação completa do fluxo de agendamento."""
    console.rule("[bold cyan]🏥 SIMULAÇÃO COMPLETA DE AGENDAMENTO — LIFELINE ONE[/bold cyan]", style="cyan")
    console.print()

    for i, msg_info in enumerate(MENSAGENS_TESTE, 1):
        msg_usuario = msg_info["texto"]
        
        console.print(Panel(
            Text(f'"{msg_usuario}"', style="bright_white"),
            title=f"👤 [Passo {i}] PACIENTE",
            title_align="left",
            border_style="blue"
        ))
        
        with console.status("[yellow]⏳ Aguardando resposta da Ana (IA)...[/yellow]", spinner="dots"):
            resposta_ia, estado, dados_coletados = enviar_mensagem(msg_usuario)
            time.sleep(1) # Pausa para simular um tempo de resposta mais natural

        console.print(Panel(
            Text(f'"{resposta_ia}"', style="bright_white") + Text(f"\n\n⚙️  STATUS BACKEND -> Estado: [bold magenta]{estado}[/bold magenta] | Dados: {dados_coletados}", style="dim"),
            title=f"🤖 [Passo {i}] ANA (IA)",
            title_align="left",
            border_style="green"
        ))
        console.print()

    console.rule("[bold green]✅ TESTE DE FLUXO COMPLETO FINALIZADO![/bold green]", style="green")

if __name__ == "__main__":
    main()