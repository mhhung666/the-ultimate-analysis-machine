"""
common.py 單元測試
"""

import sys
from datetime import datetime
from pathlib import Path
from io import StringIO

import pytest

from common import (
    ScraperError,
    get_project_root,
    get_repo_root,
    get_config_directory,
    get_data_directory,
    create_argument_parser,
    setup_output_path,
    write_output,
    print_status,
    print_error,
    print_success,
    print_warning,
    validate_positive_int,
    generate_dated_filename,
)


class TestGetProjectRoot:
    """測試 get_project_root 函數"""

    def test_returns_path(self):
        """應該返回 Path 物件"""
        result = get_project_root()
        assert isinstance(result, Path)

    def test_path_is_absolute(self):
        """應該返回絕對路徑"""
        result = get_project_root()
        assert result.is_absolute()

    def test_path_contains_expected_structure(self):
        """路徑應該包含預期的專案結構"""
        result = get_project_root()
        # 專案根目錄應該包含專案核心目錄
        scrapers_paths = [
            result / "src" / "scrapers",
            result / "scrapers",
        ]
        assert any(path.exists() for path in scrapers_paths)
        assert (result / "reports").exists()


class TestGetRepoRoot:
    """測試 get_repo_root 函數"""

    def test_contains_src_directory(self):
        """repo root 應包含 src 目錄"""
        result = get_repo_root()
        assert (result / "src").exists()
        assert (result / "config").exists()


class TestGetConfigDirectory:
    """測試 get_config_directory 函數"""

    def test_env_override(self, tmp_path, monkeypatch):
        """設定 CONFIG_DIR 時應使用自訂路徑"""
        custom_dir = tmp_path / "custom-config"
        custom_dir.mkdir()
        monkeypatch.setenv("CONFIG_DIR", str(custom_dir))
        try:
            result = get_config_directory()
            assert result == custom_dir
        finally:
            monkeypatch.delenv("CONFIG_DIR", raising=False)

    def test_defaults_to_repo_config(self):
        """預設應返回 repo 根目錄的 config"""
        result = get_config_directory()
        assert result.name == "config"
        assert (result / "holdings.yaml").exists()


class TestGetDataDirectory:
    """測試 get_data_directory 函數"""

    def test_default_year(self):
        """預設應該使用當前年份"""
        result = get_data_directory()
        current_year = datetime.now().year
        assert str(current_year) in str(result)

    def test_specific_year(self):
        """應該支援指定年份"""
        result = get_data_directory(year=2024)
        assert "2024" in str(result)

    def test_with_subdir(self):
        """應該支援子目錄"""
        result = get_data_directory(subdir="Daily")
        assert result.name == "Daily"

    def test_path_structure(self):
        """路徑結構應該正確"""
        result = get_data_directory(year=2025, subdir="Stocks")
        assert "data" in str(result)
        assert "market-data" in str(result)
        assert "2025" in str(result)
        assert "Stocks" in str(result)


class TestCreateArgumentParser:
    """測試 create_argument_parser 函數"""

    def test_returns_parser(self):
        """應該返回 ArgumentParser"""
        import argparse
        parser = create_argument_parser("Test description")
        assert isinstance(parser, argparse.ArgumentParser)

    def test_description_set(self):
        """描述應該被設定"""
        parser = create_argument_parser("My description")
        assert parser.description == "My description"

    def test_epilog_set(self):
        """epilog 應該被設定"""
        parser = create_argument_parser("Desc", epilog="My epilog")
        assert parser.epilog == "My epilog"


class TestSetupOutputPath:
    """測試 setup_output_path 函數"""

    def test_stdout_returns_none(self):
        """use_stdout=True 應該返回 None"""
        result = setup_output_path(
            output_arg=None,
            default_filename="test.md",
            use_stdout=True
        )
        assert result is None

    def test_absolute_path_preserved(self):
        """絕對路徑應該保留"""
        result = setup_output_path(
            output_arg="/tmp/test.md",
            default_filename="default.md"
        )
        assert result == Path("/tmp/test.md")

    def test_relative_path_with_dir(self):
        """包含目錄的相對路徑應該保留"""
        result = setup_output_path(
            output_arg="subdir/test.md",
            default_filename="default.md"
        )
        assert str(result) == "subdir/test.md"

    def test_filename_only_uses_default_dir(self):
        """只有檔名時應該使用預設目錄"""
        result = setup_output_path(
            output_arg="test.md",
            default_filename="default.md",
            default_subdir="Daily",
            year=2025
        )
        assert "Daily" in str(result)
        assert "test.md" in str(result)

    def test_no_output_uses_default(self):
        """沒有指定輸出時使用預設值"""
        result = setup_output_path(
            output_arg=None,
            default_filename="default.md",
            default_subdir="Stocks",
            year=2025
        )
        assert "default.md" in str(result)
        assert "Stocks" in str(result)


class TestWriteOutput:
    """測試 write_output 函數"""

    def test_write_to_stdout(self, capsys):
        """寫入 stdout 時應該印出內容"""
        write_output("Test content", None)
        captured = capsys.readouterr()
        assert "Test content" in captured.out

    def test_write_to_file(self, temp_output_dir):
        """寫入檔案時應該建立檔案"""
        output_path = temp_output_dir / "test.md"
        result = write_output("Test content", output_path)

        assert result is True
        assert output_path.exists()
        assert output_path.read_text() == "Test content"

    def test_creates_parent_directories(self, temp_output_dir):
        """應該自動建立父目錄"""
        output_path = temp_output_dir / "subdir" / "nested" / "test.md"
        result = write_output("Content", output_path)

        assert result is True
        assert output_path.exists()

    def test_returns_false_on_error(self, temp_output_dir):
        """發生錯誤時應該返回 False"""
        # 嘗試寫入不存在的根目錄
        output_path = Path("/nonexistent_root_12345/test.md")
        result = write_output("Content", output_path)

        assert result is False


class TestPrintFunctions:
    """測試印出函數"""

    def test_print_status(self, capsys):
        """print_status 應該輸出到 stderr"""
        print_status("Status message")
        captured = capsys.readouterr()
        assert "Status message" in captured.err

    def test_print_error(self, capsys):
        """print_error 應該包含錯誤前綴"""
        print_error("Error message")
        captured = capsys.readouterr()
        assert "錯誤:" in captured.err
        assert "Error message" in captured.err

    def test_print_success(self, capsys):
        """print_success 應該包含成功標記"""
        print_success("Success message")
        captured = capsys.readouterr()
        assert "✓" in captured.err
        assert "Success message" in captured.err

    def test_print_warning(self, capsys):
        """print_warning 應該包含警告標記"""
        print_warning("Warning message")
        captured = capsys.readouterr()
        assert "⚠" in captured.err
        assert "Warning message" in captured.err


class TestValidatePositiveInt:
    """測試 validate_positive_int 函數"""

    def test_valid_positive_int(self):
        """正整數應該通過驗證"""
        # 不應該拋出異常
        validate_positive_int(1, "test")
        validate_positive_int(100, "test")

    def test_zero_raises_error(self):
        """零應該拋出錯誤"""
        with pytest.raises(ScraperError) as exc_info:
            validate_positive_int(0, "count")
        assert "count" in str(exc_info.value)

    def test_negative_raises_error(self):
        """負數應該拋出錯誤"""
        with pytest.raises(ScraperError) as exc_info:
            validate_positive_int(-5, "value")
        assert "value" in str(exc_info.value)


class TestGenerateDatedFilename:
    """測試 generate_dated_filename 函數"""

    def test_default_extension(self, sample_date):
        """預設副檔名應該是 md"""
        result = generate_dated_filename("test", date=sample_date)
        assert result == "test-2025-11-20.md"

    def test_custom_extension(self, sample_date):
        """應該支援自訂副檔名"""
        result = generate_dated_filename("data", extension="json", date=sample_date)
        assert result == "data-2025-11-20.json"

    def test_default_date_is_today(self):
        """預設日期應該是今天"""
        result = generate_dated_filename("test")
        today = datetime.now().strftime("%Y-%m-%d")
        assert today in result

    def test_prefix_preserved(self, sample_date):
        """前綴應該被保留"""
        result = generate_dated_filename("global-indices", date=sample_date)
        assert result.startswith("global-indices-")

    def test_format_correct(self, sample_date):
        """格式應該正確"""
        result = generate_dated_filename("AAPL", date=sample_date)
        # 檢查格式：prefix-YYYY-MM-DD.extension
        parts = result.split("-")
        assert len(parts) == 4  # AAPL, 2025, 11, 20.md
