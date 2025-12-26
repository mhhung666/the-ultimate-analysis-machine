#!/bin/bash
###############################################################################
# Docker Cron Entrypoint
# 功能: 設定 cron 任務並啟動 cron daemon
###############################################################################

set -e

echo "🚀 Starting Daily Analysis Scheduler..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 設定 Git 認證資訊
if [ -n "$GIT_USER_NAME" ]; then
    git config --global user.name "$GIT_USER_NAME"
    echo "✅ Git user.name: $GIT_USER_NAME"
fi

if [ -n "$GIT_USER_EMAIL" ]; then
    git config --global user.email "$GIT_USER_EMAIL"
    echo "✅ Git user.email: $GIT_USER_EMAIL"
fi

# 如果有 Gitea 設定,設定 Git credential helper
if [ -n "$GITEA_USERNAME" ] && [ -n "$GITEA_PASSWORD" ] && [ -n "$GITEA_REPO_URL" ]; then
    echo "✅ Gitea credentials configured"

    # 建立 git credential helper
    cat > /tmp/git-credentials-helper.sh <<'EOF'
#!/bin/bash
echo "username=${GITEA_USERNAME}"
echo "password=${GITEA_PASSWORD}"
EOF
    chmod +x /tmp/git-credentials-helper.sh
    git config --global credential.helper '/tmp/git-credentials-helper.sh'
fi

# 驗證環境變數
echo ""
echo "📋 Environment Variables:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -z "$CLAUDE_CODE_OAUTH_TOKEN" ] && [ -z "$CLAUDE_TOKEN" ]; then
    echo "❌ ERROR: CLAUDE_CODE_OAUTH_TOKEN or CLAUDE_TOKEN not set!"
    echo "   Please add it to your .env file"
    exit 1
else
    echo "✅ Claude Token: [CONFIGURED]"
fi

echo "✅ Timezone: ${TZ:-UTC}"
echo "✅ Cron Schedule: ${CRON_SCHEDULE:-0 21 * * *}"
echo ""

# 建立 crontab
CRON_SCHEDULE="${CRON_SCHEDULE:-0 21 * * *}"
CRON_LOG_FILE="/app/logs/cron-\$(date +\%Y-\%m-\%d).log"

# 寫入 crontab
cat > /etc/cron.d/daily-analysis <<EOF
# Daily Analysis Workflow
# Runs at: ${CRON_SCHEDULE}
${CRON_SCHEDULE} root /app/utils/run_daily_workflow.sh >> ${CRON_LOG_FILE} 2>&1

# Empty line required by cron
EOF

chmod 0644 /etc/cron.d/daily-analysis

echo "📅 Cron Job Configuration:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
cat /etc/cron.d/daily-analysis
echo ""

# 建立環境變數檔案給 cron 使用
cat > /app/.env <<EOF
# Auto-generated environment for cron
CLAUDE_CODE_OAUTH_TOKEN=${CLAUDE_CODE_OAUTH_TOKEN}
CLAUDE_TOKEN=${CLAUDE_TOKEN}
GIT_USER_NAME=${GIT_USER_NAME}
GIT_USER_EMAIL=${GIT_USER_EMAIL}
GITEA_USERNAME=${GITEA_USERNAME}
GITEA_PASSWORD=${GITEA_PASSWORD}
GITEA_REPO_URL=${GITEA_REPO_URL}
TZ=${TZ}
PATH=/usr/local/bin:/usr/bin:/bin:/app/.venv/bin
EOF

echo "✅ Environment file created for cron"
echo ""

# 測試執行一次(可選)
if [ "$RUN_ON_STARTUP" = "true" ]; then
    echo "🧪 Running initial test..."
    /app/utils/run_daily_workflow.sh
    echo ""
fi

# 啟動 cron
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Starting cron daemon..."
echo "📊 Daily workflow will run at: ${CRON_SCHEDULE}"
echo "📁 Logs will be saved to: /app/logs/"
echo ""
echo "💡 To view logs:"
echo "   docker compose logs -f analysis-scheduler"
echo "   docker compose exec analysis-scheduler tail -f /app/logs/cron-*.log"
echo ""
echo "🔄 Container is now running and waiting for scheduled execution..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 啟動 cron (前景模式)
cron -f
