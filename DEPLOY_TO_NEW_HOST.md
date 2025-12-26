# 🚀 部署到新主機快速指南

## 📋 前置檢查

在新主機上確認以下環境:

```bash
# 1. 檢查 Docker 是否安裝
docker --version
docker compose version

# 2. 檢查 Git 是否安裝
git --version
```

## 📦 方法 1: 使用 Git Clone (推薦)

```bash
# 1. Clone 專案
git clone https://git.mhhung.com/mhhung/the-ultimate-analysis-machine.git
cd the-ultimate-analysis-machine

# 2. 複製環境變數檔案
cp .env.docker .env

# 3. 編輯 .env 填入 Claude Token (如果還沒填)
nano .env
# 或者如果已經在本機設定好,直接使用即可

# 4. 建置並啟動
docker compose up -d --build

# 5. 查看日誌
docker compose logs -f analysis-scheduler
```

## 📦 方法 2: 直接複製檔案

如果你已經在本機準備好所有檔案:

```bash
# 在本機執行 (假設新主機 IP 是 192.168.1.100)
scp -r /home/kasm-user/Desktop/the-ultimate-analysis-machine user@192.168.1.100:~/

# 或使用 rsync (更快,支援斷點續傳)
rsync -avz --progress /home/kasm-user/Desktop/the-ultimate-analysis-machine/ user@192.168.1.100:~/the-ultimate-analysis-machine/
```

然後在新主機上:

```bash
cd ~/the-ultimate-analysis-machine

# 確認 .env 檔案存在且有內容
cat .env | grep CLAUDE_CODE_OAUTH_TOKEN

# 建置並啟動
docker compose up -d --build

# 查看日誌
docker compose logs -f analysis-scheduler
```

## ✅ 驗證部署

### 1. 檢查容器狀態

```bash
# 查看容器是否正在運行
docker compose ps

# 應該看到:
# NAME                          STATUS
# daily-analysis-scheduler      Up X minutes
```

### 2. 檢查環境變數

```bash
# 進入容器檢查環境變數
docker compose exec analysis-scheduler env | grep -E "CLAUDE|GIT|GITEA"

# 應該看到:
# CLAUDE_CODE_OAUTH_TOKEN=sk-ant-oat01-...
# GIT_USER_NAME=MH Hung
# GIT_USER_EMAIL=mh.hung1994@gmail.com
# GITEA_USERNAME=mhhung
# ...
```

### 3. 檢查 Cron 設定

```bash
# 查看 cron 排程
docker compose exec analysis-scheduler cat /etc/cron.d/daily-analysis

# 應該看到:
# 0 21 * * * root /app/utils/run_daily_workflow.sh >> ...
```

### 4. 手動測試執行一次

```bash
# 手動執行工作流程 (測試用)
docker compose exec analysis-scheduler /app/utils/run_daily_workflow.sh

# 觀察執行過程,確保沒有錯誤
```

### 5. 查看執行日誌

```bash
# 即時查看容器日誌
docker compose logs -f analysis-scheduler

# 查看 cron 執行日誌
docker compose exec analysis-scheduler tail -f /app/logs/cron-*.log

# 列出所有日誌檔案
docker compose exec analysis-scheduler ls -la /app/logs/
```

## 🔧 常見問題排除

### 問題 1: Claude Token 無效

```bash
# 重新取得 token (在有 Claude CLI 的機器上)
claude auth login
cat ~/.config/claude/credentials.json

# 更新 .env 檔案
nano .env
# 修改 CLAUDE_CODE_OAUTH_TOKEN=新的token

# 重啟容器
docker compose down
docker compose up -d
```

### 問題 2: Git Push 失敗

```bash
# 檢查 Git 設定
docker compose exec analysis-scheduler git config --list

# 測試 Git 連線
docker compose exec analysis-scheduler git remote -v
docker compose exec analysis-scheduler git fetch

# 如果是認證問題,檢查 Gitea 密碼
nano .env
# 確認 GITEA_PASSWORD 正確
```

### 問題 3: Python 依賴問題

```bash
# 重新建置 image (不使用快取)
docker compose build --no-cache

# 或進入容器手動安裝
docker compose exec analysis-scheduler bash
cd /app
.venv/bin/pip install -r src/daily-analysis-system/requirements.txt
```

### 問題 4: Cron 沒有執行

```bash
# 檢查 cron 服務
docker compose exec analysis-scheduler ps aux | grep cron

# 手動觸發測試
docker compose exec analysis-scheduler /app/utils/run_daily_workflow.sh

# 檢查系統時間
docker compose exec analysis-scheduler date
```

## 📝 管理指令

```bash
# 停止容器
docker compose down

# 啟動容器
docker compose up -d

# 重啟容器
docker compose restart

# 查看容器狀態
docker compose ps

# 查看即時日誌
docker compose logs -f

# 進入容器 shell
docker compose exec analysis-scheduler bash

# 刪除容器和 image (重新開始)
docker compose down
docker rmi the-ultimate-analysis-machine-analysis-scheduler
docker compose up -d --build
```

## 📅 Cron 排程說明

目前設定為每天晚上 9:00 (21:00) 執行。

如果要修改時間,編輯 `.env` 檔案:

```bash
# .env
CRON_SCHEDULE=0 21 * * *   # 每天晚上 9:00

# 其他範例:
# CRON_SCHEDULE=0 9 * * *    # 每天早上 9:00
# CRON_SCHEDULE=0 */6 * * *  # 每 6 小時一次
# CRON_SCHEDULE=30 22 * * *  # 每天晚上 10:30
```

修改後重啟容器:

```bash
docker compose down
docker compose up -d
```

## 🔒 安全提醒

1. **保護 .env 檔案**: 包含敏感資訊,不要 commit 到 git
2. **定期更新 Token**: Claude token 會過期,需要定期更新
3. **檢查日誌**: 定期查看執行日誌,確保正常運作
4. **備份資料**: 定期備份 `data/` 和 `reports/` 目錄

## 📊 執行結果

每天晚上 9:00,容器會自動執行以下流程:

1. ✅ 抓取全球市場數據
2. ✅ 抓取持股價格
3. ✅ 抓取市場新聞
4. ✅ Claude AI 分析生成報告
5. ✅ 更新 GitHub Pages
6. ✅ Git commit
7. ✅ Push 到 Gitea

執行結果會記錄在:
- **Cron 日誌**: `/app/logs/cron-YYYY-MM-DD.log`
- **分析報告**: `src/daily-analysis-system/reports/markdown/`
- **GitHub Pages**: `docs/`

## 💡 提示

- 第一次執行建議先手動測試,確保所有設定正確
- 查看日誌可以幫助診斷問題
- Claude token 過期是最常見的問題,記得定期更新

## 📚 更多資訊

詳細說明請參考:
- [DOCKER_SETUP.md](DOCKER_SETUP.md) - 完整的 Docker 設定說明
- [README.md](README.md) - 專案總覽
- [AUTOMATION_SETUP.md](AUTOMATION_SETUP.md) - 自動化設定說明
