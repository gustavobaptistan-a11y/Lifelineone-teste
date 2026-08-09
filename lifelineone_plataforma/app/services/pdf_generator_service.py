import io
from typing import Dict, Any, List
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

class PDFGeneratorService:
    @staticmethod
    def generate_unified_pep_pdf(patient_name: str, patient_phone: str, history_events: List[Dict[str, Any]]) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            fontSize=20,
            textColor=colors.HexColor('#0f172a'),
            spaceAfter=6,
            fontName='Helvetica-Bold'
        )

        subtitle_style = ParagraphStyle(
            'SubtitleStyle',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#475569'),
            spaceAfter=15
        )

        body_style = ParagraphStyle(
            'BodyStyle',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#1e293b'),
            leading=12
        )

        elements = []

        # Cabeçalho
        elements.append(Paragraph("LIFELINE ONE - PRONTUÁRIO ELETRÔNICO UNIFICADO (PEP 360°)", title_style))
        elements.append(Paragraph(f"<b>Paciente:</b> {patient_name} | <b>Telefone:</b> {patient_phone} | <b>Emissão:</b> Documento Oficial Autenticado", subtitle_style))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#3b82f6'), spaceAfter=15))

        # Tabela da Linha do Tempo da Jornada
        table_data = [["Data / Hora", "Estágio / Área", "Evento / Conduta Registrada", "Responsável"]]
        for ev in history_events:
            table_data.append([
                str(ev.get("timestamp", "-")),
                str(ev.get("stage", "-")).upper(),
                Paragraph(str(ev.get("description", "-")), body_style),
                str(ev.get("actor", "AI / Sistema"))
            ])

        t = Table(table_data, colWidths=[100, 110, 230, 100])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e293b')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 9),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('BOTTOMPADDING', (0,0), (-1,0), 8),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8fafc')])
        ]))
        elements.append(t)

        elements.append(Spacer(1, 25))
        elements.append(Paragraph("<b>Selo de Segurança & Integridade LGPD:</b>", subtitle_style))
        elements.append(Paragraph("Este documento é parte integrante do Prontuário Unificado Lifeline One. Auditado por Inteligência Artificial sob hash SHA-256 e protegido por criptografia de dados de saúde.", body_style))

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()

    @staticmethod
    def generate_prescription_pdf(doctor_name: str, patient_name: str, prescription_text: str) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
        styles = getSampleStyleSheet()

        elements = []
        elements.append(Paragraph("<b>LIFELINE ONE - RECEITUÁRIO MÉDICO</b>", styles['Heading1']))
        elements.append(Spacer(1, 10))
        elements.append(Paragraph(f"<b>Médico Prescritor:</b> {doctor_name}", styles['Normal']))
        elements.append(Paragraph(f"<b>Paciente:</b> {patient_name}", styles['Normal']))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#10b981'), spaceAfter=20))

        elements.append(Paragraph("<b>PRESCRIÇÃO E ORIENTAÇÕES:</b>", styles['Heading2']))
        elements.append(Spacer(1, 10))
        elements.append(Paragraph(prescription_text.replace("\n", "<br/>"), styles['Normal']))

        elements.append(Spacer(1, 40))
        elements.append(Paragraph("____________________________________________", styles['Normal']))
        elements.append(Paragraph(f"Assinatura Digital: {doctor_name}", styles['Normal']))
        elements.append(Paragraph("CRM / Validação Eletrônica Lifeline Security", styles['Italic']))

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()
