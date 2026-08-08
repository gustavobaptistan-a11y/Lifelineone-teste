from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
import os

router = APIRouter()

@router.get("/painel", response_class=HTMLResponse)
def painel_refinamento(request: Request):
    prompts_dir = os.path.join("src", "agents", "prompts")
    arquivos = [f.replace(".txt", "") for f in os.listdir(prompts_dir) if f.endswith(".txt")]
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <title>Painel de Refinamento de IAs - Clinica</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 20px; }}
            .container {{ max-width: 1000px; margin: auto; background: #1e293b; padding: 30px; border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.3); }}
            h1 {{ color: #38bdf8; text-align: center; margin-bottom: 30px; }}
            .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
            .card {{ background: #0f172a; padding: 20px; border-radius: 8px; border: 1px solid #334155; }}
            label {{ display: block; margin-bottom: 8px; font-weight: 600; color: #94a3b8; }}
            select, textarea, input[type="text"] {{ width: 100%; padding: 12px; background: #1e293b; border: 1px solid #475569; color: #fff; border-radius: 6px; margin-bottom: 15px; font-size: 14px; box-sizing: border-box; }}
            textarea {{ height: 220px; resize: vertical; font-family: monospace; }}
            button {{ background: #0284c7; color: white; border: none; padding: 12px 20px; border-radius: 6px; cursor: pointer; font-weight: bold; width: 100%; transition: background 0.2s; }}
            button:hover {{ background: #0ea5e9; }}
            .chat-box {{ height: 180px; background: #1e293b; border: 1px solid #475569; border-radius: 6px; padding: 10px; overflow-y: auto; margin-bottom: 15px; font-size: 13px; }}
            .msg-user {{ color: #38bdf8; margin-bottom: 8px; }}
            .msg-ai {{ color: #4ade80; margin-bottom: 8px; }}
        </style>
        <script>
            async function carregarPrompt() {{
                const agente = document.getElementById("agente_select").value;
                const response = await fetch(`/api/prompt/${{agente}}`);
                const data = await response.json();
                document.getElementById("conteudo_prompt").value = data.prompt;
            }}

            async function salvarPrompt(event) {{
                event.preventDefault();
                const agente = document.getElementById("agente_select").value;
                const conteudo = document.getElementById("conteudo_prompt").value;
                
                await fetch(`/api/prompt/${{agente}}`, {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ conteudo }})
                }});
                alert("Prompt refinado e salvo com sucesso!");
            }}

            async function testarIA(event) {{
                event.preventDefault();
                const agente = document.getElementById("agente_select").value;
                const mensagem = document.getElementById("mensagem_teste").value;
                
                const chatBox = document.getElementById("chat_box");
                chatBox.innerHTML += `<div class="msg-user"><b>Você:</b> ${{mensagem}}</div>`;
                
                const response = await fetch('/api/testar', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ agente, mensagem }})
                }});
                const data = await response.json();
                
                chatBox.innerHTML += `<div class="msg-ai"><b>IA (${{agente}}):</b> ${{data.resposta}}</div>`;
                chatBox.scrollTop = chatBox.scrollHeight;
                document.getElementById("mensagem_teste").value = "";
            }}
        </script>
    </head>
    <body onload="carregarPrompt()">
        <div class="container">
            <h1>🎛️ Painel Avançado de Refinamento de Agentes</h1>
            <div style="margin-bottom: 20px;">
                <label>Selecione o Agente para Calibrar:</label>
                <select id="agente_select" onchange="carregarPrompt()">
                    {''.join([f'<option value="{a}">{a.capitalize()}</option>' for a in arquivos])}
                </select>
            </div>
            
            <div class="grid">
                <div class="card">
                    <h3>📝 Editor de System Prompt</h3>
                    <form onsubmit="salvarPrompt(event)">
                        <label>Instrução Comportamental:</label>
                        <textarea id="conteudo_prompt"></textarea>
                        <button type="submit">💾 Salvar Refinamento</button>
                    </form>
                </div>
                <div class="card">
                    <h3>💬 Simulador de Atendimento</h3>
                    <div id="chat_box" class="chat-box"></div>
                    <form onsubmit="testarIA(event)">
                        <input type="text" id="mensagem_teste" placeholder="Digite uma mensagem..." required>
                        <button type="submit" style="background: #16a34a;">⚡ Testar Resposta da IA</button>
                    </form>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return html_content
