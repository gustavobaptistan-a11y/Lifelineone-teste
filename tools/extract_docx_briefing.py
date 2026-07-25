from pathlib import Path
from docx import Document

INPUT = Path('Briefing_Rauder_de_Azevedo_CTO.docx')
OUTPUT = Path('docs') / 'BRIEFING_Rauder_de_Azevedo_CTO.md'

if not INPUT.exists():
    raise FileNotFoundError(f"Arquivo não encontrado: {INPUT}")

doc = Document(str(INPUT))
texts = []
for para in doc.paragraphs:
    if para.text and para.text.strip():
        texts.append(para.text.strip())

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text('\n\n'.join(texts), encoding='utf-8')
print(f"Extraído para: {OUTPUT}")
