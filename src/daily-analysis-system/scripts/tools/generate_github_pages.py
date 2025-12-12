#!/usr/bin/env python3
"""
自動生成 GitHub Pages 網站內容

功能:
1. 將 markdown 報告轉換為 HTML
2. 生成個股頁面到 docs/stocks/
3. 更新首頁的個股列表數據
4. 建立歷史報告備份
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

# 目錄設定
PROJECT_ROOT = Path(__file__).resolve().parents[2]  # src/daily-analysis-system
REPO_ROOT = PROJECT_ROOT.parent.parent              # repo root
REPORTS_DIR = PROJECT_ROOT / "reports" / "markdown"
DOCS_DIR = REPO_ROOT / "docs"
STOCKS_DIR = DOCS_DIR / "stocks"
CONVERTER_SCRIPT = PROJECT_ROOT / "scripts" / "tools" / "convert_md_to_html.py"


def find_latest_reports() -> Dict[str, Path]:
    """找到最新的市場分析、持股分析和個股報告"""

    if not REPORTS_DIR.exists():
        print(f"❌ 報告目錄不存在: {REPORTS_DIR}")
        sys.exit(1)

    reports = {
        "market": None,
        "holdings": None,
        "stocks": {}
    }

    # 找市場分析報告
    market_reports = sorted(REPORTS_DIR.glob("market-analysis-*.md"), reverse=True)
    if market_reports:
        reports["market"] = market_reports[0]

    # 找持股分析報告
    holdings_reports = sorted(REPORTS_DIR.glob("holdings-analysis-*.md"), reverse=True)
    if holdings_reports:
        reports["holdings"] = holdings_reports[0]

    # 找個股報告 (每個股票代碼取最新的)
    stock_reports = REPORTS_DIR.glob("stock-*.md")
    stock_dict = {}

    for report in stock_reports:
        # 從檔名提取股票代碼: stock-TSLA-2025-12-05-1345.md
        parts = report.stem.split("-")
        if len(parts) >= 2:
            symbol = parts[1]

            # 如果這個股票還沒記錄，或者這個報告更新
            if symbol not in stock_dict or report.name > stock_dict[symbol].name:
                stock_dict[symbol] = report

    reports["stocks"] = stock_dict

    return reports


def convert_markdown_to_html(md_file: Path, output_file: Path, page_type: str) -> bool:
    """呼叫轉換腳本將 markdown 轉為 HTML"""

    try:
        cmd = [
            sys.executable,
            str(CONVERTER_SCRIPT),
            str(md_file),
            str(output_file),
            page_type
        ]

        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True
        )

        print(result.stdout.strip())
        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ 轉換失敗: {md_file.name}")
        print(f"   錯誤: {e.stderr}")
        return False


def extract_stock_info(md_file: Path) -> Dict[str, str]:
    """從個股 markdown 檔案中提取資訊"""

    content = md_file.read_text(encoding="utf-8")

    # 提取股票代碼
    symbol = md_file.stem.split("-")[1] if "-" in md_file.stem else "UNKNOWN"

    # 提取公司名稱 (從標題中)
    name = symbol  # 預設

    # 提取更新日期
    import re
    date_match = re.search(r"(\d{4}-\d{2}-\d{2})", md_file.name)
    last_update = date_match.group(1) if date_match else datetime.now().strftime("%Y-%m-%d")

    # 分析情緒傾向 (簡單判斷)
    sentiment = "neutral"
    positive_count = content.count("🟢")
    negative_count = content.count("🔴")

    if positive_count > negative_count:
        sentiment = "positive"
    elif negative_count > positive_count:
        sentiment = "negative"

    # 計算新聞數量
    news_count = content.count("#### 📌")

    return {
        "symbol": symbol,
        "name": name,
        "sentiment": sentiment,
        "newsCount": news_count,
        "lastUpdate": last_update
    }


def generate_stocks_index_data(stocks: Dict[str, Path]) -> List[Dict]:
    """生成個股列表的 JSON 資料"""

    stocks_data = []

    for symbol, md_file in sorted(stocks.items()):
        info = extract_stock_info(md_file)
        stocks_data.append(info)

    return stocks_data


def update_stocks_index_html(stocks_data: List[Dict]) -> None:
    """更新 stocks/index.html 中的股票資料"""

    index_file = STOCKS_DIR / "index.html"

    if not index_file.exists():
        print(f"⚠️  找不到 {index_file}")
        return

    content = index_file.read_text(encoding="utf-8")

    # 生成 JavaScript 陣列
    js_array = json.dumps(stocks_data, indent=12, ensure_ascii=False)

    # 替換 stocks 陣列
    import re
    pattern = r"const stocks = \[.*?\];"
    replacement = f"const stocks = {js_array};"

    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

    index_file.write_text(new_content, encoding="utf-8")
    print(f"✅ 更新了個股列表資料 ({len(stocks_data)} 檔個股)")


def main() -> None:
    print("🚀 開始生成 GitHub Pages 內容...\n")

    # 確保目錄存在
    STOCKS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. 找到最新報告
    print("📋 尋找最新報告...")
    reports = find_latest_reports()

    # 2. 轉換市場分析
    if reports["market"]:
        print(f"\n📊 轉換市場分析報告...")
        output = DOCS_DIR / "market.html"
        convert_markdown_to_html(reports["market"], output, "market")
    else:
        print("⚠️  找不到市場分析報告")

    # 3. 轉換持股分析
    if reports["holdings"]:
        print(f"\n💼 轉換持股分析報告...")
        output = DOCS_DIR / "holdings.html"
        convert_markdown_to_html(reports["holdings"], output, "holdings")
    else:
        print("⚠️  找不到持股分析報告")

    # 4. 轉換個股報告
    if reports["stocks"]:
        print(f"\n📈 轉換個股報告 ({len(reports['stocks'])} 檔)...")

        stocks_data = []

        for symbol, md_file in sorted(reports["stocks"].items()):
            output = STOCKS_DIR / f"{symbol}.html"
            success = convert_markdown_to_html(md_file, output, "stock")

            if success:
                # 提取股票資訊
                info = extract_stock_info(md_file)
                stocks_data.append(info)

        # 5. 更新個股列表頁面的資料
        if stocks_data:
            print(f"\n🔄 更新個股列表資料...")
            update_stocks_index_html(stocks_data)
    else:
        print("⚠️  找不到個股報告")

    print(f"\n✅ GitHub Pages 生成完成!")
    print(f"   輸出目錄: {DOCS_DIR}")
    print(f"\n💡 下一步:")
    print(f"   1. 檢查生成的 HTML 檔案")
    print(f"   2. 提交到 Git 並推送到 GitHub")
    print(f"   3. 在 GitHub 上啟用 Pages (如果還沒有)")


if __name__ == "__main__":
    main()
