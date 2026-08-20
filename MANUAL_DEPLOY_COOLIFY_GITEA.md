# 🚀 Guia Definitivo: Deploy de Aplicações Streamlit no Coolify com Gitea Privado

Este manual documenta o passo a passo completo e todas as pegadinhas/soluções encontradas durante a integração do **Coolify** com **Gitea Privado** em ambiente de rede corporativa local.

---

## 📋 Sumário
1. [Preparação do Repositório (Código & Docker)](#1-preparação-do-repositório-código--docker)
2. [Configuração no Coolify & Integração Gitea](#2-configuração-no-coolify--integração-gitea)
3. [Configuração de Domínio & Rede (sslip.io)](#3-configuração-de-domínio--rede-sslipio)
4. [Checklist de Solução de Problemas (Troubleshooting)](#4-checklist-de-solução-de-problemas-troubleshooting)

---

## 1. Preparação do Repositório (Código & Docker)

### 📄 1.1 Dockerfile Padrão (Sem Bloqueios de Firewall)
> ⚠️ **ATENÇÃO COM APT-GET:** Em redes corporativas com proxy/firewall severo, chamadas como `apt-get install` para o `deb.debian.org` costumam retornar erro **403 Forbidden**. Evite `apt-get` e utilize os módulos nativos do Python!

Crie o arquivo `Dockerfile` na raiz do seu projeto:

```dockerfile
FROM python:3.11-slim

# Evita arquivos .pyc e força saída de log em tempo real
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8501

WORKDIR /app

# Copiar e instalar dependências do Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código-fonte da aplicação
COPY . .

# Expor a porta padrão do Streamlit
EXPOSE 8501

# Checagem de saúde usando Python nativo (Sem curl / Sem apt-get)
# start-period estendido para dar tempo de ler planilhas Excel/pandas grandes
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')" || exit 1

# Comando de inicialização direta do Streamlit
CMD ["streamlit", "run", "dashboard_streamlit.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true", "--server.enableCORS=false", "--server.enableXsrfProtection=false"]
```

### 📄 1.2 Arquivo `.dockerignore`
Crie o `.dockerignore` para impedir o envio de arquivos temporários e pesados durante o build:

```gitignore
.git
.gitignore
__pycache__
*.pyc
*.pyo
*.pyd
env/
venv/
.env
```

### 📄 1.3 Arquivo `.streamlit/config.toml`
Garante a execução contínua e sem bloqueios de CORS/XSRF:

```toml
[server]
headless = true
address = "0.0.0.0"
port = 8501
enableCORS = false
enableXsrfProtection = false

[browser]
gatherUsageStats = false
```

---

## 2. Configuração no Coolify & Integração Gitea

### 🔑 2.1 Porta SSH do Gitea (Pegadinha Frequente)
Na maioria das infraestruturas com Docker/Gitea, a porta SSH padrão `22` pertence ao sistema operacional (Ubuntu/Host), enquanto o SSH do Gitea roda na porta **`2222`**.

- **URL do Repositório no Coolify**:
  Ao criar a aplicação no Coolify, informe a URL com a porta **2222** ou defina o campo **Custom Git Port** como `2222`.
  
  ```text
  ssh://git@10.200.12.69:2222/seu-grupo/seu-repositorio.git
  ```

### 🔐 2.2 Chave Privada (Deploy Key)
1. No Coolify, em **Keys & Tokens**, cadastre uma chave SSH pública no seu Gitea (em *Deploy Keys* do repositório ou *SSH Keys* do usuário).
2. Na aplicação dentro do Coolify:
   - Vá em **Configuration** (Configuração).
   - No campo **Private Key**, selecione a sua chave fixa (ex: `Gitea Deploy Key`).
   - ⚠️ **Não deixe a chave como padrão/gerada automaticamente por deploy**, pois o Gitea irá recusar o acesso com `Permission denied (publickey)`.

---

## 3. Configuração de Domínio & Rede (sslip.io)

### 🌐 3.1 IP Interno vs IP Externo no DNS `sslip.io`
O `sslip.io` é um serviço de DNS coringa. Quando o Coolify gera um domínio automático baseado no IP público da rede (ex: `177.69.110.41`), o navegador vai tentar acessar o Firewall/Roteador da empresa (onde podem existir outros sistemas, como QlikView, IIS, etc.).

### 🛠️ Solução:
Nas configurações da aplicação no Coolify, altere o campo **Domains** para apontar para o **IP Interno da Rede (`10.200.12.69`)**:

```text
http://<subdominio-gerado>.10.200.12.69.sslip.io
```

*Exemplo:* `http://xmqgziyzbnqtpfum4poxhc57.10.200.12.69.sslip.io/`

---

## 4. Checklist de Solução de Problemas (Troubleshooting)

| Sintoma / Erro | Causa Raiz | Solução |
| :--- | :--- | :--- |
| `Permission denied (publickey,password)` no deploy | O Coolify tentou conectar na porta 22 (Host) ou usou chave randômica. | 1. Defina a porta SSH como `2222`.<br>2. Aloque a `Gitea Deploy Key` nas configurações da app no Coolify. |
| `403 Forbidden` ao rodar `apt-get install` no build | O firewall corporativo bloqueou o repositório `deb.debian.org`. | Remova o `apt-get` do `Dockerfile`. Use `python:3.11-slim` e healthcheck via `python -c "import urllib..."`. |
| O link da aplicação abre o QlikView / outro sistema | O domínio `sslip.io` apontou para o IP externo da empresa. | Altere o FQDN no Coolify para usar o IP interno: `http://<subdominio>.10.200.12.69.sslip.io`. |
| Container entra em loop de restart no inicio | O pandas/Streamlit demorou mais que o timeout do Healthcheck para carregar. | Aumente o `--start-period=60s` na instrução `HEALTHCHECK` do Dockerfile. |

---
*Manual gerado e validado em produção no Coolify.*
