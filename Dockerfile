
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Dependências do sistema necessárias para algumas wheels (ex: psycopg/build deps)
RUN apt-get update \
	&& apt-get install -y --no-install-recommends build-essential libpq-dev gcc \
	&& rm -rf /var/lib/apt/lists/*

# Instalar dependências Python
COPY requirements.txt ./
RUN pip install --upgrade pip \
	&& pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY . .

# Criar usuário não-root (melhoria de segurança)
RUN adduser --disabled-password --gecos "" app || true \
	&& chown -R app:app /app
USER app

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]