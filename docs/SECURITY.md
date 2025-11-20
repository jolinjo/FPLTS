# 安全指南 - GitHub 同步注意事項

## ⚠️ 重要安全提醒

在將代碼同步到 GitHub 之前，請確保**不會洩漏任何敏感資訊**。

## 🔒 敏感資訊清單

### 絕對不能提交到 GitHub 的檔案

1. **`credentials.json`** - Google Service Account 憑證
   - 包含私鑰和服務帳戶資訊
   - **風險等級**：🔴 極高
   - **後果**：攻擊者可以完全控制您的 Google 帳號和資源

2. **`.env`** - 環境變數檔案
   - 可能包含 API keys、tokens、ID 等
   - **風險等級**：🔴 極高
   - **後果**：攻擊者可以存取您的服務和資料

3. **任何包含真實憑證的檔案**
   - 例如：`credentials_prod.json`、`config.json` 等
   - **風險等級**：🔴 極高

### 可以提交但需要檢查的檔案

1. **`.prd_sync_log.json`** - 同步記錄
   - 目前不包含敏感資訊（只有時間戳和同步狀態）
   - **風險等級**：🟢 低
   - **建議**：可以提交，但定期檢查內容

2. **文檔檔案（`.md`）**
   - 可能包含範例 ID 或配置
   - **風險等級**：🟡 中
   - **建議**：使用範例值，不要使用真實的敏感 ID

## ✅ 安全檢查清單

在提交到 GitHub 之前，請確認：

- [ ] **執行安全檢查腳本**：`bash scripts/check_security.sh`
- [ ] `.env` 檔案已加入 `.gitignore`
- [ ] `credentials.json` 已加入 `.gitignore`
- [ ] 所有包含真實憑證的檔案都已加入 `.gitignore`
- [ ] 文檔中的範例使用假值，不是真實的敏感資訊
- [ ] 代碼中沒有硬編碼的 API keys、tokens 或密碼
- [ ] 已檢查 `git status` 確認沒有意外添加敏感檔案

## 🔍 檢查命令

### 方式 1：檢查即將提交的檔案（預防）

**設置 Git Hook 後，每次提交會自動檢查**：

```bash
# 設置 Git Hook（只需執行一次）
bash scripts/setup_git_hooks.sh
```

設置後，每次執行 `git commit` 時會自動執行安全檢查：
- ✅ 如果有安全問題，會阻止提交
- ✅ 可以使用 `git commit --no-verify` 跳過檢查（不建議）

**或手動檢查**：

```bash
bash scripts/check_security.sh
```

這個腳本會檢查：
- ✅ 是否有敏感檔案被追蹤
- ✅ .gitignore 是否正確配置
- ✅ 是否有硬編碼的敏感資訊
- ✅ 即將提交的檔案是否安全

### 方式 2：檢查 Git 歷史（診斷）

**檢查已提交到 GitHub 的歷史記錄**：

```bash
bash scripts/check_git_history.sh
```

這個腳本會檢查：
- ✅ Git 歷史中是否有 `credentials.json`
- ✅ Git 歷史中是否有 `.env`
- ✅ Git 歷史中是否有私鑰或其他敏感資訊
- ✅ 所有提交中的敏感關鍵字

**建議**：定期執行此檢查，確保歷史記錄中沒有敏感資訊。

### 手動檢查命令

```bash
# 檢查 .env 檔案
git ls-files | grep -E "\.env$|credentials\.json$"

# 檢查是否有 JSON 檔案包含敏感資訊
git ls-files | grep "\.json$" | xargs grep -l "private_key\|client_secret\|api_key" 2>/dev/null

# 查看即將提交的檔案
git status

# 查看檔案的差異
git diff --cached
```

## 📋 MCP 方式 vs 憑證方式的安全性

### MCP 方式（推薦）

**優點**：
- ✅ **不需要憑證檔案**：認證資訊存儲在 Cursor 的配置中，不會在代碼庫中
- ✅ **OAuth 認證**：使用標準的 OAuth 流程，更安全
- ✅ **無檔案風險**：沒有需要保護的憑證檔案

**風險**：
- 🟢 **低風險**：同步記錄文件不包含敏感資訊
- 🟢 **低風險**：文件 ID 不是敏感資訊（只是識別符）

### 憑證方式

**風險**：
- 🔴 **高風險**：`credentials.json` 包含私鑰，絕對不能提交
- 🔴 **高風險**：`.env` 可能包含敏感資訊
- 🟡 **中風險**：代碼中可能硬編碼文件 ID（雖然不是敏感資訊）

**防護措施**：
- ✅ 確保 `.gitignore` 正確配置
- ✅ 使用環境變數，不要硬編碼
- ✅ 定期檢查是否有敏感資訊洩漏

## 🛡️ 最佳實踐

### 1. 使用環境變數

**❌ 錯誤做法**：
```python
GOOGLE_DOC_ID = "1cX0dtEBVi0qZHniciqvS89tUG3c1f1FS5O5brg74aFk"  # 硬編碼
```

**✅ 正確做法**：
```python
GOOGLE_DOC_ID = os.getenv("GOOGLE_DOC_ID", "your_default_id_here")
```

### 2. 使用範例值

**❌ 錯誤做法**（在文檔中）：
```env
GOOGLE_DOC_ID=1cX0dtEBVi0qZHniciqvS89tUG3c1f1FS5O5brg74aFk  # 真實 ID
```

**✅ 正確做法**（在文檔中）：
```env
GOOGLE_DOC_ID=your_google_doc_id_here  # 範例值
```

### 3. 定期檢查

```bash
# 檢查是否有敏感資訊
git log --all --full-history --source -- "*credentials*" "*\.env*"
```

## 🚨 如果已經意外提交了敏感資訊

### 步驟 1：檢查歷史中是否有敏感資訊

**使用檢查腳本**：
```bash
bash scripts/check_git_history.sh
```

這個腳本會檢查：
- ✅ Git 歷史中是否有 `credentials.json`
- ✅ Git 歷史中是否有 `.env`
- ✅ Git 歷史中是否有私鑰或其他敏感資訊
- ✅ 所有提交中的敏感關鍵字

### 步驟 2：立即採取行動

#### 2.1 撤銷提交（如果還沒 push）

```bash
git reset HEAD~1  # 撤銷最後一次提交
```

#### 2.2 從歷史中移除（如果已經 push）

**方法 A：使用清理腳本（推薦）**

```bash
bash scripts/clean_git_history.sh
```

這個腳本提供三種清理方式：
1. 使用 `git filter-branch`（內建工具）
2. 使用 `git filter-repo`（推薦，需要安裝）
3. 僅刪除特定檔案

**方法 B：手動使用 git filter-branch**

```bash
# 刪除 credentials.json
git filter-branch --force --index-filter \
    "git rm --cached --ignore-unmatch credentials.json" \
    --prune-empty --tag-name-filter cat -- --all

# 刪除 .env
git filter-branch --force --index-filter \
    "git rm --cached --ignore-unmatch .env" \
    --prune-empty --tag-name-filter cat -- --all
```

**方法 C：使用 BFG Repo-Cleaner（最快）**

```bash
# 安裝 BFG
brew install bfg  # macOS
# 或下載：https://rtyley.github.io/bfg-repo-cleaner/

# 刪除檔案
bfg --delete-files credentials.json
bfg --delete-files .env

# 清理
git reflog expire --expire=now --all
git gc --prune=now --aggressive
```

#### 2.3 強制推送到遠端

```bash
# 強制推送所有分支
git push --force --all

# 強制推送所有標籤
git push --force --tags
```

#### 2.4 更換憑證

- 立即在 Google Cloud Console 中刪除舊的 Service Account
- 建立新的 Service Account 和憑證
- 更新所有使用該憑證的服務
- 更新 `.env` 檔案中的新憑證資訊

#### 2.5 通知團隊

- 如果已經 push 到遠端，通知所有協作者
- 要求他們：
  1. 刪除本地倉庫
  2. 重新 clone：`git clone <repository-url>`
  3. 不要使用 `git pull`，因為歷史已改寫

#### 2.6 檢查 GitHub

- 檢查 GitHub 的 Security 頁面
- 確認敏感資訊已從歷史中移除
- 如果 GitHub 已掃描到敏感資訊，按照提示處理

## 📚 相關資源

- [GitHub 安全最佳實踐](https://docs.github.com/en/code-security)
- [.gitignore 範例](https://github.com/github/gitignore)
- [環境變數管理](https://12factor.net/config)

## 🔐 當前專案的安全狀態

### 已保護的檔案

- ✅ `.env` - 已在 `.gitignore` 中
- ✅ `credentials.json` - 已在 `.gitignore` 中
- ✅ `*.json` - 已在 `.gitignore` 中（但排除了 `package.json`）

### 需要改進的地方

1. **文檔中的真實 ID**：
   - 部分文檔中使用了真實的 Google Docs ID
   - **建議**：使用範例值或環境變數說明

2. **同步記錄文件**：
   - `.prd_sync_log.json` 目前不包含敏感資訊
   - **建議**：定期檢查，確保不會意外記錄敏感資訊

## 💡 建議

**優先使用 MCP 方式**，因為：
- 不需要憑證檔案
- 更安全
- 更簡單

如果必須使用憑證方式，請：
- 嚴格遵守 `.gitignore` 規則
- 定期檢查是否有敏感資訊洩漏
- 使用環境變數，不要硬編碼

