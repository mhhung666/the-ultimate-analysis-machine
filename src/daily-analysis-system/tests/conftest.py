"""
pytest 配置檔案
"""

import sys
from pathlib import Path

import pytest

# 將 scrapers 目錄加入 Python 路徑
scrapers_dir = Path(__file__).parent.parent / "scrapers"
sys.path.insert(0, str(scrapers_dir))


@pytest.fixture
def temp_output_dir(tmp_path):
    """建立臨時輸出目錄"""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir


@pytest.fixture
def sample_date():
    """提供固定的測試日期"""
    from datetime import datetime
    return datetime(2025, 11, 20)
