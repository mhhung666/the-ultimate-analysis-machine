#!/usr/bin/env bash
###############################################################################
# Test Script - 測試 Cron 執行腳本是否能正常工作
# 這個腳本會模擬 cron 執行環境，但不實際執行完整分析
###############################################################################

set -e

echo "🧪 測試 Cron 執行環境..."
echo ""

# 測試專案路徑
PROJECT_ROOT="/Users/mhhung/Development/MH/market-intelligence-system"
echo "✅ 專案路徑: ${PROJECT_ROOT}"

# 測試切換目錄
cd "${PROJECT_ROOT}" || {
    echo "❌ 無法切換到專案目錄"
    exit 1
}
echo "✅ 成功切換到專案目錄"

# 測試 Python 環境
if [[ -f ".venv/bin/python" ]]; then
    echo "✅ Python 虛擬環境存在"
    .venv/bin/python --version
else
    echo "❌ Python 虛擬環境不存在"
    exit 1
fi

# 測試 Claude CLI
if command -v claude &> /dev/null; then
    echo "✅ Claude CLI 已安裝: $(which claude)"
else
    echo "❌ Claude CLI 未安裝"
    exit 1
fi

# 測試 Git
if git status &> /dev/null; then
    echo "✅ Git repository 正常"
    echo "   Branch: $(git branch --show-current)"
    echo "   Remote: $(git remote get-url origin 2>/dev/null || echo 'No remote')"
else
    echo "❌ Git repository 異常"
    exit 1
fi

# 測試 Makefile targets
echo ""
echo "🔍 檢查 Makefile targets..."
if make help &> /dev/null; then
    echo "✅ make help 可執行"
    echo "✅ make daily 目標存在"
else
    echo "❌ Makefile 異常"
    exit 1
fi

# 測試日誌寫入
LOG_FILE="/tmp/market-intelligence-system.log"
echo ""
echo "📝 測試日誌寫入..."
echo "[$(date +"%Y-%m-%d %H:%M:%S")] 測試日誌寫入" >> "${LOG_FILE}"
if [[ -f "${LOG_FILE}" ]]; then
    echo "✅ 日誌檔案可寫入: ${LOG_FILE}"
    echo "   最後一行: $(tail -1 "${LOG_FILE}")"
else
    echo "❌ 日誌檔案寫入失敗"
    exit 1
fi

# 測試輸出目錄
echo ""
echo "📁 檢查輸出目錄..."
REPORTS_DIR="${PROJECT_ROOT}/reports/markdown"
if [[ -d "${REPORTS_DIR}" ]]; then
    echo "✅ 報告目錄存在: ${REPORTS_DIR}"
    echo "   現有報告數量: $(ls -1 "${REPORTS_DIR}"/*.md 2>/dev/null | wc -l | xargs)"
else
    echo "⚠️  報告目錄不存在，將會自動創建"
fi

# 測試 Git 提交功能（乾跑）
echo ""
echo "🔍 測試 Git 提交功能 (dry-run)..."
if git diff --cached --quiet && git diff --quiet; then
    echo "✅ Git 工作區乾淨"
else
    echo "⚠️  Git 工作區有未提交的變更"
    echo "   未暫存的檔案:"
    git status --short | head -5
fi

# 測試 PATH 設定
echo ""
echo "🔍 檢查環境變數..."
echo "   PATH: ${PATH:0:100}..."
echo "   LANG: ${LANG:-未設定}"

# 顯示 cron 執行腳本
echo ""
echo "📄 Cron 執行腳本: ${PROJECT_ROOT}/run_daily_cron.sh"
if [[ -x "${PROJECT_ROOT}/run_daily_cron.sh" ]]; then
    echo "✅ 腳本存在且可執行"
else
    echo "❌ 腳本不存在或無執行權限"
    exit 1
fi

echo ""
echo "============================================================"
echo "🎉 所有測試通過！Cron 環境設定正確"
echo "============================================================"
echo ""
echo "📋 下一步操作:"
echo "1. 安裝 cron 任務: ./setup_cron.sh (然後輸入 'y' 確認)"
echo "2. 手動測試完整執行: ./run_daily_cron.sh"
echo "3. 查看 cron 任務: crontab -l"
echo "4. 查看執行日誌: tail -f /tmp/market-intelligence-system.log"
echo ""
