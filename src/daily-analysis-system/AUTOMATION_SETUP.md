# 自動化執行設定指南

本專案提供兩種自動化執行方式，請根據你的環境選擇：

---

## 方案比較

| 方案 | 適用環境 | 優點 | 缺點 |
|------|---------|------|------|
| **macOS launchd** | macOS 本地 | 原生支援、重啟自動恢復、錯過任務會補執行 | 需要電腦開機 |
| **macOS cron** | macOS 本地（不推薦） | 簡單 | 已過時、不可靠 |

---

## 方案 1: macOS launchd（推薦）

### 為什麼選擇 launchd？

- Apple 官方推薦的排程系統
- 電腦休眠時錯過的任務會在喚醒後執行
- 系統重啟後自動恢復
- 完整的日誌管理

### 完整設定步驟

詳見 [LAUNCHD_SETUP.md](LAUNCHD_SETUP.md)

**快速開始**：

1. 創建 plist 檔案：
   ```bash
   nano ~/Library/LaunchAgents/com.market-intelligence.daily.plist
   ```

2. 使用 [LAUNCHD_SETUP.md](LAUNCHD_SETUP.md) 中的模板

3. 替換以下內容：
   - `YOUR_USERNAME` → 你的 macOS 使用者名稱
   - `YOUR_OAUTH_TOKEN_HERE` → 執行 `cat ~/.config/claude/credentials.json` 取得

4. 載入並啟用：
   ```bash
   launchctl load -w ~/Library/LaunchAgents/com.market-intelligence.daily.plist
   ```

5. 查看日誌：
   ```bash
   tail -f ~/logs/market-intelligence.log
   ```

---

## 方案 2: macOS cron（不推薦，僅供參考）

### 注意事項

- 在新版 macOS 中 cron 已被標記為 legacy
- 不會執行錯過的任務（Mac 休眠時）
- 重啟後可能不會自動恢復
- **強烈建議使用 launchd 代替**

### 設定方式（僅供舊系統參考）

```bash
# 編輯 crontab
crontab -e

# 加入以下內容
SHELL=/bin/bash
PATH=/usr/local/bin:/usr/bin:/bin:/Users/YOUR_USERNAME/.local/bin
CLAUDE_CODE_OAUTH_TOKEN=YOUR_TOKEN_HERE

# 週一到週五 早上 8:00
0 8 * * 1-5 cd /Users/YOUR_USERNAME/Development/MH/the-ultimate-analysis-machine && ./utils/run_daily_workflow.sh >> /tmp/mis.log 2>&1

# 週一到週五 晚上 21:00
0 21 * * 1-5 cd /Users/YOUR_USERNAME/Development/MH/the-ultimate-analysis-machine && ./utils/run_daily_workflow.sh >> /tmp/mis.log 2>&1
```

---

## 執行內容說明

### 完整工作流程（`make daily`）

1. **資料抓取** (`make fetch-all`)
   - 全球市場指數
   - 持倉股票價格
   - 市場新聞（23 個來源）

2. **AI 分析** (`make analyze-daily`)
   - 市場分析報告（Claude Sonnet 4.5）
   - 個股分析報告（針對有新聞的持股）
   - 持倉分析報告

### 完整部署流程（`make deploy`）

包含 `make daily` + 以下步驟：

3. **更新 GitHub Pages** (`make update-pages`)
   - 將報告轉換為 HTML
   - 更新 `docs/` 目錄

4. **Git Commit** (`make commit-auto`)
   - 自動 commit 報告和 pages

5. **Push to GitHub** (`make push`)
   - 推送到 GitHub
   - 觸發 GitHub Pages 部署

---

## 排程時間建議

| 時間 | 說明 | 目的 |
|------|------|------|
| 08:00 | 早上 8 點 | 亞洲市場收盤後，分析隔夜市場 |
| 21:00 | 晚上 9 點 | 美國市場收盤後，分析當日市場 |
| 週末 | **不執行** | 股市休市，無新數據 |

---

## 監控與維護

### 查看日誌

**launchd**:
```bash
tail -f ~/logs/market-intelligence.log
```

**cron**:
```bash
tail -f /tmp/mis.log
```

### 手動執行測試

```bash
cd /Users/YOUR_USERNAME/Development/MH/market-intelligence-system

# 完整工作流程
make daily

# 或分步執行
make fetch-all        # 只抓取資料
make analyze-daily    # 只做分析
make update-pages     # 只更新 Pages
make deploy          # 完整部署（包含 commit + push）
```

### 檢查執行狀態

**launchd**:
```bash
launchctl list | grep market-intelligence
```

**cron**:
```bash
crontab -l
```

---

## 故障排除

### 任務沒有執行

1. **檢查排程是否載入**

   launchd:
   ```bash
   launchctl list | grep market-intelligence
   ```

2. **查看日誌檔案**

   ```bash
   ls -l ~/logs/market-intelligence*.log
   # 或
   ls -l /tmp/mis.log
   ```

3. **檢查腳本權限**

   ```bash
   ls -l utils/run_daily_workflow.sh
   chmod +x utils/run_daily_workflow.sh
   ```

### Claude 認證失敗

1. **檢查 token 是否有效**

   ```bash
   cat ~/.config/claude/credentials.json
   ```

2. **測試 Claude CLI**

   ```bash
   echo "test" | claude
   ```

3. **重新生成 token**

   ```bash
   claude setup-token
   ```

## 常用命令速查

### launchd

```bash
# 載入
launchctl load -w ~/Library/LaunchAgents/com.market-intelligence.daily.plist

# 卸載
launchctl unload ~/Library/LaunchAgents/com.market-intelligence.daily.plist

# 重新載入（修改後）
launchctl unload ~/Library/LaunchAgents/com.market-intelligence.daily.plist && \
launchctl load -w ~/Library/LaunchAgents/com.market-intelligence.daily.plist

# 查看狀態
launchctl list | grep market-intelligence

# 查看日誌
tail -f ~/logs/market-intelligence.log
```

### cron

```bash
# 編輯
crontab -e

# 查看
crontab -l

# 查看日誌
tail -f /tmp/mis.log
```

---

## 下一步

1. **選擇方案**：根據你的環境選擇 launchd（推薦）或 cron（備用）
2. **完成設定**：按照對應文檔完成設定（LAUNCHD_SETUP.md 或本文 cron 章節）
3. **測試執行**：手動執行一次確認正常
4. **監控日誌**：觀察第一次自動執行的結果
5. **調整排程**：根據需求調整執行時間

---

**相關文檔**：
- [LAUNCHD_SETUP.md](LAUNCHD_SETUP.md) - macOS launchd 詳細設定
- [QUICKSTART.md](QUICKSTART.md) - 快速開始指南
- [README.md](README.md) - 專案說明

**最後更新**：2025-12-08
