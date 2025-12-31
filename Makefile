.DEFAULT_GOAL := help

DAS_DIR := src/daily-analysis-system
PYTHON ?= python3
VENV := .venv
VENV_ABS := $(abspath $(VENV))
BIN := $(VENV_ABS)/bin
PYTHON_BIN := $(BIN)/python
PIP := $(BIN)/pip
PYTEST := $(BIN)/pytest
SCRAPERS_DIR := $(DAS_DIR)/scrapers
SCRIPTS_DIR := $(DAS_DIR)/scripts
REPORTS_DIR := $(DAS_DIR)/reports
DOCS_DIR := docs

help:
	@echo "daily-analysis-system targets (run from repo root):"
	@echo ""
	@echo "  make install        - Install dependencies into $(VENV)"
	@echo "  make test           - Run pytest"
	@echo "  make clean          - Remove __pycache__ inside $(DAS_DIR)"
	@echo "  make clean-venv     - Delete $(VENV)"
	@echo ""
	@echo "  make fetch-global   - Fetch global market indices"
	@echo "  make fetch-holdings - Fetch holdings prices"
	@echo "  make fetch-news     - Fetch market news for configured symbols"
	@echo "  make fetch-barrons  - Fetch Barron's signals"
	@echo "  make fetch-all      - Run all scrapers"
	@echo ""
	@echo "  make analyze-daily  - Run Claude CLI daily analysis"
	@echo "  make daily          - Run full daily workflow (fetch + analyze)"
	@echo "  make clean-old-reports - Archive old markdown reports"
	@echo ""
	@echo "  make update-pages   - Generate GitHub Pages HTML"
	@echo "  make preview-pages  - Preview GitHub Pages locally"
	@echo ""
	@echo "  make commit         - Commit docs/reports changes"
	@echo "  make commit-auto    - Auto-commit docs/reports"
	@echo "  make push           - Push to GitHub"
	@echo "  make deploy         - Full deployment (pages + commit + push)"

venv:
	$(PYTHON) -m venv $(VENV)

install: venv $(DAS_DIR)/requirements.txt
	$(PIP) install --upgrade pip
	$(PIP) install -r $(DAS_DIR)/requirements.txt

test: install
	cd $(DAS_DIR) && $(PYTEST)

clean:
	find $(DAS_DIR) -name "__pycache__" -type d -prune -exec rm -rf {} +
	rm -rf $(DAS_DIR)/.pytest_cache

clean-venv:
	rm -rf $(VENV)

fetch-global: install
	cd $(DAS_DIR) && $(PYTHON_BIN) scrapers/fetch_global_indices.py

fetch-holdings: install
	cd $(DAS_DIR) && $(PYTHON_BIN) scrapers/fetch_holdings_prices.py

fetch-news: install
	cd $(DAS_DIR) && $(PYTHON_BIN) scrapers/fetch_all_news.py

fetch-barrons: install
	cd $(DAS_DIR) && $(PYTHON_BIN) scrapers/fetch_barrons_signals.py

fetch-all: install
	@echo "Running all scrapers..."
	cd $(DAS_DIR) && $(PYTHON_BIN) scrapers/fetch_global_indices.py
	cd $(DAS_DIR) && $(PYTHON_BIN) scrapers/fetch_holdings_prices.py
	cd $(DAS_DIR) && $(PYTHON_BIN) scrapers/fetch_all_news.py
	@echo "All scrapers completed!"

analyze-daily:
	@echo "Starting daily market analysis (Claude CLI)..."
	cd $(DAS_DIR) && ./scripts/analysis/run_daily_analysis_claude_cli.sh

daily: fetch-all analyze-daily
	@echo "✅ Daily workflow completed (fetch + analyze)!"

clean-old-reports:
	@echo "📦 Archiving old markdown reports..."
	@mkdir -p $(REPORTS_DIR)/archive
	@latest_market=$$(ls $(REPORTS_DIR)/markdown/market-analysis-*.md 2>/dev/null | sort -r | head -1); \
	latest_holdings=$$(ls $(REPORTS_DIR)/markdown/holdings-analysis-*.md 2>/dev/null | sort -r | head -1); \
	if [ -n "$$latest_market" ]; then \
		ls $(REPORTS_DIR)/markdown/market-analysis-*.md 2>/dev/null | grep -v "$$latest_market" | xargs -I {} mv {} $(REPORTS_DIR)/archive/ 2>/dev/null || true; \
		echo "  ✅ Kept in markdown: $$latest_market"; \
	fi; \
	if [ -n "$$latest_holdings" ]; then \
		ls $(REPORTS_DIR)/markdown/holdings-analysis-*.md 2>/dev/null | grep -v "$$latest_holdings" | xargs -I {} mv {} $(REPORTS_DIR)/archive/ 2>/dev/null || true; \
		echo "  ✅ Kept in markdown: $$latest_holdings"; \
	fi; \
	stock_count=0; \
	for ticker in $$(ls $(REPORTS_DIR)/markdown/stock-*.md 2>/dev/null | sed 's/.*stock-\([^-]*\)-.*/\1/' | sort -u); do \
		latest_stock=$$(ls $(REPORTS_DIR)/markdown/stock-$$ticker-*.md 2>/dev/null | sort -r | head -1); \
		if [ -n "$$latest_stock" ]; then \
			archived=$$(ls $(REPORTS_DIR)/markdown/stock-$$ticker-*.md 2>/dev/null | grep -v "$$latest_stock" | wc -l); \
			ls $(REPORTS_DIR)/markdown/stock-$$ticker-*.md 2>/dev/null | grep -v "$$latest_stock" | xargs -I {} mv {} $(REPORTS_DIR)/archive/ 2>/dev/null || true; \
			stock_count=$$((stock_count + archived)); \
			echo "  ✅ Kept in markdown for $$ticker: $$latest_stock"; \
		fi; \
	done; \
	archived_count=$$(ls $(REPORTS_DIR)/archive/*.md 2>/dev/null | wc -l); \
	echo "  📦 Archived stock reports: $$stock_count"; \
	echo "  📦 Total archived reports: $$archived_count"

update-pages: install
	@echo "🚀 Generating GitHub Pages from latest reports..."
	cd $(DAS_DIR) && $(PYTHON_BIN) scripts/tools/generate_github_pages.py

preview-pages: install
	@echo "Starting preview server at http://localhost:8000"
	@echo "Press Ctrl+C to stop"
	cd $(DOCS_DIR) && $(PYTHON_BIN) -m http.server 8000

commit:
	@echo "📝 Committing changes..."
	@git add $(DOCS_DIR)/ $(REPORTS_DIR)/
	@git status
	@echo ""
	@echo "Enter commit message (or press Ctrl+C to cancel):"
	@read -p "> " msg; \
	git commit -m "$$msg"
	@echo "✅ Changes committed!"

commit-auto:
	@echo "📝 Committing with auto-generated message..."
	@git add $(DOCS_DIR)/ $(REPORTS_DIR)/
	@git commit -m "feat(daily): Update analysis reports and GitHub Pages for $$(date +%Y-%m-%d)" || echo "Nothing to commit"
	@echo "✅ Changes committed!"

push:
	@echo "🚀 Pushing to GitHub..."
	@git push origin main
	@echo "✅ Pushed to GitHub! Pages will update in 1-2 minutes."

deploy: update-pages commit-auto push
	@echo "🎉 Full deployment complete!"
	@echo "   1. ✅ HTML pages updated"
	@echo "   2. ✅ Changes committed"
	@echo "   3. ✅ Pushed to GitHub"
	@echo ""
	@echo "Check your GitHub Pages site in 1-2 minutes!"

.PHONY: help venv install test clean clean-venv fetch-global fetch-holdings fetch-news fetch-barrons fetch-all analyze-daily daily clean-old-reports update-pages preview-pages commit commit-auto push deploy
