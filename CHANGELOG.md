# 更新日誌 (Changelog)

所有重要的變更都會記錄在此文件中。

格式基於 [Keep a Changelog](https://keepachangelog.com/zh-TW/1.0.0/)，
版本號遵循 [Semantic Versioning](https://semver.org/lang/zh-TW/)。

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

