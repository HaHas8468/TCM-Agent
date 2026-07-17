FROM python:3.11-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1

COPY requirements.txt /tmp/root-requirements.txt
COPY traditional_medical_agent/requirements.txt /tmp/agent-requirements.txt
RUN pip install --no-cache-dir -r /tmp/root-requirements.txt -r /tmp/agent-requirements.txt

COPY . ./

CMD ["uvicorn", "agent_service.main:app", "--host", "0.0.0.0", "--port", "8001"]
