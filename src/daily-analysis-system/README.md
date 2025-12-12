# daily-analysis-system

每日自動化市場情報工作流：抓取全球行情、啟動 AI 分析、輸出 Markdown/HTML 報告，整個過程不需人力盯盤。

## 核心功能

- **收集市場資料**：依照 YAML 設定 (`config/indices.yaml`, `config/holdings.yaml`) 取得指數、持倉價格與精選新聞。
- **分層 AI 分析**：Claude CLI 生成市場/個股/持倉長文報告，逐層輸出洞察。
- **發佈輸出**：Markdown 置於 `reports/markdown/`，可選擇同步到 GitHub Pages (`docs/`)。
- **自動化排程**：`make daily` 串連抓取 → 分析 → 發佈，可搭配 cron、launchd 或 Docker 排程。

> 與 `financial-analysis-system` 差異：本專案聚焦市場脈動與持倉監控，不處理完整財務模型。

## 架構速覽

```
config/*.yaml ─┐
               ▼
         scrapers/ (Python)
               ▼
        output/market-data/
               ▼
        scripts/analysis (Claude CLI)
               ▼
        reports/markdown + docs/
```

- **爬蟲層 (`scrapers/`)**：以 pandas / yfinance 為基礎抓取指數、持倉與新聞。
- **資料暫存 (`output/market-data/`)**：集中 CSV/JSON，方便測試或之後重跑分析。
- **分析層 (`analysis/`, `scripts/analysis/claude_*`)**：組裝提示詞，遵循「市場 → 個股 → 持倉」順序，並跳過無最新新聞的持股。
- **輸出層 (`reports/`, `docs/`, `scripts/deployment/`)**：渲染 Markdown、轉靜態 HTML、同步 GitHub Pages。
- **自動化 (`Makefile`, `utils/run_daily_workflow.sh`, `AUTOMATION_SETUP.md`)**：支援本機、Docker 或 macOS 排程。

清楚分層讓設定與程式碼解耦、將大量 I/O 與 LLM 分開，並易於替換 AI 供應商與排程器。

## 快速開始

```bash
make install              # 安裝 python 依賴與 pre-commit
npm i -g @anthropic-ai/claude-cli && claude login
make daily                # 抓資料、跑分析、寫入報告
ls reports/markdown       # market-analysis-YYYYMMDD-HHMM.md, stock-*.md, holdings-analysis-*.md
```

只想跑單一步驟？常用指令有 `make fetch-all`、`make fetch-news`、`make analyze-daily`、`make update-pages`。

## 根目錄整合與 GitHub Pages

- 所有指令都在 **repo 根目錄** 執行 (`make ...`)，內部會自動切到 `src/daily-analysis-system/`。
- 產出的 HTML 置於根目錄 `docs/`，GitHub Pages 直接以此目錄為來源。
- `.github/workflows/build-pages.yml`：`push` 或手動觸發時執行 `make update-pages`，並將 `docs/` 變更自動 commit/push。
- `utils/run_daily.sh`、`utils/update_pages.sh`… 等 wrapper 可在自動化腳本中呼叫，省去輸入長指令。

## 最小設定

`config/holdings.yaml`

```yaml
holdings:
  - symbol: AAPL
    name: Apple Inc.
    enabled: true
    fetch_news: true
```

`config/indices.yaml`

```yaml
indices:
  us:
    - symbol: ^GSPC
      name: S&P 500
```

調整 YAML 後不必改程式碼，重新執行 `make daily` 即可。

## 自動化選項

1. Linux/Docker：在 cron 或 systemd 中跑 `make daily`（詳見 `AUTOMATION_SETUP.md`）。
2. macOS：launchd plist，支援任務補跑與開機自動恢復（`AUTOMATION_SETUP.md` 內含範例）。
3. GitHub Actions：`build-pages.yml` 偵測 `reports/markdown/**` 變動後重建 `docs/`。

每個環境擇一排程方案即可，入口腳本相同。

## 文件導航

- `QUICKSTART.md`：圖文流程、日誌範例。
- `DEVELOPMENT.md`：架構決策、資料契約、貢獻指南。
- `AUTOMATION_SETUP.md`：cron / launchd / Docker 教學與疑難排解。
- `scripts/README.md`：每支 CLI 腳本的參數說明。

## 建議後續調整

- **整併環境文件**：把 `ENV_SETUP_GUIDE.md` 內容合到 `QUICKSTART.md`，避免新手需要跳檔。
- **強化設定說明**：在 `config/README.md` 或 YAML 中加入簡短 schema，統一敘述。
- **精簡自動化章節**：於 `AUTOMATION_SETUP.md` 內用平台分節，並移除 `DEVELOPMENT.md` 的重複段落。
- **考慮自動產生文件**：例如以 mkdocs 或單一 GitHub Pages landing page 統整所有指南，減少零散 Markdown。
