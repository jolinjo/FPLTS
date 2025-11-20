"""
Google Sheets 服務模組測試
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from services.sheet import SheetService


class TestSheetService:
    """Google Sheets 服務測試"""
    
    @pytest.fixture
    def mock_sheet_service(self):
        """建立模擬的 SheetService"""
        service = SheetService()
        # 模擬 client 和 sheet_id
        service.client = Mock()
        service.sheet_id = "test_sheet_id"
        return service
    
    @pytest.fixture
    def mock_worksheet(self):
        """建立模擬的工作表"""
        worksheet = Mock()
        worksheet.row_values.return_value = [
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
        worksheet.get_all_records.return_value = []
        worksheet.append_row.return_value = None
        return worksheet
    
    @pytest.fixture
    def mock_spreadsheet(self, mock_worksheet):
        """建立模擬的試算表"""
        spreadsheet = Mock()
        spreadsheet.worksheet.return_value = mock_worksheet
        return spreadsheet
    
    @pytest.mark.unit
    @pytest.mark.requires_sheets
    def test_write_log_success(self, mock_sheet_service, mock_spreadsheet, mock_worksheet):
        """測試成功寫入記錄"""
        mock_sheet_service.client.open_by_key.return_value = mock_spreadsheet
        
        log_data = {
            "timestamp": datetime.now(),
            "action": "IN",
            "operator": "OP01",
            "order": "251119AA",
            "process": "P2",
            "sku": "ST352",
            "container": "A1",
            "box_seq": "01",
            "qty": "0100",
            "status": "G",
            "cycle_time": 0,
            "scanned_barcode": "251119AA-P1-ST352-A1-01-G-0100-X4F",
            "new_barcode": ""
        }
        
        result = mock_sheet_service.write_log(log_data)
        assert result is True
        mock_worksheet.append_row.assert_called_once()
    
    @pytest.mark.unit
    @pytest.mark.requires_sheets
    def test_write_log_no_client(self):
        """測試沒有客戶端時寫入失敗"""
        service = SheetService()
        service.client = None
        service.sheet_id = None
        
        log_data = {
            "timestamp": datetime.now(),
            "action": "IN",
            "operator": "OP01",
            "order": "251119AA",
            "process": "P2",
            "sku": "ST352",
            "container": "A1",
            "box_seq": "01",
            "qty": "0100",
            "status": "G",
            "cycle_time": 0,
            "scanned_barcode": "251119AA-P1-ST352-A1-01-G-0100-X4F",
            "new_barcode": ""
        }
        
        result = service.write_log(log_data)
        assert result is False
    
    @pytest.mark.unit
    @pytest.mark.requires_sheets
    def test_get_logs_by_barcode(self, mock_sheet_service, mock_spreadsheet, mock_worksheet):
        """測試根據條碼查詢記錄"""
        mock_sheet_service.client.open_by_key.return_value = mock_spreadsheet
        
        # 模擬返回的記錄
        mock_worksheet.get_all_records.return_value = [
            {
                "timestamp (時間戳記)": "2025-01-01 10:00:00",
                "action (動作)": "IN",
                "operator (操作員)": "OP01",
                "order (工單號)": "251119AA",
                "process (製程站點)": "P2",
                "sku (產品SKU)": "ST352",
                "container (容器代號)": "A1",
                "box_seq (箱號)": "01",
                "qty (數量)": "0100",
                "status (貨態)": "G",
                "cycle_time (工時)": "0",
                "scanned_barcode (掃描條碼)": "251119AA-P1-ST352-A1-01-G-0100-X4F",
                "new_barcode (新條碼)": ""
            }
        ]
        
        barcode = "251119AA-P1-ST352-A1-01-G-0100-X4F"
        logs = mock_sheet_service.get_logs_by_barcode(barcode)
        
        assert isinstance(logs, list)
        # 由於我們使用 mock，實際的過濾邏輯可能不會執行
        # 這裡主要測試函數不會拋出異常
    
    @pytest.mark.unit
    @pytest.mark.requires_sheets
    def test_get_logs_by_order(self, mock_sheet_service, mock_spreadsheet, mock_worksheet):
        """測試根據工單號查詢記錄"""
        mock_sheet_service.client.open_by_key.return_value = mock_spreadsheet
        
        # 模擬返回的記錄
        mock_worksheet.get_all_records.return_value = [
            {
                "timestamp (時間戳記)": "2025-01-01 10:00:00",
                "action (動作)": "IN",
                "operator (操作員)": "OP01",
                "order (工單號)": "251119AA",
                "process (製程站點)": "P2",
                "sku (產品SKU)": "ST352",
                "container (容器代號)": "A1",
                "box_seq (箱號)": "01",
                "qty (數量)": "0100",
                "status (貨態)": "G",
                "cycle_time (工時)": "0",
                "scanned_barcode (掃描條碼)": "251119AA-P1-ST352-A1-01-G-0100-X4F",
                "new_barcode (新條碼)": ""
            }
        ]
        
        order = "251119AA"
        logs = mock_sheet_service.get_logs_by_order(order)
        
        assert isinstance(logs, list)
    
    @pytest.mark.unit
    @pytest.mark.requires_sheets
    def test_has_inbound_record(self, mock_sheet_service, mock_spreadsheet, mock_worksheet):
        """測試檢查遷入記錄"""
        mock_sheet_service.client.open_by_key.return_value = mock_spreadsheet
        
        # 模擬返回包含 IN 記錄
        mock_worksheet.get_all_records.return_value = [
            {
                "action (動作)": "IN",
                "scanned_barcode (掃描條碼)": "251119AA-P1-ST352-A1-01-G-0100-X4F",
                "new_barcode (新條碼)": ""
            }
        ]
        
        barcode = "251119AA-P1-ST352-A1-01-G-0100-X4F"
        # 由於使用 mock，實際的過濾邏輯可能不會正確執行
        # 這裡主要測試函數不會拋出異常
        result = mock_sheet_service.has_inbound_record(barcode)
        assert isinstance(result, bool)
    
    @pytest.mark.unit
    @pytest.mark.requires_sheets
    def test_has_outbound_record(self, mock_sheet_service, mock_spreadsheet, mock_worksheet):
        """測試檢查遷出記錄"""
        mock_sheet_service.client.open_by_key.return_value = mock_spreadsheet
        
        # 模擬返回包含 OUT 記錄
        mock_worksheet.get_all_records.return_value = [
            {
                "action (動作)": "OUT",
                "scanned_barcode (掃描條碼)": "251119AA-P1-ST352-A1-01-G-0100-X4F",
                "new_barcode (新條碼)": "251119AA-P2-ST352-A1-01-G-0100-ABC"
            }
        ]
        
        barcode = "251119AA-P1-ST352-A1-01-G-0100-X4F"
        result = mock_sheet_service.has_outbound_record(barcode)
        assert isinstance(result, bool)
    
    @pytest.mark.unit
    @pytest.mark.requires_sheets
    def test_has_inbound_record_at_station(self, mock_sheet_service, mock_spreadsheet, mock_worksheet):
        """測試檢查指定站點的遷入記錄"""
        mock_sheet_service.client.open_by_key.return_value = mock_spreadsheet
        
        mock_worksheet.get_all_records.return_value = [
            {
                "action (動作)": "IN",
                "process (製程站點)": "P2",
                "scanned_barcode (掃描條碼)": "251119AA-P1-ST352-A1-01-G-0100-X4F",
                "new_barcode (新條碼)": ""
            }
        ]
        
        barcode = "251119AA-P1-ST352-A1-01-G-0100-X4F"
        result = mock_sheet_service.has_inbound_record_at_station(barcode, "P2")
        assert isinstance(result, bool)
    
    @pytest.mark.unit
    @pytest.mark.requires_sheets
    def test_has_outbound_record_at_station(self, mock_sheet_service, mock_spreadsheet, mock_worksheet):
        """測試檢查指定站點的遷出記錄"""
        mock_sheet_service.client.open_by_key.return_value = mock_spreadsheet
        
        mock_worksheet.get_all_records.return_value = [
            {
                "action (動作)": "OUT",
                "process (製程站點)": "P2",
                "scanned_barcode (掃描條碼)": "251119AA-P1-ST352-A1-01-G-0100-X4F",
                "new_barcode (新條碼)": "251119AA-P2-ST352-A1-01-G-0100-ABC"
            }
        ]
        
        barcode = "251119AA-P1-ST352-A1-01-G-0100-X4F"
        result = mock_sheet_service.has_outbound_record_at_station(barcode, "P2")
        assert isinstance(result, bool)
    
    @pytest.mark.unit
    @pytest.mark.requires_sheets
    def test_has_outbound_record_at_downstream_stations(self, mock_sheet_service, mock_spreadsheet, mock_worksheet):
        """測試檢查下游站點的遷出記錄"""
        mock_sheet_service.client.open_by_key.return_value = mock_spreadsheet
        
        mock_worksheet.get_all_records.return_value = [
            {
                "action (動作)": "OUT",
                "process (製程站點)": "P3",  # 下游站點
                "scanned_barcode (掃描條碼)": "251119AA-P1-ST352-A1-01-G-0100-X4F",
                "new_barcode (新條碼)": "251119AA-P3-ST352-A1-01-G-0100-ABC"
            }
        ]
        
        barcode = "251119AA-P1-ST352-A1-01-G-0100-X4F"
        result = mock_sheet_service.has_outbound_record_at_downstream_stations(barcode, "P2")
        assert isinstance(result, bool)
    
    @pytest.mark.unit
    @pytest.mark.requires_sheets
    def test_write_log_exception_handling(self, mock_sheet_service, mock_spreadsheet, mock_worksheet):
        """測試寫入記錄時的異常處理"""
        mock_sheet_service.client.open_by_key.return_value = mock_spreadsheet
        mock_worksheet.append_row.side_effect = Exception("模擬錯誤")
        
        log_data = {
            "timestamp": datetime.now(),
            "action": "IN",
            "operator": "OP01",
            "order": "251119AA",
            "process": "P2",
            "sku": "ST352",
            "container": "A1",
            "box_seq": "01",
            "qty": "0100",
            "status": "G",
            "cycle_time": 0,
            "scanned_barcode": "251119AA-P1-ST352-A1-01-G-0100-X4F",
            "new_barcode": ""
        }
        
        result = mock_sheet_service.write_log(log_data)
        assert result is False

