"""
完整工作流程整合測試
模擬實際生產流程，通過 API 端點將數據寫入 Google Sheets

測試內容：
- 10 張不同的工單
- 不同的產品線和型號
- 完整的製程流程（遷入/遷出）
- 每隔 2 秒執行一次操作
- 通過 API 端點實際寫入 Google Sheets（模擬前端調用）
- 產生良品和不良品記錄，用於測試良率計算功能

良品/不良品分配規則：
- 偶數工單索引：首站分為良品和不良品
- 奇數工單索引：中間站點分為良品和不良品
- 所有工單：最終站分為良品和不良品
- 良品比例：根據工單索引變化（80%-95%）

數量追蹤邏輯：
- 前一站遷出的良品數量 = 下一站遷入的數量
- 下一站遷出時，良品+不良品的總數 = 遷入的數量
- 只有良品會進入下一站（不良品不進入下一站）
"""
import time
import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from main import app
from services.barcode import BarcodeGenerator
from services.config_loader import config_loader


def generate_order_number(index: int) -> str:
    """
    生成工單號
    格式：6碼日期（YYMMDD）+ 2碼英文
    
    Args:
        index: 工單索引（1-10）
    
    Returns:
        工單號字串，例如：251120AA（25年11月20日 + AA）
    """
    # 取得今天的日期
    today = datetime.now()
    # 格式：YYMMDD（例如：251120 表示 25年11月20日）
    date_part = today.strftime("%y%m%d")
    
    # 2碼英文：AA, AB, AC, AD, AE, AF, AG, AH, AI, AJ
    # 使用索引生成不同的英文代碼
    # 第一碼：固定為 A（或根據需要變化）
    # 第二碼：A, B, C, D, E, F, G, H, I, J...
    first_letter = 'A'
    second_letter_index = (index - 1) % 26  # 0-25
    second_letter = chr(ord('A') + second_letter_index)
    
    return f"{date_part}{first_letter}{second_letter}"


# 測試用的工單配置（10 張工單）
# 工單號格式：6碼日期（DDMMYY）+ 2碼英文
TEST_ORDERS = [
    {"order": generate_order_number(1), "series": "ST", "model": "352", "qty": "0100", "status": "G"},
    {"order": generate_order_number(2), "series": "AC", "model": "350", "qty": "0050", "status": "G"},
    {"order": generate_order_number(3), "series": "MD", "model": "351", "qty": "0075", "status": "G"},
    {"order": generate_order_number(4), "series": "ST", "model": "325", "qty": "0120", "status": "G"},
    {"order": generate_order_number(5), "series": "CA", "model": "001", "qty": "0080", "status": "G"},
    {"order": generate_order_number(6), "series": "ST", "model": "326", "qty": "0090", "status": "G"},
    {"order": generate_order_number(7), "series": "AC", "model": "327", "qty": "0060", "status": "G"},
    {"order": generate_order_number(8), "series": "MD", "model": "328", "qty": "0110", "status": "G"},
    {"order": generate_order_number(9), "series": "ST", "model": "350", "qty": "0105", "status": "G"},
    {"order": generate_order_number(10), "series": "MB", "model": "001", "qty": "0070", "status": "G"},
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
        # 追蹤當前數量（會隨著站點變化）
        current_qty = int(qty)  # 初始數量
        
        # 步驟 1: 首站遷出（通過 API 調用）
        # 為了測試良率計算，首站遷出時也分為良品和不良品兩批
        # 規則：工單索引為偶數時，首站分為良品和不良品
        first_station = stations[0]
        should_split_first = (order_index % 2 == 0)  # 偶數工單索引
        
        if should_split_first:
            # 首站分為良品和不良品兩批遷出
            total_qty_int = current_qty
            # 良品比例：根據工單索引變化（90%-95%）
            good_ratio = 0.90 + (order_index % 2) * 0.05  # 90% 或 95%
            good_qty = int(total_qty_int * good_ratio)
            bad_qty = total_qty_int - good_qty
            # 更新當前數量為良品數量（下一站遷入的數量）
            current_qty = good_qty
            
            # 第一次遷出：良品
            print(f"  [步驟 1] 首站遷出 ({first_station}) - 良品批次 - 調用 API: POST /api/scan/first")
            print(f"    良品數量: {good_qty}")
            
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
                    "status": "G",  # 良品
                    "qty": str(good_qty).zfill(4)
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"首站良品遷出 API 調用失敗: {response.status_code} - {response.text}")
            
            data = response.json()
            if not data.get("success"):
                raise Exception(f"首站良品遷出失敗: {data.get('message', '未知錯誤')}")
            
            current_barcode_good = data["data"]["barcode"]
            process_records.append({
                "station": first_station,
                "action": "OUT",
                "barcode": current_barcode_good,
                "api": "/api/scan/first",
                "status": "G",
                "qty": good_qty
            })
            
            print(f"    良品條碼: {current_barcode_good}")
            print(f"    等待 2 秒...")
            time.sleep(2)
            
            # 第二次遷出：不良品（使用不同的容器和箱號）
            print(f"  [步驟 1+] 首站遷出 ({first_station}) - 不良品批次 - 調用 API: POST /api/scan/first")
            print(f"    不良品數量: {bad_qty}")
            
            bad_container = f"B{order_index % 3 + 1}"  # 使用不同的容器
            bad_box_seq = f"{order_index:02d}B"  # 使用不同的箱號
            
            response = client.post(
                "/api/scan/first",
                json={
                    "order": order,
                    "operator_id": operator_id,
                    "current_station_id": first_station,
                    "series_code": series,
                    "model_code": model,
                    "container": bad_container,
                    "box_seq": bad_box_seq,
                    "status": "N",  # 不良品
                    "qty": str(bad_qty).zfill(4)
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"首站不良品遷出 API 調用失敗: {response.status_code} - {response.text}")
            
            data = response.json()
            if not data.get("success"):
                raise Exception(f"首站不良品遷出失敗: {data.get('message', '未知錯誤')}")
            
            current_barcode_bad = data["data"]["barcode"]
            process_records.append({
                "station": first_station,
                "action": "OUT",
                "barcode": current_barcode_bad,
                "api": "/api/scan/first",
                "status": "N",
                "qty": bad_qty
            })
            
            print(f"    不良品條碼: {current_barcode_bad}")
            
            # 使用良品條碼作為下一站的輸入（不良品通常不進入下一站）
            current_barcode = current_barcode_good
            
            print(f"    等待 2 秒...")
            time.sleep(2)
        else:
            # 單一批次遷出（全部為良品）
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
            
            # 單一批次遷出時，數量不變（全部為良品）
            # current_qty 保持為初始數量
            
            print(f"    生成條碼: {current_barcode}")
            print(f"    等待 2 秒...")
            time.sleep(2)
        
        # 步驟 2-N: 後續站點的遷入和遷出（通過 API 調用）
        for i in range(1, len(stations)):
            current_station = stations[i]
            prev_station = stations[i-1]
            
            # 遷入（通過 API 調用）
            # 遷入的數量應該等於前一站遷出的良品數量（從條碼中解析）
            print(f"  [步驟 {i*2}] 遷入 ({current_station}) - 調用 API: POST /api/scan/inbound")
            
            # 從條碼中解析當前數量（應該等於前一站的良品數量）
            from services.barcode import BarcodeParser
            parsed = BarcodeParser.parse(current_barcode)
            if parsed and parsed.get('qty'):
                # 從條碼中獲取數量（前一站的良品數量）
                current_qty = int(parsed.get('qty'))
                print(f"    從條碼解析數量: {current_qty}")
            else:
                # 如果解析失敗，使用追蹤的數量（應該已經在上一步更新）
                print(f"    條碼解析失敗，使用追蹤數量: {current_qty}")
            
            print(f"    遷入數量: {current_qty} (來自前一站的良品數量)")
            
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
                "api": "/api/scan/inbound",
                "qty": current_qty
            })
            
            print(f"    掃描條碼: {current_barcode}")
            print(f"    等待 2 秒...")
            time.sleep(2)
            
            # 遷出（通過 API 調用）
            # 為了測試良率計算，在某些站點會分為良品和不良品兩批遷出
            # 規則：中間站點（非首站和末站）且工單索引為奇數時，分為良品和不良品
            should_split_quality = (
                i < len(stations) - 1 and  # 不是最後一站
                order_index % 2 == 1  # 奇數工單索引
            )
            
            if should_split_quality:
                # 分為良品和不良品兩批遷出
                # 遷出的總數應該等於遷入的數量（current_qty）
                total_qty_int = current_qty
                # 良品比例：根據工單索引變化（85%-95%）
                good_ratio = 0.85 + (order_index % 3) * 0.05  # 85%, 90%, 95% 循環
                good_qty = int(total_qty_int * good_ratio)
                bad_qty = total_qty_int - good_qty
                # 更新當前數量為良品數量（下一站遷入的數量）
                current_qty = good_qty
                
                # 第一次遷出：良品
                print(f"  [步驟 {i*2+1}] 遷出 ({current_station}) - 良品批次 - 調用 API: POST /api/scan/outbound")
                print(f"    良品數量: {good_qty}")
                
                response = client.post(
                    "/api/scan/outbound",
                    json={
                        "barcode": current_barcode,
                        "operator_id": operator_id,
                        "current_station_id": current_station,
                        "container": container,
                        "box_seq": box_seq,
                        "status": "G",  # 良品
                        "qty": str(good_qty).zfill(4)
                    }
                )
                
                if response.status_code != 200:
                    error_msg = response.json().get("detail", response.text) if response.status_code == 400 else response.text
                    raise Exception(f"良品遷出 API 調用失敗: {response.status_code} - {error_msg}")
                
                data = response.json()
                if not data.get("success"):
                    raise Exception(f"良品遷出失敗: {data.get('message', '未知錯誤')}")
                
                # 取得新條碼（良品批次）
                new_barcode_good = data["data"]["new_barcode"]
                process_records.append({
                    "station": current_station,
                    "action": "OUT",
                    "barcode": new_barcode_good,
                    "api": "/api/scan/outbound",
                    "status": "G",
                    "qty": good_qty
                })
                
                print(f"    良品新條碼: {new_barcode_good}")
                print(f"    等待 2 秒...")
                time.sleep(2)
                
                # 第二次遷出：不良品（使用不同的容器和箱號）
                print(f"  [步驟 {i*2+1}+] 遷出 ({current_station}) - 不良品批次 - 調用 API: POST /api/scan/outbound")
                print(f"    不良品數量: {bad_qty}")
                
                bad_container = f"B{order_index % 3 + 1}"  # 使用不同的容器
                bad_box_seq = f"{order_index:02d}B"  # 使用不同的箱號
                
                response = client.post(
                    "/api/scan/outbound",
                    json={
                        "barcode": current_barcode,  # 使用同一個舊條碼
                        "operator_id": operator_id,
                        "current_station_id": current_station,
                        "container": bad_container,
                        "box_seq": bad_box_seq,
                        "status": "N",  # 不良品
                        "qty": str(bad_qty).zfill(4)
                    }
                )
                
                if response.status_code != 200:
                    error_msg = response.json().get("detail", response.text) if response.status_code == 400 else response.text
                    raise Exception(f"不良品遷出 API 調用失敗: {response.status_code} - {error_msg}")
                
                data = response.json()
                if not data.get("success"):
                    raise Exception(f"不良品遷出失敗: {data.get('message', '未知錯誤')}")
                
                # 取得新條碼（不良品批次）
                new_barcode_bad = data["data"]["new_barcode"]
                process_records.append({
                    "station": current_station,
                    "action": "OUT",
                    "barcode": new_barcode_bad,
                    "api": "/api/scan/outbound",
                    "status": "N",
                    "qty": bad_qty
                })
                
                print(f"    不良品新條碼: {new_barcode_bad}")
                
                # 使用良品條碼作為下一站的輸入（不良品通常不進入下一站）
                current_barcode = new_barcode_good
                
                print(f"    等待 2 秒...")
                time.sleep(2)
            else:
                # 單一批次遷出（全部為良品）
                # 遷出數量應該等於遷入的數量（current_qty）
                print(f"  [步驟 {i*2+1}] 遷出 ({current_station}) - 調用 API: POST /api/scan/outbound")
                print(f"    遷出數量: {current_qty} (等於遷入數量)")
                
                response = client.post(
                    "/api/scan/outbound",
                    json={
                        "barcode": current_barcode,
                        "operator_id": operator_id,
                        "current_station_id": current_station,
                        "container": container,
                        "box_seq": box_seq,
                        "status": status,
                        "qty": str(current_qty).zfill(4)  # 使用當前數量
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
                # 單一批次遷出時，數量不變（全部為良品）
                # current_qty 保持不變
                
                print(f"    等待 2 秒...")
                time.sleep(2)
        
        # 最後一站：遷入後遷出（分為良品和不良品，用於測試良率計算）
        if len(stations) > 1:
            last_station = stations[-1]
            
            # 遷入
            # 遷入的數量應該等於前一站遷出的良品數量（從條碼中解析）
            print(f"  [最後步驟-1] 最終站遷入 ({last_station}) - 調用 API: POST /api/scan/inbound")
            
            # 從條碼中解析當前數量（應該等於前一站的良品數量）
            from services.barcode import BarcodeParser
            parsed = BarcodeParser.parse(current_barcode)
            if parsed and parsed.get('qty'):
                # 從條碼中獲取數量（前一站的良品數量）
                current_qty = int(parsed.get('qty'))
                print(f"    從條碼解析數量: {current_qty}")
            else:
                # 如果解析失敗，使用追蹤的數量（應該已經在上一步更新）
                print(f"    條碼解析失敗，使用追蹤數量: {current_qty}")
            
            print(f"    遷入數量: {current_qty} (來自前一站的良品數量)")
            
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
                "api": "/api/scan/inbound",
                "qty": current_qty
            })
            
            print(f"    掃描條碼: {current_barcode}")
            print(f"    等待 2 秒...")
            time.sleep(2)
            
            # 遷出：分為良品和不良品（用於測試良率計算）
            # 遷出的總數應該等於遷入的數量（current_qty）
            total_qty_int = current_qty
            
            # 良品比例：根據工單索引變化（80%-95%）
            good_ratio = 0.80 + (order_index % 4) * 0.05  # 80%, 85%, 90%, 95% 循環
            good_qty = int(total_qty_int * good_ratio)
            bad_qty = total_qty_int - good_qty
            
            # 第一次遷出：良品
            print(f"  [最後步驟-2] 最終站遷出 ({last_station}) - 良品批次 - 調用 API: POST /api/scan/outbound")
            print(f"    良品數量: {good_qty}")
            
            response = client.post(
                "/api/scan/outbound",
                json={
                    "barcode": current_barcode,
                    "operator_id": operator_id,
                    "current_station_id": last_station,
                    "container": container,
                    "box_seq": box_seq,
                    "status": "G",  # 良品
                    "qty": str(good_qty).zfill(4)
                }
            )
            
            if response.status_code != 200:
                error_msg = response.json().get("detail", response.text) if response.status_code == 400 else response.text
                raise Exception(f"最終站良品遷出 API 調用失敗: {response.status_code} - {error_msg}")
            
            data = response.json()
            if not data.get("success"):
                raise Exception(f"最終站良品遷出失敗: {data.get('message', '未知錯誤')}")
            
            final_barcode_good = data["data"]["new_barcode"]
            process_records.append({
                "station": last_station,
                "action": "OUT",
                "barcode": final_barcode_good,
                "api": "/api/scan/outbound",
                "status": "G",
                "qty": good_qty
            })
            
            print(f"    良品新條碼: {final_barcode_good}")
            print(f"    等待 2 秒...")
            time.sleep(2)
            
            # 第二次遷出：不良品（使用不同的容器和箱號）
            if bad_qty > 0:  # 只有當有不良品時才遷出
                print(f"  [最後步驟-3] 最終站遷出 ({last_station}) - 不良品批次 - 調用 API: POST /api/scan/outbound")
                print(f"    不良品數量: {bad_qty}")
                
                bad_container = f"B{order_index % 3 + 1}"  # 使用不同的容器
                bad_box_seq = f"{order_index:02d}B"  # 使用不同的箱號
                
                response = client.post(
                    "/api/scan/outbound",
                    json={
                        "barcode": current_barcode,  # 使用同一個舊條碼
                        "operator_id": operator_id,
                        "current_station_id": last_station,
                        "container": bad_container,
                        "box_seq": bad_box_seq,
                        "status": "N",  # 不良品
                        "qty": str(bad_qty).zfill(4)
                    }
                )
                
                if response.status_code != 200:
                    error_msg = response.json().get("detail", response.text) if response.status_code == 400 else response.text
                    raise Exception(f"最終站不良品遷出 API 調用失敗: {response.status_code} - {error_msg}")
                
                data = response.json()
                if not data.get("success"):
                    raise Exception(f"最終站不良品遷出失敗: {data.get('message', '未知錯誤')}")
                
                final_barcode_bad = data["data"]["new_barcode"]
                process_records.append({
                    "station": last_station,
                    "action": "OUT",
                    "barcode": final_barcode_bad,
                    "api": "/api/scan/outbound",
                    "status": "N",
                    "qty": bad_qty
                })
                
                print(f"    不良品新條碼: {final_barcode_bad}")
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

