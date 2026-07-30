import json

from fastapi import APIRouter
from fastapi.responses import HTMLResponse
import asyncpg

from app.config import settings
from app.database_async import get_pool

router = APIRouter()


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


def _render_json(value):
    try:
        return json.dumps(value, ensure_ascii=False, indent=2)
    except Exception:
        return str(value)


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    if not settings.DATABASE_URL:
        return HTMLResponse(
            "<h1>Dashboard Lifeline</h1>"
            "<p><strong>DATABASE_URL</strong> não está configurada. Configure o arquivo <code>.env</code> e reinicie a aplicação.</p>",
            status_code=200,
        )

    try:
        sessoes = await _query_db(
            "SELECT remote_jid, atualizado_em, dados FROM sessoes ORDER BY atualizado_em DESC LIMIT 100"
        )
        agendamentos = await _query_db(
            "SELECT id, remote_jid, criado_em, dados FROM agendamentos_confirmados ORDER BY criado_em DESC LIMIT 100"
        )
        disponiveis = await _query_db(
            "SELECT COUNT(*) AS total FROM agendamentos WHERE status = 'disponivel'"
        )
        reservados = await _query_db(
            "SELECT COUNT(*) AS total FROM agendamentos WHERE status = 'reservado'"
        )
    except Exception as exc:
        return HTMLResponse(
            f"<h1>Dashboard Lifeline</h1><p>Erro consultando o banco de dados: {exc}</p>",
            status_code=500,
        )

    disponiveis_count = disponiveis[0]["total"] if disponiveis else 0
    reservados_count = reservados[0]["total"] if reservados else 0

    sessoes_rows = []
    for row in sessoes:
        sessoes_rows.append(
            {
                "remote_jid": row["remote_jid"],
                "atualizado_em": row["atualizado_em"],
                "dados": _render_json(row["dados"]),
            }
        )

    agendamentos_rows = []
    for row in agendamentos:
        agendamentos_rows.append(
            {
                "id": row["id"],
                "remote_jid": row["remote_jid"],
                "criado_em": row["criado_em"],
                "dados": _render_json(row["dados"]),
            }
        )

    html = [
        "<html><head><title>Dashboard Lifeline</title>"
        "<style>body{font-family:Arial,sans-serif;margin:20px;}"
        "table{border-collapse:collapse;width:100%;margin-bottom:24px;}"
        "th,td{border:1px solid #ddd;padding:8px;text-align:left;vertical-align:top;}"
        "th{background:#f7f7f7;}"
        "pre{background:#f4f4f4;padding:10px;border-radius:4px;overflow:auto;}",
        "</style></head><body>"
        "<h1>Dashboard Lifeline</h1>"
        "<p>Visão geral de sessões, agendamentos confirmados e disponibilidade de horários.</p>"
        f"<p><strong>Horários disponíveis:</strong> {disponiveis_count} | "
        f"<strong>Reservados:</strong> {reservados_count}</p>"
        "<h2>Sessões de conversa</h2>"
        "<table><thead><tr><th>Remote JID</th><th>Última Atualização</th><th>Dados</th></tr></thead><tbody>"
    ]

    if sessoes_rows:
        for row in sessoes_rows:
            html.append(
                "<tr>"
                f"<td>{row['remote_jid']}</td>"
                f"<td>{row['atualizado_em']}</td>"
                f"<td><pre>{row['dados']}</pre></td>"
                "</tr>"
            )
    else:
        html.append("<tr><td colspan=3>Nenhuma sessão encontrada.</td></tr>")

    html.append("</tbody></table><h2>Agendamentos confirmados</h2>")
    html.append(
        "<table><thead><tr><th>ID</th><th>Remote JID</th><th>Criado em</th><th>Dados</th></tr></thead><tbody>"
    )

    if agendamentos_rows:
        for row in agendamentos_rows:
            html.append(
                "<tr>"
                f"<td>{row['id']}</td>"
                f"<td>{row['remote_jid']}</td>"
                f"<td>{row['criado_em']}</td>"
                f"<td><pre>{row['dados']}</pre></td>"
                "</tr>"
            )
    else:
        html.append("<tr><td colspan=4>Nenhum agendamento confirmado encontrado.</td></tr>")

    html.append("</tbody></table></body></html>")
    return HTMLResponse("".join(html))
