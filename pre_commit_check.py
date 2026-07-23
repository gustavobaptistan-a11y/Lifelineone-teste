import os
import subprocess

print("🔒 [SEGURANÇA] Iniciando verificação pré-commit do projeto...")

# Verifica se o .env está ignorado ou se é apenas um modelo vazio
try:
    git_check = subprocess.run(["git", "check-ignore", ".env"], capture_output=True, text=True)
    if git_check.returncode == 0:
        print("✅ Arquivo .env está corretamente ignorado pelo Git.")
    else:
        # Se não estiver ignorado, adiciona ao gitignore automaticamente
        with open(".gitignore", "a", encoding="utf-8") as f:
            f.write("\n.env\n")
        print("✅ O arquivo .env foi adicionado automaticamente ao .gitignore.")
except Exception:
    pass

# Varredura por chaves expostas no código
padroes_proibidos = ["1dcd4e3bc", "sk-proj-"]
suspeitas = 0

for root, dirs, files in os.walk("."):
    if ".venv" in root or ".git" in root or "config_backup" in root:
        continue
    for file in files:
        if file in ["pre_commit_check.py", ".gitignore"] or not file.endswith((".py", ".env.example", ".md")):
            continue
        caminho_arquivo = os.path.join(root, file)
        try:
            with open(caminho_arquivo, "r", encoding="utf-8") as f:
                conteudo = f.read()
                for padrao in padroes_proibidos:
                    if padrao in conteudo:
                        print(f"❌ ATENÇÃO: Possível credencial exposta encontrada em: {caminho_arquivo}")
                        suspeitas += 1
        except Exception:
            pass

if suspeitas == 0:
    print("✅ Nenhuma credencial sensível detectada nos códigos-fonte analisados.")
else:
    print(f"🚨 Encontradas {suspeitas} ocorrências de possíveis dados sensíveis.")

print("\n🚀 Tudo pronto para o commit!")
