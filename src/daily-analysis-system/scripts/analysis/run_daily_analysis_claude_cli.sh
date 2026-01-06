#!/usr/bin/env bash
###############################################################################
# The Ultimate Analysis System - Daily Analysis V3
#
# 功能說明:
#   生成三類獨立的分析報告,分析順序經過優化以提供最全面的洞察
#
# 分析流程:
#   Step 1: 市場分析 (market-analysis-{date}.md)
#           → 了解全球市場環境、趨勢、重要新聞
#
#   Step 2: 個股分析 (stock-{symbol}-{date}.md)
#           → 基於市場環境,深入分析個別股票(自動跳過指數)
#           → 標註新聞來源、評估影響、提供操作建議
#
#   Step 3: 持倉分析 (holdings-analysis-{date}.md)
#           → 綜合市場和個股分析,評估投資組合
#           → 聚焦:持股狀況、選擇權管理、績效追蹤
#
# 依賴:
#   - claude CLI: npm install -g @anthropic-ai/claude-cli
#   - 必須先登入: claude login
#
# 使用方式:
#   ./scripts/analysis/run_daily_analysis_claude_cli.sh
#
# 版本: v3.0
###############################################################################

set -e  # 遇到錯誤立即退出

###############################################################################
# 環境變數設定
###############################################################################

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日期和時間
TODAY=$(date +"%Y-%m-%d")
YEAR=$(date +"%Y")

# 路徑定義
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
REPO_ROOT="$(cd "${PROJECT_ROOT}/../.." && pwd)"
OUTPUT_DIR="${PROJECT_ROOT}/output/market-data/${YEAR}"
DAILY_DIR="${OUTPUT_DIR}/Daily"
NEWS_DIR="${OUTPUT_DIR}/News"
REPORTS_DIR="${PROJECT_ROOT}/reports/markdown"
CONFIG_DIR="${REPO_ROOT}/config"

# 輸入檔案
GLOBAL_INDICES="${DAILY_DIR}/global-indices-${TODAY}.md"
PRICES="${DAILY_DIR}/holdings-prices-${TODAY}.md"
HOLDINGS_CONFIG="${CONFIG_DIR}/holdings.yaml"
PORTFOLIO_SUMMARY="${CONFIG_DIR}/portfolio_summary.yaml"
PORTFOLIO_HOLDINGS="${REPO_ROOT}/src/financial-analysis-system/portfolio/${YEAR}/holdings.md"

# 輸出檔案
MARKET_ANALYSIS_OUTPUT="${REPORTS_DIR}/market-analysis-${TODAY}.md"
HOLDINGS_ANALYSIS_OUTPUT="${REPORTS_DIR}/holdings-analysis-${TODAY}.md"

# 臨時檔案
MARKET_PROMPT_FILE="/tmp/market-analysis-prompt-${TODAY}.txt"
HOLDINGS_PROMPT_FILE="/tmp/holdings-analysis-prompt-${TODAY}.txt"

###############################################################################
# 工具函數
###############################################################################

# 顯示程式開頭資訊
print_header() {
    echo -e "${BLUE}============================================================${NC}"
    echo -e "${BLUE}📊 The Ultimate Analysis System - 每日多報告分析 v3.0${NC}"
    echo -e "${BLUE}============================================================${NC}"
    echo ""
    echo -e "${GREEN}📅 分析日期: ${TODAY}${NC}"
    echo ""
    echo -e "${YELLOW}📋 分析流程:${NC}"
    echo -e "${GREEN}  Step 1: 市場分析 → 了解全球市場環境${NC}"
    echo -e "${GREEN}  Step 2: 個股分析 → 深入分析個別股票${NC}"
    echo -e "${GREEN}  Step 3: 持倉分析 → 評估投資組合表現${NC}"
    echo ""
}

# 檢查系統依賴
check_dependencies() {
    echo -e "${BLUE}🔍 檢查系統依賴...${NC}"

    # 檢查 claude CLI
    CLAUDE_BIN=""
    if command -v claude &> /dev/null; then
        CLAUDE_BIN="claude"
    elif [[ -x "${HOME}/.local/bin/claude" ]]; then
        CLAUDE_BIN="${HOME}/.local/bin/claude"
    elif [[ -x "/usr/local/bin/claude" ]]; then
        CLAUDE_BIN="/usr/local/bin/claude"
    else
        echo -e "${RED}❌ 錯誤: 未安裝 claude CLI${NC}"
        echo -e "${YELLOW}   安裝方式: npm install -g @anthropic-ai/claude-cli${NC}"
        echo -e "${YELLOW}   登入方式: claude login${NC}"
        exit 1
    fi

    echo -e "${GREEN}   ✅ Claude CLI 已安裝 (${CLAUDE_BIN})${NC}"
    echo ""
}

# 檢查資料檔案完整性
check_data_files() {
    echo -e "${BLUE}🔍 檢查資料檔案...${NC}"

    local missing_files=()

    if [[ ! -f "${GLOBAL_INDICES}" ]]; then
        missing_files+=("全球指數: ${GLOBAL_INDICES}")
    fi

    if [[ ! -f "${PRICES}" ]]; then
        missing_files+=("持倉價格: ${PRICES}")
    fi

    if [[ ${#missing_files[@]} -gt 0 ]]; then
        echo -e "${YELLOW}⚠️  警告: 以下資料檔案不存在:${NC}"
        for file in "${missing_files[@]}"; do
            echo -e "${YELLOW}     - ${file}${NC}"
        done
        echo ""
        echo -e "${YELLOW}   請先執行: make fetch-all${NC}"
        exit 1
    fi

    echo -e "${GREEN}   ✅ 資料檔案完整${NC}"
    echo ""
}

# 收集今日新聞檔案
collect_news_files() {
    local news_files=($(find "${NEWS_DIR}" -name "*-${TODAY}.md" 2>/dev/null || true))
    printf '%s\n' "${news_files[@]}"
}

# 從 holdings.yaml 中提取啟用的股票代碼
get_enabled_holdings() {
    if [[ ! -f "${HOLDINGS_CONFIG}" ]]; then
        echo "" >&2
        return 1
    fi

    # 提取所有 symbol 且 enabled: true 和 fetch_news: true 的股票
    # 策略：遇到 symbol 時記錄，遇到股票名稱行時檢查並輸出
    awk '
        # 遇到股票名稱行（4個空格縮排，以冒號結尾）
        /^    [^ ].*:$/ {
            # 如果上一個股票符合條件，輸出
            if (symbol && fetch_news && enabled) {
                print symbol
            }
            # 重置變數
            symbol=""; fetch_news=0; enabled=0
        }
        # 遇到 symbol 行
        /symbol:/ {
            gsub(/"/, "", $2);
            symbol=$2
        }
        # 遇到 fetch_news: true
        /fetch_news: true/ {
            fetch_news=1
        }
        # 遇到 enabled: true
        /enabled: true/ {
            enabled=1
        }
        # 文件結尾處理最後一個股票
        END {
            if (symbol && fetch_news && enabled) {
                print symbol
            }
        }
    ' "${HOLDINGS_CONFIG}" | sort -u
}

# 清理臨時檔案
cleanup() {
    rm -f "${MARKET_PROMPT_FILE}" "${HOLDINGS_PROMPT_FILE}"
}

# Claude API 重試機制
# 參數: $1=prompt_file, $2=output_file, $3=analysis_name
claude_with_retry() {
    local prompt_file="$1"
    local output_file="$2"
    local analysis_name="$3"
    local max_retries=3
    local retry_delay=10
    local attempt=1

    while [ $attempt -le $max_retries ]; do
        if [ $attempt -gt 1 ]; then
            echo -e "${YELLOW}   ⏳ 重試 $attempt/$max_retries (等待 ${retry_delay}秒...)${NC}"
            sleep $retry_delay
        fi

        if cat "${prompt_file}" | "${CLAUDE_BIN}" > "${output_file}" 2>&1; then
            # 檢查輸出文件是否有實際內容 (>100 bytes)
            if [ -s "${output_file}" ] && [ $(wc -c < "${output_file}") -gt 100 ]; then
                return 0
            else
                echo -e "${YELLOW}   ⚠️  輸出文件過小，可能失敗${NC}" >&2
            fi
        fi

        # 檢查是否有連線錯誤
        if grep -q "Connection error\|API Error" "${output_file}" 2>/dev/null; then
            echo -e "${YELLOW}   ⚠️  連線錯誤: $(head -1 "${output_file}")${NC}" >&2
        fi

        attempt=$((attempt + 1))
        retry_delay=$((retry_delay * 2))  # 指數退避
    done

    echo -e "${RED}   ❌ ${analysis_name}失敗 (已重試 $max_retries 次)${NC}" >&2
    return 1
}

###############################################################################
# Step 2: 個股分析報告生成
###############################################################################

# 檢查新聞是否為近期 (今天或昨天)
check_recent_news() {
    local news_file="$1"

    # 獲取今天和昨天的日期 (格式: Dec 09)
    # 使用 LC_ALL=C 強制英文月份格式,避免語言環境差異
    local today=$(LC_ALL=C date +"%b %d")
    local yesterday=$(LC_ALL=C date -d "1 day ago" +"%b %d" 2>/dev/null || LC_ALL=C date -v-1d +"%b %d" 2>/dev/null)

    # 檢查新聞檔案中是否有近期新聞 (發布時間在今天或昨天)
    if grep -E "發布時間.*(${today}|${yesterday})" "${news_file}" > /dev/null 2>&1; then
        return 0  # 有近期新聞
    else
        return 1  # 沒有近期新聞
    fi
}

# 生成個股分析檔案
generate_stock_analysis_files() {
    echo -e "${BLUE}📊 生成個股分析檔案...${NC}"
    echo -e "${YELLOW}   (僅分析 holdings.yaml 中啟用且有今天或昨天新聞的持股)${NC}"
    echo ""

    # 獲取啟用的持股列表
    local enabled_holdings
    enabled_holdings=()
    while IFS= read -r symbol; do
        [[ -n "$symbol" ]] && enabled_holdings+=("$symbol")
    done < <(get_enabled_holdings)

    if [[ ${#enabled_holdings[@]} -eq 0 ]]; then
        echo -e "${YELLOW}   ⚠️  警告: holdings.yaml 中沒有啟用的持股${NC}"
        echo ""
        return
    fi

    echo -e "${GREEN}   📋 持股清單: ${enabled_holdings[@]}${NC}"
    echo ""

    local count=0
    local skipped_no_news=0
    local skipped_old_news=0
    local skipped_not_holding=0

    # 遍歷啟用的持股
    for symbol in "${enabled_holdings[@]}"; do
        local news_file="${NEWS_DIR}/${symbol}-${TODAY}.md"

        # 檢查新聞檔案是否存在
        if [[ ! -f "${news_file}" ]]; then
            echo -e "${YELLOW}   ⏭️  跳過 ${symbol} (無新聞檔案)${NC}"
            skipped_no_news=$((skipped_no_news + 1))
            continue
        fi

        # 檢查是否有近期新聞
        if ! check_recent_news "${news_file}"; then
            echo -e "${YELLOW}   ⏭️  跳過 ${symbol} (無今天或昨天的新聞)${NC}"
            skipped_old_news=$((skipped_old_news + 1))
            continue
        fi

        local stock_analysis_file="${REPORTS_DIR}/stock-${symbol}-${TODAY}.md"
        local stock_prompt_file="/tmp/stock-${symbol}-prompt-${TODAY}.txt"

        # 讀取新聞內容
        local news_content
        news_content=$(<"${news_file}")

        # 讀取持倉價格資訊
        local price_info=""
        if [[ -f "${PRICES}" ]] && grep -q "${symbol}" "${PRICES}" 2>/dev/null; then
            price_info=$(grep -A 10 "## ${symbol}" "${PRICES}" 2>/dev/null || echo "")
        fi

        # 生成個股分析 prompt
        cat > "${stock_prompt_file}" <<EOF
你是一位專業的個股分析師,擅長分析個別股票的新聞、價格走勢和投資價值。

## 📋 分析任務

請針對 **${symbol}** 這檔股票,基於**今天或昨天的新聞**和價格資訊,生成一份**個股分析報告**。

### 核心要求:
1. **新聞摘要**: 總結重要新聞,並標註新聞來源和發布時間
2. **影響分析**: 評估新聞對股價的潛在影響 (正面/負面/中性)
3. **價格走勢**: 分析當前價格表現(收盤價、漲跌幅)

### 重要提示:
- **僅關注今天或昨天的新聞**,舊新聞可以忽略
- 重點分析最新發展對股價的影響
- 客觀分析,不需要提供投資建議

### 報告風格:
- 簡潔明瞭,重點突出
- 客觀描述新聞和價格變化

---

## 📊 ${symbol} 今日資料

### 股票新聞
\`\`\`markdown
${news_content}
\`\`\`

$(if [[ -n "${price_info}" ]]; then
echo "### 價格資訊
\`\`\`markdown
${price_info}
\`\`\`"
fi)

---

## 📄 報告結構

請按照以下結構生成報告:

# 📊 ${symbol} 個股分析 - ${TODAY}

> **報告生成時間**: $(date +"%Y-%m-%d %H:%M UTC")
> **分析引擎**: The Ultimate Analysis System v2.1
> **股票代碼**: ${symbol}

---

## 📰 新聞摘要

### 今日重點新聞

[針對每則重要新聞,按以下格式呈現:]

#### 📌 新聞標題
- **來源**: [新聞來源]
- **發布時間**: [時間]
- **影響評估**: 🟢 正面 / 🟡 中性 / 🔴 負面
- **摘要**: [簡述新聞內容]
- **關鍵要點**:
  - 要點1
  - 要點2

[重複以上格式分析其他新聞]

---

## 📈 綜合影響分析

### 新聞面影響

**整體情緒**: 🟢 正面 / 🟡 中性 / 🔴 負面

**關鍵驅動因素**:
1. [因素1]: 簡要說明
2. [因素2]: 簡要說明

$(if [[ -n "${price_info}" ]]; then
echo "### 價格面分析

**當前表現**:
- 收盤價: \\\$XX.XX
- 漲跌幅: ±X.XX%

**價格與新聞關聯**:
[分析價格走勢是否反映新聞面的變化]"
fi)

---

**分析引擎**: Claude (Sonnet 4.5)
**報告版本**: v2.1

---

請直接開始生成完整的個股分析報告,從標題開始,不要有任何前置說明或詢問。
EOF

        # 調用 Claude 生成個股分析
        echo -e "${YELLOW}   ⏳ 分析 ${symbol}...${NC}"
        if claude_with_retry "${stock_prompt_file}" "${stock_analysis_file}" "${symbol}個股分析"; then
            echo -e "${GREEN}   ✅ ${symbol} 分析完成${NC}"
            count=$((count + 1))
        else
            echo -e "${RED}   ❌ ${symbol} 分析失敗${NC}"
        fi

        # 清理臨時檔案
        rm -f "${stock_prompt_file}"
    done

    echo ""
    echo -e "${GREEN}   ✅ 個股分析完成!${NC}"
    echo -e "${GREEN}      生成: ${count} 檔${NC}"

    local total_skipped=$((skipped_no_news + skipped_old_news))
    if [[ ${total_skipped} -gt 0 ]]; then
        echo -e "${YELLOW}      跳過: ${total_skipped} 檔${NC}"
        if [[ ${skipped_no_news} -gt 0 ]]; then
            echo -e "${YELLOW}        - 無新聞檔案: ${skipped_no_news} 檔${NC}"
        fi
        if [[ ${skipped_old_news} -gt 0 ]]; then
            echo -e "${YELLOW}        - 無近期新聞: ${skipped_old_news} 檔${NC}"
        fi
    fi
    echo ""
}

###############################################################################
# Step 1: 市場分析報告生成
###############################################################################

# 生成市場分析 Prompt
generate_market_analysis_prompt() {
    echo -e "${BLUE}📝 生成市場分析 Prompt...${NC}"

    # 讀取全球指數數據
    local indices_data
    indices_data=$(<"${GLOBAL_INDICES}")

    # 收集所有新聞並整合
    local news_data=""
    local news_files
    news_files=()
    while IFS= read -r line; do
        news_files+=("$line")
    done < <(collect_news_files)

    for news_file in "${news_files[@]}"; do
        if [[ -f "${news_file}" ]]; then
            local symbol
            symbol=$(basename "${news_file}" | sed "s/-${TODAY}.md//")
            local news_content
            news_content=$(<"${news_file}")
            news_data="${news_data}

### ${symbol} 新聞
${news_content}"
        fi
    done

    local news_count=${#news_files[@]}

    # 生成市場分析 Prompt
    cat > "${MARKET_PROMPT_FILE}" <<'EOF'
你是一位專業的全球市場分析師,擅長解讀市場數據和新聞,提供深度市場洞察。

## 📋 分析任務

請根據以下今日市場數據,生成一份**全球市場情報分析報告**。

### 核心要求:
1. **市場趨勢分析**: 識別全球市場的主要趨勢和驅動因素
2. **新聞影響評估**: 深度解讀重要新聞對市場的潛在影響
3. **產業輪動分析**: 分析資金流向和產業表現
4. **風險與機會**: 識別當前市場風險和投資機會
5. **後市展望**: 提供未來一週的市場展望

### 報告風格:
- 專業但易懂
- 數據驅動,洞察為先
- 結構清晰,重點突出
- 避免模糊建議,提供具體方向

---

## 📊 今日市場數據

### 全球市場指數
```markdown
EOF

    cat >> "${MARKET_PROMPT_FILE}" <<EOF
${indices_data}
\`\`\`

### 市場新聞 (${news_count} 則)
\`\`\`markdown
${news_data}
\`\`\`

---

## 📄 報告結構

請按照以下結構生成報告:

# 📈 全球市場分析 - ${TODAY}

> **報告生成時間**: $(date +"%Y-%m-%d %H:%M UTC")
> **分析引擎**: The Ultimate Analysis System v2.1
> **報告類型**: 全球市場情報

---

## 📊 執行摘要

### 市場概況
[用 2-3 段文字總結今日全球市場表現:]
- 主要市場趨勢 (美股、亞股、歐股)
- 關鍵驅動因素
- 市場情緒指標 (VIX)
- 重要事件或數據

### 關鍵數據

| 指標 | 數值 | 變化 | 狀態 |
|------|------|------|------|
| S&P 500 | X,XXX.XX | +X.XX% | 🟢/🔴 描述 |
| Nasdaq | XX,XXX.XX | +X.XX% | 🟢/🔴 描述 |
| VIX | XX.XX | +X.XX% | 🟢/🔴 描述 |
| 台股加權 | XX,XXX.XX | +X.XX% | 🟢/🔴 描述 |
| 黃金 | \\\$X,XXX | +X.XX% | 🟢/🔴 描述 |

### 市場情緒評估

| 類別 | 評分 (1-10) | 說明 |
|------|-------------|------|
| 整體市場情緒 | X | 簡短說明 |
| 科技股情緒 | X | 簡短說明 |
| 波動性風險 | X | 簡短說明 |

---

## 🌍 全球市場深度分析

### 美國市場 🇺🇸

**主要指數表現**

| 指數 | 收盤價 | 漲跌幅 | 技術狀態 |
|------|--------|--------|----------|
| S&P 500 | X,XXX.XX | +X.XX% | 描述 |
| Nasdaq | XX,XXX.XX | +X.XX% | 描述 |
| Dow Jones | XX,XXX.XX | +X.XX% | 描述 |

**市場分析**:
[深入分析美國市場:]
- 主要驅動因素
- 產業輪動情況
- 技術面關鍵水平
- 後市展望

### 亞洲市場 🌏

**主要市場表現**

| 市場 | 指數 | 收盤價 | 漲跌幅 |
|------|------|--------|--------|
| 🇹🇼 台灣 | 加權指數 | XX,XXX.XX | +X.XX% |
| 🇯🇵 日本 | 日經225 | XX,XXX.XX | +X.XX% |
| 🇰🇷 韓國 | KOSPI | X,XXX.XX | +X.XX% |

**市場分析**:
[分析亞洲市場趨勢]

### 歐洲市場 🇪🇺

**市場分析**:
[簡要分析歐洲市場]

---

## 📰 重要新聞解讀

[按主題或產業分類,深入解讀影響市場的重要新聞。每則新聞必須標註來源和發布時間:]

### 科技產業

#### 📌 新聞標題
- **來源**: [新聞來源,如 Yahoo Finance、Barrons.com 等]
- **發布時間**: [時間]
- **影響評估**: 🟢 正面 / 🟡 中性 / 🔴 負面
- **深度分析**: [分析新聞內容、市場影響、投資啟示]

### 其他產業

#### 📌 新聞標題
- **來源**: [新聞來源]
- **發布時間**: [時間]
- **影響評估**: 🟢 正面 / 🟡 中性 / 🔴 負面
- **深度分析**: [同上]

---

## 🏭 產業輪動分析

### 強勢產業

| 產業 | 表現 | 驅動因素 |
|------|------|----------|
| 產業1 | +X.XX% | 簡述 |
| 產業2 | +X.XX% | 簡述 |

### 弱勢產業

| 產業 | 表現 | 原因 |
|------|------|------|
| 產業1 | -X.XX% | 簡述 |

**分析**: [深入分析產業輪動背後的邏輯]

---

## ⚠️ 風險與機會

### 市場風險

1. **風險1**: 詳細說明
2. **風險2**: 詳細說明
3. **風險3**: 詳細說明

### 投資機會

1. **機會1**: 詳細說明
2. **機會2**: 詳細說明

### VIX 恐慌指數分析

- **當前值**: XX.XX
- **變化**: ±X.XX%
- **解讀**: [分析市場情緒和波動性預期]

---

## 🔮 後市展望

### 未來一週關鍵事件

**經濟數據**:
- 日期: 數據名稱 - 預期影響
- 日期: 數據名稱 - 預期影響

**企業財報**:
- 日期: 公司名稱 - 關注重點

**其他重要事件**:
- 事件描述

### 情境分析

#### 樂觀情境 (機率: XX%)
[條件、預期影響、市場反應]

#### 基準情境 (機率: XX%)
[條件、預期影響、市場反應]

#### 悲觀情境 (機率: XX%)
[條件、預期影響、市場反應]

---

## 💡 投資策略建議

### 短期觀點 (1-2週)

**市場看法**: [總結]

**策略建議**:
1. 建議1
2. 建議2

### 中期觀點 (1-3個月)

**市場看法**: [總結]

**策略建議**:
1. 建議1
2. 建議2

---

## ⚠️ 免責聲明

本報告僅供參考,不構成投資建議。投資有風險,請根據自身情況做出獨立決策。

---

**分析引擎**: Claude (Sonnet 4.5)
**報告版本**: v2.1

---

請直接開始生成完整的市場分析報告,從標題開始,不要有任何前置說明或詢問。
EOF

    echo -e "${GREEN}   ✅ 市場分析 Prompt 已生成${NC}"
    echo ""
}

# 執行市場分析
run_market_analysis() {
    echo -e "${BLUE}🧠 調用 Claude 進行市場分析...${NC}"
    echo -e "${YELLOW}   這可能需要幾分鐘,請稍候...${NC}"
    echo ""

    mkdir -p "${REPORTS_DIR}"

    if claude_with_retry "${MARKET_PROMPT_FILE}" "${MARKET_ANALYSIS_OUTPUT}" "市場分析"; then
        echo -e "${GREEN}   ✅ 市場分析完成!${NC}"
        echo -e "${GREEN}   📄 ${MARKET_ANALYSIS_OUTPUT}${NC}"
        echo ""
    else
        echo -e "${RED}   ❌ 市場分析失敗${NC}"
        exit 1
    fi
}

###############################################################################
# Step 3: 持倉分析報告生成
###############################################################################

# 生成持倉分析 Prompt
generate_holdings_analysis_prompt() {
    echo -e "${BLUE}📝 生成持倉分析 Prompt...${NC}"

    # 讀取持倉價格數據
    local prices_data
    prices_data=$(<"${PRICES}")

    # 讀取持倉配置數據
    local holdings_config=""
    if [[ -f "${HOLDINGS_CONFIG}" ]]; then
        holdings_config=$(<"${HOLDINGS_CONFIG}")
    fi

    # 讀取投資組合績效快照數據
    local portfolio_summary=""
    if [[ -f "${PORTFOLIO_SUMMARY}" ]]; then
        portfolio_summary=$(<"${PORTFOLIO_SUMMARY}")
    fi

    # 讀取投資組合完整資訊
    local portfolio_data=""
    if [[ -f "${PORTFOLIO_HOLDINGS}" ]]; then
        portfolio_data=$(<"${PORTFOLIO_HOLDINGS}")
    fi

    # 生成持倉分析 Prompt
    cat > "${HOLDINGS_PROMPT_FILE}" <<'EOF'
你是一位專業的投資組合分析師,擅長評估持倉表現和風險管理。

## 📋 分析任務

請根據以下投資組合數據,生成一份**簡潔的持倉分析報告**。

### 核心要求(聚焦三大重點):
1. **持股狀況**: 分析每檔股票的表現、損益、倉位
2. **選擇權管理**: 評估選擇權到期風險和處理建議
3. **績效追蹤**: 整體績效表現和關鍵指標

### 報告風格:
- 簡潔精煉,重點突出
- 數據驅動,客觀分析
- 提供可操作的建議

---

## 📊 投資組合數據

### 投資組合完整資訊
```markdown
EOF

    cat >> "${HOLDINGS_PROMPT_FILE}" <<EOF
${portfolio_data}
\`\`\`

### 資產績效快照
\`\`\`yaml
${portfolio_summary}
\`\`\`

### 持倉配置詳情
\`\`\`yaml
${holdings_config}
\`\`\`

### 今日持倉價格
\`\`\`markdown
${prices_data}
\`\`\`

### 觀察清單新聞 (如果有)
\`\`\`markdown
EOF

    # 收集觀察清單的新聞
    local watchlist_news=""
    if [[ -f "${HOLDINGS_CONFIG}" ]]; then
        # 從 holdings.yaml 提取觀察清單的股票代碼
        local watchlist_symbols
        watchlist_symbols=($(awk '
            /^watchlist:/ { in_watchlist=1; next }
            in_watchlist && /^[^ ]/ { in_watchlist=0 }
            in_watchlist && /symbol:/ {
                gsub(/"/, "", $2);
                print $2
            }
        ' "${HOLDINGS_CONFIG}" 2>/dev/null || true))

        for symbol in "${watchlist_symbols[@]}"; do
            local watchlist_news_file="${NEWS_DIR}/${symbol}-${TODAY}.md"
            if [[ -f "${watchlist_news_file}" ]]; then
                local news_content
                news_content=$(<"${watchlist_news_file}")
                watchlist_news="${watchlist_news}

### ${symbol} 觀察清單新聞
${news_content}
"
            fi
        done
    fi

    cat >> "${HOLDINGS_PROMPT_FILE}" <<EOF
${watchlist_news}
\`\`\`

---

## 📄 報告結構

請按照以下結構生成報告:

# 💼 投資組合分析 - ${TODAY}

> **報告生成時間**: $(date +"%Y-%m-%d %H:%M UTC")
> **分析引擎**: The Ultimate Analysis System v2.1
> **報告類型**: 持倉分析

---

## 📊 組合概況

| 項目 | 數值 | 狀態 |
|------|------|------|
| 總資產淨值 | \\\$XXX,XXX.XX | - |
| 股票市值 | \\\$XXX,XXX.XX (XX.X%) | 🟢/🟡/🔴 |
| 現金餘額 | \\\$XX,XXX.XX (XX.X%) | 🟢/🟡/🔴 |
| 未實現損益 | ±\\\$XX,XXX (±X.X%) | 🟢/🔴 |
| 今日變化 | ±X.XX% | 🟢/🔴 |

**關鍵提示**: [1-2句話總結今日重點]

---

## 🎯 選擇權部位

[依到期日列出所有選擇權部位,僅顯示關鍵資訊:]

| 到期日 | 標的 | 類型 | 數量 | 行權價 | 當前價 | 狀態 | 處理建議 |
|--------|------|------|------|--------|--------|------|----------|
| 12/XX | TICKER | Call/Put | -X | \\\$XX.XX | \\\$XX.XX | 價內/價外 | [簡述建議] |

**重點關注**:
- [列出需要立即處理的選擇權部位]
- [列出風險較高的部位]

---

## 📈 持股狀況

[列出所有持股,按倉位大小或今日表現排序:]

| 股票 | 持股 | 成本 | 現價 | 損益 | 倉位 | 今日 | 選擇權 | 建議 |
|------|------|------|------|------|------|------|--------|------|
| TICKER | XXX | \\\$XX.XX | \\\$XX.XX | ±XX.X% | X.X% | ±X.X% | 有/無 | 持有/加碼/減碼 |

**重點關注**:
[針對以下股票進行簡要分析:]
- 今日漲跌幅 > 3%
- 倉位 > 8%
- 損益 > ±15%
- 有緊急選擇權到期

#### 📊 TICKER
- **狀態**: [1-2句話說明當前狀態]
- **建議**: [具體操作建議]
- **風險**: [關鍵風險點]

[僅分析需要關注的重點持股]

---

## 📊 績效追蹤

### 本月績效（截至今日）

| 指標 | 數值 | 評估 |
|------|------|------|
| 月度報酬率 | ±X.XX% | 🟢/🔴 |
| vs S&P 500 | ±X.XX% | 🟢/🔴 |
| 最佳持股 | TICKER (+XX.X%) | - |
| 最差持股 | TICKER (-XX.X%) | - |
| 勝率 | XX% | - |

### 年度績效（截至今日）

| 指標 | 數值 |
|------|------|
| 年度報酬率 | ±X.XX% |
| vs S&P 500 | ±X.XX% |

---

## 👀 觀察清單分析

[如果有觀察清單股票且有新聞,分析這些非持股的標的:]

### 📊 觀察標的概況

| 股票 | 當前價 | 今日漲跌 | 新聞情緒 | 評估 |
|------|--------|----------|---------|------|
| TICKER | \\\$XX.XX | ±X.XX% | 🟢/🟡/🔴 | 簡述 |

### 重點觀察標的

[針對有重要新聞或價格異動的觀察標的進行分析:]

#### 📌 TICKER
- **最新動態**: [總結最新新聞]
- **價格表現**: [價格走勢分析]
- **投資價值**: [是否值得考慮建倉]
- **風險因素**: [主要風險點]

[如果沒有觀察清單或沒有相關新聞,則省略此區塊]

---

## ⚠️ 免責聲明

本報告僅供參考,不構成投資建議。投資有風險,請根據自身情況做出獨立決策。

---

**分析引擎**: Claude (Sonnet 4.5)
**報告版本**: v2.1

---

請直接開始生成完整的持倉分析報告,從標題開始,不要有任何前置說明或詢問。
EOF

    echo -e "${GREEN}   ✅ 持倉分析 Prompt 已生成${NC}"
    echo ""
}

# 執行持倉分析
run_holdings_analysis() {
    echo -e "${BLUE}🧠 調用 Claude 進行持倉分析...${NC}"
    echo -e "${YELLOW}   這可能需要幾分鐘,請稍候...${NC}"
    echo ""

    mkdir -p "${REPORTS_DIR}"

    if claude_with_retry "${HOLDINGS_PROMPT_FILE}" "${HOLDINGS_ANALYSIS_OUTPUT}" "持倉分析"; then
        echo -e "${GREEN}   ✅ 持倉分析完成!${NC}"
        echo -e "${GREEN}   📄 ${HOLDINGS_ANALYSIS_OUTPUT}${NC}"
        echo ""
    else
        echo -e "${RED}   ❌ 持倉分析失敗${NC}"
        exit 1
    fi
}

###############################################################################
# 結果展示
###############################################################################

# 顯示所有生成的報告
show_results() {
    echo -e "${BLUE}============================================================${NC}"
    echo -e "${GREEN}✅ 所有分析報告已生成完畢!${NC}"
    echo -e "${BLUE}============================================================${NC}"
    echo ""

    echo -e "${YELLOW}📊 生成報告摘要:${NC}"
    echo ""

    echo -e "${GREEN}📈 市場分析報告:${NC}"
    echo -e "${GREEN}   ${MARKET_ANALYSIS_OUTPUT}${NC}"
    echo ""

    # 列出所有個股分析檔案
    local stock_files
    stock_files=($(find "${REPORTS_DIR}" -name "stock-*-${TODAY}.md" 2>/dev/null || true))
    if [[ ${#stock_files[@]} -gt 0 ]]; then
        echo -e "${GREEN}📊 個股分析報告 (${#stock_files[@]} 檔):${NC}"
        for stock_file in "${stock_files[@]}"; do
            local filename=$(basename "${stock_file}")
            echo -e "${GREEN}   ${filename}${NC}"
        done
        echo ""
    fi

    echo -e "${GREEN}💼 持倉分析報告:${NC}"
    echo -e "${GREEN}   ${HOLDINGS_ANALYSIS_OUTPUT}${NC}"
    echo ""

    echo -e "${BLUE}------------------------------------------------------------${NC}"
    echo -e "${YELLOW}📋 快速查看報告:${NC}"
    echo ""
    echo -e "${GREEN}   # 市場分析${NC}"
    echo -e "   cat ${MARKET_ANALYSIS_OUTPUT}"
    echo ""
    echo -e "${GREEN}   # 持倉分析${NC}"
    echo -e "   cat ${HOLDINGS_ANALYSIS_OUTPUT}"
    echo ""
    if [[ ${#stock_files[@]} -gt 0 ]]; then
        echo -e "${GREEN}   # 個股分析${NC}"
        echo -e "   ls ${REPORTS_DIR}/stock-*-${TODAY}.md"
        echo ""
    fi
    echo -e "${BLUE}------------------------------------------------------------${NC}"
    echo ""
}

###############################################################################
# 主程式
###############################################################################

main() {
    # 顯示標題
    print_header

    # 系統檢查
    check_dependencies
    check_data_files

    # Step 1: 市場分析
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}📊 Step 1/3: 市場分析 - 了解全球市場環境${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    generate_market_analysis_prompt
    run_market_analysis

    # Step 2: 個股分析
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}📈 Step 2/3: 個股分析 - 深入分析個別股票${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    generate_stock_analysis_files

    # Step 3: 持倉分析
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}💼 Step 3/3: 持倉分析 - 評估投資組合表現${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    generate_holdings_analysis_prompt
    run_holdings_analysis

    # 顯示結果
    show_results

    # 清理
    cleanup

    # 完成
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}✅ 每日分析完成! 共生成 3 類報告${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

###############################################################################
# 執行主程式
###############################################################################

main "$@"
