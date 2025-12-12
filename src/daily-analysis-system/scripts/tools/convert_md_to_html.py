#!/usr/bin/env python3
"""
Markdown → HTML converter tailored for the Market Intelligence System.

- 保留 markdown 中的 emoji、程式碼區塊、表格、巢狀清單、blockquote
- 自動產生頁面框架 (導航列、TOC、Back to Top 按鈕)
- 依照頁面類型自動高亮導航 (market/holdings)
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Tuple
from zoneinfo import ZoneInfo

try:
    from markdown import Markdown
except ImportError:  # pragma: no cover - runtime dependency check
    print(
        "❌ 需要安裝 markdown 套件才能轉換。請執行 `pip install markdown` 後再試一次。",
        file=sys.stderr,
    )
    sys.exit(1)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert a markdown report into the styled HTML used by docs/*.html",
    )
    parser.add_argument("input", type=Path, help="來源 markdown 檔案")
    parser.add_argument("output", type=Path, help="輸出 HTML 檔案路徑")
    parser.add_argument(
        "page_type",
        nargs="?",
        default="market",
        choices=["market", "holdings", "home", "stock"],
        help="用於設定導航高亮, 預設 market",
    )
    return parser.parse_args()


def read_file(filepath: Path) -> str:
    return filepath.read_text(encoding="utf-8")


def slugify_heading(value: str, separator: str = "-") -> str:
    """為中文/英文混合標題建立 slug, 供 markdown toc 使用。"""
    cleaned = re.sub(r"[^\w\s\-\u4e00-\u9fff]", "", value).strip().lower()
    cleaned = re.sub(r"\s+", separator, cleaned)
    return cleaned.strip(separator)


def extract_title_and_date(content: str, source_path: Path) -> Tuple[str, str, str]:
    """從 markdown 抓 title、日期與股票代碼 (優先抓正文, 再退回檔名)."""
    title_match = re.search(r"^#\s+(.+?)$", content, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else "Analysis Report"

    date_match = re.search(r"(\d{4}-\d{2}-\d{2})", content)
    if date_match:
        date = date_match.group(1)
    else:
        file_match = re.search(r"(\d{4}-\d{2}-\d{2})", source_path.name)
        date = file_match.group(1) if file_match else localized_now().strftime("%Y-%m-%d")

    # 提取股票代碼 (從檔名或內容)
    stock_symbol = ""
    stock_match = re.search(r"stock-([A-Z]+)-", source_path.name)
    if stock_match:
        stock_symbol = stock_match.group(1)
    else:
        # 從內容中的 metadata 提取
        symbol_match = re.search(r"[*]{2}股票代碼[*]{2}:\s*([A-Z]+)", content)
        if symbol_match:
            stock_symbol = symbol_match.group(1)

    return title, date, stock_symbol


def strip_leading_emoji(text: str) -> str:
    """移除開頭的 emoji/符號, 保留後續文字。"""
    cleaned = re.sub(r"^[\u2600-\u27BF\U0001F000-\U0001FAFF\U0001FB00-\U0001FFFF]+\s*", "", text)
    return cleaned or text


def strip_trailing_date(text: str) -> str:
    """移除標題結尾的日期 (如 " - 2025-12-08"), 僅保留主標題。"""
    return re.sub(r"\s*[-–—]\s*\d{4}-\d{2}-\d{2}\s*$", "", text).strip()


def localized_now() -> datetime:
    """Return current time with a stable tz (default Asia/Taipei, overridable via env)."""
    tz_name = os.environ.get("MIS_REPORT_TZ") or os.environ.get("TZ") or "Asia/Taipei"
    try:
        return datetime.now(ZoneInfo(tz_name))
    except Exception:
        return datetime.now()


def post_process_html(html: str) -> str:
    """附加一些 markdown 無法處理的細節樣式。"""

    def wrap_tables(match: re.Match[str]) -> str:
        return f'<div class="table-wrapper">{match.group(0)}</div>'

    html = re.sub(r"<table>.*?</table>", wrap_tables, html, flags=re.DOTALL)

    def wrap_percentages(match: re.Match[str]) -> str:
        value = match.group(1)
        css_class = "status-positive" if value.startswith("+") else "status-negative"
        return f'<span class="{css_class}">{value}</span>'

    html = re.sub(r"(?<![\w\-])([+-]\d+(?:\.\d+)?%)", wrap_percentages, html)
    # 移除 Markdown 內容中可能重複的頁面摘要區塊 (生成時間/引擎/類型)
    html = re.sub(r"<blockquote>.*?報告生成時間.*?</blockquote>", "", html, flags=re.DOTALL)
    # 移除開頭第一個 H1 (通常已在頁首呈現) 與緊接的分隔線, 避免重複
    html = re.sub(r"^<h1[^>]*>.*?</h1>\s*(?:<hr>\s*)?", "", html, flags=re.DOTALL)
    return html


def markdown_to_html(md_content: str) -> str:
    """使用 python-markdown 轉換, 支援表格/程式碼/巢狀清單/blockquote。"""
    md = Markdown(
        extensions=[
            "fenced_code",
            "tables",
            "sane_lists",
            "toc",
            "smarty",
            "attr_list",
            "md_in_html",
        ],
        extension_configs={"toc": {"slugify": slugify_heading, "permalink": False}},
        output_format="html5",
    )
    html = md.convert(md_content)
    return post_process_html(html)


def create_html_page(title: str, date: str, content_html: str, page_type: str, stock_symbol: str = "") -> str:
    """建立完整頁面 HTML。"""
    display_title = strip_leading_emoji(title)
    heading_title = display_title
    hero_note_text = "Market Intelligence System"
    if page_type in {"market", "holdings", "stock"}:
        heading_title = strip_trailing_date(display_title)
        hero_note_text = f"更新於 {date}"
    page_names = {
        "market": "Market Analysis",
        "holdings": "Holdings Analysis",
        "home": "Home",
        "stock": "Stock Analysis"
    }
    current_page = page_names.get(page_type, "Analysis")
    generated_at_dt = localized_now()
    generated_at = generated_at_dt.strftime("%Y-%m-%d %H:%M %Z%z").strip()

    def active_class(target: str) -> str:
        return ' class="nav-link active"' if target == page_type else ' class="nav-link"'

    # 個股頁面的麵包屑導航
    breadcrumb = ""
    if page_type == "stock" and stock_symbol:
        breadcrumb = f'''
        <nav class="breadcrumb">
            <a href="../index.html">Home</a>
            <span class="separator">›</span>
            <a href="index.html">Stocks</a>
            <span class="separator">›</span>
            <span class="current">{stock_symbol}</span>
        </nav>
        '''

    # 根據頁面類型調整 CSS/JS 路徑
    css_path = "../styles.css" if page_type == "stock" else "styles.css"
    home_path = "../index.html" if page_type == "stock" else "index.html"
    market_path = "../market.html" if page_type == "stock" else "market.html"
    holdings_path = "../holdings.html" if page_type == "stock" else "holdings.html"
    stocks_path = "index.html" if page_type == "stock" else "stocks/index.html"

    return f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{display_title} | Market Intelligence System</title>
    <meta name="description" content="Markdown 報告自動轉換的 {current_page}">
    <link rel="stylesheet" href="{css_path}">
</head>
<body class="notion-theme page-{page_type}" id="theme-typography">
    <div class="page-shell">
        <nav class="top-nav">
            <span class="nav-brand">📊 Market Intelligence System</span>
            <div class="nav-links">
                <a href="{home_path}"{active_class("home")}>Home</a>
                <a href="{market_path}"{active_class("market")}>Market</a>
                <a href="{holdings_path}"{active_class("holdings")}>Holdings</a>
                <a href="{stocks_path}"{active_class("stock")}>Stocks</a>
            </div>
            <div class="nav-actions">
                <button class="theme-toggle" id="themeToggle" aria-label="切換主題" title="Toggle theme">
                    <span id="themeIcon">☀️</span>
                </button>
            </div>
        </nav>
{breadcrumb}
        <header class="report-hero">
            <div>
                <p class="eyebrow">{current_page}</p>
                <h1>{heading_title}</h1>
                <p class="hero-note">{hero_note_text}</p>
                <div class="hero-meta">
                    <span class="pill">📅 {date}</span>
                    <span class="pill pill-ghost">🕐 {generated_at}</span>
                    <span class="pill pill-outline">📊 {current_page}</span>
                </div>
            </div>
        </header>

        <main class="page-layout no-toc">
            <section class="content" id="mainContent">
{content_html}
            </section>
        </main>

        <button class="back-to-top" id="backToTop" aria-label="回到頂部" title="Back to top">↑</button>

        <footer>
            <p>Market Intelligence System | MH Hung © 2025</p>
        </footer>
    </div>

    <script>
        // 主題切換 (Notion-style)
        function getPreferredTheme() {{
            const stored = localStorage.getItem('mis-theme');
            if (stored === 'light' || stored === 'dark') return stored;
            // Notion 預設為淺色模式
            return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
        }}

        function applyTheme(theme) {{
            const body = document.body;
            body.classList.toggle('theme-light', theme === 'light');
            body.classList.toggle('theme-dark', theme === 'dark');
            localStorage.setItem('mis-theme', theme);

            const icon = document.getElementById('themeIcon');
            if (icon) {{
                icon.textContent = theme === 'light' ? '🌙' : '☀️';
            }}

            const toggle = document.getElementById('themeToggle');
        if (toggle) {{
            toggle.setAttribute('aria-label', `切換為${{theme === 'light' ? '深色' : '淺色'}}模式`);
        }}
    }}

        // Mobile nav toggle
        function setupMobileNav() {{
            const nav = document.querySelector('.top-nav');
            const navLinks = nav?.querySelector('.nav-links');
            const navActions = nav?.querySelector('.nav-actions');
            const navBrand = nav?.querySelector('.nav-brand');
            if (!nav || !navLinks || !navActions || !navBrand) return;

            let toggle = document.getElementById('menuToggle');
            if (!toggle) {{
                toggle = document.createElement('button');
                toggle.id = 'menuToggle';
                toggle.type = 'button';
                toggle.className = 'menu-toggle';
                toggle.setAttribute('aria-label', '開啟選單');
                toggle.setAttribute('aria-expanded', 'false');
                toggle.textContent = '☰';
                nav.insertBefore(toggle, navBrand);
            }}

            let backdrop = document.getElementById('navBackdrop');
            if (!backdrop) {{
                backdrop = document.createElement('div');
                backdrop.id = 'navBackdrop';
                backdrop.className = 'nav-backdrop';
                document.body.appendChild(backdrop);
            }}

            const closeNav = () => {{
                document.body.classList.remove('nav-open');
                toggle.setAttribute('aria-expanded', 'false');
            }};

            const openNav = () => {{
                document.body.classList.add('nav-open');
                toggle.setAttribute('aria-expanded', 'true');
            }};

            toggle.addEventListener('click', () => {{
                const isOpen = document.body.classList.contains('nav-open');
                isOpen ? closeNav() : openNav();
            }});

            backdrop.addEventListener('click', closeNav);
            navLinks.addEventListener('click', (event) => {{
                if (event.target instanceof HTMLElement && event.target.tagName === 'A') {{
                    closeNav();
                }}
            }});

            window.addEventListener('resize', () => {{
                if (window.innerWidth > 768) {{
                    closeNav();
                }}
            }});

            document.body.classList.add('nav-ready');
        }}

        // Back to top
        function handleBackToTop() {{
            const btn = document.getElementById('backToTop');
            if (window.pageYOffset > 300) {{
                btn.classList.add('visible');
            }} else {{
                btn.classList.remove('visible');
            }}
        }}

        document.addEventListener('DOMContentLoaded', () => {{
            applyTheme(getPreferredTheme());
            handleBackToTop();

            let scrollTimeout;
            window.addEventListener('scroll', () => {{
                clearTimeout(scrollTimeout);
                scrollTimeout = setTimeout(() => {{
                    handleBackToTop();
                }}, 100);
            }});

            document.getElementById('backToTop').addEventListener('click', () => {{
                window.scrollTo({{ top: 0, behavior: 'smooth' }});
            }});

            const themeToggle = document.getElementById('themeToggle');
            if (themeToggle) {{
                themeToggle.addEventListener('click', () => {{
                    const nextTheme = document.body.classList.contains('theme-light') ? 'dark' : 'light';
                    applyTheme(nextTheme);
                }});
            }}

            setupMobileNav();
        }});
    </script>
</body>
</html>
"""


def main() -> None:
    args = parse_args()
    input_file: Path = args.input
    output_file: Path = args.output
    page_type: str = args.page_type

    if not input_file.exists():
        print(f"❌ 找不到來源檔案: {input_file}", file=sys.stderr)
        sys.exit(1)

    print(f"Converting {input_file} → {output_file} ({page_type})")

    md_content = read_file(input_file)
    title, date, stock_symbol = extract_title_and_date(md_content, input_file)
    content_html = markdown_to_html(md_content)
    html_page = create_html_page(title, date, content_html, page_type, stock_symbol)

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(html_page, encoding="utf-8")

    print(f"✅ Conversion complete: {output_file}")
    print(f"   Title: {title}")
    print(f"   Date: {date}")
    if stock_symbol:
        print(f"   Symbol: {stock_symbol}")
    print(f"   Type: {page_type}")


if __name__ == "__main__":
    main()
