"""
爬蟲共用模組

提供所有爬蟲工具共用的功能：
- argparse 設定
- 輸出處理（檔案/stdout）
- 錯誤處理
- 路徑管理
"""

import argparse
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Union


class ScraperError(Exception):
    """爬蟲錯誤基類"""
    pass


def get_project_root() -> Path:
    """
    取得專案根目錄路徑

    Returns:
        Path: 專案根目錄的絕對路徑
    """
    # 從 scrapers 目錄往上回到專案根目錄
    return Path(__file__).resolve().parents[1]


def get_repo_root() -> Path:
    """
    取得整個 monorepo 根目錄

    Returns:
        Path: repo 根目錄的絕對路徑
    """
    return get_project_root().parent.parent


def get_config_directory() -> Path:
    """
    取得配置檔所在目錄

    優先順序：
    1. 環境變數 CONFIG_DIR
    2. repo 根目錄的 config/
    3. 兼容舊版: 專案內部的 config/

    Returns:
        Path: config 目錄路徑
    """
    env_dir = os.environ.get('CONFIG_DIR')
    if env_dir:
        return Path(env_dir).expanduser().resolve()

    repo_config = get_repo_root() / "config"
    if repo_config.exists():
        return repo_config

    # 兼容舊版結構
    return get_project_root() / "config"


def get_data_directory(year: Optional[int] = None, subdir: str = "") -> Path:
    """
    取得資料目錄路徑

    Args:
        year: 年份，預設為當前年份
        subdir: 子目錄名稱 (例如: "Daily", "Stocks", "News")

    Returns:
        Path: 資料目錄的路徑
    """
    if year is None:
        year = datetime.now().year

    # 支援從環境變數讀取輸出目錄,預設為 /app/output (Docker 環境) 或專案根目錄的 output
    output_base = os.environ.get('OUTPUT_DIR')
    if output_base:
        data_dir = Path(output_base) / "market-data" / str(year)
    else:
        data_dir = get_project_root() / "output" / "market-data" / str(year)

    if subdir:
        data_dir = data_dir / subdir

    return data_dir


def create_argument_parser(
    description: str,
    epilog: str = "",
) -> argparse.ArgumentParser:
    """
    建立標準化的 ArgumentParser

    Args:
        description: 程式描述
        epilog: 使用範例說明

    Returns:
        argparse.ArgumentParser: 設定好的解析器
    """
    parser = argparse.ArgumentParser(
        description=description,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=epilog
    )
    return parser


def add_common_arguments(parser: argparse.ArgumentParser) -> None:
    """
    添加共用的命令列參數

    Args:
        parser: ArgumentParser 實例
    """
    parser.add_argument(
        '-o', '--output',
        type=str,
        help='輸出檔案路徑'
    )

    parser.add_argument(
        '--stdout',
        action='store_true',
        help='輸出到螢幕而非檔案'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='顯示詳細資訊'
    )


def setup_output_path(
    output_arg: Optional[str],
    default_filename: str,
    default_subdir: str = "Stocks",
    year: Optional[int] = None,
    use_stdout: bool = False
) -> Optional[Path]:
    """
    設定輸出路徑

    Args:
        output_arg: 使用者指定的輸出路徑
        default_filename: 預設檔名
        default_subdir: 預設子目錄 (例如: "Daily", "Stocks", "News")
        year: 年份，預設為當前年份
        use_stdout: 是否輸出到螢幕

    Returns:
        Optional[Path]: 輸出路徑，如果是 stdout 則返回 None
    """
    if use_stdout:
        return None

    if output_arg:
        output_path = Path(output_arg)
        # 如果是相對路徑且不包含目錄分隔符，放到預設目錄
        if not output_path.is_absolute() and '/' not in output_arg and '\\' not in output_arg:
            return get_data_directory(year, default_subdir) / output_arg
        return output_path

    # 使用預設路徑
    return get_data_directory(year, default_subdir) / default_filename


def write_output(
    content: str,
    output_path: Optional[Path],
    verbose: bool = False
) -> bool:
    """
    寫入輸出內容

    Args:
        content: 要寫入的內容
        output_path: 輸出路徑，None 表示輸出到 stdout
        verbose: 是否顯示詳細資訊

    Returns:
        bool: 是否成功
    """
    try:
        if output_path is None:
            print(content)
        else:
            # 確保目錄存在
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)

            if verbose:
                print_success(f"資料已儲存到: {output_path}")

        return True

    except IOError as e:
        print_error(f"寫入檔案時發生錯誤: {e}")
        return False


def print_status(message: str) -> None:
    """
    印出狀態訊息到 stderr

    Args:
        message: 狀態訊息
    """
    print(message, file=sys.stderr)


def print_error(message: str) -> None:
    """
    印出錯誤訊息到 stderr

    Args:
        message: 錯誤訊息
    """
    print(f"錯誤: {message}", file=sys.stderr)


def print_success(message: str) -> None:
    """
    印出成功訊息到 stderr

    Args:
        message: 成功訊息
    """
    print(f"✓ {message}", file=sys.stderr)


def print_warning(message: str) -> None:
    """
    印出警告訊息到 stderr

    Args:
        message: 警告訊息
    """
    print(f"⚠ {message}", file=sys.stderr)


def validate_positive_int(value: int, name: str) -> None:
    """
    驗證正整數參數

    Args:
        value: 要驗證的值
        name: 參數名稱

    Raises:
        ScraperError: 如果值不是正整數
    """
    if value <= 0:
        raise ScraperError(f"{name} 必須大於 0")


def generate_dated_filename(
    prefix: str,
    extension: str = "md",
    date: Optional[datetime] = None
) -> str:
    """
    產生帶日期的檔名

    Args:
        prefix: 檔名前綴 (例如: "AAPL", "global-indices")
        extension: 副檔名 (預設: "md")
        date: 日期，預設為今天

    Returns:
        str: 格式化的檔名 (例如: "AAPL-2025-11-20.md")
    """
    if date is None:
        date = datetime.now()

    return f"{prefix}-{date.strftime('%Y-%m-%d')}.{extension}"


def safe_exit(success: bool = True) -> None:
    """
    安全退出程式

    Args:
        success: 是否成功，False 時使用 exit code 1
    """
    sys.exit(0 if success else 1)
