# 環境變數設定指南

## 概述

`utils/run_daily_workflow.sh` 現在會優先從 **repo 根目錄** (`the-ultimate-analysis-machine/.env`) 載入環境變數，若找不到才退回子專案內的 `.env`。這讓所有 Make 指令、cron 以及 `utils/` 包裝腳本都能共用同一份設定。

---

## 方案 A: 使用 .env 檔案（推薦）✅

### 優點

- ✅ **更安全**：Token 不會出現在 plist 中
- ✅ **不會意外提交**：`.env` 已在 `.gitignore` 中
- ✅ **統一環境**：手動執行和 launchd 執行使用相同的設定
- ✅ **易於更新**：修改 `.env` 即可，不需重新載入 plist

### 設定步驟

1. **創建 .env 檔案 (在 repo 根目錄)**

   ```bash
   cd ~/Development/MH/the-ultimate-analysis-machine
   cp .env.example.local .env
   nano .env
   ```

2. **填入 token**

   ```bash
   # .env 內容
   CLAUDE_TOKEN=sk-ant-oat01-xxxxx...
   TZ=Asia/Taipei
   ```

3. **取得 token**

   ```bash
   cat ~/.config/claude/credentials.json
   # 找到 "accessToken" 欄位的值，複製整個字串
   ```

4. **launchd plist 設定**

   使用簡化版 plist（不需要在 plist 中設定 token）：

   ```xml
   <key>EnvironmentVariables</key>
   <dict>
     <key>PATH</key>
     <string>/usr/local/bin:/usr/bin:/bin:/Users/YOUR_USERNAME/.local/bin</string>
   </dict>
   ```

   只需替換 `YOUR_USERNAME`。

### 腳本工作流程

`utils/run_daily_workflow.sh` 會按以下順序尋找 token：

1. 檢查 repo 根目錄 `.env` 檔案中的 `CLAUDE_CODE_OAUTH_TOKEN`（或舊版 `CLAUDE_TOKEN`）
2. 如果都找不到，嘗試從 `~/.config/claude/credentials.json` 讀取
3. 如果還是找不到，顯示錯誤並退出

---

## 方案 B: 在 plist 中直接設定

### 適用情境

- 不想使用 `.env` 檔案
- 希望設定集中在一個地方

### plist 設定

```xml
<key>EnvironmentVariables</key>
<dict>
  <key>PATH</key>
  <string>/usr/local/bin:/usr/bin:/bin:/Users/YOUR_USERNAME/.local/bin</string>
  <key>CLAUDE_TOKEN</key>
  <string>YOUR_OAUTH_TOKEN_HERE</string>
</dict>
```

需要替換：
- `YOUR_USERNAME` → 你的 macOS 使用者名稱
- `YOUR_OAUTH_TOKEN_HERE` → 你的 token

### 缺點

- ⚠️ Token 明文存在 plist 中
- ⚠️ 更新 token 需要重新載入 plist：
  ```bash
  launchctl unload ~/Library/LaunchAgents/com.market-intelligence.daily.plist
  launchctl load -w ~/Library/LaunchAgents/com.market-intelligence.daily.plist
  ```

---

## 完整設定範例

### 方案 A 完整流程

```bash
# 1. 創建 .env (repo 根目錄)
cd ~/Development/MH/the-ultimate-analysis-machine
cp .env.example.local .env

# 2. 編輯 .env
nano .env
# 填入：
# CLAUDE_TOKEN=你的token
# TZ=Asia/Taipei

# 3. 創建 plist（簡化版，不含 token）
nano ~/Library/LaunchAgents/com.market-intelligence.daily.plist
# 使用 LAUNCHD_SETUP.md 中的方案 A 範例

# 4. 創建日誌目錄
mkdir -p ~/logs

# 5. 載入 plist
launchctl load -w ~/Library/LaunchAgents/com.market-intelligence.daily.plist

# 6. 測試
launchctl start com.market-intelligence.daily
tail -f ~/logs/market-intelligence.log
```

### 方案 B 完整流程

```bash
# 1. 取得 token
cat ~/.config/claude/credentials.json
# 複製 accessToken 的值

# 2. 創建 plist（包含 token）
nano ~/Library/LaunchAgents/com.market-intelligence.daily.plist
# 使用 LAUNCHD_SETUP.md 中的方案 B 範例
# 替換 YOUR_USERNAME 和 YOUR_OAUTH_TOKEN_HERE

# 3. 創建日誌目錄
mkdir -p ~/logs

# 4. 載入 plist
launchctl load -w ~/Library/LaunchAgents/com.market-intelligence.daily.plist

# 5. 測試
launchctl start com.market-intelligence.daily
tail -f ~/logs/market-intelligence.log
```

---

## 驗證設定

### 檢查 .env 是否被讀取

執行腳本後查看日誌：

```bash
tail ~/logs/market-intelligence.log
```

應該會看到：
```
🔐 載入 .env 環境變數...
📅 日期: 2025-12-08
⏰ 時間: 13:30:00
📂 專案路徑: /Users/mhhung/Development/MH/the-ultimate-analysis-machine/src/daily-analysis-system
```

如果看到警告訊息，表示沒有找到 `.env`。

### 除錯模式

在 `utils/run_daily_workflow.sh` 的開頭加入除錯資訊：

```bash
# 在腳本中加入（已包含在更新後的腳本中）
echo "PATH: $PATH"
echo "CLAUDE_TOKEN 前20字元: ${CLAUDE_TOKEN:0:20}..."
echo "專案路徑: $PROJECT_ROOT"
```

---

## 常見問題

### Q: 只需要 .env 嗎？

是的，目前僅使用 `.env`（macOS 本機）。過去的 `.env.docker` Docker 範本已移除，如需參考請查看 Git 歷史。

### Q: 我應該把 .env 加入 Git 嗎？

**不應該！** `.env` 已在 `.gitignore` 中。
- 提交到 Git：`.env.example.local`（範本）
- 不提交：`.env`（包含真實 token）

### Q: 手動執行腳本時會讀取 .env 嗎？

會！這是使用 `.env` 的優點之一：

```bash
cd ~/Development/MH/the-ultimate-analysis-machine
./utils/run_daily_workflow.sh
# 會自動讀取 repo 根目錄的 .env
```

### Q: 如何更新 token？

**方案 A**：
```bash
nano .env
# 修改 CLAUDE_TOKEN 的值
# 不需要重新載入 plist
```

**方案 B**：
```bash
nano ~/Library/LaunchAgents/com.market-intelligence.daily.plist
# 修改 CLAUDE_TOKEN 的值
launchctl unload ~/Library/LaunchAgents/com.market-intelligence.daily.plist
launchctl load -w ~/Library/LaunchAgents/com.market-intelligence.daily.plist
```

### Q: 腳本找不到 .env 會怎樣？

會嘗試從以下位置讀取：
1. `~/.config/claude/credentials.json`（需要 jq）
2. 如果還是失敗，顯示錯誤並退出

### Q: 需要安裝 jq 嗎？

不一定。jq 只在以下情況需要：
- 沒有 `.env` 檔案
- 需要從 `credentials.json` 讀取 token

安裝方法：
```bash
brew install jq
```

---

## 檔案清單

- ✅ `utils/run_daily_workflow.sh` - 已更新，支援 .env
- ✅ `.env.example.local` - 本地環境範本（新增）
- ❌ `.env.docker` - Docker 範本已移除，如需參考請查看 Git 歷史
- ✅ `.gitignore` - 已排除 `.env`

---

## 推薦設定

**最佳實踐**：
1. 使用方案 A（.env 檔案）
2. 在 `.env` 中設定 `CLAUDE_TOKEN`
3. plist 中只設定 `PATH`
4. 定期備份 `.env`（但不要提交到 Git）

**安全提示**：
- 不要分享 `.env` 檔案
- 不要在公開場合展示日誌（可能包含 token）
- Token 過期時只需更新 `.env`

---

**相關文檔**：
- [LAUNCHD_SETUP.md](LAUNCHD_SETUP.md) - launchd 完整設定指南
- [AUTOMATION_SETUP.md](AUTOMATION_SETUP.md) - 自動化方案比較

**最後更新**：2025-12-08
