import pytest
import uuid
from app.agents.security_filter import security_filter_agent
from app.agents.registration import registration_agent
from app.agents.receptionist import receptionist_agent


def test_security_filter_emergency():
    is_safe, is_emergency, reason = security_filter_agent.check_message_security("estou com falta de ar severa")
    assert is_emergency is True
    assert is_safe is False


def test_security_filter_safe():
    is_safe, is_emergency, reason = security_filter_agent.check_message_security("gostaria de agendar uma consulta")
    assert is_emergency is False
    assert is_safe is True


def test_extract_patient_name():
    extracted = registration_agent.extract_name_from_text("ola meu nome é Gustavo, gostaria de agendar consulta")
    assert extracted == "Gustavo"


def test_receptionist_welcoming_formatting():
    formatted = receptionist_agent.format_welcoming_response("Temos horários amanhã.", "Gustavo")
    assert "Gustavo" in formatted
