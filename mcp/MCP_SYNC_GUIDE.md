# 使用 MCP 工具同步 PRD.md 到 Google Docs

## 🎯 為什麼使用 MCP 工具？

使用 MCP 工具同步有以下優點：

1. **不需要憑證**：不需要 Google Service Account 憑證檔案
2. **不需要啟用 API**：不需要在 Google Cloud Console 中啟用 Google Docs API
3. **簡單方便**：只需要在 Cursor 中完成 OAuth 認證即可
4. **自動處理**：AI 助手會自動處理所有同步操作

## 📋 使用步驟

### 步驟 1：確保 MCP 連線已建立

在 Cursor 中，MCP 連線應該已經建立。如果沒有，系統會提示您完成 OAuth 認證。

### 步驟 2：告訴 AI 助手同步

直接在 Cursor 中告訴 AI 助手：

```
請使用 MCP 工具將 PRD.md 的內容同步到 Google Docs
```

或者：

```
請更新 Google Docs 文件，使用 PRD.md 的最新內容
```

### 步驟 3：AI 助手自動處理

AI 助手會：
1. 讀取 `PRD.md` 的內容
2. 使用 MCP 工具更新 Google Docs
3. 確認同步完成

## 🔄 同步方式

**重要**：系統會**更新現有文件**，不會創建新文件。

AI 助手會：
1. 使用 `GOOGLEDOCS_DELETE_CONTENT_RANGE` 刪除現有內容
2. 使用 `GOOGLEDOCS_CREATE_DOCUMENT_MARKDOWN` 重新創建內容（在同一個文件中）

**注意**：
- 始終使用同一個 Google Docs 文件 ID
- 不會創建新的文件
- 確保文件連結保持不變

## ⚙️ 設定

確保在 `.env` 檔案中設定 Google Docs ID：

```env
GOOGLE_DOC_ID=your_google_doc_id_here
```

**注意**：請使用您自己的 Google Docs ID，不要使用範例值。

## 📝 範例對話

**您**：
```
請使用 MCP 工具將 PRD.md 的內容同步到現有的 Google Docs 文件
```

**AI 助手**：
```
好的，我將使用 MCP 工具更新現有的 Google Docs 文件。
正在讀取 PRD.md...
正在刪除現有內容...
正在插入新內容...
✅ 同步完成！已更新現有文件，未創建新文件。
```

**重要**：請明確說明「更新現有文件」，這樣 AI 助手就不會創建新文件。

## ⚠️ 注意事項

1. **MCP 連線**：確保 MCP 連線已建立且有效
2. **文件 ID**：確保 `GOOGLE_DOC_ID` 設定正確
3. **權限**：確保您的 Google 帳號有編輯該文件的權限
4. **格式**：Markdown 格式會自動轉換為 Google Docs 格式

## 🔍 故障排除

### 問題：MCP 連線未建立

**解決方法**：
1. 在 Cursor 中檢查 MCP 連線狀態
2. 如果需要，完成 OAuth 認證

### 問題：同步失敗

**解決方法**：
1. 檢查 `GOOGLE_DOC_ID` 是否正確
2. 確認 Google 帳號有編輯權限
3. 嘗試重新建立 MCP 連線

### 問題：格式不正確

**解決方法**：
- Markdown 格式會自動轉換，但某些複雜格式可能需要手動調整
- 可以告訴 AI 助手："請確保格式正確"

## 💡 最佳實踐

1. **定期同步**：每次更新 PRD.md 後，告訴 AI 助手同步
2. **檢查結果**：同步後檢查 Google Docs 中的內容
3. **備份重要**：重要修改前建議先備份

## 📚 相關文檔

- [PRD 同步詳細說明](./PRD_SYNC_README.md)
- [快速同步指南](./QUICK_SYNC_GUIDE.md)
- [MCP 工具目錄說明](./README.md)

