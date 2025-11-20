# PRD.md 與 Google Docs 雙向同步說明

## 概述

此系統提供 PRD.md 與 Google Docs 之間的雙向同步功能，確保兩個版本的內容保持一致。

## 功能特點

- ✅ **雙向同步**：支援從 PRD.md 同步到 Google Docs，或從 Google Docs 同步回 PRD.md
- ✅ **自動判斷**：根據修改時間自動判斷同步方向
- ✅ **同步記錄**：記錄每次同步的歷史，方便追蹤
- ✅ **錯誤處理**：完善的錯誤提示和處理機制

## 設定步驟

### 1. 安裝依賴套件

```bash
pip install -r requirements.txt
```

### 2. 設定環境變數

在 `.env` 檔案中添加以下設定：

```env
# Google Docs 文件 ID（從 Google Docs 網址中取得）
GOOGLE_DOC_ID=your_google_doc_id_here

# Google Service Account 憑證路徑（與 Google Sheets 共用）
GOOGLE_CREDENTIALS_PATH=credentials.json
```

**如何取得 Google Docs ID：**
1. 開啟 Google Docs 文件
2. 從網址列複製文件 ID
   - 網址格式：`https://docs.google.com/document/d/{DOC_ID}/edit`
   - 例如：`https://docs.google.com/document/d/YOUR_DOC_ID/edit`
   - 文件 ID 就是 `YOUR_DOC_ID`（從網址中複製）

### 3. 設定 Google Service Account 權限

確保您的 Service Account 有編輯 Google Docs 的權限：

1. 開啟 Google Docs 文件
2. 點擊右上角「共用」按鈕
3. 輸入 Service Account 的 Email（在 `credentials.json` 中的 `client_email` 欄位）
4. 給予「編輯者」權限
5. 點擊「傳送」

## 使用方法

### 基本同步（自動判斷方向）

```bash
python mcp/sync_prd_gdocs.py
```

預設會將 PRD.md 的內容同步到 Google Docs。

**注意**：請從專案根目錄執行指令。

### 強制同步到 Google Docs

```bash
python mcp/sync_prd_gdocs.py --to-gdoc
```

### 從 Google Docs 同步回 PRD.md

```bash
python mcp/sync_prd_gdocs.py --from-gdoc
```

## 同步記錄

每次同步都會記錄在 `.prd_sync_log.json` 檔案中，包含：
- 最後修改時間
- 同步歷史記錄（最近 50 筆）

## 工作流程建議

### 場景 1：在本地編輯 PRD.md 後同步

1. 編輯 `PRD.md` 檔案（位於專案根目錄）
2. 執行同步：
   ```bash
   python mcp/sync_prd_gdocs.py --to-gdoc
   ```
3. 內容會自動更新到 Google Docs

### 場景 2：在 Google Docs 編輯後同步回本地

1. 在 Google Docs 中編輯文件
2. 執行同步：
   ```bash
   python mcp/sync_prd_gdocs.py --from-gdoc
   ```
3. 內容會更新到本地的 `PRD.md`

### 場景 3：定期雙向同步

建議的工作流程：
1. 編輯前先從 Google Docs 同步回本地（確保本地是最新的）
2. 在本地編輯 PRD.md
3. 編輯完成後同步到 Google Docs

## 注意事項

⚠️ **重要提醒**：

1. **備份重要**：同步前建議先備份 PRD.md
2. **衝突處理**：如果兩個版本都有修改，後執行的同步會覆蓋先前的修改
3. **格式轉換**：Google Docs 的格式可能會在轉換為 Markdown 時有所損失（特別是複雜的表格和格式）
4. **權限檢查**：確保 Service Account 有正確的權限

## 故障排除

### 錯誤：找不到憑證檔案

**解決方法**：
- 確認 `credentials.json` 檔案存在
- 或設定 `GOOGLE_CREDENTIALS_PATH` 環境變數指向正確的路徑

### 錯誤：403 Forbidden

**解決方法**：
- 確認 Service Account 有編輯 Google Docs 的權限
- 確認已將 Service Account 的 Email 加入文件的共用名單

### 錯誤：404 Not Found

**解決方法**：
- 確認 `GOOGLE_DOC_ID` 是否正確
- 確認文件是否存在且可存取

### 錯誤：缺少套件

**解決方法**：
```bash
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

## 進階使用

### 自動同步（使用 Git Hooks）

可以在 Git commit 時自動同步：

1. 創建 `.git/hooks/pre-commit`：
```bash
#!/bin/bash
python mcp/sync_prd_gdocs.py --to-gdoc
```

2. 賦予執行權限：
```bash
chmod +x .git/hooks/pre-commit
```

### 監控檔案變化（使用 watchdog）

可以安裝 `watchdog` 套件來監控 PRD.md 的變化並自動同步：

```bash
pip install watchdog
```

然後創建監控腳本（可選）。

## 相關檔案

- `mcp/sync_prd_gdocs.py` - 主要同步腳本
- `mcp/sync_prd_to_gdocs.py` - 完整版同步腳本（包含更多功能）
- `mcp/sync_prd_simple.py` - 簡化版同步腳本
- `mcp/.prd_sync_log.json` - 同步記錄檔案（自動生成）
- `PRD.md` - 產品需求文件（位於專案根目錄）

## 支援

如有問題或建議，請聯繫專案維護者。

