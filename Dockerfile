FROM python:3.11-slim

WORKDIR /app

# Installazione dipendenze di sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copia e installa dipendenze Python
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# Copia codice applicazione
COPY app/ ./app/

# Crea directory per database
RUN mkdir -p /app/data

# Espone la porta
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Avvia il server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
