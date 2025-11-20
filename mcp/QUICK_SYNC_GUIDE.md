# PRD.md ↔ Google Docs 快速同步指南

## 🚀 快速開始

### 第一次設定

1. **設定環境變數**（在 `.env` 檔案中）：
   ```env
   GOOGLE_DOC_ID=your_google_doc_id_here
   GOOGLE_CREDENTIALS_PATH=credentials.json
   ```

2. **確認 Service Account 權限**：
   - 開啟 Google Docs（使用您設定的 GOOGLE_DOC_ID）
   - 點擊「共用」→ 輸入 Service Account Email（在 `credentials.json` 中）→ 給予「編輯者」權限

3. **安裝依賴**（如果尚未安裝）：
   ```bash
   pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
   ```

### 日常使用

#### 📤 將 PRD.md 同步到 Google Docs

```bash
python mcp/sync_prd_gdocs.py
```

或明確指定方向：

```bash
python mcp/sync_prd_gdocs.py --to-gdoc
```

**注意**：請從專案根目錄執行指令。

#### 📥 從 Google Docs 同步回 PRD.md

```bash
python mcp/sync_prd_gdocs.py --from-gdoc
```

## 💡 建議工作流程

### 場景 A：主要在本地編輯

1. 編輯 `PRD.md`（位於專案根目錄）
2. 執行同步：
   ```bash
   python mcp/sync_prd_gdocs.py --to-gdoc
   ```

### 場景 B：主要在 Google Docs 編輯

1. 在 Google Docs 中編輯
2. 執行同步：
   ```bash
   python mcp/sync_prd_gdocs.py --from-gdoc
   ```

### 場景 C：混合編輯

1. **開始編輯前**：先從 Google Docs 同步回本地
   ```bash
   python mcp/sync_prd_gdocs.py --from-gdoc
   ```

2. **在本地編輯** `PRD.md`（位於專案根目錄）

3. **編輯完成後**：同步到 Google Docs
   ```bash
   python mcp/sync_prd_gdocs.py --to-gdoc
   ```

## ⚠️ 注意事項

- 同步會**覆蓋**目標文件的內容
- 建議在重要修改前先備份
- 如果兩個版本都有修改，後執行的同步會覆蓋先前的修改

## 🔧 故障排除

### 錯誤：找不到憑證檔案
```bash
# 確認 credentials.json 存在
ls credentials.json

# 或設定正確的路徑
export GOOGLE_CREDENTIALS_PATH=/path/to/credentials.json
```

### 錯誤：403 Forbidden
- 確認 Service Account 已加入 Google Docs 的共用名單
- 確認權限為「編輯者」

### 錯誤：缺少套件
```bash
pip install -r requirements.txt
```

## 📚 更多資訊

詳細說明請參考：[PRD_SYNC_README.md](./PRD_SYNC_README.md)

**注意**：執行同步腳本時，請從專案根目錄執行：
```bash
python mcp/sync_prd_gdocs.py --to-gdoc
```

