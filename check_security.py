import os
import re
from pathlib import Path

def verificar_seguranca():
    print("🔒 Iniciando auditoria de segurança do projeto...\n")
    
    # 1. Verificar .env
    env_path = Path(".env")
    if env_path.exists():
        print("✅ [OK] Arquivo .env encontrado na raiz do projeto.")
    else:
        print("❌ [ALERTA] Arquivo .env NÃO encontrado! Crie um arquivo .env para armazenar suas chaves.")

    # 2. Verificar .gitignore
    gitignore_path = Path(".gitignore")
    if gitignore_path.exists():
        conteudo_gitignore = gitignore_path.read_text(encoding="utf-8")
        ignora_env = ".env" in conteudo_gitignore
        ignora_cache = "__pycache__" in conteudo_gitignore
        if ignora_env and ignora_cache:
            print("✅ [OK] O arquivo .gitignore está protegendo o .env e os caches.")
        else:
            print("⚠️ [ATENÇÃO] O .gitignore pode estar incompleto. Garanta que .env e __pycache__/ constem nele.")
    else:
        print("❌ [ALERTA] Arquivo .gitignore não encontrado!")

    # 3. Varredura por chaves expostas (ex: OpenAI API Key sk-...)
    print("\n🔍 Varrendo arquivos Python em busca de chaves hardcoded...")
    padrao_openai = re.compile(r"sk-[a-zA-Z0-9-_]{20,}")
    arquivos_py = list(Path(".").rglob("*.py"))
    
    encontrou_chave = False
    for arquivo in arquivos_py:
        if ".venv" in arquivo.parts or "__pycache__" in arquivo.parts:
            continue
        try:
            texto = arquivo.read_text(encoding="utf-8")
            matches = padrao_openai.findall(texto)
            if matches:
                print(f"🚨 [CRÍTICO] Padrão de chave secreta detectado em: {arquivo}")
                encontrou_chave = True
        except Exception:
            pass
            
    if not encontrou_chave:
        print("✅ [OK] Nenhuma chave da OpenAI exposta foi encontrada nos arquivos do projeto.")
    
    print("\n" + "="*50)
    print("📋 GUIA DE LOCALIZAÇÃO CORRETA DOS DADOS:")
    print("="*50)
    print("1. Chaves de API e Segredos (OpenAI, DB URL):")
    print("   -> Devem ficar EXCLUSIVAMENTE no arquivo local `.env`.")
    print("2. Proteção de Repositório:")
    print("   -> O arquivo `.env` deve obrigatoriamente estar listado no `.gitignore`.")
    print("3. Consumo no Código:")
    print("   -> Devem ser carregados de forma segura via `app/config.py` (utilizando Pydantic Settings, ex: `settings.OPENAI_API_KEY`).")

if __name__ == "__main__":
    verificar_seguranca()
