FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir -U pip "typing_extensions>=4.12.2"

COPY services/knowledge-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY packages/shared_py/shared_py /app/shared_py
COPY services/knowledge-service/app ./app

RUN mkdir -p /data/faiss /data/chroma
ENV PYTHONPATH=/app
EXPOSE 8003
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8003"]
