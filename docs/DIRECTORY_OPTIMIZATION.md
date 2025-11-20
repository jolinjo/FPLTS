# 目錄結構優化總結

## 📊 優化前後對比

### 優化前（根目錄檔案過多）

根目錄包含大量檔案：
- 多個同步腳本（`sync_prd_*.py`）
- 多個文檔檔案（`*.md`）
- 多個測試腳本（`run_tests_*.py`, `test_*.py`）
- 多個啟動腳本（`start.sh`, `setup_*.py`）

### 優化後（根目錄簡潔）

根目錄現在只保留核心檔案：
- `main.py` - 應用程式入口
- `PRD.md` - 主要產品需求文件
- `CHANGELOG.md` - 變更日誌
- `requirements.txt` - 依賴清單
- `pytest.ini` - 測試配置
- `VERSION` - 版本號

## 📁 新的目錄結構

### 1. `mcp/` - MCP 同步工具目錄

**目的**：集中管理 PRD.md 與 Google Docs 的雙向同步工具

**包含檔案**：
- `sync_prd_gdocs.py` - 主要同步腳本
- `sync_prd_to_gdocs.py` - 完整版同步腳本
- `sync_prd_simple.py` - 簡化版同步腳本
- `PRD_SYNC_README.md` - 詳細使用說明
- `QUICK_SYNC_GUIDE.md` - 快速使用指南
- `README.md` - 目錄說明

### 2. `docs/` - 文檔目錄

**目的**：集中管理所有專案文檔

**包含檔案**：
- `BARCODE_SCAN_LOGIC.md` - 條碼掃描邏輯說明
- `GOOGLE_SHEETS_SETUP.md` - Google Sheets 設定指南
- `SETUP.md` - 系統設定指南
- `TEST_PLAN.md` - 測試計劃
- `TESTING.md` - 測試說明
- `PROJECT_STRUCTURE.md` - 專案結構說明
- `DIRECTORY_OPTIMIZATION.md` - 本文件

### 3. `scripts/` - 腳本目錄

**目的**：集中管理所有實用腳本

**包含檔案**：
- `start.sh` - 啟動腳本
- `run_tests.sh` - 測試執行腳本
- `run_tests_cn.py` - 中文測試報告腳本
- `setup_sheet_headers.py` - Google Sheets 表頭設定
- `test_sheet.py` - Google Sheets 測試
- `README.md` - 腳本使用說明

## 🔄 路徑更新

所有移動的檔案都已更新路徑引用：

### 同步腳本路徑更新

- `PRD_MD_PATH` 從 `Path(__file__).parent / "PRD.md"` 
  更新為 `Path(__file__).parent.parent / "PRD.md"`

### 腳本路徑更新

- `start.sh` 添加了 `cd "$(dirname "$0")/.."` 來切換到專案根目錄
- `run_tests.sh` 添加了相同的路徑處理
- `run_tests_cn.py` 添加了路徑切換邏輯

### 文檔引用更新

- `PRD.md` 中的同步工具引用已更新為 `./mcp/PRD_SYNC_README.md`
- 所有同步相關文檔中的路徑引用都已更新

## ✅ 優化成果

1. **根目錄檔案減少**：從 20+ 個檔案減少到 6 個核心檔案
2. **功能分組清晰**：相關檔案集中在對應目錄
3. **易於維護**：每個目錄都有 README 說明
4. **路徑正確**：所有路徑引用都已更新

## 📝 使用指南

### 執行同步腳本

```bash
# 從專案根目錄執行
python mcp/sync_prd_gdocs.py --to-gdoc
```

### 執行測試腳本

```bash
# 從專案根目錄執行
bash scripts/run_tests.sh
```

### 查看文檔

```bash
# 查看專案結構說明
cat docs/PROJECT_STRUCTURE.md

# 查看同步工具說明
cat mcp/README.md

# 查看腳本使用說明
cat scripts/README.md
```

## 🎯 優化原則

1. **根目錄保持簡潔**：只保留核心檔案和主要文件
2. **功能分組**：相關檔案放在同一目錄下
3. **文檔集中**：所有文檔放在 `docs/` 目錄
4. **腳本集中**：所有腳本放在 `scripts/` 目錄
5. **工具集中**：MCP 相關工具放在 `mcp/` 目錄

## 📚 相關文檔

- [專案結構說明](./PROJECT_STRUCTURE.md)
- [MCP 工具說明](../mcp/README.md)
- [腳本使用說明](../scripts/README.md)

