# Dockerfile para desplegar HuertoRentable (Flask) en Cloud Run

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Dependencias del sistema (WeasyPrint y reportlab pueden requerir libs)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libffi-dev \
    libjpeg62-turbo \
    libpng16-16 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install -r requirements.txt

# Copiar el código
COPY . .

# Variables de entorno para Flask
ENV FLASK_ENV=production

# Cloud Run inyecta PORT. Flask lo lee en run.py
CMD ["python", "run.py"]
