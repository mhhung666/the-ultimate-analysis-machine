#!/usr/bin/env python3
"""
全球市場大盤指數資料爬蟲工具
爬取今日全球主要市場的大盤指數數據
包含：日本、韓國、台灣、中國、新加坡、香港、歐洲、美國
"""

from datetime import datetime
import yfinance as yf
import pandas as pd
import yaml

from common import (
    create_argument_parser,
    setup_output_path,
    write_output,
    print_status,
    print_error,
    print_success,
    print_warning,
    generate_dated_filename,
    get_config_directory,
)


def load_indices_config():
    """
    從 YAML 配置檔載入全球指數設定

    Returns:
        dict: 全球指數配置字典
    """
    config_path = get_config_directory() / "indices.yaml"

    if not config_path.exists():
        print_error(f"找不到配置檔: {config_path}")
        exit(1)

    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    return config.get('global_indices', {})


# 從 YAML 配置檔載入全球指數設定
GLOBAL_INDICES = load_indices_config()


def fetch_index_data(symbol, index_name):
    """
    爬取單一指數的今日資料

    Args:
        symbol: Yahoo Finance 代碼
        index_name: 指數名稱

    Returns:
        dict: 包含指數資料的字典，如果失敗則返回 None
    """
    try:
        ticker = yf.Ticker(symbol)
        # 獲取最近2天的資料（確保能取到今日資料）
        df = ticker.history(period='2d')

        if df.empty:
            print_warning(f"{index_name} ({symbol}): 無法取得資料")
            return None

        # 取最新一筆資料
        latest = df.iloc[-1]
        latest_date = df.index[-1]

        # 計算漲跌
        # 優先使用前一天收盤價，如果沒有則用今天開盤價
        if len(df) >= 2:
            prev_close = df.iloc[-2]['Close']
            change = latest['Close'] - prev_close
            change_pct = (change / prev_close) * 100
        elif pd.notna(latest['Open']) and latest['Open'] > 0:
            # 盤中狀態：用今天開盤價計算
            change = latest['Close'] - latest['Open']
            change_pct = (change / latest['Open']) * 100
        else:
            change = 0
            change_pct = 0

        return {
            'name': index_name,
            'symbol': symbol,
            'date': latest_date,
            'open': latest['Open'],
            'high': latest['High'],
            'low': latest['Low'],
            'close': latest['Close'],
            'volume': latest['Volume'],
            'change': change,
            'change_pct': change_pct,
            'market': None,  # Will be set later
        }

    except Exception as e:
        print_error(f"{index_name} ({symbol}): {str(e)}")
        return None


def format_all_market_data(all_data, use_emoji=True):
    """
    格式化所有市場的資料為單一 Markdown 表格

    Args:
        all_data: 所有市場的資料字典
        use_emoji: 是否使用 emoji 符號

    Returns:
        str: Markdown 格式的表格
    """
    lines = []
    lines.append("| 國家/地區 | 指數名稱 | 收盤價 | 開盤 | 最高 | 最低 | 成交量 | 漲跌 | 漲跌幅 |")
    lines.append("|----------|---------|--------|------|------|------|--------|------|--------|")

    # 按照預定義的順序輸出
    for market_name in GLOBAL_INDICES.keys():
        if market_name not in all_data:
            continue

        indices_data = all_data[market_name]
        for data in indices_data:
            market = data['market']
            name = data['name']
            close = f"{data['close']:,.2f}"
            open_val = f"{data['open']:,.2f}"
            high = f"{data['high']:,.2f}"
            low = f"{data['low']:,.2f}"
            volume = f"{int(data['volume']):,}" if data['volume'] > 0 else "—"
            change = f"{data['change']:+,.2f}"
            change_pct = f"{data['change_pct']:+.2f}%"

            # 根據漲跌添加顏色標記
            if use_emoji:
                if data['change'] > 0:
                    change_color = f"🔺 {change}"
                    pct_color = f"🔺 {change_pct}"
                elif data['change'] < 0:
                    change_color = f"🔻 {change}"
                    pct_color = f"🔻 {change_pct}"
                else:
                    change_color = change
                    pct_color = change_pct
            else:
                change_color = change
                pct_color = change_pct

            line = f"| {market} | {name} | {close} | {open_val} | {high} | {low} | {volume} | {change_color} | {pct_color} |"
            lines.append(line)

    return '\n'.join(lines)


def fetch_all_indices(regions=None):
    """
    爬取所有或指定區域的市場指數資料

    Args:
        regions: 要爬取的區域列表，None 表示全部

    Returns:
        dict: 各區域的資料
    """
    results = {}

    markets_to_fetch = GLOBAL_INDICES
    if regions:
        markets_to_fetch = {k: v for k, v in GLOBAL_INDICES.items() if k in regions}

    for market_name, indices in markets_to_fetch.items():
        print_status(f"\n正在爬取 {market_name} 市場指數...")
        market_data = []

        for index_name, index_config in indices.items():
            # 支援新舊兩種格式
            # 新格式: {'symbol': '^GSPC', 'fetch_news': true}
            # 舊格式: '^GSPC'
            if isinstance(index_config, dict):
                symbol = index_config.get('symbol', '')
            else:
                symbol = index_config

            print_status(f"  → {index_name} ({symbol})")
            data = fetch_index_data(symbol, index_name)
            if data:
                data['market'] = market_name  # Set the market name
                market_data.append(data)
                print_status(f"  ✓ {index_name}: {data['close']:.2f} ({data['change_pct']:+.2f}%)")

        results[market_name] = market_data

    return results


def main():
    parser = create_argument_parser(
        description='爬取全球主要市場大盤指數今日資料（預設存成 data/market-data/{YEAR}/Daily/global-indices-YYYY-MM-DD.md）',
        epilog="""
使用範例:
  # 爬取所有市場指數
  python fetch_global_indices.py

  # 爬取特定區域
  python fetch_global_indices.py -r 美國 日本 台灣

  # 指定輸出檔案
  python fetch_global_indices.py -o data/market-data/2025/Daily/global-indices-2025-11-18.md

可用區域:
  日本、韓國、台灣、中國、新加坡、香港、歐洲、美國

說明:
  若未指定 -o，程式會自動產生 data/market-data/{YEAR}/Daily/global-indices-YYYY-MM-DD.md
        """
    )

    parser.add_argument(
        '-r', '--regions',
        type=str,
        nargs='+',
        help='要爬取的區域（可多選），不指定則爬取全部'
    )

    parser.add_argument(
        '-o', '--output',
        type=str,
        help='輸出檔案路徑（若未指定則自動產生檔名）'
    )

    parser.add_argument(
        '--no-emoji',
        action='store_true',
        help='不使用 emoji 符號'
    )

    args = parser.parse_args()

    # 驗證區域名稱
    if args.regions:
        invalid_regions = [r for r in args.regions if r not in GLOBAL_INDICES]
        if invalid_regions:
            print_error(f"無效的區域名稱: {', '.join(invalid_regions)}")
            print_status(f"可用區域: {', '.join(GLOBAL_INDICES.keys())}")
            exit(1)

    # 爬取資料
    print_status("=" * 60)
    print_status("全球市場大盤指數資料爬蟲")
    print_status("=" * 60)

    results = fetch_all_indices(regions=args.regions)

    # 產生報告
    today = datetime.now()
    output_lines = []
    output_lines.append(f"# 全球市場大盤指數 - {today.strftime('%Y-%m-%d')}\n")
    output_lines.append(f"**更新時間**: {today.strftime('%Y-%m-%d %H:%M:%S')}\n")

    # 使用單一表格輸出所有資料
    use_emoji = not args.no_emoji
    output_lines.append(format_all_market_data(results, use_emoji=use_emoji))

    output_lines.append("\n---\n")
    output_lines.append("*資料來源: Yahoo Finance*\n")

    result_text = '\n'.join(output_lines)

    # 決定輸出檔案路徑
    filename = generate_dated_filename("global-indices", "md")
    output_file = setup_output_path(
        output_arg=args.output,
        default_filename=filename,
        default_subdir="Daily",
        use_stdout=False
    )

    # 寫入檔案
    write_output(result_text, output_file, verbose=True)

    print_status("\n" + "=" * 60)

    # 統計資訊
    total_indices = sum(len(data) for data in results.values())
    print_success(f"總共爬取了 {len(results)} 個市場的 {total_indices} 個指數")
    print_status("=" * 60)


if __name__ == '__main__':
    main()
