#!/usr/bin/env python3
"""
OpenInsider 內部人交易抓取與格式化
提供 fetch_openinsider_markdown 給其他爬蟲整合使用
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

import requests
from bs4 import BeautifulSoup

from common import print_status, print_warning


OPENINSIDER_URL = "http://openinsider.com/search?q={symbol}"


def _parse_date(value: str) -> Optional[datetime]:
    if not value:
        return None
    value = value.strip()
    formats = [
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%b %d, %Y",
        "%b %d %Y",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def _fetch_openinsider_html(symbol: str) -> Optional[str]:
    url = OPENINSIDER_URL.format(symbol=symbol.upper())
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0 Safari/537.36"
        )
    }
    try:
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        return resp.text
    except requests.RequestException:
        return None


def _extract_trades(symbol: str, html: str, max_items: int) -> List[Dict[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    tables = soup.find_all("table")
    if not tables:
        return []

    target_table = None
    expected_headers = {
        "insider",
        "insider name",
        "ticker",
        "trans type",
        "transaction",
        "trade date",
        "filing date",
    }
    for table in tables:
        headers = [th.get_text(strip=True).lower() for th in table.find_all("th")]
        if headers and any(h in expected_headers for h in headers):
            target_table = table
            break

    if target_table is None:
        return []

    header_map = {}
    headers = [th.get_text(strip=True).lower() for th in target_table.find_all("th")]
    for idx, text in enumerate(headers):
        header_map[text] = idx

    def find_idx(possible):
        for key in possible:
            if key in header_map:
                return header_map[key]
        for key, value in header_map.items():
            if any(p in key for p in possible):
                return value
        return None

    idx_insider = find_idx(["insider name", "insider", "name"])
    idx_type = find_idx(["trans type", "transaction", "type"])
    idx_qty = find_idx(["qty", "quantity", "shares"])
    idx_price = find_idx(["price"])
    idx_ticker = find_idx(["ticker"])
    idx_trade_date = find_idx(["trade date", "date"])
    idx_filing_date = find_idx(["filing date", "filed"])
    idx_value = find_idx(["value", "amount"])

    def col_text(cols, i):
        if i is None or i >= len(cols):
            return ""
        return cols[i].get_text(strip=True)

    rows = [row for row in target_table.find_all("tr") if row.find("td")]
    items = []
    for row in rows[: max_items * 2]:
        cols = row.find_all("td")
        ticker = col_text(cols, idx_ticker).upper()
        if symbol.upper() not in ticker:
            continue
        items.append(
            {
                "insider": col_text(cols, idx_insider),
                "trans_type": col_text(cols, idx_type),
                "qty": col_text(cols, idx_qty),
                "price": col_text(cols, idx_price),
                "value": col_text(cols, idx_value),
                "trade_date": col_text(cols, idx_trade_date),
                "filing_date": col_text(cols, idx_filing_date),
            }
        )
        if len(items) >= max_items:
            break
    return items


def fetch_openinsider_markdown(
    symbol: str,
    *,
    days: int = 7,
    max_items: int = 25,
    verbose: bool = False,
) -> str:
    if verbose:
        print_status(f"抓取 OpenInsider 內部人交易: {symbol}")

    html = _fetch_openinsider_html(symbol)
    if not html:
        return ""

    items = _extract_trades(symbol, html, max_items)
    if not items:
        return ""

    cutoff = datetime.utcnow() - timedelta(days=days)
    filtered = []
    for item in items:
        trade_date = _parse_date(item.get("trade_date", ""))
        filing_date = _parse_date(item.get("filing_date", ""))
        key_date = trade_date or filing_date
        if key_date and key_date < cutoff:
            continue
        item["parsed_date"] = (key_date or datetime.utcnow()).strftime("%Y-%m-%d")
        filtered.append(item)

    if not filtered:
        return ""

    if verbose:
        print_warning(f"OpenInsider 取得 {len(filtered)} 筆 (近 {days} 天)")

    lines = [
        "",
        f"## OpenInsider 內部人交易 (近 {days} 天)",
        "",
    ]
    for item in filtered:
        lines.append("### 交易紀錄")
        lines.append(f"- 股票: {symbol.upper()}")
        lines.append(f"- 發布時間: {item.get('parsed_date', '')}")
        lines.append(f"- 交易類型: {item.get('trans_type', '')}")
        lines.append(f"- 內部人: {item.get('insider', '')}")
        lines.append(f"- 交易數量: {item.get('qty', '')}")
        lines.append(f"- 交易價格: {item.get('price', '')}")
        lines.append(f"- 交易金額: {item.get('value', '')}")
        lines.append(f"- 交易日: {item.get('trade_date', '')}")
        lines.append("")

    return "\n".join(lines).strip() + "\n"


if __name__ == "__main__":
    print_warning("此模組提供函式給其他爬蟲使用，請勿直接執行。")
