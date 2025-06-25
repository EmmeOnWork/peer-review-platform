# Usa un'immagine Python slim come base
FROM python:3.11-slim

# Imposta variabili d'ambiente utili per Python in Docker
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Imposta la directory di lavoro nel container
WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN groupadd -r appuser && useradd --no-log-init -r -g appuser appuser

RUN chown -R appuser:appuser /app

USER appuser


EXPOSE 5001

CMD ["gunicorn", "app:app", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:5001", "--workers", "1"]