#!/usr/bin/env bash
###############################################################################
# Update GitHub Pages HTML from Markdown Reports
#
# 自動將最新的 markdown 分析報告轉換成 HTML 並更新 GitHub Pages
#
# 使用方式:
#   ./scripts/deployment/update_github_pages.sh
###############################################################################

set -e

# 顏色定義
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 路徑
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
PROJECT_ROOT="${REPO_ROOT}/src/daily-analysis-system"
REPORTS_DIR="${PROJECT_ROOT}/reports/markdown"
DOCS_DIR="${REPO_ROOT}/docs"

# 檢查 claude CLI
CLAUDE_BIN=""
if command -v claude &> /dev/null; then
    CLAUDE_BIN="claude"
elif [[ -x "${HOME}/.local/bin/claude" ]]; then
    CLAUDE_BIN="${HOME}/.local/bin/claude"
else
    echo -e "${YELLOW}⚠️  警告: 未安裝 claude CLI,將跳過 HTML 更新${NC}"
    echo -e "${YELLOW}   請手動更新 docs/market.html 和 docs/holdings.html${NC}"
    exit 0
fi

echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}📝 更新 GitHub Pages HTML${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""

# 查找最新的分析報告
LATEST_MARKET=$(ls -t "${REPORTS_DIR}"/market-analysis-*.md 2>/dev/null | head -1)
LATEST_HOLDINGS=$(ls -t "${REPORTS_DIR}"/holdings-analysis-*.md 2>/dev/null | head -1)

if [[ -z "${LATEST_MARKET}" ]] && [[ -z "${LATEST_HOLDINGS}" ]]; then
    echo -e "${YELLOW}⚠️  未找到任何分析報告,跳過更新${NC}"
    exit 0
fi

# 更新市場分析頁面
if [[ -n "${LATEST_MARKET}" ]]; then
    echo -e "${GREEN}📈 轉換市場分析報告...${NC}"
    echo -e "   來源: ${LATEST_MARKET}"
    echo -e "   目標: ${DOCS_DIR}/market.html"

    # 使用 Claude CLI 進行轉換
cat <<EOF | "${CLAUDE_BIN}" > "${DOCS_DIR}/market.html"
請將以下 markdown 報告轉換成完整的 HTML 頁面,並嚴格遵循以下格式:

---

$(cat "${LATEST_MARKET}")

---

請輸出完整的 HTML,包含:

1. 使用與現有 ${DOCS_DIR}/market.html 完全相同的結構和樣式
2. 導航欄保持一致 (Home, Market Analysis, Holdings Analysis)
3. Market Analysis 頁面要 highlight (style="background: var(--primary-color);")
4. 使用 <link rel="stylesheet" href="styles.css">
5. 包含完整的 TOC (Table of Contents) 功能和 JavaScript
6. 包含 Back to Top 按鈕
7. 保留所有 emoji 圖示
8. 表格使用 <table> 標籤
9. 保持深色主題

重要:請直接輸出完整的 HTML 代碼,從 <!DOCTYPE html> 開始,不要有任何其他文字說明。
EOF

    echo -e "${GREEN}   ✅ 市場分析頁面已更新${NC}"
    echo ""
fi

# 更新持倉分析頁面
if [[ -n "${LATEST_HOLDINGS}" ]]; then
    echo -e "${GREEN}💼 轉換持倉分析報告...${NC}"
    echo -e "   來源: ${LATEST_HOLDINGS}"
    echo -e "   目標: ${DOCS_DIR}/holdings.html"

    # 使用 Claude CLI 進行轉換
cat <<EOF | "${CLAUDE_BIN}" > "${DOCS_DIR}/holdings.html"
請將以下 markdown 報告轉換成完整的 HTML 頁面,並嚴格遵循以下格式:

---

$(cat "${LATEST_HOLDINGS}")

---

請輸出完整的 HTML,包含:

1. 使用與現有 ${DOCS_DIR}/holdings.html 完全相同的結構和樣式
2. 導航欄保持一致 (Home, Market Analysis, Holdings Analysis)
3. Holdings Analysis 頁面要 highlight (style="background: var(--primary-color);")
4. 使用 <link rel="stylesheet" href="styles.css">
5. 包含完整的 TOC (Table of Contents) 功能和 JavaScript
6. 包含 Back to Top 按鈕
7. 保留所有 emoji 圖示 (🚨, ⚠️, ⭐ 等)
8. 表格使用 <table> 標籤
9. 保持深色主題
10. 警示框使用適當的樣式類 (如 alert, warning 等)

重要:請直接輸出完整的 HTML 代碼,從 <!DOCTYPE html> 開始,不要有任何其他文字說明。
EOF

    echo -e "${GREEN}   ✅ 持倉分析頁面已更新${NC}"
    echo ""
fi

# 更新首頁的日期
if [[ -n "${LATEST_MARKET}" ]] || [[ -n "${LATEST_HOLDINGS}" ]]; then
    TODAY=$(date +"%Y-%m-%d")
    echo -e "${GREEN}📅 更新首頁日期: ${TODAY}${NC}"

    # 使用 sed 更新日期 (如果存在的話)
    if [[ -f "${DOCS_DIR}/index.html" ]]; then
        # 備份
        cp "${DOCS_DIR}/index.html" "${DOCS_DIR}/index.html.bak"

        # 更新日期
        sed -i "s/最後更新: [0-9-]\+/最後更新: ${TODAY}/g" "${DOCS_DIR}/index.html"
        sed -i "s/<span class=\"date\">[0-9-]\+<\/span>/<span class=\"date\">${TODAY}<\/span>/g" "${DOCS_DIR}/index.html"

        echo -e "${GREEN}   ✅ 首頁日期已更新${NC}"
    fi
    echo ""
fi

echo -e "${BLUE}============================================================${NC}"
echo -e "${GREEN}✅ GitHub Pages 更新完成!${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""
echo -e "${GREEN}下一步:${NC}"
echo -e "  1. 預覽: cd docs && python3 -m http.server 8000"
echo -e "  2. 提交: git add docs/ && git commit -m 'Update GitHub Pages'"
echo -e "  3. 推送: git push origin main"
echo ""
