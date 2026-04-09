FROM python:3.11-slim

WORKDIR /app

ENV PIP_DEFAULT_TIMEOUT=300
ENV PIP_RETRIES=5

COPY bug_triage_env/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bug_triage_env/ .

EXPOSE 7860

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "1"]
