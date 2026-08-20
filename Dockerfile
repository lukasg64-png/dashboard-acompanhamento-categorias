FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=3000

WORKDIR /app

# Copiar arquivos do projeto
COPY . .

# Expor porta da aplicação (3000 para Coolify)
EXPOSE 3000

# Healthcheck na porta 3000
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:3000/')" || exit 1

# Servir o projeto na porta 3000
CMD ["python", "-m", "http.server", "3000"]
