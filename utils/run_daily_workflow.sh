#!/bin/bash
###############################################################################
# The Ultimate Analysis System - Complete Daily Workflow
#
# 功能: 完整的每日自動化流程
#   1. 資料抓取與分析 (make daily)
#   2. 更新 GitHub Pages (make update-pages)
#   3. 自動 Git Commit
#   4. 推送到 GitHub (make push)
#
# 使用: 由 launchd/crontab 自動執行,或手動執行
###############################################################################

set -e  # 遇到錯誤立即退出

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 專案路徑
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
PROJECT_ROOT="${REPO_ROOT}/src/daily-analysis-system"

# 設定環境變數 (launchd/cron 不會繼承 shell 環境)
export PATH="/usr/local/bin:/usr/bin:/bin:$HOME/.local/bin:$PATH"
export HOME="${HOME:-$(eval echo ~$(whoami))}"

# 載入 .env 檔案中的環境變數 (優先 root，再 fallback 專案目錄)
ENV_PATH="${REPO_ROOT}/.env"
if [ ! -f "${ENV_PATH}" ] && [ -f "${PROJECT_ROOT}/.env" ]; then
    ENV_PATH="${PROJECT_ROOT}/.env"
fi

if [ -f "${ENV_PATH}" ]; then
    echo -e "${GREEN}🔐 載入 .env 環境變數 (${ENV_PATH})...${NC}"
    set -a
    source "${ENV_PATH}"
    set +a
else
    echo -e "${YELLOW}⚠️  找不到 .env 檔案，請確認 root 或專案下有設定${NC}"
fi

# 驗證 Claude token 是否存在
if [ -z "$CLAUDE_CODE_OAUTH_TOKEN" ]; then
    # 嘗試從 Claude CLI 設定檔讀取
    if [ -f "$HOME/.config/claude/credentials.json" ]; then
        echo -e "${YELLOW}⚠️  .env 中無 token，嘗試從 Claude CLI 讀取...${NC}"
        # 如果有安裝 jq
        if command -v jq &> /dev/null; then
            export CLAUDE_CODE_OAUTH_TOKEN=$(jq -r '.claudeAiOauth.accessToken // .sessionKey // empty' "$HOME/.config/claude/credentials.json")
        fi
    fi

    if [ -z "$CLAUDE_CODE_OAUTH_TOKEN" ]; then
        echo -e "${RED}❌ 錯誤: 找不到 CLAUDE_TOKEN 或 CLAUDE_CODE_OAUTH_TOKEN${NC}"
        echo -e "${RED}   請在 .env 檔案中設定，或確認 launchd plist 中有設定${NC}"
        exit 1
    fi
else
    # 統一使用 CLAUDE_CODE_OAUTH_TOKEN
    export CLAUDE_CODE_OAUTH_TOKEN="${CLAUDE_CODE_OAUTH_TOKEN:-$CLAUDE_TOKEN}"
fi

# 日期
TODAY=$(date +"%Y-%m-%d")
TIME=$(date +"%H:%M:%S")

echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}📊 The Ultimate Analysis System - Daily Workflow${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""
echo -e "${GREEN}📅 日期: ${TODAY}${NC}"
echo -e "${GREEN}⏰ 時間: ${TIME}${NC}"
echo -e "${GREEN}📂 Repo 根目錄: ${REPO_ROOT}${NC}"
echo -e "${GREEN}📂 daily-analysis-system: ${PROJECT_ROOT}${NC}"
echo ""

# 切換到 repo 根目錄 (Makefile 位於此處)
cd "${REPO_ROOT}" || exit 1

# Step 1: 執行 make daily (資料抓取 + 分析)
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📊 Step 1/4: 執行每日分析 (make daily)${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

if make daily; then
    echo -e "${GREEN}✅ 每日分析完成!${NC}"
    echo ""
else
    echo -e "${RED}❌ 每日分析失敗!${NC}"
    exit 1
fi

# Step 2: 更新 GitHub Pages
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🚀 Step 2/4: 更新 GitHub Pages (make update-pages)${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

if make update-pages; then
    echo -e "${GREEN}✅ GitHub Pages 已更新!${NC}"
    echo ""
else
    echo -e "${YELLOW}⚠️  GitHub Pages 更新失敗,繼續執行...${NC}"
    echo ""
fi

# Step 3: Git Commit
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📝 Step 3/4: Git Commit (make commit-auto)${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

if make commit-auto; then
    echo -e "${GREEN}✅ Git Commit 完成!${NC}"
    echo ""
else
    echo -e "${YELLOW}⚠️  沒有變更需要 commit${NC}"
    echo ""
fi

# Step 4: Push to GitHub
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🚀 Step 4/4: Push to GitHub (make push)${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

if make push; then
    echo -e "${GREEN}✅ Push 完成!${NC}"
    echo ""
else
    echo -e "${YELLOW}⚠️  Push 失敗或沒有需要 push 的內容${NC}"
    echo ""
fi

# 完成
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ 完整工作流程執行完畢!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}📊 執行摘要:${NC}"
echo -e "  1. ✅ 資料抓取與分析"
echo -e "  2. ✅ GitHub Pages 更新"
echo -e "  3. ✅ Git Commit"
echo -e "  4. ✅ Push to GitHub"
echo ""
echo -e "${GREEN}完成時間: $(date +"%Y-%m-%d %H:%M:%S")${NC}"
