# 整合測試說明

## 完整工作流程測試

`test_full_workflow.py` 是一個整合測試，**通過 API 端點**（模擬前端調用）將數據寫入 Google Sheets，模擬完整的生產流程。

### ⚠️ 重要說明

此測試**通過 FastAPI 的 TestClient 調用實際的 API 端點**，完全模擬前端頁面的調用方式：
- ✅ 使用 `POST /api/scan/first` 進行首站遷出
- ✅ 使用 `POST /api/scan/inbound` 進行遷入
- ✅ 使用 `POST /api/scan/outbound` 進行遷出
- ✅ 包含所有 API 驗證邏輯（流程驗證、CRC16 驗證等）
- ✅ 使用背景任務寫入 Google Sheets

## 測試內容

### 測試規模
- **10 張不同的工單**：TEST001 到 TEST010
- **不同的產品線**：ST, AC, MD, CA, MB
- **不同的型號**：325, 326, 327, 328, 350, 351, 352, 001
- **完整的製程流程**：從首站到末站的所有遷入/遷出操作
- **時間間隔**：每隔 2 秒執行一次操作

### 測試流程（通過 API 端點）

每張工單會執行以下流程，**完全模擬前端調用**：

1. **首站遷出**：調用 `POST /api/scan/first` 生成第一個條碼（P1）
2. **後續站點**：
   - 遷入：調用 `POST /api/scan/inbound` 掃描上一站的條碼
   - 遷出：調用 `POST /api/scan/outbound` 生成新條碼（更新製程代號）
   - 每個操作間隔 2 秒
3. **最終站**：調用 `POST /api/scan/inbound` 只執行遷入（不遷出）

### API 調用流程

```
前端頁面操作          →  API 端點調用
─────────────────────────────────────────
首站遷出（輸入工單）  →  POST /api/scan/first
掃描條碼遷入         →  POST /api/scan/inbound
掃描條碼遷出         →  POST /api/scan/outbound
```

測試完全模擬這個流程，確保 API 端點功能正常。

### 工單配置

| 工單號 | 產品線 | 型號 | 數量 | 狀態 |
|--------|--------|------|------|------|
| TEST001 | ST | 352 | 0100 | G |
| TEST002 | AC | 350 | 0050 | G |
| TEST003 | MD | 351 | 0075 | G |
| TEST004 | ST | 325 | 0120 | G |
| TEST005 | CA | 001 | 0080 | G |
| TEST006 | ST | 326 | 0090 | G |
| TEST007 | AC | 327 | 0060 | G |
| TEST008 | MD | 328 | 0110 | G |
| TEST009 | ST | 350 | 0105 | G |
| TEST010 | MB | 001 | 0070 | G |

## 執行測試

### 前置條件

1. **Google Sheets 配置**：
   - 設定 `GOOGLE_SHEET_ID` 環境變數
   - 準備好 `credentials.json` 憑證文件
   - 確保 Google Sheets 有 "Logs" 工作表

2. **測試標記**：
   - 此測試標記為 `@pytest.mark.integration`
   - 標記為 `@pytest.mark.requires_sheets`
   - 標記為 `@pytest.mark.slow`（執行時間較長）

### 執行完整測試（10 張工單）

```bash
# 執行完整工作流程測試
pytest tests/integration/test_full_workflow.py::TestFullWorkflow::test_full_production_workflow -v

# 或使用標記
pytest -m integration -v
```

**注意**：完整測試會執行約 5-10 分鐘（取決於流程長度和延遲）

### 執行單一工單測試（快速測試）

```bash
# 執行單一工單測試（用於快速驗證）
pytest tests/integration/test_full_workflow.py::TestFullWorkflow::test_single_order_workflow -v
```

**注意**：單一工單測試只需約 1-2 分鐘

### 跳過整合測試

如果不想執行整合測試（例如在 CI/CD 中）：

```bash
# 排除整合測試
pytest -m "not integration"

# 排除需要 Google Sheets 的測試
pytest -m "not requires_sheets"

# 排除慢速測試
pytest -m "not slow"
```

## 測試輸出

測試執行時會顯示詳細的進度信息：

```
================================================================================
開始完整生產流程測試（通過 API 端點）
================================================================================
測試時間: 2025-01-20 10:00:00
工單數量: 10
================================================================================

[工單 1/10] 處理工單: TEST001
  產品線: ST, 型號: 352
  流程站點: P1 -> P2 -> P3 -> P4 -> P5
  [步驟 1] 首站遷出 (P1) - 調用 API: POST /api/scan/first
    生成條碼: TEST001-P1-ST352-A1-01-G-0100-XXX
    等待 2 秒...
  [步驟 2] 遷入 (P2) - 調用 API: POST /api/scan/inbound
    掃描條碼: TEST001-P1-ST352-A1-01-G-0100-XXX
    等待 2 秒...
  [步驟 3] 遷出 (P2) - 調用 API: POST /api/scan/outbound
    新條碼: TEST001-P2-ST352-A1-01-G-0100-YYY
    等待 2 秒...
  ...
  ✅ 工單 TEST001 處理完成
```

## 驗證結果

測試完成後，可以：

1. **檢查 Google Sheets**：
   - 打開 Google Sheets
   - 查看 "Logs" 工作表
   - 驗證所有工單的記錄都已寫入

2. **使用追溯查詢**：
   - 使用 API 或前端查詢任意工單
   - 驗證時間軸和統計數據

3. **檢查測試輸出**：
   - 查看測試結果摘要
   - 確認所有工單都成功處理

## 測試特點

### ✅ 通過 API 端點執行

- **完全模擬前端調用**：使用 FastAPI TestClient 調用實際的 API 端點
- **包含完整驗證**：流程驗證、CRC16 驗證、防呆檢查等所有邏輯都會執行
- **背景任務處理**：測試會等待背景任務完成（Google Sheets 寫入）
- **真實場景模擬**：與實際前端操作完全一致

### 🔄 API 調用順序

1. `POST /api/scan/first` - 首站遷出
2. `POST /api/scan/inbound` - 遷入（每個後續站點）
3. `POST /api/scan/outbound` - 遷出（每個後續站點）
4. `POST /api/scan/inbound` - 最終站遷入

## 注意事項

1. **實際寫入數據**：此測試會實際寫入 Google Sheets，請確保使用測試環境
2. **通過 API 執行**：測試通過 API 端點執行，會觸發所有驗證邏輯和背景任務
3. **執行時間**：完整測試需要較長時間（約 5-10 分鐘），建議使用單一工單測試進行快速驗證
4. **數據清理**：測試後可能需要手動清理測試數據，或使用測試專用的 Google Sheet
5. **網路連接**：需要穩定的網路連接來訪問 Google Sheets API
6. **API 配額**：注意 Google Sheets API 的使用配額限制
7. **背景任務**：由於使用背景任務寫入，測試會等待寫入完成

## 自定義測試

可以修改 `TEST_ORDERS` 列表來：
- 調整工單數量
- 更改產品線和型號組合
- 修改數量和狀態
- 調整時間間隔（修改 `time.sleep(2)` 的值）

## 故障排除

### Google Sheets 連接失敗
- 檢查 `credentials.json` 是否存在且有效
- 檢查 `GOOGLE_SHEET_ID` 環境變數是否設定
- 確認 Google Sheets API 已啟用

### 測試超時
- 減少工單數量
- 減少時間間隔
- 使用單一工單測試

### 數據寫入失敗
- 檢查 Google Sheets 權限
- 確認 "Logs" 工作表存在
- 檢查網路連接

