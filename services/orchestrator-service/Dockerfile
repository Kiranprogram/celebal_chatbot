FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir -U pip "typing_extensions>=4.12.2"

COPY services/orchestrator-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY packages/shared_py/shared_py /app/shared_py
COPY services/orchestrator-service/app ./app

ENV PYTHONPATH=/app
EXPOSE 8002
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]
