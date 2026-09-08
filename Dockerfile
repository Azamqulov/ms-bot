# ==========================================
# Multi-stage / Optimized Python Dockerfile
# Milliy Sertifikat Matematika Bot & Web App
# ==========================================

FROM python:3.13-slim

# Muhit o'zgaruvchilari
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Tizim paketlarini yangilash va curl (healthcheck uchun) o'rnatish
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Xavfsiz non-root foydalanuvchi yaratish
RUN useradd -m -u 1000 -s /bin/bash appuser

WORKDIR /app

# Dependency keshini optimallashtirish
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Loyiha kodlarini ko'chirish
COPY . /app/

# Fayllar va jildlar uchun ruxsatlar
RUN mkdir -p /app/uploads /app/data /app/web && \
    chown -R appuser:appuser /app

# Non-root foydalanuvchiga o'tish
USER appuser

# API porti
EXPOSE 8000

# Salomatlik tekshiruvi (Healthcheck)
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/healthz || exit 1

# Standart ishga tushirish buyrug'i
CMD ["python", "-m", "bot.main"]
