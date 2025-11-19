# 更新日誌 (Changelog)

所有重要的變更都會記錄在此文件中。

格式基於 [Keep a Changelog](https://keepachangelog.com/zh-TW/1.0.0/)，
版本號遵循 [Semantic Versioning](https://semver.org/lang/zh-TW/)。

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

