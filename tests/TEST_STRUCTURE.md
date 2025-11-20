# 測試目錄結構說明

## 目錄組織

測試文件已重新組織為更清晰的結構：

```
專案根目錄/
├── run_tests.sh              # 測試啟動腳本（根目錄）
├── run_tests_cn.py           # 中文測試報告腳本（根目錄）
├── pytest.ini                # pytest 配置
└── tests/                    # 測試目錄
    ├── __init__.py
    ├── conftest.py           # pytest 共享配置
    ├── README.md             # 測試說明文件
    ├── unit/                 # 單元測試
    │   ├── __init__.py
    │   ├── test_barcode.py
    │   ├── test_config_loader.py
    │   ├── test_flow_validator.py
    │   ├── test_qrcode_generator.py
    │   └── test_sheet.py
    ├── integration/          # 整合測試（待補充）
    │   └── __init__.py
    └── api/                  # API 測試
        ├── __init__.py
        └── test_api.py
```

## 設計原則

1. **測試啟動文件在根目錄**：方便快速執行測試
2. **測試類文件在 tests/ 子目錄**：按類型分類組織
3. **清晰的目錄結構**：unit、integration、api 分類明確

## 執行測試

### 從根目錄執行（推薦）

```bash
# 執行所有測試
./run_tests.sh

# 執行所有測試（中文輸出）
./run_tests.sh --cn

# 或使用 Python 腳本
python3 run_tests_cn.py
```

### 執行特定類別的測試

```bash
# 只執行單元測試
pytest tests/unit/

# 只執行 API 測試
pytest tests/api/

# 只執行整合測試
pytest tests/integration/
```

## 配置文件

- **pytest.ini**: 配置測試路徑為 `tests/unit tests/integration tests/api`
- **conftest.py**: 位於 `tests/` 根目錄，所有子目錄共享

## 更新記錄

- 2025-01-XX: 重組測試目錄結構，將測試文件分類到 unit/、api/、integration/ 子目錄

