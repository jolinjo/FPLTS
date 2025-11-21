# 產品需求文件 (PRD)
## 專案：工廠製程物流追溯與分析系統 (FPLTS) - V6 Final
### Project: Factory Process Logistics & Traceability System

---

## 1. 專案概觀 (Overview)

本系統為工廠生產追溯原型。透過手機掃描二維條碼，管理貨物在各製程站點流轉。

**核心價值**：
1. **全流程追溯**：紀錄遷入/遷出時間、工時與良率。
2. **流程防呆 (New)**：透過 INI 定義製程流，防止漏站或跳站。
3. **權限管控**：強制工號登入。
4. **iOS 風格介面**：極致的行動端操作體驗。

---

## 2. 技術架構 (Tech Stack)

- **Backend**: Python (FastAPI) + Background Tasks
- **Database**: Google Sheets (via `gspread`)
- **Frontend**: Mobile Web (HTML5 + Tailwind CSS)
- **Config**: INI Files (Process, Product, Flow)

---

## 3. 設定檔驅動邏輯 (Configuration Logic)

系統啟動時讀取 `config/` 下的所有 INI 檔。

### 3.1 `config/process.ini` (製程站點)

```ini
[Process]
P1 = 射出
P2 = 烘烤
P3 = 修邊
P4 = 組裝
P5 = 包裝
```

### 3.2 `config/series.ini` (產品系列)

```ini
[Series]
AC = AirCase
MD = Mod NX 邊框
ST = SolidSuit
CA = CCA
```

### 3.3 `config/model.ini` (產品機型)

```ini
[Model]
350 = iPhone 17
351 = iPhone 17 Air
352 = iPhone 17 Pro
001 = 通用型
```

### 3.4 `config/flow.ini` (製程流 - New!)

**用途**：定義產品的正確流向，用於遷入時的防呆驗證。

```ini
[Flow]
# AirCase: 不需要烘烤與組裝
AC = P1, P3, P5
# SolidSuit: 全製程
ST = P1, P2, P3, P4, P5
# Mod NX: 不需要烘烤
MD = P1, P3, P4, P5
# 預設
DEFAULT = P1, P2, P3, P4, P5
```

### 3.5 `config/container.ini` & `config/status.ini`

- **Container**: A1=100, OT=0...
- **Status**: G=良品, N=不良, S=特採, R=返工, E=遺失

---

## 4. 條碼結構定義 (Barcode Structure - 34 Chars)

**格式**：`[工單8]-[製程2]-[SKU5]-[容器2]-[箱號2]-[貨態1]-[數量4]-[校驗3]`

**範例**：`251119AA-P2-ST352-A1-01-G-0100-X4F`

---

## 5. 業務流程與 API (Business Workflow)

### 5.1 🔐 開工與登入 (Setup)

- **前端**：檢查 localStorage。若無工號，鎖定在設定頁。
- **設定頁**：輸入工號 (OP01)、選擇當前站點 (e.g., P2)。

### 5.2 📦 貨物遷入 (Inbound) - 含防呆邏輯

**API**: `POST /api/scan/inbound`

**Payload**: 
```json
{
  "barcode": "251119AA-P1-ST352-A1-01-G-0100-X4F",
  "operator_id": "OP01",
  "current_station_id": "P2"
}
```

**後端邏輯**：
1. 解析條碼，取得 SKU (前2碼) 與 上一站 ID (e.g., P1)。
2. **防呆檢查**：
   - 讀取 `flow.ini` 找到該 SKU 的流程清單。
   - 檢查 `current_station_id` (P2) 是否為 `previous_station_id` (P1) 的合法下一站。
   - 若錯誤：回傳 400 Error ("錯誤！P1 後續應為 P3，不可跳至 P2")。
   - 若正確：寫入 Google Sheet (Action='IN')。

**UI**：成功顯示綠色卡片；流程錯誤顯示紅色警示彈窗。

### 5.2.1 🔍 智能條碼檢查與功能切換

**API**: `POST /api/scan/check`

系統在掃描條碼時會自動檢查條碼狀態，並根據以下優先級邏輯決定應該開啟哪個功能：

**優先級順序**：
1. **最高優先級**: ZZ 製程（新工單）→ 首站遷出
2. **第二優先級**: 上一站條碼 + 當前站點或下游站點已有遷出記錄 → 只允許查詢（防止數據錯亂）
3. **第三優先級**: 本站條碼（無論是否有記錄）→ 只允許查詢（防止在錯誤站點操作）
4. **第四優先級**: 當前站點已有遷入記錄 → 遷出
5. **第五優先級**: 當前站點已有遷出記錄 → 遷出
6. **最低優先級**: 沒有記錄 → 根據條碼與站點關係決定（上一站條碼 → 遷入，下一站條碼 → 只允許查詢）

**邏輯說明**：
- **本站條碼特殊處理**：如果條碼製程代號與當前站點相同（例如：P1 站點掃到 P1 條碼），無論是否有記錄，都只允許查詢，防止在錯誤的站點進行操作。
- **防止數據錯亂**：如果上一站條碼在當前站點或下游站點已有遷出記錄，只允許查詢，防止條碼已經流到下游後又被重新遷入或遷出。
- **自動功能切換**：系統會根據檢查結果自動開啟對應的功能（遷入、遷出、首站遷出或查詢），並自動填入條碼。

**詳細邏輯定義**：請參考 [BARCODE_SCAN_LOGIC.md](./BARCODE_SCAN_LOGIC.md)

### 5.3 🚀 貨物遷出 (Outbound)

**API**: `POST /api/scan/outbound`

**動作**：
1. 掃描條碼。
2. 確認/修改容器與數量。
3. 生成新條碼：
   - 新製程代號 = 當前站點 (P2)。
   - 計算工時。
   - 寫入 Sheet 並回傳新條碼字串。

**前端提示**：遷出成功時，可根據 `flow.ini` 提示使用者 "下一站建議送往: P3"。

### 5.4 🔍 追溯與首站 (Trace & First)

- **首站遷出**：手動輸入工單資訊，生成第一個條碼。
- **追溯查詢**：掃描任一條碼，顯示該工單的時間軸與良率統計。

---

## 6. 資料庫設計 (Google Sheets)

單一工作表 **Logs**，欄位：

| 欄位名稱 | 說明 |
|---------|------|
| timestamp | 時間戳記 |
| action | 動作 (IN/OUT) |
| operator | 操作員工號 |
| order | 工單號 |
| process | 製程站點 |
| sku | 產品 SKU |
| container | 容器代號 |
| box_seq | 箱號 |
| qty | 數量 |
| status | 貨態 |
| cycle_time | 工時 |
| scanned_barcode | 掃描的條碼 |
| new_barcode | 新生成的條碼 |

---

## 7. 前端 UI/UX 規範 (iOS Style)

**Framework**: Tailwind CSS

**⚠️ 重要規範：嚴格遵守 Apple Human Interface Guidelines**

所有前端頁面設計必須嚴格遵守 [Apple Human Interface Guidelines](https://developer.apple.com/design/human-interface-guidelines/) 的設計原則，包括但不限於：

### 7.1 設計原則

1. **清晰度 (Clarity)**
   - 使用清晰的文字和圖標
   - 避免不必要的裝飾元素
   - 確保內容易於閱讀和理解

2. **一致性 (Deference)**
   - 介面元素應與 iOS 原生應用保持一致
   - 使用標準的 iOS 手勢和互動模式
   - 保持視覺風格的一致性

3. **深度 (Depth)**
   - 使用層次結構和動畫來傳達層次感
   - 適當使用陰影和模糊效果
   - 透過視覺層次引導使用者注意力

### 7.2 具體設計規範

**Typography（字體）**：
- 使用系統字體（San Francisco 或類似字體）
- 字體大小應符合 iOS 標準（最小 17px 用於可點擊元素）
- 適當的 letter-spacing（負值用於大標題，正值用於小標籤）
- 使用語義化的字體權重（regular, semibold, bold）

**Color（顏色）**：
- 使用 iOS 標準顏色系統
- 主要操作使用藍色（#007AFF 或類似）
- 成功狀態使用綠色，錯誤狀態使用紅色
- 確保足夠的對比度以符合無障礙標準

**Spacing（間距）**：
- 使用一致的間距系統（4px、8px、16px、24px 等）
- 確保觸控目標至少 44x44 點
- 適當的留白以提升可讀性

**Buttons（按鈕）**：
- 主要操作使用填充按鈕
- 次要操作使用邊框按鈕或文字按鈕
- 按鈕應有明確的視覺回饋（hover、active 狀態）
- 使用適當的圓角（通常 8-12px）

**Navigation（導航）**：
- 使用清晰的導航結構
- 設定按鈕應放在標題區域的右上角
- 使用標準的返回和關閉按鈕樣式

**Cards & Containers（卡片與容器）**：
- 使用適當的圓角（通常 12-18px）
- 使用微妙的陰影來建立層次感
- 適當的內邊距（通常 16-24px）

**Feedback（回饋）**：
- 所有操作都應有視覺或觸覺回饋
- 使用動畫來傳達狀態變化
- 錯誤訊息應清晰且可操作

### 7.3 頁面特定規範

- **Setup Page**: iOS Grouped List (輸入工號、選擇站點)
- **Dashboard**: iOS Widgets (Grid layout)，清晰的視覺層次
- **Scan Sheet**: Bottom Sheet，帶有動態顏色回饋
- **Flow Alert**: 當防呆觸發時，彈出 iOS Style Alert Dialog (震動+紅色)
- **Trace Page**: 全螢幕頁面，清晰的時間軸視覺化

### 7.4 參考資源

- [Apple Human Interface Guidelines](https://developer.apple.com/design/human-interface-guidelines/)
- [iOS Design Resources](https://developer.apple.com/design/resources/)
- [SF Symbols](https://developer.apple.com/sf-symbols/)（圖標系統）

---

## 8. 專案目錄結構 (Project Structure)

```
fplts_project/
├── config/                     # 設定檔目錄
│   ├── process.ini             # 製程站點定義
│   ├── series.ini              # 產品系列定義
│   ├── model.ini               # 產品機型定義
│   ├── flow.ini                # 製程流防呆定義
│   ├── container.ini           # 容器與容量定義
│   ├── status.ini              # 貨態定義
│   ├── qrcode.ini              # QR Code 設定
│   └── settings.ini            # 系統設定
├── services/                   # 核心邏輯層
│   ├── __init__.py
│   ├── barcode.py              # 條碼解析、生成、CRC校驗
│   ├── sheet.py                # Google Sheets 讀寫操作
│   ├── config_loader.py        # INI 讀取器
│   ├── flow_validator.py       # 防呆驗證邏輯
│   └── qrcode_generator.py     # QR Code 生成器
├── tests/                      # 測試目錄
│   ├── __init__.py
│   ├── conftest.py             # pytest 共享配置
│   ├── unit/                   # 單元測試
│   │   ├── __init__.py
│   │   ├── test_barcode.py
│   │   ├── test_config_loader.py
│   │   ├── test_flow_validator.py
│   │   ├── test_qrcode_generator.py
│   │   └── test_sheet.py
│   ├── integration/            # 整合測試
│   │   └── __init__.py
│   └── api/                    # API 測試
│       ├── __init__.py
│       └── test_api.py
├── static/                     # 前端資源
│   ├── index.html              # SPA 主頁面
│   └── app.js                  # 前端控制邏輯
├── .env                        # 環境變數 (GOOGLE_SHEET_ID)
├── credentials.json            # Google Service Account Key
├── main.py                     # FastAPI 應用程式入口
├── pytest.ini                  # pytest 配置
├── requirements.txt            # Python 依賴清單
├── run_tests.sh                # 測試執行腳本（根目錄）
└── run_tests_cn.py             # 中文測試報告腳本（根目錄）
```

---

## 9. 附錄

### 9.1 參考文件

- [PRD 同步使用說明](./mcp/PRD_SYNC_README.md) - PRD.md 與 Google Docs 雙向同步功能

### 9.2 版本歷史

| 版本 | 日期 | 作者 | 說明 |
|------|------|------|------|
| 1.0 | YYYY-MM-DD | [作者] | 初始版本 |

### 9.3 PRD.md 與 Google Docs 同步

本文件支援與 Google Docs 雙向同步，確保兩個版本的內容保持一致。

**快速同步指令**：
```bash
# 同步到 Google Docs（預設）
python mcp/sync_prd_gdocs.py

# 從 Google Docs 同步回本地
python mcp/sync_prd_gdocs.py --from-gdoc
```

**詳細說明**：請參考 [PRD_SYNC_README.md](./mcp/PRD_SYNC_README.md)

**Google Docs 連結**：
- 文件 ID: 請在 `.env` 檔案中設定 `GOOGLE_DOC_ID`
- 連結: 根據您設定的文件 ID 而定

---

**文件狀態**：草稿  
**最後更新**：YYYY-MM-DD  
**負責人**：[待填寫]
