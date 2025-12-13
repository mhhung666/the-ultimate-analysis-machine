# 自動化執行設定指南

本專案提供完整的每日自動化分析功能，可設定在每天 8:00（亞洲市場收盤後）和 21:00（美國市場收盤後）自動執行。

---

## 快速設定步驟

### 1. 設定環境變數

```bash
# 取得 Claude Token
cat ~/.config/claude/credentials.json

# 複製 token 到 .env 檔案
nano .env
```

在 `.env` 中填入你的 `CLAUDE_CODE_OAUTH_TOKEN`：

```bash
CLAUDE_CODE_OAUTH_TOKEN=your_actual_token_here
TZ=Asia/Taipei
```

### 2. 設定 Crontab

```bash
# 編輯 crontab
crontab -e
```

加入以下內容（請替換 `YOUR_USERNAME` 為你的使用者名稱）：

```cron
# The Ultimate Analysis System - Daily Automation
# 設定環境變數
SHELL=/bin/bash
PATH=/usr/local/bin:/usr/bin:/bin:/Users/YOUR_USERNAME/.local/bin
HOME=/Users/YOUR_USERNAME

# 完整每日工作流程 (平日執行)
# run_daily_workflow.sh 會自動從 .env 讀取 CLAUDE_CODE_OAUTH_TOKEN

# 早上 8:00 - 亞洲市場收盤後 (週一到週五)
0 8 * * 1-5 cd /Users/YOUR_USERNAME/Development/the-ultimate-analysis-machine && ./utils/run_daily_workflow.sh >> /tmp/ultimate-analysis.log 2>&1

# 晚上 21:00 - 美國市場收盤後 (週一到週五)
0 21 * * 1-5 cd /Users/YOUR_USERNAME/Development/the-ultimate-analysis-machine && ./utils/run_daily_workflow.sh >> /tmp/ultimate-analysis.log 2>&1
```

**重要提醒：**
- 將 `YOUR_USERNAME` 替換為你的實際使用者名稱（執行 `whoami` 查看）
- 確認專案路徑是否正確
- 確保 `run_daily_workflow.sh` 有執行權限

### 3. 賦予腳本執行權限

```bash
chmod +x ./utils/run_daily_workflow.sh
```

### 4. 測試手動執行

在設定 crontab 之前，先手動測試一次：

```bash
cd /Users/YOUR_USERNAME/Development/the-ultimate-analysis-machine
./utils/run_daily_workflow.sh
```

檢查是否正常運作。

---

## 工作流程說明

[run_daily_workflow.sh](utils/run_daily_workflow.sh) 會依序執行：

1. **資料抓取與分析** (`make daily`)
   - 抓取全球市場指數
   - 抓取持倉股票價格
   - 抓取市場新聞
   - 使用 Claude AI 進行每日分析

2. **更新 GitHub Pages** (`make update-pages`)
   - 將分析報告轉換為 HTML
   - 更新 `docs/` 目錄

3. **Git Commit** (`make commit-auto`)
   - 自動 commit 報告和 pages
   - 使用日期作為 commit message

4. **Push to GitHub** (`make push`)
   - 推送到 GitHub
   - 觸發 GitHub Pages 自動部署

---

## 排程時間說明

| 時間 | 說明 | 目的 |
|------|------|------|
| 08:00 | 早上 8 點（週一到週五） | 亞洲市場收盤後，分析隔夜市場 |
| 21:00 | 晚上 9 點（週一到週五） | 美國市場收盤後，分析當日市場 |

週末不執行（股市休市）。

---

## 監控與維護

### 查看執行日誌

```bash
# 即時查看日誌
tail -f /tmp/ultimate-analysis.log

# 查看完整日誌
cat /tmp/ultimate-analysis.log
```

### 檢查 Crontab 狀態

```bash
# 查看已設定的 crontab
crontab -l

# 編輯 crontab
crontab -e

# 移除所有 crontab（小心使用！）
crontab -r
```

### 手動執行各個步驟

```bash
# 切換到專案目錄
cd /Users/YOUR_USERNAME/Development/the-ultimate-analysis-machine

# 只執行資料抓取
make fetch-all

# 只執行分析
make analyze-daily

# 完整每日流程（抓取 + 分析）
make daily

# 更新 GitHub Pages
make update-pages

# 完整部署（pages + commit + push）
make deploy
```

---

## 故障排除

### 1. Crontab 沒有執行

**檢查權限：**
```bash
ls -l ./utils/run_daily_workflow.sh
chmod +x ./utils/run_daily_workflow.sh
```

**檢查日誌：**
```bash
tail -f /tmp/ultimate-analysis.log
```

**測試手動執行：**
```bash
cd /Users/YOUR_USERNAME/Development/the-ultimate-analysis-machine
./utils/run_daily_workflow.sh
```

### 2. Claude 認證失敗

**檢查 token：**
```bash
cat ~/.config/claude/credentials.json
```

**測試 Claude CLI：**
```bash
echo "test" | claude
```

**更新 .env 檔案：**
```bash
nano .env
# 確認 CLAUDE_CODE_OAUTH_TOKEN 已正確填入
```

### 3. 找不到 Python 或相依套件

**檢查虛擬環境：**
```bash
ls -la .venv
```

**重新安裝相依套件：**
```bash
make clean-venv
make install
```

### 4. Git Push 失敗

**檢查 Git 狀態：**
```bash
git status
git remote -v
```

**確認 Git 認證：**
```bash
git config --list | grep user
```

---

## 替代方案：macOS launchd

如果你使用 macOS，也可以使用更可靠的 `launchd` 替代 cron。launchd 的優點：

- 電腦休眠時錯過的任務會在喚醒後執行
- 系統重啟後自動恢復
- 更完整的日誌管理

詳細設定可參考舊專案的 [LAUNCHD_SETUP.md](https://github.com/YOUR_REPO/market-intelligence-system/blob/main/LAUNCHD_SETUP.md)。

---

## 常用指令速查

```bash
# 查看 crontab
crontab -l

# 編輯 crontab
crontab -e

# 查看執行日誌
tail -f /tmp/ultimate-analysis.log

# 手動執行完整流程
cd /Users/YOUR_USERNAME/Development/the-ultimate-analysis-machine
./utils/run_daily_workflow.sh

# 測試各個功能
make fetch-all         # 抓取所有資料
make analyze-daily     # 執行 AI 分析
make daily             # 完整每日流程
make update-pages      # 更新 GitHub Pages
make deploy            # 部署到 GitHub
```

---

## Makefile 指令說明

```bash
make help              # 顯示所有可用指令
make install           # 安裝 Python 相依套件
make test              # 執行測試
make clean             # 清理 cache 檔案

# 資料抓取
make fetch-global      # 抓取全球市場指數
make fetch-holdings    # 抓取持倉股票價格
make fetch-news        # 抓取市場新聞
make fetch-all         # 抓取所有資料

# 分析與報告
make analyze-daily     # 執行每日 AI 分析
make daily             # 完整流程（抓取 + 分析）
make clean-old-reports # 歸檔舊報告

# GitHub Pages
make update-pages      # 生成 HTML 頁面
make preview-pages     # 本地預覽（localhost:8000）

# Git 操作
make commit            # 手動 commit
make commit-auto       # 自動 commit
make push              # 推送到 GitHub
make deploy            # 完整部署（pages + commit + push）
```

---

**最後更新：** 2025-12-13
