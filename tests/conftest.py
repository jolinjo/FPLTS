"""
pytest 共享配置和夾具
"""
import pytest
import sys
from pathlib import Path

# 添加專案根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 測試用的配置檔目錄
TEST_CONFIG_DIR = project_root / "config"


@pytest.fixture
def sample_barcode():
    """測試用的完整條碼（使用正確的 CRC16 校驗碼）"""
    from services.barcode import BarcodeGenerator
    return BarcodeGenerator.generate(
        "251119AA", "P2", "ST352", "A1", "01", "G", "0100"
    )


@pytest.fixture
def sample_barcode_parsed():
    """測試用的解析後條碼字典"""
    return {
        'order': '251119AA',
        'process': 'P2',
        'sku': 'ST352',
        'container': 'A1',
        'box_seq': '01',
        'status': 'G',
        'qty': '0100',
        'crc': 'X4F'
    }


@pytest.fixture
def sample_zz_barcode():
    """測試用的 ZZ 製程條碼（新工單）"""
    return "251119AB-ZZ-AC001"


@pytest.fixture
def sample_partial_barcode():
    """測試用的部分條碼"""
    return "251119AB-ZZ"


@pytest.fixture
def sample_invalid_barcode():
    """測試用的無效條碼"""
    return "INVALID-BARCODE"


@pytest.fixture
def sample_order():
    """測試用的工單號"""
    return "251119AA"


@pytest.fixture
def sample_sku():
    """測試用的 SKU"""
    return "ST352"


@pytest.fixture
def sample_series():
    """測試用的產品系列"""
    return "ST"


@pytest.fixture
def sample_model():
    """測試用的機種"""
    return "352"

