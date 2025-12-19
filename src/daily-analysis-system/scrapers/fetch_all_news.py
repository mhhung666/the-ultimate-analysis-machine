#!/usr/bin/env python3
"""
批次爬取所有配置的股票和指數新聞
從 repo 根目錄的 config/holdings.yaml 與 config/indices.yaml 讀取設定
只爬取 fetch_news: true 的項目
"""

import sys
import yaml
from fetch_market_news import fetch_market_news
from openinsider_trades import fetch_openinsider_markdown
from common import (
    print_status,
    print_error,
    safe_exit,
    get_config_directory,
    generate_dated_filename,
    setup_output_path,
)


def load_config(config_file):
    """載入 YAML 配置檔"""
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print_error(f"無法讀取配置檔 {config_file}: {e}")
        return None


def extract_symbols_from_holdings(config):
    """從 holdings.yaml 提取需要爬取新聞的股票代碼"""
    symbols = []
    if not config or 'holdings' not in config:
        return symbols

    for category, stocks in config['holdings'].items():
        # 檢查群組是否為空
        if stocks is None:
            continue
        for name, data in stocks.items():
            if data.get('enabled', True) and data.get('fetch_news', False):
                symbols.append({
                    'symbol': data['symbol'],
                    'name': name,
                    'type': 'stock'
                })

    return symbols


def extract_symbols_from_watchlist(config):
    """從 holdings.yaml 提取觀察清單中需要爬取新聞的股票代碼"""
    symbols = []
    if not config or 'watchlist' not in config:
        return symbols

    for category, stocks in config['watchlist'].items():
        # 檢查群組是否為空
        if stocks is None:
            continue
        for name, data in stocks.items():
            if data.get('enabled', True) and data.get('fetch_news', False):
                symbols.append({
                    'symbol': data['symbol'],
                    'name': name,
                    'type': 'watchlist'
                })

    return symbols


def extract_symbols_from_indices(config):
    """從 indices.yaml 提取需要爬取新聞的指數代碼"""
    symbols = []
    if not config or 'global_indices' not in config:
        return symbols

    for region, indices in config['global_indices'].items():
        # 檢查群組是否為空
        if indices is None:
            continue
        for name, data in indices.items():
            if data.get('fetch_news', False):
                symbols.append({
                    'symbol': data['symbol'],
                    'name': name,
                    'type': 'index'
                })

    return symbols


def main():
    # 取得配置檔路徑
    config_dir = get_config_directory()
    holdings_config_file = config_dir / 'holdings.yaml'
    indices_config_file = config_dir / 'indices.yaml'

    print_status("正在載入配置檔...")

    # 載入配置
    holdings_config = load_config(holdings_config_file)
    indices_config = load_config(indices_config_file)

    if not holdings_config and not indices_config:
        print_error("無法載入任何配置檔")
        safe_exit(False)

    # 提取需要爬取新聞的股票和指數
    symbols = []

    if holdings_config:
        stock_symbols = extract_symbols_from_holdings(holdings_config)
        symbols.extend(stock_symbols)
        print_status(f"從 holdings.yaml 找到 {len(stock_symbols)} 隻需要爬取新聞的股票")

        watchlist_symbols = extract_symbols_from_watchlist(holdings_config)
        symbols.extend(watchlist_symbols)
        print_status(f"從 holdings.yaml 找到 {len(watchlist_symbols)} 隻觀察清單股票")

    if indices_config:
        index_symbols = extract_symbols_from_indices(indices_config)
        symbols.extend(index_symbols)
        print_status(f"從 indices.yaml 找到 {len(index_symbols)} 個需要爬取新聞的指數")

    if not symbols:
        print_error("沒有找到任何需要爬取新聞的項目（請檢查配置檔中的 fetch_news 設定）")
        safe_exit(False)

    print_status(f"總共需要爬取 {len(symbols)} 個項目的新聞\n")

    # 依序爬取每個項目的新聞
    success_count = 0
    failed_count = 0

    for i, item in enumerate(symbols, 1):
        symbol = item['symbol']
        name = item['name']
        item_type = item['type']

        print_status(f"[{i}/{len(symbols)}] 正在爬取 {name} ({symbol}) 的新聞...")

        try:
            # 爬取新聞（自動產生檔名，預設 10 則新聞）
            success = fetch_market_news(
                symbol=symbol,
                limit=10,
                output_file=None,
                json_output=False,
                auto_filename=True
            )

            if success:
                if item_type in ("stock", "watchlist"):
                    news_filename = generate_dated_filename(symbol, "md")
                    news_path = setup_output_path(
                        output_arg=news_filename,
                        default_filename=news_filename,
                        default_subdir="News",
                        use_stdout=False,
                    )
                    insider_section = fetch_openinsider_markdown(symbol, days=7, max_items=25)
                    if insider_section and news_path:
                        existing = ""
                        try:
                            with open(news_path, "r", encoding="utf-8") as f:
                                existing = f.read()
                        except OSError:
                            existing = ""
                        if "OpenInsider 內部人交易" not in existing:
                            with open(news_path, "a", encoding="utf-8") as f:
                                f.write("\n")
                                f.write(insider_section)
                success_count += 1
                print_status(f"  ✓ 完成\n")
            else:
                failed_count += 1
                print_error(f"  ✗ 失敗\n")

        except Exception as e:
            failed_count += 1
            print_error(f"  ✗ 發生錯誤: {e}\n")

    # 顯示總結
    print("=" * 60)
    print_status(f"新聞爬取完成!")
    print_status(f"成功: {success_count}/{len(symbols)}")
    if failed_count > 0:
        print_error(f"失敗: {failed_count}/{len(symbols)}")
    print("=" * 60)

    # 如果所有項目都成功，則回傳成功
    safe_exit(failed_count == 0)


if __name__ == '__main__':
    main()
