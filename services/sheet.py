"""
Google Sheets 讀寫操作
"""
import os
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from typing import Dict, Optional
from dotenv import load_dotenv

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
        self._initialize()
    
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
                if not headers or len(headers) == 0:
                    # 第一行為空，建立標題列（使用帶中文說明的標題）
                    worksheet.append_row(COLUMN_HEADERS)
                    headers = COLUMN_HEADERS
            except:
                # 如果無法讀取第一行，嘗試建立標題列
                try:
                    worksheet.append_row(COLUMN_HEADERS)
                    headers = COLUMN_HEADERS
                except:
                    # 如果已經有標題列，使用預設順序
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
            
            # 準備資料列（按照 Sheet 中的實際欄位順序）
            row_data = []
            for header in headers:
                # 找到對應的欄位名
                column_name = header_to_column.get(header, None)
                if column_name:
                    value = log_data.get(column_name, "")
                else:
                    # 如果找不到對應的欄位，嘗試直接從標題提取
                    if "(" in header:
                        column_name = header.split("(")[0].strip()
                        value = log_data.get(column_name, "")
                    else:
                        value = ""
                
                # 轉換為字串
                if value is None:
                    value = ""
                elif isinstance(value, datetime):
                    value = value.strftime("%Y-%m-%d %H:%M:%S")
                else:
                    value = str(value)
                row_data.append(value)
            
            # 追加到工作表
            worksheet.append_row(row_data)
            return True
        
        except Exception as e:
            print(f"寫入 Google Sheets 失敗：{e}")
            return False
    
    def get_logs_by_barcode(self, barcode: str, limit: int = 100) -> list:
        """
        根據條碼查詢記錄（查詢 scanned_barcode 或 new_barcode 欄位）
        
        Args:
            barcode: 條碼字串
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
                    # 沒有標題列，手動讀取資料
                    all_values = worksheet.get_all_values()
                    if len(all_values) <= 1:
                        return []
                    
                    headers = COLUMNS
                    records = []
                    for row in all_values[1:]:
                        if len(row) > 0:
                            record = {}
                            for i, header in enumerate(headers):
                                if i < len(row):
                                    record[header] = row[i]
                                else:
                                    record[header] = ""
                            records.append(record)
                else:
                    # 有標題列，轉換為英文欄位名
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
                    
                    all_records = worksheet.get_all_records()
                    records = []
                    for record in all_records:
                        new_record = {}
                        for header, value in record.items():
                            column_name = header_to_column.get(header, header.split("(")[0].strip() if "(" in header else header)
                            new_record[column_name] = value
                        records.append(new_record)
            except Exception as e:
                print(f"讀取記錄時發生錯誤：{e}")
                return []
            
            # 過濾出符合條碼的記錄（檢查 scanned_barcode 或 new_barcode）
            filtered = []
            # 標準化條碼（移除可能的 domain 前綴）
            barcode_normalized = barcode
            if "/b=" in barcode:
                # 如果包含 domain，提取條碼部分
                barcode_normalized = barcode.split("/b=")[-1]
            
            for record in records:
                scanned = record.get("scanned_barcode", "").strip()
                new = record.get("new_barcode", "").strip()
                
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
        
        except Exception as e:
            print(f"查詢條碼記錄失敗：{e}")
            return []
    
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
        
        Args:
            barcode: 條碼字串
            station_id: 製程站點代號（例如：P1, P2）
        
        Returns:
            如果在指定站點有 OUT 記錄則返回 True，否則返回 False
        """
        logs = self.get_logs_by_barcode(barcode, limit=100)
        station_id_upper = station_id.upper()
        for log in logs:
            if log.get("action", "").upper() == "OUT":
                # 檢查記錄中的 process 欄位是否匹配指定站點
                log_process = log.get("process", "").upper()
                if log_process == station_id_upper:
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
            
            # 過濾出符合工單號的記錄
            filtered = [record for record in records if record.get("order") == order]
            
            # 限制筆數
            return filtered[:limit]
        
        except Exception as e:
            print(f"查詢 Google Sheets 失敗：{e}")
            return []


# 全域單例實例
sheet_service = SheetService()

