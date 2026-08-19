FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

WORKDIR /app

# Copiar arquivos do projeto
COPY . .

# Expor porta da aplicação
EXPOSE 8080

# Healthcheck simples e robusto
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/')" || exit 1

# Servir a pasta dist (ou raiz) diretamente via módulo HTTP nativo do Python
CMD ["python", "-m", "http.server", "8080", "--directory", "dist"]
