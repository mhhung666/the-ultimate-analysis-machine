# Cron 自動化腳本

這個目錄包含所有 cron 自動化相關的腳本。

## 📁 檔案說明

### 設定腳本

| 檔案 | 用途 | 使用引擎 | 成本 |
|------|------|----------|------|
| **setup_cron.sh** | 設定 Claude CLI 版本的 cron | Claude API | 付費 |

### 執行腳本

| 檔案 | 用途 | 由誰調用 |
|------|------|----------|
| **run_daily_cron.sh** | Claude 版本的每日任務 | cron |

### 測試腳本

| 檔案 | 用途 |
|------|------|
| **test_cron.sh** | 測試 cron 環境設定 |

## 🚀 快速開始（Claude CLI）

```bash
# 1. 確保已登入 Claude CLI
claude login

# 2. 執行 Claude 版本的設定腳本
./scripts/cron/setup_cron.sh

# 3. 按提示輸入 'y' 確認
```

## 📋 Cron 執行時間

預設會在以下時間自動執行：

- **早上 08:00** - 美國股市收盤後的新聞分析
- **晚上 20:00** - 亞洲股市收盤後的新聞分析

## 🔍 查看和管理

### 查看已安裝的 cron 任務

```bash
crontab -l
```

### 查看執行日誌

```bash
tail -f /tmp/market-intelligence-system.log
```

### 手動測試執行

```bash
./scripts/cron/run_daily_cron.sh
```

### 測試環境設定

```bash
./scripts/cron/test_cron.sh
```

### 移除 cron 任務

```bash
# 編輯 crontab
crontab -e

# 刪除 The Ultimate Analysis System 相關的行
# 或還原備份
crontab /path/to/backup/file
```

## 📊 輸出結果

自動化會生成固定格式的報告：

```
reports/markdown/
├── market-analysis-2025-12-02.md      # 市場分析
└── holdings-analysis-2025-12-02.md    # 持倉分析
```

報告會自動 commit 並 push 到 Git repository。

## ⚙️ 自訂設定

### 修改執行時間

編輯 cron 時間（在 setup 腳本中）：

```bash
# 格式: 分 時 日 月 星期
0 8 * * *   # 每天 08:00
0 20 * * *  # 每天 20:00
```

## 🐛 故障排除

### Cron 沒有執行

1. 檢查 cron 服務：`ps aux | grep cron`
2. 檢查日誌：`tail -f /tmp/market-intelligence-system*.log`
3. 手動測試：`./scripts/cron/run_daily_cron.sh`

### Git 推送失敗

確認 Git 認證設定：

```bash
# 檢查 credential helper
git config --get credential.helper

# 測試推送
git push origin main
```

## 📚 更多資訊

- [CRON_SETUP.md](../../../CRON_SETUP.md) - Claude 版本詳細指南

---
