import os

TEST_ENV_DEFAULTS = {
    "OPENAI_API_KEY": "",
    "EVOLUTION_SEND_ENABLED": "false",
    "DATABASE_URL": "",
    "REDIS_ENABLED": "false",
    "REDIS_URL": "",
    "GOOGLE_CALENDAR_ENABLED": "false",
    "WEBHOOK_SECRET": "",
    "WEBHOOK_GLOBAL_ENABLED": "false",
}

for key, value in TEST_ENV_DEFAULTS.items():
    os.environ[key] = value