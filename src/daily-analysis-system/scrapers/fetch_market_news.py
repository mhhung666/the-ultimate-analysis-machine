#!/usr/bin/env python3
"""
Yahoo Finance 金融新聞爬蟲工具
從 Yahoo Finance 爬取特定股票的最新金融新聞
"""

from datetime import datetime
import yfinance as yf
import json

from common import (
    create_argument_parser,
    setup_output_path,
    write_output,
    print_status,
    print_error,
    validate_positive_int,
    safe_exit,
    generate_dated_filename,
    ScraperError,
)


def format_datetime(date_str):
    """
    將 ISO 8601 格式的日期時間轉換為易讀格式

    Args:
        date_str: ISO 8601 格式的日期時間字串 (例如: 2025-11-17T21:06:41Z)

    Returns:
        格式化後的日期時間字串 (例如: Nov 17, 2025 21:06 UTC)
    """
    try:
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return dt.strftime('%b %d, %Y %H:%M UTC')
    except:
        return date_str


def fetch_market_news(symbol, limit=10, output_file=None, json_output=False, auto_filename=False):
    """
    爬取股票相關新聞

    Args:
        symbol: 股票代碼 (例如: AAPL, TSLA, NVDA)
        limit: 要顯示的新聞數量，預設10則
        output_file: 輸出檔案路徑，如果為 None 則根據 auto_filename 決定
        json_output: 是否輸出為 JSON 格式，預設 False (Markdown 格式)
        auto_filename: 是否自動產生檔名（格式：SYMBOL-YYYY-MM-DD.md）
    """
    print_status(f"正在爬取 {symbol} 的最新新聞...")

    # 使用 yfinance 爬取新聞
    ticker = yf.Ticker(symbol)
    news = ticker.news

    if not news:
        print_error("無法取得新聞資料")
        return False

    # 限制新聞數量
    news = news[:limit]

    print_status(f"找到 {len(news)} 則新聞")

    # 格式化輸出
    if json_output:
        # JSON 格式輸出
        output_data = []
        for article in news:
            content = article.get('content', {})
            output_data.append({
                'id': content.get('id'),
                'title': content.get('title'),
                'summary': content.get('summary'),
                'publisher': content.get('provider', {}).get('displayName'),
                'published_at': content.get('pubDate'),
                'url': content.get('canonicalUrl', {}).get('url'),
                'content_type': content.get('contentType')
            })

        result = json.dumps(output_data, indent=2, ensure_ascii=False)
    else:
        # Markdown 格式輸出
        output_lines = []
        output_lines.append(f"# {symbol} 最新金融新聞\n")
        output_lines.append(f"**更新時間**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        output_lines.append(f"**新聞數量**: {len(news)} 則\n")
        output_lines.append("---\n")

        for i, article in enumerate(news, 1):
            content = article.get('content', {})

            # 提取資訊
            title = content.get('title', 'N/A')
            summary = content.get('summary', 'N/A')
            pub_date = content.get('pubDate', 'N/A')
            provider = content.get('provider', {}).get('displayName', 'N/A')
            url = content.get('canonicalUrl', {}).get('url', '#')
            content_type = content.get('contentType', 'ARTICLE')

            # 格式化日期
            formatted_date = format_datetime(pub_date) if pub_date != 'N/A' else 'N/A'

            # 新聞類型圖示
            type_icon = "🎥" if content_type == "VIDEO" else "📰"

            # 組合輸出
            output_lines.append(f"## {i}. {type_icon} {title}\n")
            output_lines.append(f"**來源**: {provider}  ")
            output_lines.append(f"**發布時間**: {formatted_date}  ")
            output_lines.append(f"**連結**: [{url}]({url})\n")
            output_lines.append(f"**摘要**:  ")
            output_lines.append(f"{summary}\n")
            output_lines.append("---\n")

        result = '\n'.join(output_lines)

    # 決定輸出檔案路徑
    if output_file:
        final_output = output_file
    elif auto_filename:
        # 自動產生檔名（格式：SYMBOL-YYYY-MM-DD.md 或 .json）
        extension = 'json' if json_output else 'md'
        filename = generate_dated_filename(symbol, extension)
        final_output = setup_output_path(
            output_arg=filename,
            default_filename=filename,
            default_subdir="News",
            use_stdout=False
        )
    else:
        final_output = None

    # 輸出結果
    return write_output(result, final_output, verbose=True)


def main():
    parser = create_argument_parser(
        description='爬取 Yahoo Finance 股票相關新聞（預設輸出 data/market-data/{YEAR}/News/SYMBOL-YYYY-MM-DD.md）',
        epilog="""
使用範例:
  # 爬取 Apple 的最新新聞 (預設10則，自動產生檔名)
  python fetch_market_news.py AAPL

  # 爬取 Tesla 的最新5則新聞並儲存為 Markdown
  python fetch_market_news.py TSLA -l 5

  # 指定輸出檔案
  python fetch_market_news.py NVDA -o data/market-data/2025/News/NVDA-2025-11-18.md

  # 爬取多家公司的新聞（會自動產生帶日期的檔名）
  python fetch_market_news.py AAPL
  python fetch_market_news.py MSFT

常用股票代碼:
  科技股: AAPL (Apple), TSLA (Tesla), NVDA (Nvidia), MSFT (Microsoft), GOOGL (Google)
  金融股: JPM (JP Morgan), BAC (Bank of America), GS (Goldman Sachs)
  其他: UPS, AMZN (Amazon), META (Meta/Facebook)
        """
    )

    parser.add_argument(
        'symbol',
        type=str,
        help='股票代碼 (例如: AAPL, TSLA, NVDA)'
    )

    parser.add_argument(
        '-l', '--limit',
        type=int,
        default=10,
        help='要顯示的新聞數量 (預設: 10則)'
    )

    parser.add_argument(
        '-o', '--output',
        type=str,
        help='輸出檔案路徑 (若未指定則自動產生帶日期的檔名)'
    )

    parser.add_argument(
        '--json',
        action='store_true',
        help='輸出為 JSON 格式 (預設為 Markdown 格式)'
    )

    parser.add_argument(
        '--stdout',
        action='store_true',
        help='輸出到螢幕而非檔案'
    )

    args = parser.parse_args()

    # 檢查參數
    try:
        validate_positive_int(args.limit, "新聞數量")
    except ScraperError as e:
        print_error(str(e))
        safe_exit(False)

    # 決定是否使用自動檔名
    # 如果有指定 -o 或 --stdout，則不使用自動檔名
    auto_filename = not args.output and not args.stdout

    # 執行爬蟲
    success = fetch_market_news(
        symbol=args.symbol,
        limit=args.limit,
        output_file=args.output,
        json_output=args.json,
        auto_filename=auto_filename
    )

    safe_exit(success)


if __name__ == '__main__':
    main()
