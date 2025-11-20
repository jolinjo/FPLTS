# Google Sheets Service Account 設定指南

## ⚠️ 目前問題

您的 `credentials.json` 檔案是 **OAuth 客戶端憑證**，但系統需要 **Service Account 憑證**。

這兩種憑證格式不同，無法互換使用。

## 📋 正確的設定步驟

### 步驟 1：前往 Google Cloud Console

1. 開啟瀏覽器，前往：https://console.cloud.google.com/
2. 登入您的 Google 帳號

### 步驟 2：建立或選擇專案

1. 點擊頂部的專案選擇器
2. 選擇現有專案或點擊「新增專案」
3. 輸入專案名稱（例如：`Factory-Logistics-System`）
4. 點擊「建立」

### 步驟 3：啟用必要的 API

1. 在左側選單中，點擊「API 和服務」→「程式庫」
2. 搜尋並啟用以下 API：
   - **Google Sheets API**
   - **Google Drive API**

### 步驟 4：建立 Service Account

1. 在左側選單中，點擊「API 和服務」→「憑證」
2. 點擊頂部的「建立憑證」→「服務帳戶」
3. 填寫服務帳戶資訊：
   - **服務帳戶名稱**：例如 `sheets-service`
   - **服務帳戶 ID**：會自動產生
   - **說明**（選填）：`用於存取 Google Sheets 的服務帳戶`
4. 點擊「建立並繼續」
5. 在「授予此服務帳戶存取專案的權限」步驟：
   - 角色選擇：`編輯者` 或 `專案` → `編輯者`
   - 點擊「繼續」
6. 在「授予使用者存取此服務帳戶的權限」步驟：
   - 可以跳過（點擊「完成」）

### 步驟 5：建立並下載金鑰

1. 在「憑證」頁面，找到剛才建立的服務帳戶
2. 點擊服務帳戶的 Email（例如：`sheets-service@your-project.iam.gserviceaccount.com`）
3. 切換到「金鑰」標籤
4. 點擊「新增金鑰」→「建立新金鑰」
5. 選擇「JSON」格式
6. 點擊「建立」
7. **JSON 檔案會自動下載**（檔案名稱類似：`your-project-xxxxx.json`）

### 步驟 6：設定憑證檔案

1. 將下載的 JSON 檔案重新命名為 `credentials.json`
2. 將檔案放到專案根目錄（與 `main.py` 同一層）
3. **重要**：確認檔案包含以下欄位：
   ```json
   {
     "type": "service_account",
     "project_id": "your-project-id",
     "private_key_id": "your-private-key-id",
     "private_key": "-----BEGIN PRIVATE KEY-----\n[您的私鑰內容]\n-----END PRIVATE KEY-----\n",
     "client_email": "your-service-account@your-project.iam.gserviceaccount.com",
     "client_id": "your-client-id",
     "auth_uri": "https://accounts.google.com/o/oauth2/auth",
     "token_uri": "https://oauth2.googleapis.com/token",
     ...
   }
   ```
   
   **注意**：這只是範例格式，實際的 `credentials.json` 會包含真實的私鑰和憑證資訊。

### 步驟 7：分享 Google Sheets 給 Service Account

1. 開啟您的 Google Sheets 文件
2. 點擊右上角的「共用」按鈕
3. 在「新增使用者和群組」欄位中，輸入 Service Account 的 Email
   - Email 格式：`xxxxx@your-project.iam.gserviceaccount.com`
   - 可以在 `credentials.json` 的 `client_email` 欄位找到
4. 選擇權限為「編輯者」
5. **取消勾選「通知人員」**（Service Account 不需要通知）
6. 點擊「共用」

### 步驟 8：建立 Logs 工作表

1. 在 Google Sheets 中，確保第一個工作表名稱為 **Logs**
2. 在第一行建立以下欄位標題：
   ```
   timestamp | action | operator | order | process | sku | container | box_seq | qty | status | cycle_time | scanned_barcode | new_barcode
   ```

### 步驟 9：驗證設定

執行測試腳本：

```bash
source venv/bin/activate
python test_sheet.py
```

如果所有測試通過，表示設定成功！

## 🔍 如何確認憑證類型

執行以下命令檢查您的憑證檔案：

```bash
python3 -c "import json; f=open('credentials.json'); data=json.load(f); print('Type:', data.get('type', 'OAuth Client')); print('Has client_email:', 'client_email' in data); f.close()"
```

**正確的 Service Account 憑證應該顯示：**
- `Type: service_account`
- `Has client_email: True`

**錯誤的 OAuth 客戶端憑證會顯示：**
- `Type: OAuth Client`
- `Has client_email: False`

## ❓ 常見問題

### Q: 為什麼不能使用 OAuth 客戶端憑證？

A: OAuth 客戶端憑證需要使用者互動授權，不適合伺服器端自動化應用。Service Account 是專為伺服器端應用設計的，無需使用者互動。

### Q: Service Account 的 Email 是什麼？

A: 格式為 `service-account-name@project-id.iam.gserviceaccount.com`，可以在 `credentials.json` 的 `client_email` 欄位找到。

### Q: 如何確認 Service Account 有權限？

A: 在 Google Sheets 的「共用」設定中，應該能看到 Service Account 的 Email 列在編輯者清單中。

## 📝 檢查清單

- [ ] 已在 Google Cloud Console 建立專案
- [ ] 已啟用 Google Sheets API 和 Google Drive API
- [ ] 已建立 Service Account（不是 OAuth 客戶端）
- [ ] 已下載 Service Account 的 JSON 金鑰
- [ ] 已將 JSON 檔案重新命名為 `credentials.json` 並放在專案根目錄
- [ ] 已在 Google Sheets 中分享給 Service Account（編輯者權限）
- [ ] 已在 Google Sheets 中建立名為 "Logs" 的工作表
- [ ] 已執行測試腳本並通過所有測試


