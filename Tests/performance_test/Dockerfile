# In performance_test/Dockerfile

FROM python:3.9-slim

WORKDIR /app

# Copia prima requirements.txt per sfruttare il caching di Docker
COPY requirements.txt .
# Installa le dipendenze da requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copia il tuo script Locust (rinominato locustfile.py nel tuo filesystem)
COPY locustfile.py . 


# Definisce il comando predefinito quando il container viene eseguito
ENTRYPOINT ["locust"]

EXPOSE 8089