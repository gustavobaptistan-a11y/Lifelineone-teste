import os


def criar_estrutura():
  print("Criando a estrutura profissional para o Robô IA BTCUSD#...")

  # Definindo as pastas do projeto
  pastas = ["logs", "modelos", "config"]

  for pasta in pastas:
    os.makedirs(pasta, exist_ok=True)
    print(f"[+] Pasta criada/verificada: {pasta}/")

  # Criando o arquivo .env de exemplo para credenciais/configurações futuras
  env_path = ".env"
  if not os.path.exists(env_path):
    with open(env_path, "w", encoding="utf-8") as f:
      f.write("MT5_LOGIN=\nMT5_PASSWORD=\nMT5_SERVER=\n")
    print("[+] Arquivo .env criado.")

  # Criando o arquivo requirements.txt com as dependências necessárias
  req_path = "requirements.txt"
  conteudo_req = (
      "MetaTrader5==5.0.45\npandas==2.2.2\nnumpy==1.26.4\nscikit-learn==1.4.2\n"
  )
  with open(req_path, "w", encoding="utf-8") as f:
    f.write(conteudo_req)
  print("[+] Arquivo requirements.txt criado.")

  print(
      "\nEstrutura criada com sucesso! Agora execute 'pip install -r"
      " requirements.txt' no terminal."
  )


if __name__ == "__main__":
  criar_estrutura()