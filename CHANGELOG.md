# 更新日誌 (Changelog)

所有重要的變更都會記錄在此文件中。

格式基於 [Keep a Changelog](https://keepachangelog.com/zh-TW/1.0.0/)，
版本號遵循 [Semantic Versioning](https://semver.org/lang/zh-TW/)。

## [0.1.0] - 2025-11-20

### 新增
- **PRD.md 與 Google Docs 雙向同步功能**：
  - 支援使用 MCP 工具同步（不需要憑證）
  - 支援使用 Google Docs API 同步（需要憑證）
  - 自動判斷同步方向
  - 記錄同步歷史
- **目錄結構優化**：
  - 創建 `mcp/` 目錄集中管理同步工具
  - 創建 `docs/` 目錄集中管理文檔
  - 創建 `scripts/` 目錄集中管理腳本
  - 根目錄檔案從 20+ 個減少到 6 個核心檔案
- **安全檢查工具**：
  - `check_security.sh` - 檢查即將提交的檔案
  - `check_git_history.sh` - 檢查 Git 歷史中的敏感資訊
  - `clean_git_history.sh` - 清理 Git 歷史中的敏感資訊
  - Git pre-commit hook 自動執行安全檢查
- **安全文檔**：
  - `docs/SECURITY.md` - 完整的安全指南
  - `docs/CLEAN_HISTORY_SUMMARY.md` - 清理總結
  - `docs/CLEAN_HISTORY_COMPLETE.md` - 清理完成指南

### 改進
- **目錄結構**：更清晰的目錄組織，易於維護
- **安全性**：完善的安全檢查機制，防止敏感資訊洩漏
- **文檔管理**：所有文檔集中管理，結構更清晰
- **腳本管理**：所有腳本集中管理，使用更方便

### 文檔
- `mcp/README.md` - MCP 工具說明
- `mcp/MCP_SYNC_GUIDE.md` - MCP 同步指南
- `mcp/PRD_SYNC_README.md` - PRD 同步詳細說明
- `mcp/QUICK_SYNC_GUIDE.md` - 快速同步指南
- `mcp/UPDATE_EXISTING_DOC.md` - 更新現有文件說明
- `docs/PROJECT_STRUCTURE.md` - 專案結構說明
- `docs/DIRECTORY_OPTIMIZATION.md` - 目錄優化總結
- `scripts/README.md` - 腳本使用說明

## [0.0.7] - 2025-01-XX

### 新增
- 完整測試框架：新增 pytest 測試框架和配置
- 單元測試套件：新增 5 個單元測試文件（條碼、配置、流程驗證、QR Code、Sheets）
- API 端點測試：新增完整的 API 端點測試，覆蓋所有 API 功能
- 整合測試：新增完整工作流程整合測試，通過 API 端點模擬前端調用（10 張工單）
- 中文測試報告：新增中文測試輸出功能，清楚顯示通過/失敗的測試項目
- 測試目錄結構：重組測試文件到 unit/、api/、integration/ 子目錄
- 測試文檔：新增完整的測試計劃和說明文檔（TEST_PLAN.md、TESTING.md 等）
- 測試啟動腳本：新增 run_tests.sh 和 run_tests_cn.py 方便執行測試

### 改進
- 測試覆蓋率：達到 77% 的測試覆蓋率
- 測試組織：按類型分類測試文件，結構更清晰
- 測試文檔集中管理：所有測試相關文檔統一放在 tests/ 目錄

### 修復
- 修復 QR Code 生成器 bytes 處理問題（img.to_string() 返回 bytes 的處理）
- 修復配置檔大小寫問題（ConfigParser 將鍵轉為小寫的處理）
- 修復條碼 CRC16 校驗碼測試問題
- 修復 API 測試中條碼校驗碼不正確的問題

### 測試
- 96 個測試用例，涵蓋所有核心功能
- 單元測試：條碼解析、生成、CRC16 校驗、配置載入、流程驗證等
- API 測試：所有 API 端點的完整測試
- 整合測試：完整生產流程測試（通過 API 端點）

### 文檔
- TEST_PLAN.md：詳細的測試計劃（598 行）
- TESTING.md：測試程序說明
- TEST_FIXES.md：測試修復記錄
- TEST_OUTPUT_CN.md：中文測試輸出說明
- TEST_STRUCTURE.md：測試目錄結構說明
- DOCS_INDEX.md：測試文檔索引

## [0.0.6] - 2025-01-XX

### 改進
- 站點代號統一為大寫：所有寫入 Google Sheets 的站點代號統一轉換為大寫格式
- 前端顯示統一為大寫：人機界面中顯示的站點代號統一轉換為大寫格式（例如：`P2 - 烘烤`）
- API 返回統一為大寫：所有 API 返回的站點資訊（`current_station`、`next_station`、`prev_station`）統一轉換為大寫
- Google Sheets 寫入邏輯優化：寫入時自動適應 Sheet 中的實際欄位順序，支援手動變更欄位順序

### 修復
- 修復寫入 Google Sheets 時站點代號為小寫的問題
- 修復前端界面顯示站點代號為小寫的問題
- 修復手動變更 Sheet 欄位順序時資料寫入錯誤欄位的問題

### 技術細節
- 寫入 Sheet 時會讀取實際標題列，建立標題到欄位的映射，確保資料寫入正確的欄位
- 所有站點相關的資料處理都統一轉換為大寫，保持一致性

## [0.0.5] - 2025-01-XX

### 新增
- 部分條碼解析功能：新增 `parse_partial()` 方法，支援解析不完整的條碼（例如：`251119AB-ZZ-AC001`）
- 智能條碼檢查 API：新增 `/api/scan/check` 端點，自動判斷條碼應該使用哪個功能（遷入、遷出、首站遷出）
- 智能掃描按鈕：前端新增「掃描條碼（智能識別）」按鈕，自動檢查條碼並跳轉到對應功能
- 站點特定遷出記錄檢查：新增 `has_outbound_record_at_station()` 方法，檢查條碼在指定站點是否有遷出記錄
- 新工單條碼格式支援：支援新工單條碼格式（工單號-ZZ-SKU），後續欄位為空
- 自動填入產品資訊：檢測到 ZZ 製程時，自動從 SKU 提取產品線和機種並填入首站遷出表單

### 改進
- 條碼檢查邏輯優化：根據條碼的製程代號與當前站點的關係，智能判斷應該使用遷入還是遷出功能
- 跨站點遷入邏輯：遷入時只檢查當前站點的遷出記錄，而不是所有站點的遷出記錄
- 首站遷出 domain 整合：首站遷出時將包含 domain 的完整條碼 URL 寫入 Google Sheets 和生成 QR Code
- 條碼清理邏輯：前端和後端都支援清理 `b=` 前綴，正確處理 URL 參數格式的條碼
- 機種代碼匹配：前端自動匹配機種代碼，處理前導零的差異（例如：`001` 和 `1`）

### 修復
- 修復首站遷出時新條碼未包含 domain 的問題
- 修復跨站點遷入時被錯誤拒絕的問題（例如：P2 讀取 P1 條碼時）
- 修復不完整條碼（如 `251119AB-ZZ`）無法解析的問題

### API 端點
- `POST /api/scan/check` - 智能條碼檢查，返回建議的操作類型

### 技術細節
- 條碼解析支援兩種模式：完整解析（34碼）和部分解析（至少包含工單號和製程代號）
- ZZ 製程（新工單）跳過 CRC16 驗證，因為可能是不完整的條碼
- 智能檢查邏輯：根據條碼製程代號與當前站點的關係，以及當前站點的遷出記錄，決定建議的操作

## [0.0.4] - 2025-01-XX

### 新增
- 綜合設定檔：`config/settings.ini` 用於存放系統綜合設定（包含 IP domain 設定）
- Domain 整合：遷出時自動將 domain 寫入新條碼 URL 並記錄到 Google Sheets
- 條碼記錄查詢：新增 `get_logs_by_barcode()` 方法，可根據條碼查詢歷史記錄
- 遷出記錄檢查：新增 `has_outbound_record()` 方法，檢查條碼是否有遷出記錄
- 智能功能切換：遷入時自動檢查條碼是否有 OUT 記錄，如有則自動切換到遷出功能

### 改進
- 流程驗證大小寫處理：統一將站點代號轉換為大寫進行比較，解決 P2 和 p2 不一致的問題
- 條碼匹配邏輯：優化條碼匹配，正確處理包含 domain 的條碼（例如：`http://localhost:8000/b=條碼`）
- 多次遷出支援：同一條碼可被遷出多次（例如：良品一批、不良品一批）
- 自動切換邏輯：下游站點掃到上游製程條碼時，如有 OUT 記錄則自動切換到遷出功能

### 修復
- 修復流程驗證中大小寫不一致導致的驗證失敗問題

### API 端點
- 遷入 API 新增智能檢查：自動判斷條碼是否有 OUT 記錄並返回切換提示

### 設定檔
- `config/settings.ini` - 綜合設定檔（包含 domain 設定）

## [0.0.3] - 2025-01-XX

### 新增
- QR Code 生成功能：提交成功後自動生成並顯示 QR Code SVG
- QR Code 下載功能：提供下載按鈕，可下載 QR Code 為 SVG 檔案
- QR Code 配置檔：`config/qrcode.ini` 用於設定 QR Code 大小、容錯率、定位點形狀和 logo 比例
- 工單號自動轉大寫：前端輸入和後端寫入時自動轉換為大寫
- 容器下拉選單：遷出和首站遷出功能改為從 `config/container.ini` 動態載入容器選項
- 站點中文名稱顯示：主頁面頂部顯示站點時同時顯示中文名稱（例如：P1 - 射出）
- 製程站點動態載入：設定頁面的站點選單從 `config/process.ini` 動態載入
- URL 重定向支援：新增 `/b=條碼` 路徑重定向，支援 QR code 中沒有 `?` 的情況
- 條碼解析功能：支援移除所有 `-` 後按固定位置解析條碼
- 智能工單識別：自動識別 ZZ 製程（新工單），自動切換到首站遷出功能

### 改進
- 產品線與機種選擇：系統自動從 ini 檔案反查代號並組合成 SKU
- 容器選擇：改為下拉選單，顯示「代號 - 容量」格式
- 站點顯示：主頁面和設定頁面都顯示「代號 - 中文名稱」格式
- 成功訊息：儲存設定時顯示站點中文名稱

### API 端點
- `GET /api/config/containers` - 取得容器選項
- `GET /api/config/processes` - 取得製程站點選項
- `GET /b={barcode}` - URL 重定向支援（QR code 掃描）

### 設定檔
- `config/qrcode.ini` - QR Code 生成設定（大小、容錯率、定位點形狀、logo 比例）

### 依賴
- `qrcode[pil]==7.4.2` - QR Code 生成庫

## [0.0.2] - 2025-01-XX

### 新增
- QR Code 掃描支援：從 URL 參數自動解析條碼並填入
- 支援手機條碼掃描器掃描 QR code 後自動開啟瀏覽器並帶入條碼
- 自動開啟遷入功能並聚焦到條碼輸入框

### 改進
- 簡化 URL 參數格式：使用 `?b=條碼` 取代 `?barcode=條碼`，減少 QR code 字數
- 未登入時保存條碼參數，登入後自動處理

## [0.0.1] - 2025-01-XX

### 新增
- 工廠製程物流追溯與分析系統初始版本
- FastAPI 後端服務
- iOS 風格行動端前端介面
- 條碼解析與生成功能（34碼條碼，含CRC16校驗）
- 製程流程驗證（防呆檢查）
- Google Sheets 整合（記錄遷入/遷出）
- 產品線與機種選擇功能（取代直接輸入SKU）
  - 產品線下拉選單（從 config/series.ini 讀取）
  - 機種下拉選單（從 config/model.ini 讀取）
  - 系統自動組合成 SKU 代號

### 功能
- 貨物遷入（IN）：驗證流程並記錄
- 貨物遷出（OUT）：生成新條碼並記錄
- 首站遷出（FIRST）：手動輸入工單資訊，生成第一個條碼
- 追溯查詢（TRACE）：查詢工單的時間軸與良率統計

### 設定檔
- `config/process.ini` - 製程站點定義
- `config/series.ini` - 產品系列定義
- `config/model.ini` - 產品機型定義
- `config/flow.ini` - 製程流程定義
- `config/container.ini` - 容器定義
- `config/status.ini` - 貨態定義

### API 端點
- `GET /` - 前端頁面
- `POST /api/scan/inbound` - 貨物遷入
- `POST /api/scan/outbound` - 貨物遷出
- `POST /api/scan/first` - 首站遷出
- `POST /api/scan/trace` - 追溯查詢
- `GET /api/config/series` - 取得產品線選項
- `GET /api/config/models` - 取得機種選項

