FROM python:3.11-slim

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    git \
    curl \
    wget \
    cron \
    make \
    jq \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 安裝 Claude CLI
# 下載並安裝 Claude CLI binary
RUN mkdir -p ~/.local/bin && \
    wget -q https://cdn.anthropic.com/claude-cli/claude-linux-x64 -O ~/.local/bin/claude && \
    chmod +x ~/.local/bin/claude && \
    ln -s ~/.local/bin/claude /usr/local/bin/claude || true

# 設定工作目錄
WORKDIR /app

# 複製專案檔案
COPY . /app/

# 安裝 Python 依賴
RUN python3 -m venv .venv && \
    .venv/bin/pip install --upgrade pip && \
    .venv/bin/pip install -r src/daily-analysis-system/requirements.txt

# 設定權限
RUN chmod +x utils/run_daily_workflow.sh && \
    chmod +x utils/cron-entrypoint.sh

# 建立 log 目錄
RUN mkdir -p /app/logs

# 使用 entrypoint 啟動 cron
ENTRYPOINT ["/app/utils/cron-entrypoint.sh"]
