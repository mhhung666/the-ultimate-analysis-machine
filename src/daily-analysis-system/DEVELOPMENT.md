# DEVELOPMENT.md - The Ultimate Analysis System

開發文檔，包含專案架構、工作流程、GitHub Pages 自動化、以及開發路線圖。

---

## 📁 專案架構 (重構後)

```
market-intelligence-system/
├── scrapers/                     # 爬蟲層 - 數據收集
│   ├── common.py                 # 共用模組
│   ├── fetch_global_indices.py
│   ├── fetch_holdings_prices.py
│   ├── fetch_all_news.py
│   └── README.md
│
├── scripts/                      # 執行腳本
│   ├── analysis/                 # Bash 分析腳本
│   │   └── run_daily_analysis_claude_cli.sh   # Claude CLI 分析
│   ├── deployment/               # 部署/轉檔腳本
│   ├── tools/                    # Markdown → HTML 轉換
│   └── README.md
│
├── ../../config/                 # 配置文件（位於 repo 根目錄）
│   ├── holdings.yaml             # 投資組合配置
│   └── indices.yaml              # 全球指數配置
│
├── output/market-data/{YEAR}/    # 爬蟲數據輸出
│   ├── Daily/                    # 每日指數和價格
│   ├── News/                     # 新聞數據
│   └── Stocks/                   # 歷史數據
│
├── reports/                      # 報告目錄
│   ├── markdown/                 # 最新報告
│   │   ├── market-analysis-{date}.md
│   │   └── holdings-analysis-{date}.md
│   └── archive/                  # 歷史報告歸檔
│
├── docs/                         # GitHub Pages
│   ├── index.html
│   ├── market.html
│   ├── holdings.html
│   └── styles.css
│
├── tests/                        # 測試文件
├── .github/workflows/            # GitHub Actions
│   └── build-pages.yml
│
├── README.md                     # 專案概覽
├── QUICKSTART.md                 # 快速開始
├── DEVELOPMENT.md                # 本文件
├── CHANGELOG.md                  # 版本歷史
└── Makefile                      # 任務自動化
```

---

## 🔄 工作流程

### 爬蟲層
```bash
make fetch-global    # 全球指數
make fetch-holdings  # 持股價格
make fetch-news      # 市場新聞
make fetch-all       # 執行所有爬蟲
```

### 分析層

```bash
make analyze-daily
# → market-analysis-{date}-{time}.md
# → holdings-analysis-{date}-{time}.md
```

### 報告命名規則

**時間標記自動判斷**:
- 使用執行時間 (HHMM 格式)
- 範例: `market-analysis-2025-12-03-0800.md`、`market-analysis-2025-12-03-1430.md`、`market-analysis-2025-12-03-2000.md`

**手動指定時間標記**:
```bash
TIME_SUFFIX=0800 make analyze-daily
TIME_SUFFIX=1430 make analyze-daily
TIME_SUFFIX=2000 make analyze-daily
```

**設計目的**: 支援每日多次分析 (無限制時段數量)，自動按時間排序

**排序規則**:
- 檔名格式: `market-analysis-{YYYY-MM-DD}-{HHMM}.md`
- 使用 `sort -r` 按字母順序反向排序，自然選出最新報告
- 範例: `2025-12-03-2000` > `2025-12-03-1430` > `2025-12-03-0800` > `2025-12-02-2000`

### 報告管理

- 報告位置：`reports/markdown/`
- 歸檔舊報告：`make clean-old-reports` → 移動到 `reports/archive/`
- GitHub Pages 更新：`make update-pages` → 自動選取最新報告 (按日期+時間排序)

---

## 🌐 GitHub Pages 自動化

### 架構設計

**本地轉換器**：`scripts/tools/convert_md_to_html.py`
- 輸入：`reports/markdown/*.md`
- 輸出：`docs/*.html`
- 使用：`make update-pages`

**GitHub Actions 自動化**：`.github/workflows/build-pages.yml`

1. **觸發條件**：
   - Push 到 `main` 且變動 `reports/markdown/**`
   - Push 到 `main` 且變動轉檔腳本或 Makefile
   - 手動執行 (`workflow_dispatch`)

2. **執行流程**：
   ```
   Checkout → 安裝依賴 → make update-pages → Commit docs/ → Push
   ```

3. **關鍵修復** (2025-12-03)：
   - ✅ 使用檔名排序 (`ls | sort -r`) 取代時間排序 (`ls -t`)
   - ✅ 解決 GitHub Actions 中 `git checkout` 重設時間戳的問題
   - ✅ 移除重複的 HTML 生成邏輯（節省 API calls）

### 部署流程

**自動部署** (推薦)
```bash
# 生成報告後推送
make daily
git push origin main
# → GitHub Actions 自動更新 HTML
```

**手動部署**
```bash
# 本地生成 HTML 並推送
make update-pages
make commit-auto
make push

# 或一鍵完成
make deploy
```

### 本地預覽

```bash
make preview-pages
# 訪問 http://localhost:8000
```

### GitHub Pages 設定

1. Repository Settings → Pages
2. Source: Branch `main`, Folder `/docs`
3. 網站 URL: `https://USERNAME.github.io/REPO/`

## 🛠️ 開發者備忘

### 建置

```bash
make venv      # 創建虛擬環境
make install   # 安裝依賴
make test      # 執行測試
```

### 腳本權限

```bash
chmod +x scripts/analysis/*.sh
chmod +x scripts/deployment/*.sh
```

### 路徑管理

- 所有程式碼：`src/`
- 數據輸出：`output/market-data/{YEAR}/`
- 報告輸出：`reports/markdown/`
- 可用 `OUTPUT_DIR` 環境變數覆寫

---

## 🚀 開發路線圖

### 已完成 ✅

- [x] 架構重構（統一 src/ 目錄）
- [x] 雙報告系統（市場分析 + 持倉分析）
- [x] GitHub Pages 自動化
- [x] 報告歸檔機制
- [x] Makefile 任務自動化
- [x] 修復 GitHub Actions 時間戳問題

### 進行中 🔵

- [ ] 文檔整合與精簡
- [ ] 測試覆蓋率提升

### 規劃中 📋

**報告層級系統**
- [ ] 週報生成（匯總 5 個交易日）
- [ ] 月報生成（匯總整月市場表現）
- [ ] 報告目錄結構優化（daily/weekly/monthly）

**功能擴充**
- [ ] Telegram/Discord 通知整合
- [ ] 更多 AI 模型支援 (GPT-4, Gemini)
- [ ] 技術指標分析 (RSI, MACD, 布林通道)
- [ ] 回測系統整合
- [ ] 投資決策追蹤與學習系統

---

## 📝 貢獻指南

### 代碼風格

- Python: PEP 8
- Bash: Google Shell Style Guide
- Makefile: Tab indentation
- 所有腳本需可執行權限

### 提交規範

```bash
# Commit message 格式
<type>(<scope>): <subject>

# 類型
feat     # 新功能
fix      # 修復
refactor # 重構
docs     # 文檔
test     # 測試
chore    # 雜項
```

### Pull Request 流程

1. Fork repository
2. 創建 feature branch
3. 提交變更
4. 創建 PR 並說明變更內容
5. 等待 review

---

## 🔗 相關資源

- [Python 專案最佳實踐](https://docs.python-guide.org/writing/structure/)
- [GitHub Pages 文檔](https://docs.github.com/en/pages)
- [Claude CLI 文檔](https://github.com/anthropics/claude-cli)
- [Makefile 風格指南](https://clarkgrubb.com/makefile-style-guide)

---

**最後更新**: 2025-12-03
**維護者**: The Ultimate Analysis System Team
