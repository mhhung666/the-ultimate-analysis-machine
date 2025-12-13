# Config 配置檔案說明

投資組合分析系統的配置檔案資料夾。

## 設計目的

- **給爬蟲程式使用** - `holdings.yaml` 和 `indices.yaml` 定義爬蟲要抓取的股票與指數
- **給 Claude CLI 分析** - 所有檔案都會餵給 Claude CLI 進行投資組合分析、風險檢查、績效計算等
- **結構化數據** - 易於程式解析與自動化處理

## 檔案結構

```
config/
├── holdings.yaml              # 持股明細與選擇權部位
├── indices.yaml              # 全球市場指數追蹤
├── portfolio_summary.yaml    # 投資組合績效快照
├── portfolio_config.yaml     # 投資組合目標配置與限制
├── transaction_log.yaml      # 交易記錄日誌
└── settings.yaml            # 系統通用設定
```

## 各檔案用途

| 檔案 | 主要用途 | 爬蟲使用 |
|------|---------|---------|
| **holdings.yaml** | 持股配置、選擇權部位管理 | ✅ 抓取持股價格與新聞 |
| **indices.yaml** | 全球市場指數追蹤 | ✅ 抓取指數價格與新聞 |
| **portfolio_summary.yaml** | 每日帳戶快照、績效追蹤 | ❌ |
| **portfolio_config.yaml** | 目標配置、風險限制、再平衡規則 | ❌ |
| **transaction_log.yaml** | 交易記錄、已實現損益 | ❌ |
| **settings.yaml** | 系統設定、輸出路徑 | ❌ |

> 詳細欄位說明請查看各 YAML 檔案頂部的註釋。

---

## 日常使用流程

### 每日更新
1. 執行爬蟲 → 自動更新 `holdings.yaml` 和 `indices.yaml` 的價格
2. 新增快照到 `portfolio_summary.yaml`
3. 記錄當日交易到 `transaction_log.yaml`（如有交易）

### 每週檢視
1. 用 Claude CLI 檢查投資組合配置偏離度
2. 檢視選擇權到期日
3. 產生週報告

### 每月/季度
1. 評估是否需要再平衡
2. 更新投資組合目標（如有調整）
3. 檢討交易績效

---

## Claude CLI 分析範例

所有 config 檔案都會餵給 Claude CLI 進行分析：

```bash
# 投資組合配置分析
"我的科技股佔比是多少？是否超過目標上限？"

# 績效計算
"計算我過去 30 天的報酬率"

# 風險檢查
"檢查我的投資組合是否超過風險限制"

# 選擇權管理
"哪些選擇權即將到期？"

# 再平衡建議
"我的投資組合是否需要再平衡？"
```

Claude CLI 可以提供：
- 產業配置分析與偏離度檢查
- 績效計算與基準比較
- 風險指標計算（波動率、最大回撤、夏普比率）
- 選擇權到期提醒
- 再平衡建議

---

## 程式整合範例

### 爬蟲讀取配置

```python
import yaml

# 讀取持股配置
with open('config/holdings.yaml', 'r', encoding='utf-8') as f:
    holdings = yaml.safe_load(f)

# 找出需要爬取新聞的股票
for category, stocks in holdings['holdings'].items():
    for name, info in stocks.items():
        if info.get('enabled') and info.get('fetch_news'):
            symbol = info['symbol']
            # 爬取 symbol 的價格與新聞
```

---

## 注意事項

1. **詳細欄位說明** - 請查看各 YAML 檔案頂部的註釋
2. **備份** - 建議定期備份這些配置檔案
3. **隱私** - 包含個人財務資訊，不要上傳到公開 repo
4. **一致性** - 確保 holdings.yaml 與 portfolio_summary.yaml 的數據一致

---

最後更新：2025-12-13
