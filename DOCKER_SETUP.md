# Docker Compose 定期執行設定

使用 Docker Compose 設定每日自動執行分析工作流程。

## 📋 功能特色

- ✅ 每天晚上 9:00 自動執行完整工作流程
- ✅ 自動化資料抓取、分析、commit、push
- ✅ 支援 Claude Code OAuth Token
- ✅ 支援 Gitea 私有倉庫認證
- ✅ 可自訂 cron 執行時間
- ✅ 完整的日誌記錄
- ✅ 容器自動重啟

## 🚀 快速開始

### 1️⃣ 設定環境變數

複製環境變數範例檔案:

```bash
cp .env.docker .env
```

編輯 `.env` 檔案,填入必要資訊:

```bash
# Claude Code Token (必填)
CLAUDE_CODE_OAUTH_TOKEN=your_token_here

# Git 設定
GIT_USER_NAME=Daily Analysis Bot
GIT_USER_EMAIL=bot@example.com

# Gitea 認證 (如果使用 Gitea,選填)
GITEA_USERNAME=your_username
GITEA_PASSWORD=your_password
GITEA_REPO_URL=https://gitea.example.com/user/repo.git

# Cron 排程 (預設每天晚上 9:00)
CRON_SCHEDULE=0 21 * * *
```

#### 如何取得 Claude Token?

```bash
# 1. 登入 Claude CLI
claude auth login

# 2. 查看 credentials
cat ~/.config/claude/credentials.json

# 3. 複製 "accessToken" 的值到 .env 檔案
```

### 2️⃣ 建立並啟動容器

```bash
# 建立並啟動容器 (背景執行)
docker compose up -d --build

# 查看容器狀態
docker compose ps

# 查看啟動日誌
docker compose logs -f analysis-scheduler
```

### 3️⃣ 驗證運作

```bash
# 查看 cron 設定
docker compose exec analysis-scheduler cat /etc/cron.d/daily-analysis

# 查看環境變數
docker compose exec analysis-scheduler env | grep CLAUDE

# 手動測試執行一次
docker compose exec analysis-scheduler /app/utils/run_daily_workflow.sh
```

## 📊 監控與管理

### 查看日誌

```bash
# 即時查看容器日誌
docker compose logs -f analysis-scheduler

# 查看 cron 執行日誌
docker compose exec analysis-scheduler tail -f /app/logs/cron-*.log

# 查看最新的執行日誌
docker compose exec analysis-scheduler ls -lt /app/logs/
```

### 管理容器

```bash
# 停止容器
docker compose down

# 重啟容器
docker compose restart

# 重新建置並啟動
docker compose up -d --build

# 進入容器 shell
docker compose exec analysis-scheduler bash
```

### 手動觸發執行

```bash
# 在容器內手動執行工作流程
docker compose exec analysis-scheduler /app/utils/run_daily_workflow.sh

# 或進入容器後執行
docker compose exec analysis-scheduler bash
cd /app
./utils/run_daily_workflow.sh
```

## ⚙️ 自訂設定

### 修改執行時間

編輯 `.env` 檔案中的 `CRON_SCHEDULE`:

```bash
# 每天早上 9:00
CRON_SCHEDULE=0 9 * * *

# 每 6 小時一次
CRON_SCHEDULE=0 */6 * * *

# 每週一晚上 9:00
CRON_SCHEDULE=0 21 * * 1

# 每天上午 10:30 和晚上 10:30
# 需要在 cron-entrypoint.sh 中加入多行
```

修改後重啟容器:

```bash
docker compose down
docker compose up -d
```

### 啟動時立即執行一次

在 `.env` 檔案中設定:

```bash
RUN_ON_STARTUP=true
```

### 使用 Gitea 私有倉庫

如果你的倉庫是在 Gitea 上,設定以下環境變數:

```bash
GITEA_USERNAME=your_username
GITEA_PASSWORD=your_password
GITEA_REPO_URL=https://gitea.example.com/username/repo.git
```

容器會自動設定 Git credential helper 來處理認證。

## 🔧 故障排除

### 問題 1: Claude Token 無效

```bash
# 檢查 token 是否正確設定
docker compose exec analysis-scheduler env | grep CLAUDE

# 重新取得 token
claude auth login
cat ~/.config/claude/credentials.json

# 更新 .env 並重啟
docker compose down
docker compose up -d
```

### 問題 2: Git Push 失敗

```bash
# 檢查 Git 認證
docker compose exec analysis-scheduler git config --list

# 測試 Git 連線
docker compose exec analysis-scheduler git remote -v
docker compose exec analysis-scheduler git pull

# 如果使用 Gitea,確認帳號密碼正確
```

### 問題 3: Cron 沒有執行

```bash
# 檢查 cron 服務狀態
docker compose exec analysis-scheduler ps aux | grep cron

# 檢查 cron 設定
docker compose exec analysis-scheduler cat /etc/cron.d/daily-analysis

# 查看系統時間
docker compose exec analysis-scheduler date

# 查看 cron 日誌
docker compose logs analysis-scheduler
```

### 問題 4: Python 依賴問題

```bash
# 重新建置 image
docker compose build --no-cache

# 檢查 Python 環境
docker compose exec analysis-scheduler .venv/bin/pip list
```

## 📁 檔案結構

```
.
├── Dockerfile                  # Docker image 定義
├── docker-compose.yml          # Docker Compose 設定
├── .env                        # 環境變數 (需自行建立)
├── .env.docker                 # 環境變數範例
├── logs/                       # Cron 執行日誌
│   └── cron-YYYY-MM-DD.log
└── utils/
    ├── cron-entrypoint.sh     # Cron 啟動腳本
    └── run_daily_workflow.sh  # 主要工作流程腳本
```

## 🔒 安全建議

1. **保護 .env 檔案**: 確保 `.env` 已加入 `.gitignore`
2. **Token 安全**: 定期更新 Claude OAuth Token
3. **Git 認證**: 使用專用的 bot 帳號而非個人帳號
4. **Log 清理**: 定期清理舊的日誌檔案

## 📚 相關文件

- [Makefile 使用說明](README.md)
- [自動化設定說明](AUTOMATION_SETUP.md)
- [重試機制說明](RETRY_MECHANISM.md)

## 💡 進階用法

### 多個排程時間

如果需要一天執行多次,修改 `utils/cron-entrypoint.sh`:

```bash
cat > /etc/cron.d/daily-analysis <<EOF
# Morning run at 9:00
0 9 * * * root /app/utils/run_daily_workflow.sh >> /app/logs/cron-morning-\$(date +\%Y-\%m-\%d).log 2>&1

# Evening run at 21:00
0 21 * * * root /app/utils/run_daily_workflow.sh >> /app/logs/cron-evening-\$(date +\%Y-\%m-\%d).log 2>&1

EOF
```

### 與現有系統整合

如果你已有其他 Docker Compose 服務,可以整合到同一個 `docker-compose.yml`:

```yaml
version: '3.8'

services:
  # 你現有的服務
  web:
    # ...

  # 加入分析排程器
  analysis-scheduler:
    build:
      context: .
      dockerfile: Dockerfile
    # ... (其他設定)
```

## ❓ 常見問題

**Q: 可以在本機開發時使用嗎?**
A: 可以,但建議在 `.env` 中設定 `CRON_SCHEDULE` 為更頻繁的時間做測試,例如每 5 分鐘一次: `*/5 * * * *`

**Q: 容器重啟後會遺失資料嗎?**
A: 不會,所有重要資料都透過 volumes 掛載到本機,包括 data、reports、docs 和 .git 目錄。

**Q: 如何暫停自動執行?**
A: 執行 `docker compose down` 停止容器即可。

**Q: 可以同時使用 GitHub 和 Gitea 嗎?**
A: 需要修改 `run_daily_workflow.sh` 來支援推送到多個遠端倉庫。
