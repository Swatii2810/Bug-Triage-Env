FROM python:3.11-slim

WORKDIR /app

ENV PIP_DEFAULT_TIMEOUT=300
ENV PIP_RETRIES=5

COPY requirements.txt .
RUN pip install --no-cache-dir --timeout 300 \
    fastapi==0.104.1 \
    uvicorn==0.24.0 \
    pydantic==2.5.0 \
    "openai>=2.7.2" \
    pyyaml==6.0.1 \
    python-dotenv==1.0.0 \
    requests==2.31.0 \
    "openenv-core>=0.2.0"

COPY . .

EXPOSE 7860

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "1"]
