# Claude API 重試機制

## 功能說明

為了提高系統的穩定性，已在 `run_daily_analysis_claude_cli.sh` 中實作了自動重試機制，當 Claude API 調用失敗時會自動重試。

## 重試策略

### 基本參數
- **最大重試次數**: 3 次
- **初始等待時間**: 10 秒
- **退避策略**: 指數退避（每次重試等待時間加倍）
  - 第 1 次嘗試：立即執行
  - 第 2 次嘗試：等待 10 秒
  - 第 3 次嘗試：等待 20 秒

### 重試條件

系統會在以下情況觸發重試：

1. **API 連線錯誤**
   - `Connection error`
   - `API Error`

2. **輸出檔案異常**
   - 檔案大小 < 100 bytes
   - 檔案為空

3. **其他執行失敗**
   - Claude CLI 返回非零退出碼

## 適用範圍

重試機制已應用於所有 AI 分析步驟：

1. ✅ **市場分析** (`market-analysis-{date}.md`)
2. ✅ **個股分析** (`stock-{symbol}-{date}.md`)
3. ✅ **持倉分析** (`holdings-analysis-{date}.md`)

## 日誌輸出

### 正常執行
```
🧠 調用 Claude 進行市場分析...
   這可能需要幾分鐘,請稍候...

   ✅ 市場分析完成!
```

### 重試場景
```
🧠 調用 Claude 進行市場分析...
   這可能需要幾分鐘,請稍候...

   ⚠️  連線錯誤: API Error: Connection error.
   ⏳ 重試 2/3 (等待 10秒...)

   ✅ 市場分析完成!
```

### 最終失敗
```
🧠 調用 Claude 進行市場分析...
   這可能需要幾分鐘,請稍候...

   ⚠️  連線錯誤: API Error: Connection error.
   ⏳ 重試 2/3 (等待 10秒...)
   ⚠️  連線錯誤: API Error: Connection error.
   ⏳ 重試 3/3 (等待 20秒...)
   ⚠️  連線錯誤: API Error: Connection error.

   ❌ 市場分析失敗 (已重試 3 次)
```

## 效益

### 解決的問題
1. **暫時性網路問題** - 短暫的網路中斷不會導致整個流程失敗
2. **API 服務波動** - Anthropic API 暫時不可用時會自動重試
3. **連線超時** - 給予 API 更多時間回應

### 提升的可靠性
- 單次失敗率：假設 5%
- 連續 3 次失敗率：0.05³ = 0.000125 (0.0125%)
- **可靠性提升**: 從 95% → 99.99%

## 修改重試參數

如需調整重試參數，編輯 `run_daily_analysis_claude_cli.sh` 的 `claude_with_retry` 函數：

```bash
claude_with_retry() {
    local prompt_file="$1"
    local output_file="$2"
    local analysis_name="$3"
    local max_retries=3          # 修改此處：最大重試次數
    local retry_delay=10         # 修改此處：初始等待時間（秒）
    local attempt=1

    # ...
}
```

## 監控與除錯

### 查看重試記錄
```bash
# launchd 日誌
grep "重試\|連線錯誤" ~/logs/ultimate-analysis.log

# 手動執行日誌
grep "重試\|連線錯誤" ~/logs/manual-run-*.log
```

### 測試重試機制
```bash
# 暫時修改 max_retries 為 1，模擬失敗場景
# 或者在網路不穩定時觀察重試行為
tail -f ~/logs/ultimate-analysis.log
```

## 注意事項

1. **執行時間增加** - 如果需要重試，整體執行時間會增加（最多額外 30 秒）
2. **API 配額** - 重試會消耗額外的 API 調用次數
3. **不會無限重試** - 最多 3 次後會失敗退出，避免無謂的資源消耗

## 相關檔案

- 主要實作：`src/daily-analysis-system/scripts/analysis/run_daily_analysis_claude_cli.sh`
- 工作流程：`utils/run_daily_workflow.sh`
- 自動化設定：`~/Library/LaunchAgents/com.ultimate-analysis.daily.plist`

---

**實作日期**: 2025-12-17
**版本**: v3.1
