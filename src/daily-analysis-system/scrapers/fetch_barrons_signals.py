#!/usr/bin/env python3
"""
Barron's 股票推薦訊號爬蟲
輸出到 output/market-data/{YEAR}/Signals/barrons-YYYY-MM-DD.md
"""

from datetime import datetime, timedelta
import os
from pathlib import Path
from typing import List, Dict, Optional

import requests
from bs4 import BeautifulSoup

from common import (
    create_argument_parser,
    add_common_arguments,
    setup_output_path,
    write_output,
    print_status,
    print_error,
    print_warning,
    safe_exit,
    generate_dated_filename,
    load_env_file,
)


BARRONS_URL = "https://www.barrons.com/market-data/stocks/stock-picks?mod=BOL_TOPNAV"


def _fetch_barrons_html() -> Optional[str]:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://www.barrons.com/market-data/stocks/stock-picks",
    }
    cookie = os.getenv("BARRONS_COOKIE")
    if cookie:
        headers["Cookie"] = cookie
    try:
        resp = requests.get(BARRONS_URL, headers=headers, timeout=30)
        resp.raise_for_status()
        return resp.text
    except requests.RequestException as exc:
        if getattr(exc, "response", None) is not None and exc.response.status_code == 401:
            print_error("Barron's 需要登入 Cookie，請設定 BARRONS_COOKIE 再試一次")
        print_error(f"獲取 Barron's 頁面失敗: {exc}")
        return None


def _parse_barrons_items(html: str, limit: int) -> List[Dict[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    selectors = [
        'article[data-module="ArticleItem"]',
        ".WSJTheme--headline",
        ".MarketDataModule-headline",
        "h3 a, h4 a",
        '[data-module] a[href*="articles"]',
    ]

    elements = []
    for selector in selectors:
        elements = soup.select(selector)
        if elements:
            break

    items = []
    for element in elements[:limit]:
        title = element.get_text(strip=True) if element else ""
        link = None
        if getattr(element, "name", "") == "a":
            link = element.get("href")
        else:
            anchor = element.find("a", href=True) if element else None
            link = anchor.get("href") if anchor else None
        if link and link.startswith("/"):
            link = f"https://www.barrons.com{link}"
        if title and len(title) > 10:
            items.append(
                {
                    "title": title,
                    "link": link or "",
                }
            )
    return items


def _load_previous_titles(signals_dir: Path) -> List[str]:
    files = sorted(signals_dir.glob("barrons-*.md"), reverse=True)
    if not files:
        return []
    latest = files[0]
    titles = []
    try:
        with open(latest, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("- 標題:"):
                    titles.append(line.replace("- 標題:", "").strip())
    except OSError:
        return []
    return titles


def _build_markdown(items: List[Dict[str, str]], days: int) -> str:
    now = datetime.utcnow()
    start_date = (now - timedelta(days=days)).strftime("%Y-%m-%d")
    today = now.strftime("%Y-%m-%d")

    lines = [
        f"# Barron's 股票推薦訊號 - {today}",
        "",
        f"**資料來源**: Barron's stock picks",
        f"**抓取時間**: {now.strftime('%Y-%m-%d %H:%M UTC')}",
        f"**近 {days} 天區間**: {start_date} ~ {today}",
        "",
        "---",
        "",
        "## 推薦清單",
        "",
    ]

    for item in items:
        title = item.get("title", "N/A")
        link = item.get("link", "")
        lines.append("### 推薦項目")
        lines.append(f"- 標題: {title}")
        lines.append(f"- 來源: Barron's")
        lines.append(f"- 發布時間: {today}")
        lines.append(f"- 連結: {link if link else 'N/A'}")
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def fetch_barrons_signals(limit: int, days: int, output_path: Optional[Path], force: bool) -> bool:
    html = _fetch_barrons_html()
    if not html:
        return False

    items = _parse_barrons_items(html, limit)
    if not items:
        print_warning("未解析到 Barron's 推薦內容")
        return False

    if output_path is None:
        print_status("輸出到 stdout，跳過重複檢查")
        content = _build_markdown(items, days)
        return write_output(content, output_path, verbose=True)

    previous_titles = _load_previous_titles(output_path.parent)
    current_titles = [item.get("title", "") for item in items]
    if not force and previous_titles and current_titles == previous_titles:
        print_warning("Barron's 推薦與上次相同，跳過輸出")
        return True

    content = _build_markdown(items, days)
    return write_output(content, output_path, verbose=True)


def main() -> None:
    load_env_file()
    parser = create_argument_parser(
        description="抓取 Barron's 股票推薦訊號並輸出 Markdown"
    )
    add_common_arguments(parser)
    parser.add_argument(
        "-l",
        "--limit",
        type=int,
        default=10,
        help="最多抓取筆數 (預設: 10)",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="訊號視窗天數 (預設: 7)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="即使內容相同仍覆蓋輸出",
    )

    args = parser.parse_args()

    filename = generate_dated_filename("barrons", "md")
    output_path = setup_output_path(
        output_arg=args.output,
        default_filename=filename,
        default_subdir="Signals",
        use_stdout=args.stdout,
    )

    success = fetch_barrons_signals(args.limit, args.days, output_path, args.force)
    safe_exit(success)


if __name__ == "__main__":
    main()
