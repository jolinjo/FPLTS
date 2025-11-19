# 系統設定指南

## ✅ 服務狀態

服務已成功啟動！您可以訪問：**http://localhost:8000**

## ⚠️ Google Sheets 設定（可選）

目前系統會顯示「找不到憑證檔案」的警告，這是正常的。如果您需要使用 Google Sheets 功能，請按照以下步驟設定：

### 步驟 1：建立 Google Service Account

1. 前往 [Google Cloud Console](https://console.cloud.google.com/)
2. 建立新專案或選擇現有專案
3. 啟用 **Google Sheets API** 和 **Google Drive API**
4. 建立 **Service Account**：
   - 前往「IAM & Admin」→「Service Accounts」
   - 點擊「Create Service Account」
   - 輸入名稱並建立
5. 建立金鑰：
   - 點擊建立的 Service Account
   - 前往「Keys」標籤
   - 點擊「Add Key」→「Create new key」
   - 選擇 JSON 格式下載
   - 將下載的 JSON 檔案重新命名為 `credentials.json` 並放在專案根目錄

### 步驟 2：建立 Google Sheets

1. 建立新的 Google Sheets 文件
2. 將第一個工作表重新命名為 **Logs**
3. 在第一行建立以下欄位標題：
   ```
   timestamp | action | operator | order | process | sku | container | box_seq | qty | status | cycle_time | scanned_barcode | new_barcode
   ```
4. 取得 Sheet ID：
   - 從網址列複製 Sheet ID（例如：`https://docs.google.com/spreadsheets/d/1ABC123.../edit` 中的 `1ABC123...`）

### 步驟 3：設定環境變數

在專案根目錄建立 `.env` 檔案：

```env
GOOGLE_SHEET_ID=your_sheet_id_here
GOOGLE_CREDENTIALS_PATH=credentials.json
```

### 步驟 4：分享 Google Sheets 給 Service Account

1. 開啟 Google Sheets 文件
2. 點擊右上角「共用」按鈕
3. 輸入 Service Account 的 Email（在 `credentials.json` 中的 `client_email` 欄位）
4. 給予「編輯者」權限
5. 點擊「傳送」

## 🧪 測試系統（無需 Google Sheets）

即使沒有設定 Google Sheets，您仍然可以：

1. ✅ 測試前端介面（iOS 風格 UI）
2. ✅ 測試登入功能
3. ✅ 測試條碼解析邏輯
4. ✅ 測試流程驗證邏輯（防呆功能）
5. ⚠️ 資料寫入會失敗（但不會影響其他功能測試）

## 📱 使用系統

1. 開啟瀏覽器訪問：`http://localhost:8000`
2. 首次使用會要求輸入：
   - **工號**：例如 `OP01`
   - **當前站點**：選擇 `P1` 到 `P5`
3. 點擊「儲存設定」後即可使用各項功能

## 🔧 功能說明

### 貨物遷入
- 掃描或輸入條碼
- 系統會自動驗證流程是否合法（防呆檢查）
- 如果流程錯誤（如跳站），會立即顯示紅色警示

### 貨物遷出
- 掃描舊條碼
- 可選擇性修改容器、箱號、貨態、數量
- 系統會生成新條碼並提示下一站

### 追溯查詢
- 掃描條碼查詢該工單的所有記錄
- 顯示良率統計

### 首站遷出
- 手動輸入工單資訊
- 生成第一個條碼

## 📱 QR Code 掃描功能

系統支援從 QR code 掃描條碼並自動填入。當您使用手機條碼掃描器掃描 QR code 時，系統會自動開啟瀏覽器並帶入條碼資料。

### QR Code URL 格式

系統支援兩種 URL 格式，都可以正常運作：

#### 格式 1：查詢參數格式（推薦）
```
http://localhost:8000/?b=條碼內容
```

#### 格式 2：路徑格式
```
http://localhost:8000/b=條碼內容
```

**注意**：格式 2 會自動重定向到格式 1，兩種格式都能正常運作。

### 使用範例

假設您的系統網址是 `http://localhost:8000`，條碼是 `251119AA01P1010100G0100`：

- **格式 1**：`http://localhost:8000/?b=251119AA01P1010100G0100`
- **格式 2**：`http://localhost:8000/b=251119AA01P1010100G0100`

### 特殊功能：ZZ 製程（新工單）

如果條碼中的製程代號是 `ZZ`（例如：`251119AA-ZZ-00000-00-00-G-0000-XXX`），系統會：

1. 自動開啟「首站遷出」功能
2. 自動填入工單號（從條碼中提取）
3. 使用者只需填寫其他欄位（產品線、機種、容器等）即可完成首站遷出

### 工作流程

1. **掃描 QR code** → 開啟瀏覽器並帶入條碼參數
2. **如果已登入** → 自動開啟對應功能並填入條碼
3. **如果未登入** → 條碼會被保存，登入後自動處理

### 注意事項

- 條碼參數使用簡化的 `b=` 格式，以減少 QR code 字數
- 系統會自動識別條碼中的製程代號，判斷應該開啟哪個功能
- 如果製程是 `ZZ`，會自動開啟首站遷出；否則預設開啟遷入功能

## 🛑 停止服務

在終端機中按 `Ctrl + C` 即可停止服務。

