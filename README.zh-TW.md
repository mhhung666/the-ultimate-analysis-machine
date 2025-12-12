# 終極分析機器

> AI 驅動的自動化投資組合分析系統

## 專案簡介

每日自動收集市場數據、運行 Claude AI 分析、生成精美報告並發布到 GitHub Pages。

**核心功能**：
- 🤖 自動抓取全球市場指數、持股價格、相關新聞
- 🧠 使用 Claude AI 進行市場分析、個股研究、持倉評估
- 📊 自動生成 HTML 報告並發布到 GitHub Pages
- ⏰ 支援 Cron/Launchd 定時執行
- 📈 選擇權部位管理與風險追蹤

## 專案架構

```
the-ultimate-analysis-machine/
├── config/                      # 全局配置
│   ├── holdings.yaml            # 持股清單（含選擇權）
│   ├── indices.yaml             # 全球市場指數
│   └── portfolio_summary.yaml   # 投資組合績效快照
│
├── src/daily-analysis-system/   # 核心分析系統
│   ├── scrapers/                # 數據爬蟲
│   ├── scripts/                 # 分析與部署腳本
│   ├── reports/markdown/        # Markdown 報告
│   └── output/market-data/      # 原始數據暫存
│
├── docs/                        # GitHub Pages 發布目錄
└── Makefile                     # 任務管理
```

## 快速開始

```bash
# 1. 安裝依賴
make install

# 2. 安裝並登入 Claude CLI
npm install -g @anthropic-ai/claude-cli
claude login

# 3. 配置環境變數
cp .env.example.local .env
# 編輯 .env 填入必要配置

# 4. 執行完整工作流
make daily                # 抓取數據 → AI 分析 → 生成報告

# 5. 查看報告
ls src/daily-analysis-system/reports/markdown/

# 6. 生成 GitHub Pages
make update-pages         # Markdown → HTML
make preview-pages        # 本地預覽 :8000
```

## 常用指令

### 數據收集
```bash
make fetch-all         # 抓取所有數據
make fetch-global      # 只抓取市場指數
make fetch-holdings    # 只抓取持股價格
make fetch-news        # 只抓取新聞
```

### 分析與發布
```bash
make analyze-daily     # 執行 AI 分析
make daily             # 完整工作流（抓取 + 分析）
make update-pages      # 轉換為 HTML
make deploy            # 部署到 GitHub（更新 + 提交 + 推送）
```

### 維護
```bash
make clean-old-reports # 歸檔舊報告
make preview-pages     # 本地預覽 GitHub Pages
```

## 配置說明

### 持股配置 (`config/holdings.yaml`)

```yaml
holdings:
  核心持倉:
    Apple:
      symbol: "AAPL"
      fetch_news: true
      enabled: true
      position: 15.0%
      shares: 100

  選擇權部位:
    Apple (AAPL):
      symbol: "AAPL"
      options:
        - type: "Sell Call"
          strike: $190.00
          expiry: "2025-12-19"

watchlist:
  潛在投資標的:
    Microsoft:
      symbol: "MSFT"
      fetch_news: true
      enabled: true
```

### 市場指數 (`config/indices.yaml`)

```yaml
indices:
  美國市場:
    S&P 500:
      symbol: "^GSPC"
      fetch_news: true

  亞洲市場:
    台灣加權指數:
      symbol: "^TWII"
      fetch_news: true
```

## 分析流程

系統採用三階段分層分析：

1. **市場分析** - 分析全球市場趨勢、識別驅動因素
2. **個股分析** - 深入研究每支持股（自動跳過無新聞標的）
3. **持倉分析** - 綜合評估投資組合、提供操作建議

## 自動化設定

### Linux / macOS (Cron)

```bash
# 編輯 crontab
crontab -e

# 每天早上 8:00 執行分析
0 8 * * * cd /path/to/project && make daily >> /var/log/analysis.log 2>&1

# 每天下午 5:00 部署到 GitHub Pages
0 17 * * * cd /path/to/project && make deploy >> /var/log/deploy.log 2>&1
```

### macOS (Launchd)

```bash
cd src/daily-analysis-system
./scripts/cron/setup_cron.sh
```

詳見 [`src/daily-analysis-system/AUTOMATION_SETUP.md`](src/daily-analysis-system/AUTOMATION_SETUP.md)

## 資料流程

```
配置文件 (holdings.yaml, indices.yaml)
    ↓
爬蟲層 (fetch 指數/持股/新聞)
    ↓
暫存層 (output/market-data/)
    ↓
分析層 (Claude AI 三階段分析)
    ↓
報告層 (reports/markdown/)
    ↓
發布層 (docs/ → GitHub Pages)
```

## 技術棧

- **Python 3.8+** - 爬蟲與數據處理 (yfinance, pandas)
- **Claude CLI** - AI 分析引擎
- **GNU Make** - 任務自動化
- **GitHub Actions** - CI/CD 自動發布

## 文檔

- [README.md](README.md) - 英文版
- [TODO.md](TODO.md) - 待辦事項與改進建議
- [QUICKSTART.md](src/daily-analysis-system/QUICKSTART.md) - 詳細快速指南
- [DEVELOPMENT.md](src/daily-analysis-system/DEVELOPMENT.md) - 開發者指南
- [AUTOMATION_SETUP.md](src/daily-analysis-system/AUTOMATION_SETUP.md) - 自動化教學

## 常見問題

**Q: 需要付費訂閱嗎？**
A: 需要 Anthropic Claude 帳號，建議 Claude Pro 獲得更高限額。

**Q: 可以追蹤加密貨幣嗎？**
A: 可以，在 `indices.yaml` 加入 `BTC-USD`、`ETH-USD` 即可。

**Q: 持倉數據會上傳嗎？**
A: 只有執行 `make deploy` 才會推送到 GitHub。可設為私有倉庫或只在本地使用。

**Q: 如何修改執行時間？**
A: 調整 crontab 或 launchd 配置，參考 AUTOMATION_SETUP.md。

## 安全提醒

⚠️ **重要**：
- 絕不提交 `.env` 文件到 Git
- 如報告含真實數據，考慮設 GitHub Pages 為私有
- 定期輪換 API tokens

## 授權

MIT License

---

**最後更新**: 2025-12-12
