"""
金融資料爬蟲工具集

此模組包含用於爬取各種金融資料的工具：
- fetch_market_data: 爬取股票/匯率歷史價格
- fetch_market_news: 爬取股票相關新聞
- fetch_global_indices: 爬取全球市場大盤指數
- fetch_holdings_prices: 爬取持倉股票當前價格
"""

from .common import (
    ScraperError,
    create_argument_parser,
    setup_output_path,
    write_output,
    print_status,
    print_error,
    print_success,
    get_project_root,
    get_data_directory,
)

__all__ = [
    'ScraperError',
    'create_argument_parser',
    'setup_output_path',
    'write_output',
    'print_status',
    'print_error',
    'print_success',
    'get_project_root',
    'get_data_directory',
]
