# MCP 同步工具目錄

此目錄包含 PRD.md 與 Google Docs 之間的雙向同步工具。

## 📁 檔案說明

- **`sync_prd_gdocs.py`** - 主要同步腳本（推薦使用）
  - 支援雙向同步
  - 自動判斷同步方向
  - 記錄同步歷史

- **`sync_prd_to_gdocs.py`** - 完整版同步腳本
  - 包含更多進階功能
  - 支援 MCP 工具整合

- **`sync_prd_simple.py`** - 簡化版同步腳本
  - 用於準備同步資料

- **`PRD_SYNC_README.md`** - 詳細使用說明
  - 完整設定步驟
  - 故障排除指南

- **`QUICK_SYNC_GUIDE.md`** - 快速使用指南
  - 快速開始步驟
  - 常用工作流程

## 🚀 快速開始

### 方法 1：使用 MCP 工具（推薦，不需要憑證）

**在 Cursor 中直接告訴 AI 助手**：
```
請使用 MCP 工具將 PRD.md 的內容同步到現有的 Google Docs 文件
```

**重要**：請明確說明「更新現有文件」，AI 助手會：
1. 讀取 PRD.md 的內容
2. 使用 MCP 工具**更新現有 Google Docs**（不會創建新文件）
3. 確保使用相同的文件 ID

**優點**：
- ✅ 不需要 Google Service Account 憑證
- ✅ 不需要啟用 Google Docs API
- ✅ 只需要在 Cursor 中完成 OAuth 認證
- ✅ 保持文件連結不變

### 方法 2：使用 Python 腳本（需要憑證和 API 啟用）

從專案根目錄執行：

```bash
# 同步到 Google Docs（需要憑證）
python mcp/sync_prd_gdocs.py --to-gdoc

# 從 Google Docs 同步回本地（需要憑證）
python mcp/sync_prd_gdocs.py --from-gdoc
```

**注意**：此方法需要：
- Google Service Account 憑證
- 啟用 Google Docs API
- 設定正確的權限

### 設定

在專案根目錄的 `.env` 檔案中設定：

```env
GOOGLE_DOC_ID=your_google_doc_id_here
GOOGLE_CREDENTIALS_PATH=credentials.json
```

## 📚 更多資訊

- 詳細說明：請參考 [PRD_SYNC_README.md](./PRD_SYNC_README.md)
- 快速指南：請參考 [QUICK_SYNC_GUIDE.md](./QUICK_SYNC_GUIDE.md)

## ⚠️ 注意事項

- 所有同步腳本都假設從專案根目錄執行
- PRD.md 位於專案根目錄
- 同步記錄檔案（`.prd_sync_log.json`）會保存在此目錄下

