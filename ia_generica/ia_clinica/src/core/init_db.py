import time
from sqlalchemy.exc import OperationalError
from src.core.database import engine, Base
from src.models.paciente import PacienteModel

def init_db():
    print("Conectando ao banco de dados e aguardando o serviço ficar pronto...")
    
    tentativas = 10
    for tentativa in range(1, tentativas + 1):
        try:
            # Tenta conectar e criar as tabelas
            Base.metadata.create_all(bind=engine)
            print("Tabelas criadas com sucesso!")
            return
        except OperationalError:
            if tentativa == tentativas:
                raise
            print(f"Banco ainda inicializando (tentativa {tentativa}/{tentativas}). Aguardando 3 segundos...")
            time.sleep(3)

if __name__ == "__main__":
    init_db()