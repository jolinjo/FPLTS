"""
API 端點測試
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from main import app


@pytest.fixture
def client():
    """建立測試客戶端"""
    return TestClient(app)


class TestConfigAPI:
    """配置查詢 API 測試"""
    
    @pytest.mark.api
    def test_get_series_options(self, client):
        """測試取得產品線選項"""
        response = client.get("/api/config/series")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert isinstance(data["data"], list)
        # 驗證每個選項包含 code 和 name
        if len(data["data"]) > 0:
            assert "code" in data["data"][0]
            assert "name" in data["data"][0]
    
    @pytest.mark.api
    def test_get_model_options(self, client):
        """測試取得機種選項"""
        response = client.get("/api/config/models")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert isinstance(data["data"], list)
        if len(data["data"]) > 0:
            assert "code" in data["data"][0]
            assert "name" in data["data"][0]
    
    @pytest.mark.api
    def test_get_container_options(self, client):
        """測試取得容器選項"""
        response = client.get("/api/config/containers")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert isinstance(data["data"], list)
        if len(data["data"]) > 0:
            assert "code" in data["data"][0]
            assert "capacity" in data["data"][0]
    
    @pytest.mark.api
    def test_get_process_options(self, client):
        """測試取得製程站點選項"""
        response = client.get("/api/config/processes")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert isinstance(data["data"], list)
        if len(data["data"]) > 0:
            assert "code" in data["data"][0]
            assert "name" in data["data"][0]


class TestBarcodeCheckAPI:
    """條碼檢查 API 測試"""
    
    @pytest.mark.api
    def test_check_zz_barcode(self, client):
        """測試檢查 ZZ 製程條碼（新工單）"""
        response = client.post(
            "/api/scan/check",
            json={
                "barcode": "251119AB-ZZ-AC001",
                "current_station_id": "P1"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["suggested_action"] == "first"
        assert "data" in data
    
    @pytest.mark.api
    def test_check_invalid_barcode(self, client):
        """測試檢查無效條碼"""
        response = client.post(
            "/api/scan/check",
            json={
                "barcode": "INVALID-BARCODE",
                "current_station_id": "P2"
            }
        )
        assert response.status_code == 400
    
    @pytest.mark.api
    @patch('main.sheet_service')
    def test_check_barcode_with_inbound_record(self, mock_sheet_service, client):
        """測試檢查已有遷入記錄的條碼"""
        from services.barcode import BarcodeGenerator
        # 生成正確的測試條碼
        test_barcode = BarcodeGenerator.generate(
            "251119AA", "P1", "ST352", "A1", "01", "G", "0100"
        )
        
        # 模擬已有遷入記錄
        mock_sheet_service.has_inbound_record_at_station.return_value = True
        mock_sheet_service.has_outbound_record_at_station.return_value = False
        mock_sheet_service.has_outbound_record_at_downstream_stations.return_value = False
        
        response = client.post(
            "/api/scan/check",
            json={
                "barcode": test_barcode,
                "current_station_id": "P2"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["suggested_action"] == "outbound"
    
    @pytest.mark.api
    @patch('main.sheet_service')
    def test_check_barcode_with_outbound_record(self, mock_sheet_service, client):
        """測試檢查已有遷出記錄的條碼"""
        from services.barcode import BarcodeGenerator
        # 生成正確的測試條碼（使用 P2 條碼，這樣就不會被「上一站條碼」邏輯攔截）
        test_barcode = BarcodeGenerator.generate(
            "251119AA", "P2", "ST352", "A1", "01", "G", "0100"
        )
        
        # 模擬已有遷出記錄（當前站點 P2 有遷出記錄）
        mock_sheet_service.has_inbound_record_at_station.return_value = False
        mock_sheet_service.has_outbound_record_at_station.return_value = True
        mock_sheet_service.has_outbound_record_at_downstream_stations.return_value = False
        
        response = client.post(
            "/api/scan/check",
            json={
                "barcode": test_barcode,
                "current_station_id": "P2"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["suggested_action"] == "outbound"


class TestInboundAPI:
    """遷入 API 測試"""
    
    @pytest.mark.api
    @patch('main.sheet_service')
    @patch('main.validate_process_flow')
    def test_inbound_success(self, mock_validate, mock_sheet_service, client):
        """測試成功遷入"""
        from services.barcode import BarcodeGenerator
        # 生成正確的測試條碼
        test_barcode = BarcodeGenerator.generate(
            "251119AA", "P1", "ST352", "A1", "01", "G", "0100"
        )
        
        # 模擬流程驗證通過
        mock_validate.return_value = (True, None)
        # 模擬沒有遷入和遷出記錄
        mock_sheet_service.has_inbound_record_at_station.return_value = False
        mock_sheet_service.has_outbound_record_at_station.return_value = False
        
        response = client.post(
            "/api/scan/inbound",
            json={
                "barcode": test_barcode,
                "operator_id": "OP01",
                "current_station_id": "P2"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    @pytest.mark.api
    def test_inbound_invalid_barcode(self, client):
        """測試遷入無效條碼"""
        response = client.post(
            "/api/scan/inbound",
            json={
                "barcode": "INVALID-BARCODE",
                "operator_id": "OP01",
                "current_station_id": "P2"
            }
        )
        assert response.status_code == 400
    
    @pytest.mark.api
    @patch('main.sheet_service')
    @patch('main.validate_process_flow')
    def test_inbound_flow_validation_failed(self, mock_validate, mock_sheet_service, client):
        """測試遷入流程驗證失敗"""
        from services.barcode import BarcodeGenerator
        # 生成正確的測試條碼
        test_barcode = BarcodeGenerator.generate(
            "251119AA", "P1", "ST352", "A1", "01", "G", "0100"
        )
        
        # 模擬流程驗證失敗
        mock_validate.return_value = (False, "錯誤！P1 後續應為 P3，不可跳至 P2")
        mock_sheet_service.has_inbound_record_at_station.return_value = False
        mock_sheet_service.has_outbound_record_at_station.return_value = False
        
        response = client.post(
            "/api/scan/inbound",
            json={
                "barcode": test_barcode,
                "operator_id": "OP01",
                "current_station_id": "P2"
            }
        )
        assert response.status_code == 400
        assert "錯誤" in response.json()["detail"]


class TestOutboundAPI:
    """遷出 API 測試"""
    
    @pytest.mark.api
    @patch('main.sheet_service')
    def test_outbound_success(self, mock_sheet_service, client):
        """測試成功遷出"""
        from services.barcode import BarcodeGenerator
        # 生成正確的測試條碼
        test_barcode = BarcodeGenerator.generate(
            "251119AA", "P1", "ST352", "A1", "01", "G", "0100"
        )
        
        response = client.post(
            "/api/scan/outbound",
            json={
                "barcode": test_barcode,
                "operator_id": "OP01",
                "current_station_id": "P2",
                "container": "A2",
                "box_seq": "02",
                "status": "G",
                "qty": "0100"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "new_barcode" in data["data"]
        assert "qr_code_svg" in data["data"]
    
    @pytest.mark.api
    def test_outbound_invalid_barcode(self, client):
        """測試遷出無效條碼"""
        response = client.post(
            "/api/scan/outbound",
            json={
                "barcode": "INVALID-BARCODE",
                "operator_id": "OP01",
                "current_station_id": "P2"
            }
        )
        assert response.status_code == 400


class TestFirstStationAPI:
    """首站遷出 API 測試"""
    
    @pytest.mark.api
    def test_first_station_success(self, client):
        """測試成功首站遷出"""
        response = client.post(
            "/api/scan/first",
            json={
                "order": "251119AA",
                "operator_id": "OP01",
                "current_station_id": "P1",
                "series_code": "ST",
                "model_code": "352",
                "container": "A1",
                "box_seq": "01",
                "status": "G",
                "qty": "0100"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "barcode" in data["data"]
        assert "qr_code_svg" in data["data"]
    
    @pytest.mark.api
    def test_first_station_invalid_series(self, client):
        """測試無效的產品線代號"""
        response = client.post(
            "/api/scan/first",
            json={
                "order": "251119AA",
                "operator_id": "OP01",
                "current_station_id": "P1",
                "series_code": "XX",  # 不存在的產品線
                "model_code": "352",
                "container": "A1",
                "box_seq": "01",
                "status": "G",
                "qty": "0100"
            }
        )
        assert response.status_code == 400
    
    @pytest.mark.api
    def test_first_station_invalid_model(self, client):
        """測試無效的機種代號"""
        response = client.post(
            "/api/scan/first",
            json={
                "order": "251119AA",
                "operator_id": "OP01",
                "current_station_id": "P1",
                "series_code": "ST",
                "model_code": "999",  # 不存在的機種
                "container": "A1",
                "box_seq": "01",
                "status": "G",
                "qty": "0100"
            }
        )
        assert response.status_code == 400


class TestTraceAPI:
    """追溯查詢 API 測試"""
    
    @pytest.mark.api
    @patch('main.sheet_service')
    def test_trace_success(self, mock_sheet_service, client):
        """測試成功追溯查詢"""
        from services.barcode import BarcodeGenerator
        # 生成正確的測試條碼
        test_barcode = BarcodeGenerator.generate(
            "251119AA", "P1", "ST352", "A1", "01", "G", "0100"
        )
        
        # 模擬返回記錄
        mock_sheet_service.get_logs_by_order.return_value = [
            {
                "timestamp": "2025-01-01 10:00:00",
                "action": "OUT",
                "operator": "OP01",
                "order": "251119AA",
                "process": "P1",
                "sku": "ST352",
                "container": "A1",
                "box_seq": "01",
                "qty": "0100",
                "status": "G",
                "cycle_time": "0",
                "scanned_barcode": "",
                "new_barcode": test_barcode
            }
        ]
        
        response = client.post(
            "/api/scan/trace",
            json={
                "barcode": test_barcode
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "station_timeline" in data["data"]
        assert "statistics" in data["data"]
    
    @pytest.mark.api
    def test_trace_invalid_barcode(self, client):
        """測試追溯查詢無效條碼"""
        response = client.post(
            "/api/scan/trace",
            json={
                "barcode": "INVALID-BARCODE"
            }
        )
        assert response.status_code == 400


class TestRoutes:
    """路由測試"""
    
    @pytest.mark.api
    def test_root_route(self, client):
        """測試根路由"""
        response = client.get("/")
        # 應該返回前端頁面或 API 訊息
        assert response.status_code in [200, 404]
    
    @pytest.mark.api
    def test_barcode_redirect_route(self, client):
        """測試條碼重定向路由"""
        barcode = "251119AA-P1-ST352-A1-01-G-0100-X4F"
        response = client.get(f"/b={barcode}", follow_redirects=False)
        assert response.status_code == 302
        assert f"?b={barcode}" in response.headers.get("location", "")

