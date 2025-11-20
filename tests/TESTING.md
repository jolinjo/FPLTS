# 測試程序說明

## 概述

已為工廠製程物流追溯與分析系統建立完整的測試框架和測試程序。

## 已完成的測試

### 1. 測試框架設定 ✅

- **pytest.ini**: pytest 配置文件
- **tests/conftest.py**: 共享測試配置和夾具
- **tests/__init__.py**: 測試套件初始化
- **requirements.txt**: 已更新，包含測試依賴

### 2. 單元測試 ✅

#### 2.1 條碼處理模組 (`test_barcode.py`)
- ✅ 條碼解析測試（完整、部分、錯誤格式）
- ✅ CRC16 校驗測試（計算、驗證）
- ✅ 條碼生成測試（完整生成、從舊條碼生成）
- ✅ 欄位格式化測試
- ✅ SKU 提取測試

#### 2.2 配置載入模組 (`test_config_loader.py`)
- ✅ 配置檔載入測試
- ✅ 配置值讀取測試
- ✅ 區段字典取得測試
- ✅ 所有配置檔類型測試

#### 2.3 流程驗證模組 (`test_flow_validator.py`)
- ✅ 正常流程驗證測試
- ✅ 跳站防呆測試
- ✅ 漏站防呆測試
- ✅ 反向流程測試
- ✅ 取得下一站測試
- ✅ 不同 SKU 系列測試

#### 2.4 QR Code 生成模組 (`test_qrcode_generator.py`)
- ✅ SVG 生成測試
- ✅ 不同數據格式測試
- ✅ 錯誤處理測試

#### 2.5 Google Sheets 服務模組 (`test_sheet.py`)
- ✅ 記錄寫入測試
- ✅ 記錄查詢測試
- ✅ 記錄檢查測試
- ✅ 錯誤處理測試
- ✅ 使用 Mock 物件模擬外部依賴

### 3. API 端點測試 ✅

#### 3.1 配置查詢 API (`test_api.py`)
- ✅ GET /api/config/series
- ✅ GET /api/config/models
- ✅ GET /api/config/containers
- ✅ GET /api/config/processes

#### 3.2 條碼檢查 API
- ✅ POST /api/scan/check（ZZ 製程、已有記錄等情況）

#### 3.3 遷入 API
- ✅ POST /api/scan/inbound（成功、流程驗證失敗）

#### 3.4 遷出 API
- ✅ POST /api/scan/outbound

#### 3.5 首站遷出 API
- ✅ POST /api/scan/first（成功、參數驗證）

#### 3.6 追溯查詢 API
- ✅ POST /api/scan/trace

#### 3.7 路由測試
- ✅ GET /
- ✅ GET /b={barcode:path}

## 測試統計

- **測試文件數**: 6 個
- **測試類別數**: 約 15 個
- **測試函數數**: 約 80+ 個
- **測試覆蓋範圍**: 
  - 所有核心模組
  - 所有 API 端點
  - 主要業務邏輯

## 如何執行測試

### 快速開始

```bash
# 1. 啟動虛擬環境
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 2. 安裝測試依賴（如果還沒安裝）
pip install -r requirements.txt

# 3. 執行所有測試
pytest

# 或使用提供的腳本
./run_tests.sh
```

### 常用命令

```bash
# 執行所有測試
pytest

# 執行特定測試文件
pytest tests/test_barcode.py

# 只執行單元測試
pytest -m unit

# 只執行 API 測試
pytest -m api

# 排除需要 Google Sheets 的測試
pytest -m "not requires_sheets"

# 查看測試覆蓋率
pytest --cov=services --cov-report=html

# 詳細輸出
pytest -vv -s
```

## 測試標記

測試使用以下標記分類：

- `@pytest.mark.unit`: 單元測試
- `@pytest.mark.integration`: 整合測試
- `@pytest.mark.api`: API 測試
- `@pytest.mark.slow`: 執行較慢的測試
- `@pytest.mark.requires_sheets`: 需要 Google Sheets 連接的測試

## 測試依賴

測試框架使用以下工具：

- **pytest**: 測試框架
- **pytest-asyncio**: 非同步測試支援
- **pytest-mock**: Mock 物件支援
- **pytest-cov**: 測試覆蓋率
- **httpx**: HTTP 客戶端（用於 API 測試）

## 注意事項

### 1. Google Sheets 測試

標記為 `@pytest.mark.requires_sheets` 的測試需要實際的 Google Sheets 連接。如果沒有設定，可以使用：

```bash
pytest -m "not requires_sheets"
```

大部分測試使用 Mock 物件，不需要實際連接。

### 2. 配置檔

測試會讀取 `config/` 目錄下的實際配置檔。確保配置檔存在且格式正確。

### 3. 測試數據

測試使用模擬數據和 Mock 物件，不會修改實際的 Google Sheets 數據。

## 測試計劃對照

根據 `TEST_PLAN.md` 中的測試計劃，已完成：

- ✅ 單元測試（核心模組）
- ✅ API 端點測試（所有端點）
- ✅ 業務邏輯測試（主要情況）
- ✅ 錯誤處理測試（基本情況）

待完成（可選）：

- ⏳ 完整工作流程整合測試
- ⏳ 性能測試
- ⏳ 前端測試
- ⏳ 更詳細的邊界情況測試

## 下一步

1. **執行測試**：運行 `pytest` 確保所有測試通過
2. **查看覆蓋率**：使用 `pytest --cov` 查看測試覆蓋率
3. **持續改進**：根據測試結果補充更多測試案例
4. **整合到 CI/CD**：將測試整合到持續整合流程中

## 相關文件

- `TEST_PLAN.md`: 詳細的測試計劃
- `tests/README.md`: 測試目錄說明
- `pytest.ini`: pytest 配置
- `run_tests.sh`: 測試執行腳本

