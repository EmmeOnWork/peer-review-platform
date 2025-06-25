FROM python:3.11-slim

WORKDIR /app

# Copia tutto nella working directory del container
COPY . .

# Installa le dipendenze
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5003

CMD ["python", "app.py"]
