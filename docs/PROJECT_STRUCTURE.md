# 專案目錄結構說明

## 📁 目錄結構

```
FactoryProcessLogistics&Traceability System/
├── config/              # 設定檔目錄
│   ├── container.ini     # 容器與容量定義
│   ├── model.ini         # 產品機型定義
│   ├── process.ini        # 製程站點定義
│   ├── qrcode.ini        # QR Code 設定
│   ├── series.ini        # 產品系列定義
│   ├── settings.ini      # 系統設定
│   └── status.ini        # 貨態定義
│
├── docs/                 # 文檔目錄
│   ├── BARCODE_SCAN_LOGIC.md      # 條碼掃描邏輯說明
│   ├── GOOGLE_SHEETS_SETUP.md     # Google Sheets 設定指南
│   ├── SETUP.md                   # 系統設定指南
│   ├── TEST_PLAN.md               # 測試計劃
│   ├── TESTING.md                 # 測試說明
│   └── PROJECT_STRUCTURE.md        # 本文件
│
├── mcp/                  # MCP 同步工具目錄
│   ├── README.md                  # MCP 工具說明
│   ├── PRD_SYNC_README.md         # PRD 同步詳細說明
│   ├── QUICK_SYNC_GUIDE.md        # PRD 同步快速指南
│   ├── sync_prd_gdocs.py          # 主要同步腳本
│   ├── sync_prd_to_gdocs.py       # 完整版同步腳本
│   └── sync_prd_simple.py         # 簡化版同步腳本
│
├── scripts/              # 腳本目錄
│   ├── start.sh                   # 啟動腳本
│   ├── run_tests.sh               # 測試執行腳本
│   ├── run_tests_cn.py            # 中文測試報告腳本
│   ├── setup_sheet_headers.py     # Google Sheets 表頭設定
│   └── test_sheet.py              # Google Sheets 測試
│
├── services/             # 核心邏輯層
│   ├── __init__.py
│   ├── barcode.py                 # 條碼解析、生成、CRC校驗
│   ├── config_loader.py           # INI 讀取器
│   ├── qrcode_generator.py        # QR Code 生成器
│   └── sheet.py                   # Google Sheets 讀寫操作
│
├── static/               # 前端資源
│   ├── index.html                 # SPA 主頁面
│   └── app.js                     # 前端控制邏輯
│
├── tests/                # 測試目錄
│   ├── __init__.py
│   ├── conftest.py                # pytest 共享配置
│   ├── conftest_cn.py             # 中文測試配置
│   ├── pytest_custom_report.py    # 自訂測試報告
│   ├── unit/                      # 單元測試
│   │   ├── test_barcode.py
│   │   ├── test_config_loader.py
│   │   ├── test_qrcode_generator.py
│   │   └── test_sheet.py
│   ├── integration/               # 整合測試
│   │   └── test_full_workflow.py
│   └── api/                       # API 測試
│       └── test_api.py
│
├── venv/                 # Python 虛擬環境（不應提交到版本控制）
│
├── htmlcov/              # 測試覆蓋率報告（自動生成）
│
├── __pycache__/          # Python 快取（不應提交到版本控制）
│
├── main.py               # FastAPI 應用程式入口
├── PRD.md                # 產品需求文件（主要文件）
├── CHANGELOG.md          # 變更日誌
├── requirements.txt      # Python 依賴清單
├── pytest.ini           # pytest 配置
└── VERSION               # 版本號
```

## 📋 目錄說明

### 根目錄檔案

- **`main.py`** - FastAPI 應用程式入口點
- **`PRD.md`** - 產品需求文件（主要文件，保留在根目錄以便快速存取）
- **`CHANGELOG.md`** - 專案變更日誌
- **`requirements.txt`** - Python 套件依賴清單
- **`pytest.ini`** - pytest 測試框架配置
- **`VERSION`** - 當前版本號

### config/ - 設定檔目錄

包含所有 INI 格式的設定檔，用於定義：
- 製程站點
- 產品系列和機型
- 容器和貨態
- 系統設定

### docs/ - 文檔目錄

包含專案的各種說明文檔：
- 設定指南
- 測試文件
- 邏輯說明

### mcp/ - MCP 同步工具目錄

包含 PRD.md 與 Google Docs 之間的雙向同步工具：
- 同步腳本
- 使用說明文件

### scripts/ - 腳本目錄

包含各種實用腳本：
- 啟動腳本
- 測試腳本
- 設定腳本

### services/ - 核心邏輯層

包含系統的核心業務邏輯：
- 條碼處理
- Google Sheets 操作
- QR Code 生成

### static/ - 前端資源

包含前端靜態檔案：
- HTML 頁面
- JavaScript 邏輯

### tests/ - 測試目錄

包含所有測試檔案：
- 單元測試
- 整合測試
- API 測試

## 🔄 目錄結構優化原則

1. **根目錄保持簡潔**：只保留核心檔案和主要文件
2. **功能分組**：相關檔案放在同一目錄下
3. **文檔集中**：所有文檔放在 `docs/` 目錄
4. **腳本集中**：所有腳本放在 `scripts/` 目錄
5. **工具集中**：MCP 相關工具放在 `mcp/` 目錄

## 📝 檔案命名規範

- **Python 檔案**：使用小寫字母和底線（snake_case）
- **Markdown 檔案**：使用大寫字母和底線（UPPER_CASE）
- **設定檔**：使用小寫字母和底線（snake_case），副檔名為 `.ini`
- **腳本檔案**：使用小寫字母和底線（snake_case），副檔名為 `.sh` 或 `.py`

## 🚀 快速導航

- **開始使用**：查看 [SETUP.md](./SETUP.md)
- **產品需求**：查看 [PRD.md](../PRD.md)
- **同步工具**：查看 [mcp/README.md](../mcp/README.md)
- **測試說明**：查看 [TESTING.md](./TESTING.md)

