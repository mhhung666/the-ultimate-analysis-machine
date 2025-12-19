# 爬蟲工具

## 共用模組 (`common.py`)

所有爬蟲工具共用的功能模組，提供：

- **路徑管理**: `get_project_root()`, `get_data_directory()`
- **Argparse**: `create_argument_parser()`
- **輸出處理**: `setup_output_path()`, `write_output()`
- **狀態訊息**: `print_status()`, `print_error()`, `print_success()`, `print_warning()`
- **工具函數**: `validate_positive_int()`, `generate_dated_filename()`, `safe_exit()`

---

## 1. 市場資料爬蟲 (`fetch_market_data.py`)

從 Yahoo Finance 爬取股票或匯率歷史價格資料。

```bash
# UPS 股票（只輸入 symbol，自動儲存為當年目錄下的 UPS.md）
python3 tools/python/scrapers/fetch_market_data.py UPS

# USD/JPY 匯率（儲存至 Stocks/ 目錄）
python3 tools/python/scrapers/fetch_market_data.py JPY=X -o data/market-data/2025/Stocks/USDJPY.md

# UPS 股票（只輸入檔名會自動儲存到當年 data/market-data/{YEAR}/Stocks/）
python3 tools/python/scrapers/fetch_market_data.py UPS -o UPS.md

# UPS 股票（只輸出 2024 年資料，並自動儲存到當年目錄）
python3 tools/python/scrapers/fetch_market_data.py UPS -y 2024 -o UPS-2024.md

# 強制輸出到螢幕（不儲存檔案）
python3 tools/python/scrapers/fetch_market_data.py UPS --stdout

# Apple 股票 (26週，儲存至 Stocks/ 目錄)
python3 tools/python/scrapers/fetch_market_data.py AAPL -w 26 -o data/market-data/2025/Stocks/AAPL.md
```

**參數:**
- `symbol`: 股票代碼或匯率代碼 (預設 JPY=X)
- `-w, --weeks`: 週數 (預設 52)
- `-o, --output`: 輸出檔案路徑或檔名。若只給檔名（如 `UPS.md`），會自動存到 `data/market-data/{YEAR}/Stocks/`。
- `-y, --year`: 只輸出指定年份資料（自動抓整年度並忽略 `-w`）。
- `--stdout`: 強制輸出到螢幕（不寫入檔案）。

**常用代碼:** AAPL, TSLA, MSFT, UPS, GOOGL, JPY=X, EUR=X

> 歷史價格一次手動抓完整年度，建議檔名統一為 `data/market-data/{YEAR}/Stocks/{SYMBOL}.md`（不含日期）。

## 2. 全球市場指數爬蟲 (`fetch_global_indices.py`)

爬取全球主要市場的大盤指數今日資料，包含亞洲、歐洲、美國等主要市場。

```bash
# 爬取所有市場指數
python3 tools/python/scrapers/fetch_global_indices.py

# 爬取特定區域
python3 tools/python/scrapers/fetch_global_indices.py -r 台灣 美國 日本

# 指定輸出檔案
python3 tools/python/scrapers/fetch_global_indices.py -o data/market-data/2025/Daily/global-indices-2025-11-18.md

# 不使用 emoji
python3 tools/python/scrapers/fetch_global_indices.py --no-emoji
```

**參數:**
- `-r, --regions`: 要爬取的區域（可多選）
- `-o, --output`: 輸出檔案路徑（預設自動產生）
- `--no-emoji`: 不使用 emoji 符號

**支援市場與指數:**
- **日本**: 日經225、TOPIX
- **韓國**: KOSPI、KOSDAQ
- **台灣**: 台灣加權指數
- **中國**: 上證指數、深證成指、滬深300
- **新加坡**: 海峽時報指數
- **香港**: 恆生指數、國企指數
- **歐洲**: STOXX 50、德國DAX、法國CAC 40、英國FTSE 100
- **美國**: S&P 500、Dow Jones、NASDAQ、Russell 2000

- 💡 市場與指數設定存於 repo 根目錄的 `config/` 目錄，可自訂追蹤市場無需修改程式碼。

**輸出格式:**
- 單一表格包含所有市場指數
- 包含國家/地區、指數名稱、收盤價、開盤、最高、最低、成交量、漲跌、漲跌幅
- 自動計算漲跌幅並用 🔺/🔻 標示
- 預設儲存至 `data/market-data/{YEAR}/Daily/global-indices-{YYYY-MM-DD}.md`（年份自動取得）

## 3. 金融新聞爬蟲

### 批次新聞爬蟲 (`fetch_all_news.py`) ⭐ 推薦

從配置檔自動批次爬取所有配置的股票和指數新聞。

**使用 Makefile（推薦）：**
```bash
# 爬取所有配置的新聞
make fetch-news

# 執行所有爬蟲（包含新聞）
make fetch-all
```

**直接執行腳本：**
```bash
python3 scrapers/fetch_all_news.py
```

**功能特色：**
- ✅ 自動從 repo 根目錄的 `config/holdings.yaml` 與 `config/indices.yaml` 讀取配置
- ✅ 只爬取標記為 `fetch_news: true` 且 `enabled: true` 的項目
- ✅ 自動產生帶日期的檔名（格式：`SYMBOL-YYYY-MM-DD.md`）
- ✅ 顯示進度和成功/失敗統計
- ✅ 支援股票和指數兩種類型

**配置範例：**

在 `../../config/holdings.yaml` 中設定：
```yaml
holdings:
  核心持倉:
    Tesla:
      symbol: "TSLA"
      fetch_news: true    # 啟用新聞爬取
      enabled: true
```

在 `../../config/indices.yaml` 中設定：
```yaml
global_indices:
  美國:
    S&P 500:
      symbol: "^GSPC"
      fetch_news: true    # 啟用新聞爬取
```

**輸出範例：**
```
正在載入配置檔...
從 holdings.yaml 找到 12 隻需要爬取新聞的股票
從 indices.yaml 找到 11 個需要爬取新聞的指數
總共需要爬取 23 個項目的新聞

[1/23] 正在爬取 Tesla (TSLA) 的新聞...
  ✓ 完成

[2/23] 正在爬取 S&P 500 (^GSPC) 的新聞...
  ✓ 完成

新聞爬取完成!
成功: 23/23
```

### 單一新聞爬蟲 (`fetch_market_news.py`)

從 Yahoo Finance 爬取特定股票或市場指數的最新金融新聞。

**爬取個股新聞：**
```bash
# 爬取 Apple 最新新聞（預設 10 則，自動產生檔名）
python3 scrapers/fetch_market_news.py AAPL

# 爬取 Tesla 最新 5 則新聞並儲存
python3 scrapers/fetch_market_news.py TSLA -l 5

# 爬取 NVIDIA 新聞並輸出為 JSON 格式
python3 scrapers/fetch_market_news.py NVDA --json

# 指定輸出檔案
python3 scrapers/fetch_market_news.py GOOGL -o data/market-data/2025/News/GOOGL-2025-12-01.md

# 輸出到螢幕
python3 scrapers/fetch_market_news.py GOOGL --stdout
```

**爬取大盤指數新聞：**
```bash
# S&P 500 新聞
python3 scrapers/fetch_market_news.py "^GSPC"

# NASDAQ 新聞
python3 scrapers/fetch_market_news.py "^IXIC"

# 道瓊工業指數新聞
python3 scrapers/fetch_market_news.py "^DJI"

# 恆生指數新聞
python3 scrapers/fetch_market_news.py "^HSI"
```

> 💡 預設會自動產生檔名：`{SYMBOL}-{YYYY-MM-DD}.md`，並儲存至 `output/market-data/{YEAR}/News/` 目錄。

### 參數說明

- `symbol`: 股票代碼或指數代碼（必填）
- `-l, --limit`: 新聞數量（預設 10 則）
- `-o, --output`: 輸出檔案路徑（若未指定則自動產生）
- `--json`: 輸出為 JSON 格式（預設 Markdown）
- `--stdout`: 輸出到螢幕而非檔案

### 支援的代碼

**個股代碼：**
- 科技股: `AAPL` (Apple), `TSLA` (Tesla), `NVDA` (Nvidia), `MSFT` (Microsoft), `GOOGL` (Google)
- 金融股: `JPM` (JP Morgan), `BAC` (Bank of America), `GS` (Goldman Sachs)
- 其他: `UPS`, `AMZN` (Amazon), `META` (Meta/Facebook), `INTC` (Intel), `PINS` (Pinterest)

**市場指數代碼：**
- 美國: `^GSPC` (S&P 500), `^DJI` (Dow Jones), `^IXIC` (NASDAQ), `^VIX` (恐慌指數), `^SOX` (費城半導體)
- 亞洲: `^HSI` (恆生指數), `^N225` (日經225), `^TWII` (台灣加權)
- 商品: `GC=F` (黃金期貨), `CL=F` (WTI原油), `BTC-USD` (比特幣)
- 債券: `^TNX` (美國10年期公債殖利率)

### 輸出格式

**Markdown 格式**（預設）：
- 包含標題、摘要、來源、發布時間、連結
- 自動標示新聞類型（📰 文章 / 🎥 影片）
- 格式化日期時間為易讀格式
- 適合直接閱讀和儲存

**JSON 格式**：
- 結構化資料，適合程式化處理
- 包含 `id`, `title`, `summary`, `publisher`, `published_at`, `url`, `content_type`
- 可用於進一步分析或整合

預設儲存路徑：`output/market-data/{YEAR}/News/{SYMBOL}-{YYYY-MM-DD}.md`（年份自動取得）

### 新聞資訊來源

- Yahoo Finance、WSJ、Barrons、Investor's Business Daily 等多元來源
- 每個股票/指數通常返回約 10 則最新新聞
- 免費使用，無需 API key

---

## 4. Barron's 訊號爬蟲 (`fetch_barrons_signals.py`)

抓取 Barron's 股票推薦並輸出到 `output/market-data/{YEAR}/Signals/`。

```bash
# 抓取 Barron's 推薦 (預設 10 筆)
python3 scrapers/fetch_barrons_signals.py

# 使用 Makefile
make fetch-barrons

# 指定輸出路徑
python3 scrapers/fetch_barrons_signals.py -o output/market-data/2025/Signals/barrons-2025-12-19.md

# 強制覆蓋輸出
python3 scrapers/fetch_barrons_signals.py --force
```

**參數:**
- `-l, --limit`: 最高筆數 (預設 10)
- `--days`: 視窗天數 (預設 7)
- `--force`: 即使內容相同仍覆蓋輸出

**認證:**
- 若遇到 401 Forbidden，請在環境變數設定 `BARRONS_COOKIE`（可從瀏覽器已登入的 Cookie 取得）

---

## 5. OpenInsider 內部人交易 (由 `fetch_all_news.py` 自動附加)

`fetch_all_news.py` 會在抓取 Yahoo News 後，針對持股與觀察清單股票附加 OpenInsider 近 7 天交易到同一個 Markdown 檔案最後。

## 6. 持倉股票價格爬蟲 (`fetch_holdings_prices.py`)

從 [portfolio/2025/holdings.md](../../../portfolio/2025/holdings.md) 自動提取股票代碼，並從 Yahoo Finance 獲取當天的即時價格資訊。

### 使用範例

**基本用法：**
```bash
# 分析預設的 holdings 檔案（輸出到螢幕）
python3 tools/python/scrapers/fetch_holdings_prices.py

# 儲存到檔案
python3 tools/python/scrapers/fetch_holdings_prices.py -o portfolio/2025/prices-2025-11-18.md

# 顯示詳細資訊
python3 tools/python/scrapers/fetch_holdings_prices.py -v
```

**進階用法：**
```bash
# 指定不同的 holdings 檔案
python3 tools/python/scrapers/fetch_holdings_prices.py -i portfolio/2024/holdings.md -o portfolio/2024/prices-today.md

# 使用 Shell 包裝腳本（推薦）
./tools/python/fetch_holdings_prices.sh

# 使用 Makefile
make holdings-prices

# 使用快捷腳本
./check-holdings.sh
```

> 建議使用 Shell 腳本或 Makefile，會自動儲存到 `portfolio/2025/prices-{YYYY-MM-DD}.md`（預設行為）。

### 參數說明

- `-i, --input`: holdings.md 檔案路徑（預設：`portfolio/2025/holdings.md`）
- `-o, --output`: 輸出檔案路徑（若未指定則輸出到螢幕）
- `-v, --verbose`: 顯示詳細資訊

### 功能特色

- ✅ **自動提取股票代碼**：從 holdings.md 的「當前持倉」表格中提取
- ✅ **支援多種格式**：AAPL, SET.SI, BRK.B 等格式
- ✅ **即時價格資訊**：獲取最新收盤價、開盤價、最高價、最低價
- ✅ **漲跌幅計算**：自動計算與前一日收盤價的漲跌幅
- ✅ **視覺化標示**：🟢 上漲 / 🔴 下跌 / ⚪ 持平
- ✅ **市場概況統計**：統計上漲/下跌股票數及占比
- ✅ **多市場支援**：美股、新加坡股市等（通過代碼後綴識別）

### 輸出格式

**Markdown 表格**（預設）：

```markdown
# 📊 持倉股票價格分析

> 更新時間: 2025-11-18

---

| 代碼 | 名稱 | 當前價格 | 漲跌 | 漲跌幅 | 開盤 | 最高 | 最低 | 成交量 | 市值 |
|------|------|----------|------|--------|------|------|------|--------|------|
| U | Unity Software Inc. | $36.67 | -$0.05 | 🔴 -0.14% | $36.60 | $37.63 | $36.10 | 6,872,500 | $15.69B |
| GOOGL | Alphabet Inc. | $285.02 | +$8.61 | 🟢 +3.11% | $285.78 | $293.95 | $283.57 | 52,577,600 | $3452.20B |
| TSLA | Tesla, Inc. | $408.92 | +$4.57 | 🟢 +1.13% | $398.74 | $423.96 | $398.74 | 101,741,100 | $1359.99B |
...

---

## 📈 市場概況

- **總股票數**: 15
- **上漲**: 🟢 3 (20.0%)
- **下跌**: 🔴 12 (80.0%)
- **持平**: ⚪ 0 (0.0%)
```

### 工作原理

1. **讀取 holdings.md**：解析 Markdown 文件
2. **提取股票代碼**：使用正則表達式 `r'\|\s*([A-Z]+(?:\.[A-Z]+)?)\s*\|'` 匹配表格中的股票代碼
3. **查詢價格**：通過 yfinance 庫從 Yahoo Finance 獲取即時數據
4. **計算指標**：計算漲跌、漲跌幅、統計市場概況
5. **格式化輸出**：生成 Markdown 表格或儲存到檔案

### 支援的股票代碼格式

- **美股**：`AAPL`, `GOOGL`, `TSLA`, `INTC` 等
- **新加坡股市**：`SET.SI`（需要 `.SI` 後綴）
- **特殊格式**：`BRK.B`（波克夏B股）等

### 預設儲存路徑

當使用 Shell 包裝腳本時，預設儲存至：
```
portfolio/2025/prices-{YYYY-MM-DD}.md
```

例如：`portfolio/2025/prices-2025-11-18.md`

### 注意事項

- ⚠️ **市場時間**：工具獲取的是最新可用數據，盤中價格可能有延遲
- ⚠️ **網路連線**：需要穩定的網路訪問 Yahoo Finance
- ⚠️ **股票代碼**：確保 holdings.md 中的股票代碼正確
- ⚠️ **市場後綴**：非美股需要正確的市場後綴（如 `.SI`, `.L`, `.HK` 等）
- ⚠️ **依賴套件**：需要 `yfinance` 和 `pandas` 套件

### 常見使用場景

**每日檢查持倉**：
```bash
# 開盤前/收盤後快速查看持倉表現
./check-holdings.sh
```

**定期存檔**：
```bash
# 每週或每月保存價格快照
./tools/python/fetch_holdings_prices.sh  # 自動儲存到 prices-YYYY-MM-DD.md
```

**結合大盤分析**：
```bash
# 先查看大盤
make fetch-daily

# 再查看持倉
make holdings-prices
```

### 與其他工具的差異

| 工具 | 用途 | 資料來源 | 輸出格式 |
|------|------|---------|---------|
| `fetch_market_data.py` | 單一股票歷史價格 | Yahoo Finance | 完整歷史資料 |
| `fetch_global_indices.py` | 全球大盤指數 | Yahoo Finance | 當日指數快照 |
| `fetch_market_news.py` | 股票/指數新聞 | Yahoo Finance | 新聞文章列表 |
| **`fetch_holdings_prices.py`** | **持倉股票當日價格** | Yahoo Finance | **多股票價格快照** |

### 相關文件

- [holdings.md](../../../portfolio/2025/holdings.md) - 持倉列表（資料來源）
- [tools/README.md](../README.md) - 工具總覽
- [Makefile](../../../Makefile) - Make 快捷指令
