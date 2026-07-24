import os
import requests
from dotenv import load_dotenv, find_dotenv

# Forca o carregamento explisito do .env da raiz
load_dotenv(find_dotenv(), override=True)

EVOLUTION_URL = os.getenv("EVOLUTION_API_URL")
EVOLUTION_KEY = os.getenv("EVOLUTION_API_KEY")
INSTANCE_NAME = os.getenv("EVOLUTION_INSTANCE")

def testar_conexao():
    print(f"URL Lida: {EVOLUTION_URL}")
    print(f"Instancia Lida: {INSTANCE_NAME}")
    
    if not EVOLUTION_URL or not EVOLUTION_KEY or not INSTANCE_NAME:
        print("Erro: Alguma variavel importante esta faltando no .env!")
        return

    url = f"{EVOLUTION_URL.rstrip('/')}/instance/connectionState/{INSTANCE_NAME}"
    headers = {"apikey": EVOLUTION_KEY}
    
    print(f"Testando conexao com a instancia '{INSTANCE_NAME}'...")
    try:
        response = requests.get(url, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Resposta: {response.json()}")
    except Exception as e:
        print(f"Erro ao conectar com a Evolution API: {e}")

if __name__ == "__main__":
    testar_conexao()
