import json
from datetime import datetime

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from app.config import settings
from app.services import session_repository
from app.services.llm_service import llm_service
from app.database_async import get_pool
import asyncpg

router = APIRouter()


class SessionAction(BaseModel):
    remote_jid: str
    conversation_id: str | None = None


class SessionUpdateRequest(SessionAction):
    dados: dict


class LLMPayload(BaseModel):
    estado: str
    texto: str


def _session_summary(row: dict) -> dict:
    dados = row.get("dados") or {}
    return {
        "remote_jid": row.get("remote_jid"),
        "conversation_id": dados.get("conversation_id"),
        "atualizado_em": row.get("atualizado_em"),
        "estado": dados.get("estado"),
        "nome": dados.get("nome"),
        "sintoma": dados.get("sintoma"),
        "convenio": dados.get("convenio"),
        "preferencia_horario": dados.get("preferencia_horario"),
        "ultimo_estado_raw": dados,
    }


async def _query_db(query: str, *args):
    pool = get_pool()
    if pool is not None:
        async with pool.acquire() as conn:
            return await conn.fetch(query, *args)

    if settings.DATABASE_URL:
        conn = await asyncpg.connect(settings.DATABASE_URL)
        try:
            return await conn.fetch(query, *args)
        finally:
            await conn.close()

    return []


@router.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    html = [
        "<!DOCTYPE html>",
        "<html lang=\"pt-BR\">",
        "<head>",
        "<meta charset=\"UTF-8\" />",
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />",
        "<title>Painel de Controle LifelineOne</title>",
        "<script src=\"https://cdn.tailwindcss.com\"></script>",
        "</head>",
        "<body class=\"bg-slate-50 text-slate-900\">",
        "<div class=\"max-w-7xl mx-auto p-6\">",
        "<header class=\"mb-8\">",
        "<h1 class=\"text-3xl font-semibold text-slate-900\">Painel de Controle LifelineOne</h1>",
        "<p class=\"mt-2 text-slate-600\">Monitoramento de sessões, testes de IA e ajuste de estados do agente clínico.</p>",
        "</header>",
        "<section class=\"grid gap-4 lg:grid-cols-3 mb-8\">",
        "<div class=\"rounded-2xl border border-slate-200 bg-white p-5 shadow-sm\">",
        "<h2 class=\"text-sm font-semibold text-slate-500 uppercase tracking-[0.16em]\">Conversas Ativas</h2>",
        "<p class=\"mt-2 text-xs text-slate-500 flex items-start gap-2\"><span class=\"mt-1 inline-flex h-2 w-2 rounded-full bg-slate-500\"></span>Resumo: quantas conversas estão em andamento. Ex: paciente aguardando coleta de sintomas.</p>",
        "<p id=\"metric-active\" class=\"mt-4 text-3xl font-bold text-slate-900\">—</p>",
        "</div>",
        "<div class=\"rounded-2xl border border-slate-200 bg-white p-5 shadow-sm\">",
        "<h2 class=\"text-sm font-semibold text-slate-500 uppercase tracking-[0.16em]\">Urgências Detectadas</h2>",
        "<p class=\"mt-2 text-xs text-slate-500 flex items-start gap-2\"><span class=\"mt-1 inline-flex h-2 w-2 rounded-full bg-rose-500\"></span>Resumo: mostra casos críticos detectados. Ex: paciente com dor intensa após triagem.</p>",
        "<p id=\"metric-urgent\" class=\"mt-4 text-3xl font-bold text-rose-600\">—</p>",
        "</div>",
        "<div class=\"rounded-2xl border border-slate-200 bg-white p-5 shadow-sm\">",
        "<h2 class=\"text-sm font-semibold text-slate-500 uppercase tracking-[0.16em]\">Consultas Agendadas</h2>",
        "<p class=\"mt-2 text-xs text-slate-500 flex items-start gap-2\"><span class=\"mt-1 inline-flex h-2 w-2 rounded-full bg-emerald-500\"></span>Resumo: total de agendamentos confirmados. Ex: consulta marcada para 10h de amanhã.</p>",
        "<p id=\"metric-scheduled\" class=\"mt-4 text-3xl font-bold text-emerald-600\">—</p>",
        "</div>",
        "</section>",
        "<div class=\"grid gap-6 xl:grid-cols-[1.5fr_1fr]\">",
        "<div class=\"space-y-6\">",
        "<div class=\"rounded-2xl border border-slate-200 bg-white p-6 shadow-sm\">",
        "<div class=\"mb-4 flex items-center justify-between\">",
        "<div>",
        "<h2 class=\"text-lg font-semibold text-slate-900\">Sessões Ativas</h2>",
        "<p class=\"text-sm text-slate-500\">Lista de conversas ativas com estado atual e dados coletados.</p>",
        "</div>",
        "<button id=\"refresh-sessions\" class=\"rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-700\">Atualizar</button>",
        "</div>",
        "<div class=\"overflow-x-auto\">",
        "<table class=\"min-w-full divide-y divide-slate-200\">",
        "<thead class=\"bg-slate-50\">",
        "<tr>",
        "<th class=\"px-4 py-3 text-left text-xs font-semibold uppercase tracking-[0.16em] text-slate-500\">Conversation ID</th>",
        "<th class=\"px-4 py-3 text-left text-xs font-semibold uppercase tracking-[0.16em] text-slate-500\">Remote JID</th>",
        "<th class=\"px-4 py-3 text-left text-xs font-semibold uppercase tracking-[0.16em] text-slate-500\">Conversation ID</th>",        "<th class=\"px-4 py-3 text-left text-xs font-semibold uppercase tracking-[0.16em] text-slate-500\">Conversation ID</th>",        "<th class=\"px-4 py-3 text-left text-xs font-semibold uppercase tracking-[0.16em] text-slate-500\">Estado</th>",
        "<th class=\"px-4 py-3 text-left text-xs font-semibold uppercase tracking-[0.16em] text-slate-500\">Nome</th>",
        "<th class=\"px-4 py-3 text-left text-xs font-semibold uppercase tracking-[0.16em] text-slate-500\">Sintoma</th>",
        "<th class=\"px-4 py-3 text-left text-xs font-semibold uppercase tracking-[0.16em] text-slate-500\">Última Atualização</th>",
        "<th class=\"px-4 py-3 text-left text-xs font-semibold uppercase tracking-[0.16em] text-slate-500\">Ações</th>",
        "</tr>",
        "</thead>",
        "<tbody id=\"sessions-table\" class=\"divide-y divide-slate-200 bg-white\"></tbody>",
        "</table>",
        "</div>",
        "</div>",
        "<div class=\"rounded-2xl border border-slate-200 bg-white p-6 shadow-sm\">",
        "<h2 class=\"text-lg font-semibold text-slate-900\">Playground de Teste da IA</h2>",
        "<p class=\"text-sm text-slate-500\">Envie um estado de máquina e uma mensagem para avaliar o JSON retornado pelo LLM.</p>",
        "<div class=\"mt-5 space-y-4\">",
        "<label class=\"block text-sm font-medium text-slate-700\">Estado atual</label>",
        "<input id=\"llm-estado\" class=\"w-full rounded-xl border border-slate-300 px-4 py-2 text-slate-900 focus:border-slate-500 focus:outline-none\" placeholder=\"inicio, aguardando_nome, aguardando_sintoma...\" />",
        "<label class=\"block text-sm font-medium text-slate-700\">Mensagem do paciente</label>",
        "<textarea id=\"llm-texto\" rows=4 class=\"w-full rounded-xl border border-slate-300 px-4 py-2 text-slate-900 focus:border-slate-500 focus:outline-none\" placeholder=\"Digite o texto para testar a extração do LLM...\"></textarea>",
        "<button id=\"run-playground\" class=\"mt-2 inline-flex items-center justify-center rounded-xl bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-700\">Executar teste</button>",
        "<pre id=\"playground-result\" class=\"mt-4 max-h-72 overflow-auto rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-800\">Aguardando teste...</pre>",
        "</div>",
        "</div>",
        "</div>",
        "<div class=\"rounded-2xl border border-slate-200 bg-white p-6 shadow-sm\">",
        "<h2 class=\"text-lg font-semibold text-slate-900\">Log de Urgências</h2>",
        "<p class=\"text-sm text-slate-500\">Casos em que a sessão entrou no estado de urgência.</p>",
        "<div id=\"urgency-list\" class=\"mt-4 space-y-3 text-sm text-slate-800\">Carregando...</div>",
        "</div>",
        "</div>",
        "</div>",
        "<script>",
        "const formatDate = (value) => {",
        "  if (!value) return '-';",
        "  try { return new Date(value).toLocaleString('pt-BR'); } catch { return value; }",
        "};",
        "async function fetchJson(path, method='GET', body=null) {",
        "  const opts = { method, headers: {'Content-Type':'application/json'} };",
        "  if (body) opts.body = JSON.stringify(body);",
        "  const response = await fetch(path, opts);",
        "  if (!response.ok) throw new Error('Falha ao carregar ' + path);",
        "  return await response.json();",
        "}",
        "async function refreshDashboard() {",
        "  try {",
        "    const metrics = await fetchJson('/admin/metrics');",
        "    document.getElementById('metric-active').textContent = metrics.active_sessions;",
        "    document.getElementById('metric-urgent').textContent = metrics.urgent_sessions;",
        "    document.getElementById('metric-scheduled').textContent = metrics.scheduled_consultations;",
        "    const sessions = await fetchJson('/admin/sessions');",
        "    const tbody = document.getElementById('sessions-table');",
        "    tbody.innerHTML = '';",
        "    if (sessions.sessions.length === 0) {",
        "      tbody.innerHTML = '<tr><td class=\"px-4 py-4 text-slate-500\" colspan=\"6\">Nenhuma sessão ativa encontrada.</td></tr>';",
        "    } else {",
        "      sessions.sessions.forEach(session => {",
        "        const row = document.createElement('tr');",
        "        row.className = 'border-b border-slate-100';",
        "        row.innerHTML = `",
        "          <td class=\"px-4 py-3 text-slate-700\">${session.remote_jid}</td>",
        "          <td class=\"px-4 py-3 text-slate-700\">${session.conversation_id || '-'} </td>",
        "          <td class=\"px-4 py-3 text-slate-700\">${session.estado || '-'} </td>",
        "          <td class=\"px-4 py-3 text-slate-700\">${session.nome || '-'} </td>",
        "          <td class=\"px-4 py-3 text-slate-700\">${session.sintoma || '-'} </td>",
        "          <td class=\"px-4 py-3 text-slate-700\">${formatDate(session.atualizado_em)}</td>",
        "          <td class=\"px-4 py-3\">",
        "            <button class=\"rounded-full bg-amber-500 px-3 py-1 text-xs font-semibold text-slate-900 hover:bg-amber-400\" onclick=\"resetSession('${session.remote_jid}')\">Resetar</button>",
        "          </td>",
        "        `;",
        "        tbody.appendChild(row);",
        "      });",
        "    }",
        "    const urgencies = await fetchJson('/admin/urgencies');",
        "    const list = document.getElementById('urgency-list');",
        "    if (!urgencies.urgent_sessions.length) {",
        "      list.innerHTML = '<div class=\"rounded-2xl border border-slate-200 bg-slate-50 p-4\">Nenhum caso de urgência registrado no momento.</div>';",
        "    } else {",
        "      list.innerHTML = urgencies.urgent_sessions.map(item => `",
        "        <div class=\"rounded-2xl border border-rose-200 bg-rose-50 p-4\">",
        "          <strong>${item.remote_jid}</strong> — estado: ${item.estado || '-'}<br/>",
        "          nome: ${item.nome || '-'}<br/>",
        "          sintoma: ${item.sintoma || '-'}<br/>",
        "          atualizado em: ${formatDate(item.atualizado_em)}",
        "        </div>"
        "      `).join('');",
        "    }",
        "  } catch (error) {",
        "    console.error(error);",
        "  }",
        "}",
        "async function resetSession(remote_jid) {",
        "  if (!confirm('Deseja resetar a sessão ' + remote_jid + ' para o estado inicial?')) return;",
        "  await fetchJson('/admin/session/reset', 'POST', { remote_jid });",
        "  await refreshDashboard();",
        "}",
        "document.getElementById('refresh-sessions').addEventListener('click', refreshDashboard);",
        "document.getElementById('run-playground').addEventListener('click', async () => {",
        "  const estado = document.getElementById('llm-estado').value.trim();",
        "  const texto = document.getElementById('llm-texto').value.trim();",
        "  if (!estado || !texto) {",
        "    document.getElementById('playground-result').textContent = 'Preencha o estado e o texto para testar.';",
        "    return;",
        "  }",
        "  document.getElementById('playground-result').textContent = 'Carregando...';",
        "  try {",
        "    const result = await fetchJson('/admin/llm-playground', 'POST', { estado, texto });",
        "    document.getElementById('playground-result').textContent = JSON.stringify(result, null, 2);",
        "  } catch (error) {",
        "    document.getElementById('playground-result').textContent = 'Erro ao executar o playground: ' + error.message;",
        "  }",
        "});",
        "refreshDashboard();",
        "setInterval(refreshDashboard, 15000);",
        "</script>",
        "</body>",
        "</html>",
    ]
    return HTMLResponse("".join(html))


@router.get('/admin/sessions')
async def admin_sessions():
    sessions = await session_repository.obter_todas_sessoes_async()
    return JSONResponse({"sessions": [_session_summary(s) for s in sessions]})


@router.get('/admin/metrics')
async def admin_metrics():
    sessions = await session_repository.obter_todas_sessoes_async()
    active_sessions = len(sessions)
    urgent_sessions = sum(1 for s in sessions if (s.get('dados') or {}).get('estado') == 'urgencia_detectada')
    scheduled_count = 0
    if settings.DATABASE_URL:
        try:
            result = await _query_db('SELECT COUNT(*) AS total FROM agendamentos_confirmados')
            scheduled_count = result[0]['total'] if result else 0
        except Exception:
            scheduled_count = 0
    return JSONResponse({
        'active_sessions': active_sessions,
        'urgent_sessions': urgent_sessions,
        'scheduled_consultations': scheduled_count,
    })


@router.get('/admin/urgencies')
async def admin_urgencies():
    sessions = await session_repository.obter_todas_sessoes_async()
    urgent_sessions = [
        _session_summary(s)
        for s in sessions
        if (s.get('dados') or {}).get('estado') == 'urgencia_detectada'
    ]
    return JSONResponse({'urgent_sessions': urgent_sessions})


@router.post('/admin/session/reset')
async def admin_reset_session(payload: SessionAction):
    await session_repository.resetar_sessao_async(payload.remote_jid)
    return JSONResponse({'status': 'ok', 'remote_jid': payload.remote_jid})


@router.post('/admin/session/update')
async def admin_update_session(payload: SessionUpdateRequest):
    if not payload.dados:
        raise HTTPException(status_code=400, detail='Dados da sessão são obrigatórios')
    await session_repository.salvar_sessao_async(payload.remote_jid, payload.dados)
    return JSONResponse({'status': 'ok', 'remote_jid': payload.remote_jid})


@router.post('/admin/llm-playground')
async def admin_llm_playground(payload: LLMPayload):
    if not payload.estado or not payload.texto:
        raise HTTPException(status_code=400, detail='Estado e texto são obrigatórios')
    resultado = llm_service.extract_structured(payload.estado, payload.texto)
    return JSONResponse({
        'enabled': llm_service.enabled,
        'resultado': resultado,
    })
