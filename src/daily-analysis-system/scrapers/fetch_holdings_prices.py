#!/usr/bin/env python3
"""
持倉股票價格獲取工具
從 holdings.md 檔案中提取股票代碼，並從 Yahoo Finance 獲取當天價格
"""

import re
from datetime import datetime
from pathlib import Path
import yfinance as yf
import yaml

from common import (
    create_argument_parser,
    write_output,
    print_status,
    print_error,
    print_warning,
    get_project_root,
    get_config_directory,
    safe_exit,
    setup_output_path,
    generate_dated_filename,
)


def extract_holdings_from_yaml(holdings_file):
    """
    從 holdings.yaml 檔案中提取股票代碼

    Args:
        holdings_file: holdings.yaml 檔案路徑

    Returns:
        list: 股票代碼列表
    """
    holdings = []

    try:
        with open(holdings_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        # 遍歷所有持股群組
        if 'holdings' not in config:
            print_error("YAML 檔案中未找到 'holdings' 欄位")
            safe_exit(False)

        for group_name, stocks in config['holdings'].items():
            # 檢查群組是否為空
            if stocks is None:
                continue
            for stock_name, stock_info in stocks.items():
                # 只提取啟用的股票
                if stock_info.get('enabled', True):  # 預設為啟用
                    symbol = stock_info.get('symbol')
                    if symbol:
                        holdings.append(symbol)

        # 遍歷觀察清單
        if 'watchlist' in config:
            for group_name, stocks in config['watchlist'].items():
                # 檢查群組是否為空
                if stocks is None:
                    continue
                for stock_name, stock_info in stocks.items():
                    # 只提取啟用的股票
                    if stock_info.get('enabled', True):
                        symbol = stock_info.get('symbol')
                        if symbol and symbol not in holdings:  # 避免重複
                            holdings.append(symbol)

        print_status(f"從 {holdings_file} 中提取到 {len(holdings)} 隻啟用的股票（包含觀察清單）")

    except FileNotFoundError:
        print_error(f"找不到檔案 {holdings_file}")
        safe_exit(False)
    except yaml.YAMLError as e:
        print_error(f"解析 YAML 檔案時發生錯誤: {e}")
        safe_exit(False)
    except Exception as e:
        print_error(f"讀取檔案時發生錯誤: {e}")
        safe_exit(False)

    return holdings


def fetch_stock_price(symbol, verbose=False):
    """
    獲取單隻股票的當前價格資訊

    Args:
        symbol: 股票代碼
        verbose: 是否顯示詳細資訊

    Returns:
        dict: 包含股票資訊的字典，失敗返回 None
    """
    try:
        if verbose:
            print_status(f"正在獲取 {symbol} 的價格...")

        ticker = yf.Ticker(symbol)

        # 獲取最新價格資訊
        info = ticker.info

        # 獲取歷史數據（最近1天）
        hist = ticker.history(period='1d')

        if hist.empty:
            print_warning(f"{symbol} 無法獲取歷史數據")
            return None

        latest = hist.iloc[-1]

        # 提取關鍵資訊
        data = {
            'symbol': symbol,
            'name': info.get('longName', info.get('shortName', symbol)),
            'current_price': latest['Close'],
            'open': latest['Open'],
            'high': latest['High'],
            'low': latest['Low'],
            'volume': latest['Volume'],
            'previous_close': info.get('previousClose', latest['Close']),
            'market_cap': info.get('marketCap', None),
            'pe_ratio': info.get('trailingPE', None),
            'currency': info.get('currency', 'USD')
        }

        # 計算漲跌幅
        if data['previous_close'] and data['previous_close'] > 0:
            change = data['current_price'] - data['previous_close']
            change_percent = (change / data['previous_close']) * 100
            data['change'] = change
            data['change_percent'] = change_percent
        else:
            data['change'] = 0
            data['change_percent'] = 0

        return data

    except Exception as e:
        print_error(f"獲取 {symbol} 數據時發生錯誤: {e}")
        return None


def format_markdown_table(holdings_data):
    """
    將持倉數據格式化為 Markdown 表格

    Args:
        holdings_data: 包含股票數據的列表

    Returns:
        str: Markdown 格式的表格
    """
    lines = []

    # 添加標題和日期
    today = datetime.now().strftime('%Y-%m-%d')
    lines.append(f"# 📊 持倉股票價格分析")
    lines.append(f"\n> 更新時間: {today}\n")
    lines.append("---\n")

    # 表格頭部
    lines.append("| 代碼 | 名稱 | 當前價格 | 漲跌 | 漲跌幅 | 開盤 | 最高 | 最低 | 成交量 | 市值 |")
    lines.append("|------|------|----------|------|--------|------|------|------|--------|------|")

    # 統計數據
    total_stocks = len(holdings_data)
    up_count = 0
    down_count = 0
    flat_count = 0

    # 表格內容
    for data in holdings_data:
        if data is None:
            continue

        # 格式化價格
        price = f"${data['current_price']:.2f}"

        # 格式化漲跌
        change = data['change']
        change_percent = data['change_percent']

        if change > 0:
            change_str = f"+${change:.2f}"
            percent_str = f"🟢 +{change_percent:.2f}%"
            up_count += 1
        elif change < 0:
            change_str = f"-${abs(change):.2f}"
            percent_str = f"🔴 {change_percent:.2f}%"
            down_count += 1
        else:
            change_str = "$0.00"
            percent_str = "⚪ 0.00%"
            flat_count += 1

        # 格式化其他數值
        open_val = f"${data['open']:.2f}"
        high_val = f"${data['high']:.2f}"
        low_val = f"${data['low']:.2f}"
        volume_val = f"{int(data['volume']):,}" if data['volume'] > 0 else "—"

        # 格式化市值
        if data['market_cap']:
            market_cap_b = data['market_cap'] / 1_000_000_000
            market_cap_str = f"${market_cap_b:.2f}B"
        else:
            market_cap_str = "—"

        # 限制名稱長度
        name = data['name'][:30] + '...' if len(data['name']) > 30 else data['name']

        line = f"| {data['symbol']} | {name} | {price} | {change_str} | {percent_str} | {open_val} | {high_val} | {low_val} | {volume_val} | {market_cap_str} |"
        lines.append(line)

    # 添加統計資訊
    lines.append("\n---\n")
    lines.append("## 📈 市場概況\n")
    lines.append(f"- **總股票數**: {total_stocks}")
    lines.append(f"- **上漲**: 🟢 {up_count} ({up_count/total_stocks*100:.1f}%)")
    lines.append(f"- **下跌**: 🔴 {down_count} ({down_count/total_stocks*100:.1f}%)")
    lines.append(f"- **持平**: ⚪ {flat_count} ({flat_count/total_stocks*100:.1f}%)")

    return '\n'.join(lines)


def main():
    parser = create_argument_parser(
        description='獲取持倉股票的當天價格資訊（預設存成 output/market-data/{YEAR}/Daily/holdings-prices-YYYY-MM-DD.md）',
        epilog="""
使用範例:
  # 分析預設的 holdings 檔案
  python fetch_holdings_prices.py

  # 指定輸出檔案
  python fetch_holdings_prices.py -o output/market-data/2025/Daily/holdings-prices-2025-12-02.md

  # 顯示詳細資訊
  python fetch_holdings_prices.py -v

說明:
  若未指定 -o，程式會自動產生 output/market-data/{YEAR}/Daily/holdings-prices-YYYY-MM-DD.md
        """
    )

    parser.add_argument(
        '-i', '--input',
        type=str,
        default=None,
        help='holdings.yaml 檔案路徑 (預設: repo 根目錄的 config/holdings.yaml)'
    )

    parser.add_argument(
        '-o', '--output',
        type=str,
        help='輸出檔案路徑（若未指定則自動產生檔名）'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='顯示詳細資訊'
    )

    args = parser.parse_args()

    # 轉換為絕對路徑
    project_root = get_project_root()

    if args.input:
        holdings_file = Path(args.input)
        if not holdings_file.is_absolute():
            holdings_file = (project_root / holdings_file).resolve()
    else:
        holdings_file = get_config_directory() / 'holdings.yaml'

    if args.verbose:
        print_status(f"專案根目錄: {project_root}")
        print_status(f"Holdings 檔案: {holdings_file}")

    # 提取股票代碼
    symbols = extract_holdings_from_yaml(holdings_file)

    if not symbols:
        print_error("未找到任何股票代碼")
        safe_exit(False)

    if args.verbose:
        print_status(f"找到的股票: {', '.join(symbols)}")

    # 獲取每隻股票的價格
    print_status(f"\n正在獲取 {len(symbols)} 隻股票的價格資訊...\n")

    holdings_data = []
    for i, symbol in enumerate(symbols, 1):
        print_status(f"[{i}/{len(symbols)}] {symbol}...")
        data = fetch_stock_price(symbol, verbose=args.verbose)
        if data:
            holdings_data.append(data)
            print_status("  ✓")
        else:
            print_status("  ✗")

    if not holdings_data:
        print_error("無法獲取任何股票數據")
        safe_exit(False)

    # 產生 Markdown 表格
    markdown_output = format_markdown_table(holdings_data)

    # 決定輸出檔案路徑
    filename = generate_dated_filename("holdings-prices", "md")
    output_file = setup_output_path(
        output_arg=args.output,
        default_filename=filename,
        default_subdir="Daily",
        use_stdout=False
    )

    # 寫入檔案
    write_output(markdown_output, output_file, verbose=True)

    print_status(f"\n成功獲取 {len(holdings_data)}/{len(symbols)} 隻股票的價格資訊")


if __name__ == '__main__':
    main()
