# Image RUNTIME server MCP (bukan image test — itu milik Dockerfile.test).
# Ramping, deterministik, dan berjalan sebagai user non-root.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install paket dari source. README.md ikut di-COPY karena direferensikan
# sebagai `readme` di pyproject.toml (tanpa itu `pip install .` gagal).
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install . \
    && useradd --create-home --uid 1000 appuser

USER appuser

# Jalan sebagai service HTTP (Streamable HTTP) via uvicorn — kompatibel Claude Web.
# Auth Authentik diatur lewat environment (lihat .env.example).
ENV MCP_LOG_LEVEL=INFO
EXPOSE 8000

CMD ["uvicorn", "content_validity_index_mcp.asgi:app", "--host", "0.0.0.0", "--port", "8000"]
