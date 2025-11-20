"""
完整工作流程整合測試
模擬實際生產流程，通過 API 端點將數據寫入 Google Sheets

測試內容：
- 10 張不同的工單
- 不同的產品線和型號
- 完整的製程流程（遷入/遷出）
- 每隔 2 秒執行一次操作
- 通過 API 端點實際寫入 Google Sheets（模擬前端調用）
"""
import time
import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from main import app
from services.barcode import BarcodeGenerator
from services.config_loader import config_loader


# 測試用的工單配置（10 張工單）
TEST_ORDERS = [
    {"order": "TEST001", "series": "ST", "model": "352", "qty": "0100", "status": "G"},
    {"order": "TEST002", "series": "AC", "model": "350", "qty": "0050", "status": "G"},
    {"order": "TEST003", "series": "MD", "model": "351", "qty": "0075", "status": "G"},
    {"order": "TEST004", "series": "ST", "model": "325", "qty": "0120", "status": "G"},
    {"order": "TEST005", "series": "CA", "model": "001", "qty": "0080", "status": "G"},
    {"order": "TEST006", "series": "ST", "model": "326", "qty": "0090", "status": "G"},
    {"order": "TEST007", "series": "AC", "model": "327", "qty": "0060", "status": "G"},
    {"order": "TEST008", "series": "MD", "model": "328", "qty": "0110", "status": "G"},
    {"order": "TEST009", "series": "ST", "model": "350", "qty": "0105", "status": "G"},
    {"order": "TEST010", "series": "MB", "model": "001", "qty": "0070", "status": "G"},
]


class TestFullWorkflow:
    """完整工作流程測試（通過 API 端點）"""
    
    @pytest.fixture
    def client(self):
        """建立測試客戶端"""
        return TestClient(app)
    
    @pytest.mark.integration
    @pytest.mark.requires_sheets
    @pytest.mark.slow
    def test_full_production_workflow(self, client):
        """
        測試完整的生產流程
        通過 API 端點模擬前端調用，處理 10 張工單從首站到末站的完整流程
        """
        print("\n" + "="*80)
        print("開始完整生產流程測試（通過 API 端點）")
        print("="*80)
        print(f"測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"工單數量: {len(TEST_ORDERS)}")
        print("="*80 + "\n")
        
        results = []
        
        for idx, order_config in enumerate(TEST_ORDERS, 1):
            print(f"\n[工單 {idx}/{len(TEST_ORDERS)}] 處理工單: {order_config['order']}")
            print(f"  產品線: {order_config['series']}, 型號: {order_config['model']}")
            
            try:
                result = self._process_single_order_via_api(client, order_config, idx)
                results.append({
                    "order": order_config['order'],
                    "success": True,
                    "result": result
                })
                print(f"  ✅ 工單 {order_config['order']} 處理完成")
            except Exception as e:
                print(f"  ❌ 工單 {order_config['order']} 處理失敗: {e}")
                import traceback
                traceback.print_exc()
                results.append({
                    "order": order_config['order'],
                    "success": False,
                    "error": str(e)
                })
            
            # 工單之間稍作延遲
            if idx < len(TEST_ORDERS):
                print(f"  等待 2 秒後處理下一個工單...")
                time.sleep(2)
        
        # 輸出測試結果摘要
        print("\n" + "="*80)
        print("測試結果摘要")
        print("="*80)
        success_count = sum(1 for r in results if r['success'])
        print(f"成功: {success_count}/{len(TEST_ORDERS)}")
        print(f"失敗: {len(TEST_ORDERS) - success_count}/{len(TEST_ORDERS)}")
        print("="*80 + "\n")
        
        # 驗證所有工單都成功
        failed_orders = [r['order'] for r in results if not r['success']]
        if failed_orders:
            pytest.fail(f"以下工單處理失敗: {', '.join(failed_orders)}")
    
    def _process_single_order_via_api(self, client, order_config, order_index):
        """
        通過 API 端點處理單一工單的完整流程（模擬前端調用）
        
        Args:
            client: FastAPI TestClient
            order_config: 工單配置
            order_index: 工單索引（用於生成不同的容器和箱號）
        
        Returns:
            處理結果字典
        """
        order = order_config['order']
        series = order_config['series']
        model = order_config['model']
        qty = order_config['qty']
        status = order_config['status']
        
        # 組合成 SKU
        model_padded = model.zfill(3)[:3]
        sku = f"{series}{model_padded}"
        
        # 取得該產品線的流程
        flow_config = config_loader.get_config('flow')
        if not flow_config:
            raise Exception("無法讀取流程配置")
        
        flow_section = flow_config.get('Flow', series.upper(), fallback=None)
        if not flow_section:
            flow_section = flow_config.get('Flow', 'DEFAULT', fallback='')
        
        if not flow_section:
            raise Exception(f"找不到產品線 {series} 的流程定義")
        
        # 解析流程站點
        stations = [s.strip().upper() for s in flow_section.split(',')]
        
        print(f"  流程站點: {' -> '.join(stations)}")
        
        # 生成容器和箱號（每個工單使用不同的值）
        container = f"A{order_index % 3 + 1}"  # A1, A2, A3 循環
        box_seq = f"{order_index:02d}"  # 01, 02, 03...
        operator_id = f"TEST_OP{order_index:02d}"
        
        current_barcode = None
        process_records = []
        
        # 步驟 1: 首站遷出（通過 API 調用）
        first_station = stations[0]
        print(f"  [步驟 1] 首站遷出 ({first_station}) - 調用 API: POST /api/scan/first")
        
        response = client.post(
            "/api/scan/first",
            json={
                "order": order,
                "operator_id": operator_id,
                "current_station_id": first_station,
                "series_code": series,
                "model_code": model,
                "container": container,
                "box_seq": box_seq,
                "status": status,
                "qty": qty
            }
        )
        
        if response.status_code != 200:
            raise Exception(f"首站遷出 API 調用失敗: {response.status_code} - {response.text}")
        
        data = response.json()
        if not data.get("success"):
            raise Exception(f"首站遷出失敗: {data.get('message', '未知錯誤')}")
        
        current_barcode = data["data"]["barcode"]
        process_records.append({
            "station": first_station,
            "action": "OUT",
            "barcode": current_barcode,
            "api": "/api/scan/first"
        })
        
        print(f"    生成條碼: {current_barcode}")
        print(f"    等待 2 秒...")
        time.sleep(2)
        
        # 步驟 2-N: 後續站點的遷入和遷出（通過 API 調用）
        for i in range(1, len(stations)):
            current_station = stations[i]
            prev_station = stations[i-1]
            
            # 遷入（通過 API 調用）
            print(f"  [步驟 {i*2}] 遷入 ({current_station}) - 調用 API: POST /api/scan/inbound")
            
            response = client.post(
                "/api/scan/inbound",
                json={
                    "barcode": current_barcode,
                    "operator_id": operator_id,
                    "current_station_id": current_station
                }
            )
            
            if response.status_code != 200:
                error_msg = response.json().get("detail", response.text) if response.status_code == 400 else response.text
                raise Exception(f"遷入 API 調用失敗: {response.status_code} - {error_msg}")
            
            data = response.json()
            if not data.get("success"):
                raise Exception(f"遷入失敗: {data.get('message', '未知錯誤')}")
            
            process_records.append({
                "station": current_station,
                "action": "IN",
                "barcode": current_barcode,
                "api": "/api/scan/inbound"
            })
            
            print(f"    掃描條碼: {current_barcode}")
            print(f"    等待 2 秒...")
            time.sleep(2)
            
            # 遷出（通過 API 調用）
            print(f"  [步驟 {i*2+1}] 遷出 ({current_station}) - 調用 API: POST /api/scan/outbound")
            
            response = client.post(
                "/api/scan/outbound",
                json={
                    "barcode": current_barcode,
                    "operator_id": operator_id,
                    "current_station_id": current_station,
                    "container": container,
                    "box_seq": box_seq,
                    "status": status,
                    "qty": qty
                }
            )
            
            if response.status_code != 200:
                error_msg = response.json().get("detail", response.text) if response.status_code == 400 else response.text
                raise Exception(f"遷出 API 調用失敗: {response.status_code} - {error_msg}")
            
            data = response.json()
            if not data.get("success"):
                raise Exception(f"遷出失敗: {data.get('message', '未知錯誤')}")
            
            # 取得新條碼
            new_barcode = data["data"]["new_barcode"]
            process_records.append({
                "station": current_station,
                "action": "OUT",
                "barcode": new_barcode,
                "api": "/api/scan/outbound"
            })
            
            print(f"    新條碼: {new_barcode}")
            current_barcode = new_barcode
            
            print(f"    等待 2 秒...")
            time.sleep(2)
        
        # 最後一站只遷入（不遷出）
        if len(stations) > 1:
            last_station = stations[-1]
            print(f"  [最後步驟] 最終站遷入 ({last_station}) - 調用 API: POST /api/scan/inbound")
            
            response = client.post(
                "/api/scan/inbound",
                json={
                    "barcode": current_barcode,
                    "operator_id": operator_id,
                    "current_station_id": last_station
                }
            )
            
            if response.status_code != 200:
                error_msg = response.json().get("detail", response.text) if response.status_code == 400 else response.text
                raise Exception(f"最終站遷入 API 調用失敗: {response.status_code} - {error_msg}")
            
            data = response.json()
            if not data.get("success"):
                raise Exception(f"最終站遷入失敗: {data.get('message', '未知錯誤')}")
            
            process_records.append({
                "station": last_station,
                "action": "IN",
                "barcode": current_barcode,
                "api": "/api/scan/inbound"
            })
            
            print(f"    掃描條碼: {current_barcode}")
            print(f"    等待 2 秒...")
            time.sleep(2)
        
        return {
            "order": order,
            "sku": sku,
            "stations": stations,
            "process_records": process_records,
            "total_steps": len(process_records)
        }
    
    @pytest.mark.integration
    @pytest.mark.requires_sheets
    @pytest.mark.slow
    def test_single_order_workflow(self, client):
        """
        測試單一工單的完整流程（用於快速測試）
        通過 API 端點執行
        """
        print("\n" + "="*80)
        print("單一工單流程測試（通過 API 端點）")
        print("="*80)
        
        # 使用第一張工單進行測試
        order_config = TEST_ORDERS[0]
        result = self._process_single_order_via_api(client, order_config, 1)
        
        assert result is not None
        assert result['order'] == order_config['order']
        assert len(result['process_records']) > 0
        
        print(f"\n✅ 單一工單測試完成")
        print(f"   工單: {result['order']}")
        print(f"   總步驟數: {result['total_steps']}")
        print("="*80 + "\n")

