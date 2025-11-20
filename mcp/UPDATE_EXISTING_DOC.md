# 更新現有 Google Docs 文件（不創建新文件）

## ⚠️ 重要原則

**所有同步操作都應該更新現有文件，而不是創建新文件。**

## 📋 為什麼要更新現有文件？

1. **保持連結不變**：文件連結和 ID 保持不變，方便分享和引用
2. **避免文件散亂**：不會產生多個版本的文件
3. **保持歷史記錄**：Google Docs 的版本歷史會保留在同一文件中

## 🔧 如何確保更新現有文件？

### 在 Cursor 中告訴 AI 助手時

**正確的說法**：
```
請使用 MCP 工具將 PRD.md 的內容同步到現有的 Google Docs 文件
```

或者：
```
請更新 Google Docs 文件（使用 .env 中設定的 GOOGLE_DOC_ID），使用 PRD.md 的最新內容
```

**錯誤的說法**（會創建新文件）：
```
請創建一個新的 Google Docs 文件
```

### AI 助手會執行的操作

1. **讀取 PRD.md** 的內容
2. **刪除現有文件內容**（使用 `GOOGLEDOCS_DELETE_CONTENT_RANGE`）
3. **重新創建內容**（使用 `GOOGLEDOCS_CREATE_DOCUMENT_MARKDOWN`，但指定現有文件 ID）

## 📝 文件 ID 設定

確保在 `.env` 檔案中設定正確的文件 ID：

```env
GOOGLE_DOC_ID=your_google_doc_id_here
```

**注意**：請使用您自己的 Google Docs ID，不要使用範例值。

## ✅ 驗證更新

同步完成後，檢查：
1. 文件連結是否相同（使用您設定的 GOOGLE_DOC_ID）
2. 文件 ID 是否與 `.env` 中的設定相同
3. 內容是否已更新

## 🔍 如果意外創建了新文件

如果 AI 助手意外創建了新文件：
1. 不要使用新文件
2. 告訴 AI 助手：「請更新現有文件，不要創建新文件」
3. 刪除意外創建的新文件

## 📚 相關文檔

- [MCP 同步指南](./MCP_SYNC_GUIDE.md)
- [PRD 同步詳細說明](./PRD_SYNC_README.md)

