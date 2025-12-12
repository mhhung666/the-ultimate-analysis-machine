#!/usr/bin/env python3
"""
Yahoo Finance 資料爬蟲工具
從 Yahoo Finance 爬取股票/匯率近期價格資料
"""

from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd

from common import (
    create_argument_parser,
    setup_output_path,
    write_output,
    print_status,
    print_error,
    validate_positive_int,
    safe_exit,
    ScraperError,
)


def fetch_market_data(symbol, weeks=52, output_file=None, year=None):
    """
    爬取市場資料

    Args:
        symbol: 股票代碼或匯率代碼 (例如: AAPL, TSLA, JPY=X)
        weeks: 要爬取的週數，預設52週（若指定 year 則忽略）
        output_file: 輸出檔案路徑，如果為 None 則輸出到 stdout
        year: 只輸出指定年份的資料
    """
    # 計算日期範圍
    if year:
        start_date = datetime(year, 1, 1)
        end_date = datetime(year + 1, 1, 1)
        display_end_date = datetime(year, 12, 31)
    else:
        end_date = datetime.now()
        start_date = end_date - timedelta(weeks=weeks)
        display_end_date = end_date

    print_status(f"正在爬取 {symbol} 資料...")
    print_status(f"日期範圍: {start_date.strftime('%Y-%m-%d')} 到 {display_end_date.strftime('%Y-%m-%d')}")

    # 使用 yfinance 爬取資料
    ticker = yf.Ticker(symbol)
    df = ticker.history(start=start_date, end=end_date)

    if df.empty:
        print_error("無法取得資料")
        return False

    if year:
        df = df[df.index.year == year]
        if df.empty:
            print_error(f"找不到 {year} 年的資料")
            return False

    # 排序資料 (最新的在上面)
    df = df.sort_index(ascending=False)

    # 格式化數據
    output_lines = []
    output_lines.append("| Date         | Open   | High   | Low    | Close  | Adj Close | Volume     |")
    output_lines.append("|--------------|--------|--------|--------|--------|-----------|------------|")

    for date, row in df.iterrows():
        date_str = date.strftime('%b %d, %Y')

        # 格式化數字 - 保留2位小數
        open_val = f"{row['Open']:.2f}" if pd.notna(row['Open']) else "—"
        high_val = f"{row['High']:.2f}" if pd.notna(row['High']) else "—"
        low_val = f"{row['Low']:.2f}" if pd.notna(row['Low']) else "—"
        close_val = f"{row['Close']:.2f}" if pd.notna(row['Close']) else "—"
        adj_close_val = f"{row['Close']:.2f}" if pd.notna(row['Close']) else "—"

        # 格式化交易量 - 加入千分位逗號
        volume_val = f"{int(row['Volume']):,}" if pd.notna(row['Volume']) and row['Volume'] > 0 else "—"

        line = f"| {date_str:12} | {open_val:6} | {high_val:6} | {low_val:6} | {close_val:6} | {adj_close_val:9} | {volume_val:10} |"
        output_lines.append(line)

    # 輸出結果
    result = '\n'.join(output_lines)

    success = write_output(result, output_file, verbose=True)
    if success:
        print_status(f"總共爬取了 {len(df)} 筆資料")

    return success


def main():
    parser = create_argument_parser(
        description='爬取 Yahoo Finance 股票/匯率歷史資料（建議輸出檔名：data/market-data/{YEAR}/Stocks/SYMBOL-YYYY-MM-DD.md）',
        epilog="""
使用範例:
  # 爬取 USD/JPY 匯率 (52週)
  python fetch_market_data.py JPY=X -o data/market-data/2025/Stocks/USDJPY.md

  # 爬取 UPS 股票 (52週)
  python fetch_market_data.py UPS -o UPS.md

  # 只輸入 symbol，自動儲存為 data/market-data/{YEAR}/Stocks/UPS.md
  python fetch_market_data.py UPS

  # 爬取 Apple 股票 (26週)
  python fetch_market_data.py AAPL -w 26 -o data/market-data/2025/Stocks/AAPL_26w.md

  # 只輸出 UPS 於 2024 年的資料
  python fetch_market_data.py UPS -y 2024 -o data/market-data/2024/Stocks/UPS-2024.md

常用代碼:
  股票: AAPL (Apple), TSLA (Tesla), MSFT (Microsoft), UPS, GOOGL
  匯率: JPY=X (USD/JPY), EUR=X (USD/EUR), GBP=X (USD/GBP)

命名建議:
  若每日更新，建議輸出為 data/market-data/{YEAR}/Stocks/SYMBOL-YYYY-MM-DD.md 以保留歷史資料
  若一次抓全年資料，可使用 data/market-data/{YEAR}/Stocks/SYMBOL.md
        """
    )

    parser.add_argument(
        'symbol',
        type=str,
        nargs='?',
        default='JPY=X',
        help='股票代碼或匯率代碼 (預設: JPY=X)'
    )

    parser.add_argument(
        '-w', '--weeks',
        type=int,
        default=52,
        help='要爬取的週數 (預設: 52週)'
    )

    parser.add_argument(
        '-o', '--output',
        type=str,
        help='輸出檔案路徑或檔名'
    )

    parser.add_argument(
        '-y', '--year',
        type=int,
        help='只輸出指定年份的資料（自動抓取整年度，忽略 -w 參數）'
    )

    parser.add_argument(
        '--stdout',
        action='store_true',
        help='強制輸出到螢幕（不自動儲存檔案）'
    )

    args = parser.parse_args()

    # 檢查參數
    try:
        if not args.year:
            validate_positive_int(args.weeks, "週數")
    except ScraperError as e:
        print_error(str(e))
        safe_exit(False)

    if args.stdout and args.output:
        print_error("已指定 --stdout 便無需再提供輸出檔案")
        safe_exit(False)

    # 設定輸出路徑
    default_filename = f"{args.symbol}.md"
    year = args.year if args.year else datetime.now().year
    output_file = setup_output_path(
        output_arg=args.output,
        default_filename=default_filename,
        default_subdir="Stocks",
        year=year,
        use_stdout=args.stdout
    )

    # 執行爬蟲
    success = fetch_market_data(
        symbol=args.symbol,
        weeks=args.weeks,
        output_file=output_file,
        year=args.year
    )

    safe_exit(success)


if __name__ == '__main__':
    main()
