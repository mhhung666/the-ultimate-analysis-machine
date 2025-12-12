#!/usr/bin/env bash
###############################################################################
# The Ultimate Analysis System - Weekly Analysis (Claude CLI)
#
# 生成一份「週度市場與持倉週報」,匯總最近 5 個交易日的每日報告:
# 1. 市場分析週報: 總結指數走勢、產業輪動、重大新聞
# 2. 持倉分析週報: 回顧組合績效、選擇權風險、下週行動清單
#
# 依賴:
#   - claude CLI (npm install -g @anthropic-ai/claude-cli)
#   - 已登入 Claude CLI (claude login)
#
# 使用方式:
#   ./scripts/analysis/run_weekly_analysis_claude_cli.sh
#   # 如需指定時間後綴,可用: TIME_SUFFIX=2300 ./run_weekly_analysis_claude_cli.sh
###############################################################################

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 參數設定
MAX_REPORTS=5
MIN_REPORTS=3
WEEK_LABEL=$(date +"%G-W%V")

# 支援時間後綴 (可選)
if [ -z "${TIME_SUFFIX:-}" ]; then
    TIME_SUFFIX=$(date +"%H%M")
fi

# 路徑
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
REPORTS_MARKDOWN_DIR="${PROJECT_ROOT}/reports/markdown"
REPORTS_ARCHIVE_DIR="${PROJECT_ROOT}/reports/archive"
WEEKLY_OUTPUT_DIR="${PROJECT_ROOT}/reports/weekly"

# 檔案路徑
WEEKLY_OUTPUT="${WEEKLY_OUTPUT_DIR}/weekly-analysis-${WEEK_LABEL}-${TIME_SUFFIX}.md"
WEEKLY_PROMPT_FILE="/tmp/weekly-analysis-prompt-${WEEK_LABEL}-${TIME_SUFFIX}.txt"

# 狀態
CLAUDE_BIN=""
MARKET_REPORTS=()
HOLDINGS_REPORTS=()
WEEK_START_DATE=""
WEEK_END_DATE=""

###############################################################################
# 函數定義
###############################################################################

print_header() {
    echo -e "${BLUE}============================================================${NC}"
    echo -e "${BLUE}📊 The Ultimate Analysis System - 週度報告生成${NC}"
    echo -e "${BLUE}============================================================${NC}"
    echo ""
    echo -e "${GREEN}📅 週次: ${WEEK_LABEL}${NC}"
    echo -e "${GREEN}🕒 時間後綴: ${TIME_SUFFIX}${NC}"
    echo ""
}

check_dependencies() {
    echo -e "${BLUE}🔍 檢查依賴...${NC}"

    if command -v claude &> /dev/null; then
        CLAUDE_BIN="claude"
    elif [[ -x "${HOME}/.local/bin/claude" ]]; then
        CLAUDE_BIN="${HOME}/.local/bin/claude"
    elif [[ -x "/usr/local/bin/claude" ]]; then
        CLAUDE_BIN="/usr/local/bin/claude"
    else
        echo -e "${RED}❌ 錯誤: 未安裝 claude CLI${NC}"
        echo -e "${YELLOW}請執行: npm install -g @anthropic-ai/claude-cli${NC}"
        exit 1
    fi

    echo -e "${GREEN}   ✅ Claude CLI 已安裝 (${CLAUDE_BIN})${NC}"
    echo ""
}

collect_latest_reports() {
    local prefix="$1"
    (find "${REPORTS_MARKDOWN_DIR}" -maxdepth 1 -type f -name "${prefix}-*.md" 2>/dev/null
     find "${REPORTS_ARCHIVE_DIR}" -maxdepth 1 -type f -name "${prefix}-*.md" 2>/dev/null) \
    | sort -r \
    | head -n "${MAX_REPORTS}" \
    | sort
}

extract_date_from_filename() {
    local filename
    filename="$(basename "$1")"
    echo "${filename}" | sed -E 's/.*([0-9]{4}-[0-9]{2}-[0-9]{2}).*/\1/'
}

load_report_lists() {
    echo -e "${BLUE}📂 收集每日報告...${NC}"

    mapfile -t MARKET_REPORTS < <(collect_latest_reports "market-analysis")
    mapfile -t HOLDINGS_REPORTS < <(collect_latest_reports "holdings-analysis")

    if (( ${#MARKET_REPORTS[@]} < MIN_REPORTS )); then
        echo -e "${YELLOW}⚠️  找到的市場分析報告不足 ${MIN_REPORTS} 份 (目前 ${#MARKET_REPORTS[@]} 份)。${NC}"
        echo -e "${YELLOW}請先累積至少 ${MIN_REPORTS}-${MAX_REPORTS} 份每日市場分析後再試。${NC}"
        exit 1
    fi

    if (( ${#HOLDINGS_REPORTS[@]} < MIN_REPORTS )); then
        echo -e "${YELLOW}⚠️  找到的持倉分析報告不足 ${MIN_REPORTS} 份 (目前 ${#HOLDINGS_REPORTS[@]} 份)。${NC}"
        echo -e "${YELLOW}請先累積至少 ${MIN_REPORTS}-${MAX_REPORTS} 份每日持倉分析後再試。${NC}"
        exit 1
    fi

    WEEK_START_DATE=$(extract_date_from_filename "${MARKET_REPORTS[0]}")
    WEEK_END_DATE=$(extract_date_from_filename "${MARKET_REPORTS[${#MARKET_REPORTS[@]}-1]}")

    echo -e "${GREEN}   ✅ 市場分析報告: ${#MARKET_REPORTS[@]} 份 (${WEEK_START_DATE} ~ ${WEEK_END_DATE})${NC}"
    for file in "${MARKET_REPORTS[@]}"; do
        echo "      - $(basename "$file")"
    done
    echo ""

    echo -e "${GREEN}   ✅ 持倉分析報告: ${#HOLDINGS_REPORTS[@]} 份${NC}"
    for file in "${HOLDINGS_REPORTS[@]}"; do
        echo "      - $(basename "$file")"
    done
    echo ""
}

generate_weekly_prompt() {
    echo -e "${BLUE}📝 生成週報 Prompt...${NC}"

    local market_count=${#MARKET_REPORTS[@]}
    local holdings_count=${#HOLDINGS_REPORTS[@]}
    local paired_count=$market_count

    if (( holdings_count < paired_count )); then
        paired_count=$holdings_count
    fi

    mkdir -p "${WEEKLY_OUTPUT_DIR}"

    cat > "${WEEKLY_PROMPT_FILE}" <<'EOF'
你是一位專業的市場與投資組合分析師,需要基於最近一週的「每日市場分析」與「每日持倉分析」報告,撰寫一份**週報**。

## 🎯 任務目標
1. 總結本週市場趨勢、產業輪動與重大新聞
2. 盤點投資組合週度績效 (前/後 3 名持股、倉位、風險)
3. 評估選擇權與風險暴露,提出具體控管措施
4. 擬定下週行動清單與觀察重點 (事件/財報/經濟數據)

## ✍️ 輸出風格
- 以決策重點為先,避免逐字抄錄
- 先結論後脈絡,每節開頭 2-3 句摘要
- 給出可操作的調整建議 (倉位/買賣價位/風險對沖)

---
EOF

    cat >> "${WEEKLY_PROMPT_FILE}" <<EOF
# 📆 每週市場與持倉週報 - ${WEEK_LABEL}

> **覆蓋區間**: ${WEEK_START_DATE} ~ ${WEEK_END_DATE}
> **來源報告**: 市場 ${market_count} 份, 持倉 ${holdings_count} 份
> **生成時間**: $(date +"%Y-%m-%d %H:%M UTC")
> **分析引擎**: The Ultimate Analysis System v2.0 (Claude Sonnet 4.5)

---

## 🧭 本週重點 (5 行內)
- 主要市場主題與情緒
- 產業/風格輪動 (成長 vs 價值, 大型 vs 中小型)
- 重大新聞/事件對指數的影響
- 組合整體表現與風險點
- 下週需立即關注的項目

## 📈 週度市場總結
### 指數與風險指標
| 指標 | 週度變化 | 關鍵觀察 |
|------|----------|----------|
| S&P 500 | | |
| Nasdaq | | |
| Dow Jones | | |
| 台股加權 | | |
| VIX | | |

### 市場敘事與驅動因素
- 美股/亞股/歐股核心推力
- 宏觀數據、政策或企業財報的影響
- 資金流向與風格偏好

### 產業輪動
- 強勢產業 (原因與持續性)
- 弱勢產業 (壓力來源)
- 檢視是否出現防禦/成長切換

### 重要新聞解讀
- 逐條列出本週重大新聞 → 短期/中期影響 → 潛在交易方向

## 💼 投資組合週度表現
### 概覽
| 指標 | 本週 | 評語 |
|------|------|------|
| 組合週度報酬 | | |
| vs S&P 500 | | |
| 現金比例 | | |
| 最大回撤/風險點 | | |

### Top / Bottom 3 持股
| 類別 | 股票 | 週度變化 | 核心原因 | 建議 |
|------|------|----------|----------|------|
| Top | | | | |
| Top | | | | |
| Top | | | | |
| Bottom | | | | |
| Bottom | | | | |
| Bottom | | | | |

### 選擇權與風險
- 需關注的到期日與行權價
- 可能被指派/回補的部位與處理策略
- 波動率變化對組合的影響

### 倉位調整建議 (下週)
- 高優先級調整 (立即/本週內執行)
- 中期調整 (1-3 週)
- 觀望項目與觀測觸發條件

## 🔭 下週展望與行動清單
- 關鍵經濟數據/財報/政策事件
- 交易計畫 (入場/出場區間、規模、風險控管)
- 需要驗證的假設與觀測指標

## 📜 附錄: 每日重點摘要
- 將每日報告各用 2-3 行摘要 (市場 + 持倉) 方便快速回顧

---

## 📚 每日市場分析原文
EOF

    for file in "${MARKET_REPORTS[@]}"; do
        local date_label
        date_label=$(extract_date_from_filename "${file}")
        cat >> "${WEEKLY_PROMPT_FILE}" <<EOF

### ${date_label} 市場分析
\`\`\`markdown
$(<"${file}")
\`\`\`
EOF
    done

    cat >> "${WEEKLY_PROMPT_FILE}" <<'EOF'

## 💼 每日持倉分析原文
EOF

    for file in "${HOLDINGS_REPORTS[@]}"; do
        local date_label
        date_label=$(extract_date_from_filename "${file}")
        cat >> "${WEEKLY_PROMPT_FILE}" <<EOF

### ${date_label} 持倉分析
\`\`\`markdown
$(<"${file}")
\`\`\`
EOF
    done

    echo -e "${GREEN}   ✅ 週報 Prompt 已生成${NC}"
    echo ""
}

run_weekly_analysis() {
    echo -e "${BLUE}🧠 調用 Claude 生成週報...${NC}"
    echo -e "${YELLOW}   這可能需要幾分鐘,請稍候...${NC}"
    echo ""

    if cat "${WEEKLY_PROMPT_FILE}" | "${CLAUDE_BIN}" > "${WEEKLY_OUTPUT}" 2>&1; then
        echo -e "${GREEN}   ✅ 週報生成完成!${NC}"
        echo ""
    else
        echo -e "${RED}   ❌ 週報生成失敗${NC}"
        exit 1
    fi
}

show_results() {
    echo -e "${BLUE}============================================================${NC}"
    echo -e "${GREEN}📄 週報已生成!${NC}"
    echo -e "${BLUE}============================================================${NC}"
    echo ""

    echo -e "${GREEN}🗂️  週報路徑:${NC}"
    echo -e "${GREEN}   ${WEEKLY_OUTPUT}${NC}"
    echo ""

    echo -e "${BLUE}📋 週報預覽 (前 20 行):${NC}"
    echo -e "${BLUE}------------------------------------------------------------${NC}"
    head -n 20 "${WEEKLY_OUTPUT}"
    echo -e "${BLUE}------------------------------------------------------------${NC}"
    echo ""

    echo -e "${GREEN}💡 查看完整週報:${NC}"
    echo -e "${GREEN}   cat ${WEEKLY_OUTPUT}${NC}"
    echo ""
}

cleanup() {
    rm -f "${WEEKLY_PROMPT_FILE}"
}

###############################################################################
# 主程式
###############################################################################

main() {
    print_header
    check_dependencies
    load_report_lists
    generate_weekly_prompt
    run_weekly_analysis
    show_results
    cleanup

    echo -e "${GREEN}✅ 週度報告流程完成!${NC}"
    echo ""
}

main "$@"
