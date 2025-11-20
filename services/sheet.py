"""
Google Sheets 讀寫操作
"""
import os
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from typing import Dict, Optional, List
from dotenv import load_dotenv
import threading
import time

load_dotenv()

# Google Sheets API 設定
SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

# 工作表欄位順序（內部使用，英文欄位名）
COLUMNS = [
    "timestamp",
    "action",
    "operator",
    "order",
    "process",
    "sku",
    "container",
    "box_seq",
    "qty",
    "status",
    "cycle_time",
    "scanned_barcode",
    "new_barcode"
]

# 工作表欄位標題（顯示用，包含中文說明）
COLUMN_HEADERS = [
    "timestamp (時間戳記)",
    "action (動作)",
    "operator (操作員)",
    "order (工單號)",
    "process (製程站點)",
    "sku (產品SKU)",
    "container (容器代號)",
    "box_seq (箱號)",
    "qty (數量)",
    "status (貨態)",
    "cycle_time (工時)",
    "scanned_barcode (掃描條碼)",
    "new_barcode (新條碼)"
]


class SheetService:
    """Google Sheets 服務類別"""
    
    def __init__(self):
        self.client: Optional[gspread.Client] = None
        self.sheet_id: Optional[str] = None
        # 緩存相關
        self._cache: List[Dict] = []  # 內存緩存，存儲所有記錄
        self._cache_lock = threading.Lock()  # 緩存鎖，確保線程安全
        self._last_sync_time: Optional[float] = None  # 最後同步時間
        self._sync_interval = 30  # 同步間隔（秒）- 增加到 30 秒，避免速率限制
        self._sync_thread: Optional[threading.Thread] = None
        self._stop_sync = False  # 停止同步標誌
        self._sync_failure_count = 0  # 同步失敗計數
        self._initialize()
        # 初始化後立即同步一次，然後啟動定期同步
        if self.client and self.sheet_id:
            print("[緩存初始化] 後端啟動，開始首次同步資料...")
            self._sync_from_sheet()
            self._start_periodic_sync()
        else:
            print("[緩存初始化] 警告：Google Sheets 客戶端未初始化，無法同步資料")
    
    def _initialize(self):
        """初始化 Google Sheets 客戶端"""
        credentials_path = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
        sheet_id = os.getenv("GOOGLE_SHEET_ID")
        
        if not os.path.exists(credentials_path):
            print(f"警告：找不到憑證檔案 {credentials_path}")
            return
        
        if not sheet_id:
            print("警告：未設定 GOOGLE_SHEET_ID 環境變數")
            return
        
        try:
            # 檢查憑證檔案類型
            import json
            with open(credentials_path, 'r') as f:
                cred_data = json.load(f)
            
            # 判斷是 Service Account 還是 OAuth 客戶端憑證
            if 'type' in cred_data and cred_data['type'] == 'service_account':
                # Service Account 憑證
                creds = Credentials.from_service_account_file(credentials_path, scopes=SCOPE)
                self.client = gspread.authorize(creds)
                self.sheet_id = sheet_id
                print("✓ 使用 Service Account 憑證初始化成功")
            elif 'installed' in cred_data or 'web' in cred_data:
                # OAuth 客戶端憑證（不支援，需要 Service Account）
                print("❌ 錯誤：偵測到 OAuth 客戶端憑證，但系統需要 Service Account 憑證")
                print("   請按照以下步驟取得正確的憑證：")
                print("   1. 前往 Google Cloud Console")
                print("   2. 建立或選擇專案")
                print("   3. 啟用 Google Sheets API 和 Google Drive API")
                print("   4. 建立 Service Account（不是 OAuth 客戶端）")
                print("   5. 下載 Service Account 的 JSON 金鑰")
                print("   6. 將下載的 JSON 檔案重新命名為 credentials.json")
                return
            else:
                print(f"❌ 錯誤：無法識別的憑證格式")
                print(f"   憑證檔案應為 Service Account JSON 格式")
                return
        except json.JSONDecodeError:
            print(f"❌ 錯誤：憑證檔案不是有效的 JSON 格式")
            return
        except Exception as e:
            print(f"❌ 初始化 Google Sheets 客戶端失敗：{e}")
            import traceback
            traceback.print_exc()
    
    def _sync_from_sheet(self) -> bool:
        """
        從 Google Sheets 同步所有數據到緩存
        
        Returns:
            是否同步成功
        """
        if not self.client or not self.sheet_id:
            return False
        
        try:
            spreadsheet = self.client.open_by_key(self.sheet_id)
            worksheet = spreadsheet.worksheet("Logs")
            
            # 讀取所有記錄
            try:
                headers = worksheet.row_values(1)
                if not headers or len(headers) == 0:
                    # 沒有標題列，可能是空工作表
                    with self._cache_lock:
                        self._cache = []
                        self._last_sync_time = time.time()
                    print("[緩存同步] 工作表為空，清空緩存")
                    return True
                
                # 檢查第一行是否為標題欄
                first_cell = headers[0] if headers else ""
                is_header_row = False
                if first_cell:
                    header_keywords = ["timestamp", "時間戳記", "action", "動作"]
                    first_cell_lower = str(first_cell).lower()
                    is_header_row = any(keyword in first_cell_lower for keyword in header_keywords)
                
                if not is_header_row:
                    # 第一行不是標題欄，可能是空工作表
                    with self._cache_lock:
                        self._cache = []
                        self._last_sync_time = time.time()
                    print("[緩存同步] 工作表沒有標題列，清空緩存")
                    return True
                
                # 建立標題對應字典
                header_to_column = {}
                for i, header in enumerate(headers):
                    if "(" in header:
                        column_name = header.split("(")[0].strip()
                    else:
                        column_name = header.strip()
                    
                    if column_name in COLUMNS:
                        header_to_column[header] = column_name
                    elif i < len(COLUMNS):
                        header_to_column[header] = COLUMNS[i]
                
                # 讀取所有記錄（從第二行開始）
                all_records = worksheet.get_all_records()
                records = []
                for record in all_records:
                    new_record = {}
                    for header, value in record.items():
                        column_name = header_to_column.get(header, header.split("(")[0].strip() if "(" in header else header)
                        new_record[column_name] = str(value) if value is not None else ""
                    records.append(new_record)
                
                # 更新緩存
                with self._cache_lock:
                    self._cache = records
                    self._last_sync_time = time.time()
                
                # 同步成功，重置失敗計數
                if self._sync_failure_count > 0:
                    self._sync_failure_count = 0
                    print(f"[緩存同步] 同步恢復正常，間隔恢復為 {self._sync_interval} 秒")
                
                print(f"[緩存同步] 成功同步 {len(records)} 筆記錄到緩存")
                return True
                
            except Exception as e:
                print(f"[緩存同步] 讀取記錄失敗：{e}")
                import traceback
                traceback.print_exc()
                return False
                
        except Exception as e:
            error_str = str(e)
            # 檢查是否為速率限制錯誤
            if '429' in error_str or 'Quota exceeded' in error_str or 'RATE_LIMIT_EXCEEDED' in error_str:
                self._sync_failure_count += 1
                print(f"[緩存同步] 速率限制錯誤（第 {self._sync_failure_count} 次），將延長同步間隔")
                # 如果連續失敗，增加同步間隔
                if self._sync_failure_count >= 3:
                    self._sync_interval = min(self._sync_interval * 2, 300)  # 最多 5 分鐘
                    print(f"[緩存同步] 同步間隔已調整為 {self._sync_interval} 秒")
                    self._sync_failure_count = 0  # 重置計數
            else:
                print(f"[緩存同步] 同步失敗：{e}")
                import traceback
                traceback.print_exc()
            return False
    
    def _start_periodic_sync(self):
        """啟動定期同步線程"""
        if self._sync_thread and self._sync_thread.is_alive():
            return  # 已經在運行
        
        def sync_worker():
            while not self._stop_sync:
                # 使用動態間隔（可能因為錯誤而調整）
                current_interval = self._sync_interval
                time.sleep(current_interval)
                if not self._stop_sync:
                    print(f"[緩存同步] 開始定期同步（間隔 {current_interval} 秒）...")
                    self._sync_from_sheet()
        
        self._stop_sync = False
        self._sync_thread = threading.Thread(target=sync_worker, daemon=True)
        self._sync_thread.start()
        print(f"[緩存同步] 已啟動定期同步線程（每 {self._sync_interval} 秒同步一次）")
    
    def stop_periodic_sync(self):
        """停止定期同步"""
        self._stop_sync = True
        if self._sync_thread:
            self._sync_thread.join(timeout=1)
        print("[緩存同步] 已停止定期同步線程")
    
    def force_sync(self) -> bool:
        """
        強制立即同步（手動觸發）
        
        Returns:
            是否同步成功
        """
        print("[緩存同步] 手動觸發同步...")
        return self._sync_from_sheet()
    
    def write_log(self, log_data: Dict[str, any]) -> bool:
        """
        寫入一筆記錄到 Google Sheets
        
        Args:
            log_data: 記錄資料字典，應包含所有 COLUMNS 欄位
        
        Returns:
            是否寫入成功
        """
        if not self.client or not self.sheet_id:
            print("Google Sheets 客戶端未初始化")
            return False
        
        try:
            spreadsheet = self.client.open_by_key(self.sheet_id)
            worksheet = spreadsheet.worksheet("Logs")
            
            # 讀取或建立標題列
            try:
                headers = worksheet.row_values(1)
                # 檢查第一行是否為空或不是標題欄
                if not headers or len(headers) == 0:
                    # 第一行為空，建立標題列（使用帶中文說明的標題）
                    # 使用 update 而不是 append_row，確保寫入第一行
                    worksheet.update('A1', [COLUMN_HEADERS])
                    headers = COLUMN_HEADERS
                else:
                    # 檢查第一行是否已經是標題欄（檢查是否包含關鍵字）
                    first_cell = headers[0] if headers else ""
                    is_header_row = False
                    if first_cell:
                        # 檢查第一個單元格是否包含標題欄的關鍵字
                        header_keywords = ["timestamp", "時間戳記", "action", "動作"]
                        first_cell_lower = str(first_cell).lower()
                        is_header_row = any(keyword in first_cell_lower for keyword in header_keywords)
                    
                    if not is_header_row:
                        # 第一行不是標題欄，插入標題欄到第一行
                        worksheet.insert_row(COLUMN_HEADERS, 1)
                        headers = COLUMN_HEADERS
                    # 如果已經是標題欄，使用現有的標題
            except Exception as e:
                # 如果無法讀取第一行，嘗試檢查工作表是否為空
                try:
                    all_values = worksheet.get_all_values()
                    if not all_values or len(all_values) == 0:
                        # 工作表為空，建立標題列
                        worksheet.update('A1', [COLUMN_HEADERS])
                        headers = COLUMN_HEADERS
                    else:
                        # 工作表有內容，讀取第一行作為標題
                        headers = all_values[0] if all_values else COLUMN_HEADERS
                        # 檢查第一行是否為標題欄
                        first_cell = headers[0] if headers else ""
                        is_header_row = False
                        if first_cell:
                            header_keywords = ["timestamp", "時間戳記", "action", "動作"]
                            first_cell_lower = str(first_cell).lower()
                            is_header_row = any(keyword in first_cell_lower for keyword in header_keywords)
                        
                        if not is_header_row:
                            # 第一行不是標題欄，插入標題欄
                            worksheet.insert_row(COLUMN_HEADERS, 1)
                            headers = COLUMN_HEADERS
                except:
                    # 如果所有操作都失敗，使用預設標題
                    headers = COLUMN_HEADERS
            
            # 建立標題到欄位的映射（根據 Sheet 中的實際標題順序）
            header_to_column = {}
            for i, header in enumerate(headers):
                # 從標題中提取欄位名（例如："order (工單號)" -> "order"）
                if "(" in header:
                    column_name = header.split("(")[0].strip()
                else:
                    column_name = header.strip()
                
                # 如果提取的欄位名在 COLUMNS 中，使用它；否則使用索引對應的 COLUMNS
                if column_name in COLUMNS:
                    header_to_column[header] = column_name
                elif i < len(COLUMNS):
                    header_to_column[header] = COLUMNS[i]
            
            # 定義需要轉換為大寫的欄位（字串欄位）
            uppercase_fields = {"action", "operator", "order", "process", "sku", "container", 
                              "box_seq", "status", "scanned_barcode", "new_barcode"}
            
            # 準備資料列（按照 Sheet 中的實際欄位順序）
            row_data = []
            for header in headers:
                # 找到對應的欄位名
                column_name = header_to_column.get(header, None)
                if not column_name:
                    # 如果找不到對應的欄位，嘗試直接從標題提取
                    if "(" in header:
                        column_name = header.split("(")[0].strip()
                    else:
                        column_name = header.strip()
                
                # 取得值
                if column_name:
                    value = log_data.get(column_name, "")
                else:
                    value = ""
                
                # 轉換為字串並統一轉換為大寫（如果是需要轉換的欄位）
                if value is None:
                    value = ""
                elif isinstance(value, datetime):
                    value = value.strftime("%Y-%m-%d %H:%M:%S")
                else:
                    value = str(value)
                    # 如果是需要轉換為大寫的欄位，統一轉換
                    if column_name and column_name in uppercase_fields:
                        # 特殊處理：new_barcode 欄位如果是 URL，只轉換條碼部分，保留 domain 為小寫
                        if column_name == "new_barcode" and ("http://" in value.lower() or "https://" in value.lower() or "/b=" in value):
                            # 分離 domain 和條碼部分
                            if "/b=" in value:
                                parts = value.split("/b=", 1)
                                if len(parts) == 2:
                                    domain_part = parts[0]  # 保留 domain 為原始大小寫
                                    barcode_part = parts[1].upper()  # 只轉換條碼部分為大寫
                                    value = f"{domain_part}/b={barcode_part}"
                                else:
                                    value = value.upper()
                            else:
                                value = value.upper()
                        else:
                            value = value.upper()
                
                row_data.append(value)
            
            # 追加到工作表
            worksheet.append_row(row_data)
            
            # 寫入成功後，立即更新緩存（保持數據一致性）
            with self._cache_lock:
                # 確保 log_data 的格式與緩存中的記錄格式一致
                cache_record = {}
                for col in COLUMNS:
                    cache_record[col] = str(log_data.get(col, ""))
                self._cache.append(cache_record)
                print(f"[緩存更新] 已將新記錄添加到緩存（總計 {len(self._cache)} 筆）")
            
            return True
        
        except Exception as e:
            print(f"寫入 Google Sheets 失敗：{e}")
            return False
    
    def write_logs_batch(self, log_data_list: list) -> tuple:
        """
        批量寫入多筆記錄到 Google Sheets（一次性 API 調用）
        
        Args:
            log_data_list: 記錄資料字典列表，每個字典應包含所有 COLUMNS 欄位
        
        Returns:
            Tuple[int, list]: (成功筆數, 失敗的記錄索引列表)
        """
        if not self.client or not self.sheet_id:
            print("Google Sheets 客戶端未初始化")
            return (0, list(range(len(log_data_list))))
        
        if not log_data_list or len(log_data_list) == 0:
            return (0, [])
        
        try:
            spreadsheet = self.client.open_by_key(self.sheet_id)
            worksheet = spreadsheet.worksheet("Logs")
            
            # 讀取或建立標題列（只讀取一次）
            try:
                headers = worksheet.row_values(1)
                # 檢查第一行是否為空或不是標題欄
                if not headers or len(headers) == 0:
                    worksheet.update('A1', [COLUMN_HEADERS])
                    headers = COLUMN_HEADERS
                else:
                    first_cell = headers[0] if headers else ""
                    is_header_row = False
                    if first_cell:
                        header_keywords = ["timestamp", "時間戳記", "action", "動作"]
                        first_cell_lower = str(first_cell).lower()
                        is_header_row = any(keyword in first_cell_lower for keyword in header_keywords)
                    
                    if not is_header_row:
                        worksheet.insert_row(COLUMN_HEADERS, 1)
                        headers = COLUMN_HEADERS
            except Exception as e:
                try:
                    all_values = worksheet.get_all_values()
                    if not all_values or len(all_values) == 0:
                        worksheet.update('A1', [COLUMN_HEADERS])
                        headers = COLUMN_HEADERS
                    else:
                        headers = all_values[0] if all_values else COLUMN_HEADERS
                        first_cell = headers[0] if headers else ""
                        is_header_row = False
                        if first_cell:
                            header_keywords = ["timestamp", "時間戳記", "action", "動作"]
                            first_cell_lower = str(first_cell).lower()
                            is_header_row = any(keyword in first_cell_lower for keyword in header_keywords)
                        
                        if not is_header_row:
                            worksheet.insert_row(COLUMN_HEADERS, 1)
                            headers = COLUMN_HEADERS
                except:
                    headers = COLUMN_HEADERS
            
            # 建立標題到欄位的映射（只建立一次）
            header_to_column = {}
            for i, header in enumerate(headers):
                if "(" in header:
                    column_name = header.split("(")[0].strip()
                else:
                    column_name = header.strip()
                
                if column_name in COLUMNS:
                    header_to_column[header] = column_name
                elif i < len(COLUMNS):
                    header_to_column[header] = COLUMNS[i]
            
            # 定義需要轉換為大寫的欄位
            uppercase_fields = {"action", "operator", "order", "process", "sku", "container", 
                              "box_seq", "status", "scanned_barcode", "new_barcode"}
            
            # 準備所有資料列（批量處理）
            rows_data = []
            for log_data in log_data_list:
                row_data = []
                for header in headers:
                    column_name = header_to_column.get(header, None)
                    if not column_name:
                        if "(" in header:
                            column_name = header.split("(")[0].strip()
                        else:
                            column_name = header.strip()
                    
                    if column_name:
                        value = log_data.get(column_name, "")
                    else:
                        value = ""
                    
                    # 轉換為字串並統一轉換為大寫（如果是需要轉換的欄位）
                    if value is None:
                        value = ""
                    elif isinstance(value, datetime):
                        value = value.strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        value = str(value)
                        if column_name and column_name in uppercase_fields:
                            if column_name == "new_barcode" and ("http://" in value.lower() or "https://" in value.lower() or "/b=" in value):
                                if "/b=" in value:
                                    parts = value.split("/b=", 1)
                                    if len(parts) == 2:
                                        domain_part = parts[0]
                                        barcode_part = parts[1].upper()
                                        value = f"{domain_part}/b={barcode_part}"
                                    else:
                                        value = value.upper()
                                else:
                                    value = value.upper()
                            else:
                                value = value.upper()
                    
                    row_data.append(value)
                
                rows_data.append(row_data)
            
            # 批量追加到工作表（一次性 API 調用）
            if rows_data:
                worksheet.append_rows(rows_data)
                print(f"[批量寫入] 成功寫入 {len(rows_data)} 筆記錄")
                return (len(rows_data), [])
            else:
                return (0, list(range(len(log_data_list))))
        
        except Exception as e:
            print(f"批量寫入 Google Sheets 失敗：{e}")
            import traceback
            traceback.print_exc()
            return (0, list(range(len(log_data_list))))
    
    def get_logs_by_barcode(self, barcode: str, limit: int = 100) -> list:
        """
        根據條碼查詢記錄（查詢 scanned_barcode 或 new_barcode 欄位）
        優先從緩存讀取，避免 API 調用
        
        Args:
            barcode: 條碼字串
            limit: 最大返回筆數
        
        Returns:
            記錄列表
        """
        # 標準化條碼（移除可能的 domain 前綴）
        barcode_normalized = barcode
        if "/b=" in barcode:
            barcode_normalized = barcode.split("/b=")[-1]
        
        # 從緩存讀取
        with self._cache_lock:
            filtered = []
            for record in self._cache:
                scanned = str(record.get("scanned_barcode", "")).strip()
                new = str(record.get("new_barcode", "")).strip()
                
                # 標準化記錄中的條碼
                scanned_normalized = scanned
                if "/b=" in scanned:
                    scanned_normalized = scanned.split("/b=")[-1]
                
                new_normalized = new
                if "/b=" in new:
                    new_normalized = new.split("/b=")[-1]
                
                # 檢查條碼是否匹配（精確匹配）
                if (barcode_normalized == scanned_normalized or 
                    barcode_normalized == new_normalized):
                    filtered.append(record)
            
            # 限制筆數
            return filtered[:limit]
    
    def has_inbound_record(self, barcode: str) -> bool:
        """
        檢查條碼是否有遷入（IN）記錄
        
        Args:
            barcode: 條碼字串
        
        Returns:
            如果有 IN 記錄則返回 True，否則返回 False
        """
        logs = self.get_logs_by_barcode(barcode, limit=10)
        for log in logs:
            if log.get("action", "").upper() == "IN":
                return True
        return False
    
    def has_outbound_record(self, barcode: str) -> bool:
        """
        檢查條碼是否有遷出（OUT）記錄
        
        Args:
            barcode: 條碼字串
        
        Returns:
            如果有 OUT 記錄則返回 True，否則返回 False
        """
        logs = self.get_logs_by_barcode(barcode, limit=10)
        for log in logs:
            if log.get("action", "").upper() == "OUT":
                return True
        return False
    
    def has_outbound_record_at_station(self, barcode: str, station_id: str) -> bool:
        """
        檢查條碼在指定站點是否有遷出（OUT）記錄
        優先從緩存讀取，避免 API 調用
        
        Args:
            barcode: 條碼字串
            station_id: 製程站點代號（例如：P1, P2）
        
        Returns:
            如果在指定站點有 OUT 記錄則返回 True，否則返回 False
        """
        # 標準化條碼（移除 domain 前綴）
        barcode_norm = barcode.split("/b=")[-1] if "/b=" in barcode else barcode
        station_id_upper = station_id.upper()
        
        # 從緩存讀取
        with self._cache_lock:
            for record in self._cache:
                scanned = str(record.get("scanned_barcode", "")).strip()
                scanned_norm = scanned.split("/b=")[-1] if "/b=" in scanned else scanned
                
                if scanned_norm == barcode_norm:
                    action = str(record.get("action", "")).strip().upper()
                    process = str(record.get("process", "")).strip().upper()
                    
                    if action == "OUT" and process == station_id_upper:
                        return True
        
        return False
    
    def has_inbound_record_at_station(self, barcode: str, station_id: str) -> bool:
        """
        檢查條碼在指定站點是否有遷入（IN）記錄
        使用 findall 直接查詢，避免讀取整個工作表
        
        Args:
            barcode: 條碼字串
            station_id: 製程站點代號（例如：P1, P2）
        
        Returns:
            如果在指定站點有 IN 記錄則返回 True，否則返回 False
        """
        if not self.client or not self.sheet_id:
            return False
        
        try:
            spreadsheet = self.client.open_by_key(self.sheet_id)
            worksheet = spreadsheet.worksheet("Logs")
            
            # 讀取標題列
            try:
                headers = worksheet.row_values(1)
                if not headers or len(headers) == 0:
                    return False
            except:
                return False
            
            # 找到 scanned_barcode、process 和 action 欄位的位置
            scanned_barcode_col = None
            process_col = None
            action_col = None
            
            for i, header in enumerate(headers):
                if "(" in header:
                    column_name = header.split("(")[0].strip()
                else:
                    column_name = header.strip()
                
                if column_name == "scanned_barcode":
                    scanned_barcode_col = i + 1
                elif column_name == "process":
                    process_col = i + 1
                elif column_name == "action":
                    action_col = i + 1
            
            if not scanned_barcode_col or not process_col or not action_col:
                return False
            
            # 標準化條碼（移除 domain 前綴）
            barcode_norm = barcode.split("/b=")[-1] if "/b=" in barcode else barcode
            station_id_upper = station_id.upper()
            
            # 使用 findall 直接查詢條碼
            try:
                cells = worksheet.findall(barcode_norm)
                for cell in cells:
                    # 只考慮 scanned_barcode 欄位中的匹配
                    if cell.col == scanned_barcode_col:
                        # 驗證是否為完整匹配
                        cell_value = str(cell.value).strip()
                        cell_value_norm = cell_value.split("/b=")[-1] if "/b=" in cell_value else cell_value
                        
                        if cell_value_norm == barcode_norm:
                            row_num = cell.row
                            if row_num == 1:  # 跳過標題行
                                continue
                            
                            # 讀取該行的 process 和 action 欄位
                            try:
                                process_value = worksheet.cell(row_num, process_col).value
                                action_value = worksheet.cell(row_num, action_col).value if action_col else None
                                
                                # 檢查是否為 IN 記錄且 process 匹配
                                if str(action_value).strip().upper() == "IN" and \
                                   str(process_value).strip().upper() == station_id_upper:
                                    return True
                            except:
                                continue
            except:
                return False
        
        except Exception as e:
            print(f"檢查遷入記錄失敗：{e}")
            return False
        
        return False
    
    def batch_check_inbound_records(self, barcodes: list, station_id: str) -> dict:
        """
        批量檢查多個條碼在指定站點是否有遷入（IN）記錄
        優先從緩存讀取，避免 API 調用
        
        Args:
            barcodes: 條碼字串列表
            station_id: 製程站點代號（例如：P1, P2）
        
        Returns:
            dict: {barcode: bool} 映射，表示每個條碼是否有 IN 記錄
        """
        if not barcodes or len(barcodes) == 0:
            return {}
        
        result = {barcode: False for barcode in barcodes}
        
        if not self.client or not self.sheet_id:
            return result
        
        try:
            spreadsheet = self.client.open_by_key(self.sheet_id)
            worksheet = spreadsheet.worksheet("Logs")
            
            # 讀取標題列（只讀一次）
            try:
                headers = worksheet.row_values(1)
                if not headers or len(headers) == 0:
                    return result
            except:
                return result
            
            # 找到 scanned_barcode、process 和 action 欄位的位置
            scanned_barcode_col = None
            process_col = None
            action_col = None
            
            for i, header in enumerate(headers):
                if "(" in header:
                    column_name = header.split("(")[0].strip()
                else:
                    column_name = header.strip()
                
                if column_name == "scanned_barcode":
                    scanned_barcode_col = i + 1
                elif column_name == "process":
                    process_col = i + 1
                elif column_name == "action":
                    action_col = i + 1
            
            if not scanned_barcode_col or not process_col or not action_col:
                return result
            
            # 標準化條碼（移除 domain 前綴）
            barcodes_normalized = {}
            for barcode in barcodes:
                barcode_norm = barcode.split("/b=")[-1] if "/b=" in barcode else barcode
                barcodes_normalized[barcode_norm] = barcode
            
            station_id_upper = station_id.upper()
            
            # 使用 findall 直接查詢每個條碼（只查詢 scanned_barcode 欄位）
            # 這樣可以快速定位到包含該條碼的行
            found_rows = {}  # {row_num: [barcode_norm]}
            
            for barcode_norm in barcodes_normalized.keys():
                try:
                    # 查找包含該條碼的單元格（在 scanned_barcode 欄位中）
                    # 使用完整匹配模式，避免部分匹配
                    cells = worksheet.findall(barcode_norm)
                    for cell in cells:
                        # 只考慮 scanned_barcode 欄位中的匹配
                        if cell.col == scanned_barcode_col:
                            # 驗證是否為完整匹配（讀取單元格值進行驗證）
                            cell_value = str(cell.value).strip()
                            cell_value_norm = cell_value.split("/b=")[-1] if "/b=" in cell_value else cell_value
                            
                            if cell_value_norm == barcode_norm:
                                if cell.row not in found_rows:
                                    found_rows[cell.row] = []
                                found_rows[cell.row].append(barcode_norm)
                except:
                    continue
            
            # 對於找到的行，批量讀取 process 和 action 欄位來驗證
            if found_rows:
                # 使用 batch_get 批量讀取多個單元格，比逐個讀取快
                try:
                    # 準備要讀取的範圍列表
                    ranges_to_read = []
                    row_nums = sorted([r for r in found_rows.keys() if r > 1])  # 跳過標題行
                    
                    if row_nums:
                        # 批量讀取這些行的 process 和 action 欄位
                        # 使用 A1 表示法構建範圍
                        process_col_letter = gspread.utils.rowcol_to_a1(1, process_col)[0]
                        action_col_letter = gspread.utils.rowcol_to_a1(1, action_col)[0] if action_col else None
                        
                        # 構建範圍字符串（例如：D2:D100, E2:E100）
                        if len(row_nums) > 0:
                            min_row = min(row_nums)
                            max_row = max(row_nums)
                            ranges_to_read.append(f"{process_col_letter}{min_row}:{process_col_letter}{max_row}")
                            if action_col_letter:
                                ranges_to_read.append(f"{action_col_letter}{min_row}:{action_col_letter}{max_row}")
                        
                        # 批量讀取
                        if ranges_to_read:
                            batch_values = worksheet.batch_get(ranges_to_read)
                            
                            # 處理讀取的數據
                            process_values = batch_values[0] if batch_values else []
                            action_values = batch_values[1] if len(batch_values) > 1 and action_col_letter else []
                            
                            # 建立行號到索引的映射
                            row_to_index = {row_num: idx for idx, row_num in enumerate(row_nums)}
                            
                            # 檢查每一行
                            for row_num, matched_barcodes in found_rows.items():
                                if row_num == 1:  # 跳過標題行
                                    continue
                                
                                idx = row_to_index.get(row_num)
                                if idx is not None and idx < len(process_values):
                                    process_row = process_values[idx]
                                    action_row = action_values[idx] if idx < len(action_values) else []
                                    
                                    process_value = process_row[0] if process_row else ""
                                    action_value = action_row[0] if action_row else ""
                                    
                                    # 檢查是否為 IN 記錄且 process 匹配
                                    if str(action_value).strip().upper() == "IN" and \
                                       str(process_value).strip().upper() == station_id_upper:
                                        # 標記所有匹配的條碼
                                        for barcode_norm in matched_barcodes:
                                            original_barcode = barcodes_normalized[barcode_norm]
                                            result[original_barcode] = True
                except Exception as e:
                    print(f"批量讀取行數據失敗，降級為逐個讀取：{e}")
                    # 降級為逐個讀取
                    for row_num, matched_barcodes in found_rows.items():
                        if row_num == 1:
                            continue
                        try:
                            process_value = worksheet.cell(row_num, process_col).value
                            action_value = worksheet.cell(row_num, action_col).value if action_col else None
                            
                            if str(action_value).strip().upper() == "IN" and \
                               str(process_value).strip().upper() == station_id_upper:
                                for barcode_norm in matched_barcodes:
                                    original_barcode = barcodes_normalized[barcode_norm]
                                    result[original_barcode] = True
                        except:
                            continue
        
        except Exception as e:
            print(f"批量檢查遷入記錄失敗：{e}")
            import traceback
            traceback.print_exc()
            # 如果查詢失敗，返回全部 False（不降級為逐個檢查，避免更多 API 調用）
        
        return result
    
    def has_outbound_record_at_downstream_stations(self, barcode: str, current_station: str) -> bool:
        """
        檢查條碼在下游站點是否有遷出（OUT）記錄
        
        Args:
            barcode: 條碼字串
            current_station: 當前站點代號（例如：P2）
        
        Returns:
            如果在下游站點有 OUT 記錄則返回 True，否則返回 False
        """
        # 定義站點順序
        station_order = {'P1': 1, 'P2': 2, 'P3': 3, 'P4': 4, 'P5': 5}
        current_order = station_order.get(current_station.upper(), 999)
        
        # 如果當前站點不在定義中，返回 False
        if current_order == 999:
            return False
        
        logs = self.get_logs_by_barcode(barcode, limit=100)
        for log in logs:
            if log.get("action", "").upper() == "OUT":
                log_process = log.get("process", "").upper()
                log_order = station_order.get(log_process, 999)
                # 如果記錄的站點順序大於當前站點，說明是下游站點
                if log_order > current_order:
                    return True
        return False
    
    def get_logs_by_order(self, order: str, limit: int = 100) -> list:
        """
        根據工單號查詢記錄
        
        Args:
            order: 工單號
            limit: 最大返回筆數
        
        Returns:
            記錄列表
        """
        if not self.client or not self.sheet_id:
            return []
        
        try:
            spreadsheet = self.client.open_by_key(self.sheet_id)
            worksheet = spreadsheet.worksheet("Logs")
            
            # 檢查是否有標題列
            try:
                headers = worksheet.row_values(1)
                if not headers or len(headers) == 0:
                    # 沒有標題列，無法使用 get_all_records
                    # 手動讀取資料
                    all_values = worksheet.get_all_values()
                    if len(all_values) <= 1:
                        return []  # 只有標題列或沒有資料
                    
                    # 使用預設標題（英文欄位名）
                    headers = COLUMNS
                    records = []
                    for row in all_values[1:]:  # 跳過標題列
                        if len(row) > 0:  # 確保不是空行
                            record = {}
                            for i, header in enumerate(headers):
                                if i < len(row):
                                    record[header] = row[i]
                                else:
                                    record[header] = ""
                            records.append(record)
                else:
                    # 有標題列，需要將帶中文的標題轉換為英文欄位名
                    # 建立標題對應字典
                    header_to_column = {}
                    for i, header in enumerate(headers):
                        # 從標題中提取英文欄位名（移除括號和中文）
                        if "(" in header:
                            # 格式：timestamp (時間戳記) -> timestamp
                            column_name = header.split("(")[0].strip()
                        else:
                            # 如果沒有括號，直接使用
                            column_name = header.strip()
                        
                        # 如果提取的欄位名在 COLUMNS 中，使用它；否則使用索引對應的 COLUMNS
                        if column_name in COLUMNS:
                            header_to_column[header] = column_name
                        elif i < len(COLUMNS):
                            header_to_column[header] = COLUMNS[i]
                    
                    # 讀取所有記錄
                    all_records = worksheet.get_all_records()
                    # 轉換標題為英文欄位名
                    records = []
                    for record in all_records:
                        new_record = {}
                        for header, value in record.items():
                            # 使用對應的英文欄位名
                            column_name = header_to_column.get(header, header.split("(")[0].strip() if "(" in header else header)
                            new_record[column_name] = value
                        records.append(new_record)
            except Exception as e:
                print(f"讀取記錄時發生錯誤：{e}")
                return []
            
            # 過濾出符合工單號的記錄（不區分大小寫，去除前導零）
            order_normalized = order.upper().lstrip('0') or '0'  # 標準化工單號
            filtered = []
            for record in records:
                record_order = record.get("order", "").strip()
                if record_order:
                    # 標準化記錄中的工單號（轉大寫，去除前導零）
                    record_order_normalized = record_order.upper().lstrip('0') or '0'
                    if record_order_normalized == order_normalized:
                        filtered.append(record)
            
            # 限制筆數
            return filtered[:limit]
        
        except Exception as e:
            print(f"查詢 Google Sheets 失敗：{e}")
            return []
    
    def get_previous_station_barcodes(self, order: str, current_station: str) -> list:
        """
        查詢相同工單的上一站條碼（OUT 記錄）
        
        Args:
            order: 工單號
            current_station: 當前站點（例如：P2）
        
        Returns:
            上一站條碼列表，每個條碼包含：barcode, box_seq, qty, status, container
        """
        # 取得所有該工單的記錄
        logs = self.get_logs_by_order(order, limit=1000)
        
        # 判斷上一站（根據站點順序）
        station_order = {'P1': 1, 'P2': 2, 'P3': 3, 'P4': 4, 'P5': 5}
        current_order = station_order.get(current_station.upper(), 999)
        
        if current_order <= 1:
            # 如果是 P1 或更早，沒有上一站
            return []
        
        # 找出上一站代號
        prev_station = None
        for station, order_num in station_order.items():
            if order_num == current_order - 1:
                prev_station = station
                break
        
        if not prev_station:
            return []
        
        # 過濾出上一站的 OUT 記錄
        prev_station_out_logs = []
        for log in logs:
            action = log.get("action", "").upper()
            process = log.get("process", "").upper()
            new_barcode = log.get("new_barcode", "").strip()
            
            # 只取上一站的 OUT 記錄，且必須有 new_barcode（表示已遷出）
            if action == "OUT" and process == prev_station and new_barcode:
                # 標準化條碼（移除可能的 domain 前綴）
                barcode_normalized = new_barcode
                if "/b=" in new_barcode:
                    barcode_normalized = new_barcode.split("/b=")[-1]
                
                # 檢查該條碼是否已在當前站點遷入過
                scanned_barcode = str(log.get("scanned_barcode", "")).strip()
                box_seq = str(log.get("box_seq", "")).strip()
                qty = str(log.get("qty", "")).strip()
                status = str(log.get("status", "")).strip()
                container = str(log.get("container", "")).strip()
                
                # 檢查該條碼在當前站點是否已有 IN 記錄
                has_in = self.has_inbound_record_at_station(barcode_normalized, current_station)
                
                # 篩除不良品（status = 'N'）
                status_upper = status.upper()
                
                if not has_in and status_upper != 'N':
                    # 該條碼尚未在當前站點遷入，且不是不良品，加入列表
                    prev_station_out_logs.append({
                        "barcode": barcode_normalized,
                        "box_seq": box_seq,
                        "qty": qty,
                        "status": status,
                        "container": container,
                        "process": process
                    })
        
        # 去重（根據條碼）
        seen_barcodes = set()
        unique_logs = []
        for log in prev_station_out_logs:
            if log["barcode"] not in seen_barcodes:
                seen_barcodes.add(log["barcode"])
                unique_logs.append(log)
        
        return unique_logs


# 全域單例實例
sheet_service = SheetService()

