# 腳本目錄說明

此目錄包含專案的各種實用腳本。

## 📁 檔案說明

### 啟動腳本

- **`start.sh`** - 啟動 FastAPI 服務
  ```bash
  # 從專案根目錄執行
  bash scripts/start.sh
  
  # 或從 scripts 目錄執行
  cd scripts && bash start.sh
  ```
  功能：
  - 自動檢查並建立虛擬環境
  - 自動安裝依賴套件
  - 啟動 FastAPI 服務

### 測試腳本

- **`run_tests.sh`** - 執行測試套件（支援中文輸出）
  ```bash
  # 從專案根目錄執行
  bash scripts/run_tests.sh
  
  # 使用中文輸出模式
  bash scripts/run_tests.sh --cn
  ```

- **`run_tests_cn.py`** - 中文測試報告生成器
  ```bash
  # 從專案根目錄執行
  python scripts/run_tests_cn.py
  ```

### Google Sheets 相關腳本

- **`setup_sheet_headers.py`** - 設定 Google Sheets 表頭
  ```bash
  # 從專案根目錄執行
  python scripts/setup_sheet_headers.py
  ```
  功能：
  - 在 Google Sheets 的 Logs 工作表中建立標準標題列
  - 檢查並確認是否覆蓋現有標題

- **`test_sheet.py`** - Google Sheets 服務測試
  ```bash
  # 從專案根目錄執行
  python scripts/test_sheet.py
  ```
  功能：
  - 測試 Google Sheets 連線
  - 測試讀取功能
  - 測試寫入功能

- **`check_security.sh`** - 安全檢查腳本
  ```bash
  # 從專案根目錄執行
  bash scripts/check_security.sh
  ```
  功能：
  - 檢查是否有敏感檔案被追蹤
  - 檢查 .gitignore 配置
  - 檢查是否有硬編碼的敏感資訊
  - **建議在每次提交到 GitHub 前執行**

- **`setup_git_hooks.sh`** - 設置 Git Hooks（自動安全檢查）
  ```bash
  # 從專案根目錄執行（只需執行一次）
  bash scripts/setup_git_hooks.sh
  ```
  功能：
  - 設置 pre-commit hook
  - 每次 `git commit` 時自動執行安全檢查
  - 如果檢查失敗，會阻止提交
  - **推薦使用**：設置後就不需要手動執行檢查了

- **`check_git_history.sh`** - 檢查 Git 歷史中的敏感資訊
  ```bash
  # 從專案根目錄執行
  bash scripts/check_git_history.sh
  ```
  功能：
  - 檢查已提交到 Git 歷史中的敏感資訊
  - 檢查是否有 `credentials.json` 或 `.env` 在歷史中
  - 檢查是否有私鑰或其他敏感資訊
  - **建議定期執行**：確保歷史記錄安全

- **`clean_git_history.sh`** - 清理 Git 歷史中的敏感資訊
  ```bash
  # 從專案根目錄執行（謹慎使用！）
  bash scripts/clean_git_history.sh
  ```
  功能：
  - 從 Git 歷史中移除敏感檔案
  - 提供多種清理方式
  - **警告**：會改寫 Git 歷史，需要所有協作者重新 clone
  - **使用前請先執行** `check_git_history.sh` 確認問題

## ⚠️ 注意事項

1. **執行位置**：所有腳本都設計為從專案根目錄執行
   - 腳本內部會自動切換到正確的工作目錄
   - 也可以直接從 `scripts/` 目錄執行，腳本會自動處理路徑

2. **虛擬環境**：建議在執行前先啟動虛擬環境
   ```bash
   source venv/bin/activate
   ```

3. **環境變數**：某些腳本需要設定環境變數（在 `.env` 檔案中）
   - `GOOGLE_SHEET_ID` - Google Sheets ID
   - `GOOGLE_CREDENTIALS_PATH` - 憑證檔案路徑

## 🔧 腳本開發規範

- 所有腳本都應該能夠從專案根目錄執行
- 使用相對路徑時，應該考慮腳本的位置
- 在腳本開頭添加路徑處理邏輯：
  ```python
  # Python 腳本
  import os
  from pathlib import Path
  script_dir = Path(__file__).parent
  project_root = script_dir.parent
  os.chdir(project_root)
  ```
  
  ```bash
  # Bash 腳本
  cd "$(dirname "$0")/.."
  ```

## 📚 相關文檔

- 測試說明：查看 [docs/TESTING.md](../docs/TESTING.md)
- Google Sheets 設定：查看 [docs/GOOGLE_SHEETS_SETUP.md](../docs/GOOGLE_SHEETS_SETUP.md)
- 專案結構：查看 [docs/PROJECT_STRUCTURE.md](../docs/PROJECT_STRUCTURE.md)

