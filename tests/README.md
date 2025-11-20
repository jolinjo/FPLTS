# 測試目錄說明

## 目錄結構

```
tests/
├── __init__.py                 # 測試套件初始化
├── conftest.py                 # pytest 共享配置和夾具
├── README.md                   # 本文件（測試目錄說明）
├── TEST_PLAN.md                # 測試計劃文件（詳細測試項目）
├── TESTING.md                  # 測試程序說明
├── TEST_FIXES.md               # 測試修復記錄
├── TEST_OUTPUT_CN.md           # 中文測試輸出說明
├── TEST_STRUCTURE.md           # 測試目錄結構說明
├── unit/                       # 單元測試
│   ├── __init__.py
│   ├── test_barcode.py         # 條碼處理模組測試
│   ├── test_config_loader.py  # 配置載入模組測試
│   ├── test_flow_validator.py # 流程驗證模組測試
│   ├── test_qrcode_generator.py # QR Code 生成模組測試
│   └── test_sheet.py          # Google Sheets 服務測試
├── integration/                # 整合測試
│   ├── __init__.py
│   └── test_full_workflow.py  # 完整工作流程測試（實際寫入 Google Sheets）
└── api/                        # API 端點測試
    ├── __init__.py
    └── test_api.py            # API 端點測試
```

## 測試文件說明

### 測試計劃和文檔

- **TEST_PLAN.md**: 完整的測試計劃，列出所有需要測試的項目和分類
- **TESTING.md**: 測試程序說明，包含如何執行測試、測試統計等
- **TEST_FIXES.md**: 測試修復記錄，記錄測試過程中發現和修復的問題
- **TEST_OUTPUT_CN.md**: 中文測試輸出說明，如何使用中文測試報告功能
- **TEST_STRUCTURE.md**: 測試目錄結構說明，解釋測試文件的組織方式

## 測試分類

### 單元測試 (`tests/unit/`)

測試各個服務模組的獨立功能：
- **test_barcode.py**: 條碼解析、生成、CRC16 校驗
- **test_config_loader.py**: 配置檔讀取
- **test_flow_validator.py**: 流程驗證邏輯
- **test_qrcode_generator.py**: QR Code 生成
- **test_sheet.py**: Google Sheets 操作（使用 Mock）

### API 測試 (`tests/api/`)

測試 FastAPI 端點：
- **test_api.py**: 所有 API 端點的測試

### 整合測試 (`tests/integration/`)

測試完整工作流程（待補充）

## 執行測試

### 從根目錄執行

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

### 執行特定測試文件

```bash
# 執行條碼測試
pytest tests/unit/test_barcode.py

# 執行特定測試類別
pytest tests/unit/test_barcode.py::TestBarcodeParser

# 執行特定測試函數
pytest tests/unit/test_barcode.py::TestBarcodeParser::test_parse_valid_barcode
```

## 測試標記

使用 pytest 標記來分類測試：

```bash
# 只執行單元測試
pytest -m unit

# 只執行 API 測試
pytest -m api

# 排除需要 Google Sheets 的測試
pytest -m "not requires_sheets"
```

## 測試文檔

測試相關的文檔都位於 `tests/` 目錄下：

- **TEST_PLAN.md**: 詳細的測試計劃，包含所有測試項目
- **TESTING.md**: 測試程序說明和使用指南
- **TEST_FIXES.md**: 測試修復記錄和問題解決方案
- **TEST_OUTPUT_CN.md**: 中文測試輸出功能說明
- **TEST_STRUCTURE.md**: 測試目錄結構說明

## 注意事項

1. **conftest.py**: 位於 `tests/` 根目錄，所有子目錄的測試都可以使用其中定義的 fixture
2. **測試啟動腳本**: 位於專案根目錄（`run_tests.sh`, `run_tests_cn.py`），方便執行
3. **測試文件命名**: 所有測試文件必須以 `test_` 開頭
4. **測試類別命名**: 所有測試類別必須以 `Test` 開頭
5. **測試文檔**: 所有測試相關的 .md 文件都位於 `tests/` 目錄下
