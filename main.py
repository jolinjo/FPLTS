"""
FastAPI 應用程式入口
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import os
from dotenv import load_dotenv

from services.barcode import BarcodeParser, BarcodeGenerator, CRC16
from services.flow_validator import validate_process_flow, get_next_station
from services.sheet import sheet_service
from services.config_loader import config_loader
from services.qrcode_generator import QRCodeGenerator

load_dotenv()

app = FastAPI(title="工廠製程物流追溯與分析系統", version="0.0.7")

# 掛載靜態檔案目錄
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


# Pydantic 模型
class InboundRequest(BaseModel):
    """遷入請求模型"""
    barcode: str
    operator_id: str
    current_station_id: str


class OutboundRequest(BaseModel):
    """遷出請求模型"""
    barcode: str
    operator_id: str
    current_station_id: str
    container: Optional[str] = None
    box_seq: Optional[str] = None
    status: Optional[str] = None
    qty: Optional[str] = None


class TraceRequest(BaseModel):
    """追溯請求模型"""
    barcode: str


class CheckBarcodeRequest(BaseModel):
    """條碼檢查請求模型"""
    barcode: str
    current_station_id: str


class FirstStationRequest(BaseModel):
    """首站遷出請求模型"""
    order: str
    operator_id: str
    current_station_id: str
    series_code: str  # 產品線代號（例如：AC, ST）
    model_code: str   # 機種代號（例如：350, 351）
    container: str
    box_seq: str
    status: str
    qty: str


# 背景任務：寫入 Google Sheets
def write_to_sheet(log_data: dict):
    """背景任務：寫入記錄到 Google Sheets"""
    sheet_service.write_log(log_data)


@app.get("/")
async def root():
    """根路徑，返回前端頁面"""
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "工廠製程物流追溯與分析系統 API"}


@app.get("/b={barcode:path}")
async def redirect_barcode_path(barcode: str):
    """
    處理 /b=條碼 格式的 URL，重定向到正確的查詢參數格式
    這樣可以支援 QR code 中沒有 ? 的情況
    """
    # 重定向到正確的查詢參數格式
    return RedirectResponse(url=f"/?b={barcode}", status_code=302)


@app.post("/api/scan/check")
async def check_barcode(request: CheckBarcodeRequest):
    """
    檢查條碼狀態 API
    
    用於在執行遷入/遷出前，先檢查條碼的狀態，決定應該使用哪個功能
    返回建議的操作類型：'inbound', 'outbound', 'first'
    """
    # 先嘗試完整解析條碼
    parsed = BarcodeParser.parse(request.barcode)
    
    # 如果完整解析失敗，嘗試部分解析（至少識別工單號和製程代號）
    if not parsed:
        parsed = BarcodeParser.parse_partial(request.barcode)
        if not parsed:
            raise HTTPException(status_code=400, detail="條碼格式錯誤，無法解析")
    
    # 檢查製程代號
    process_code = parsed['process'].upper()
    
    # 如果是 ZZ 製程（新工單），建議使用首站遷出
    # 對於 ZZ 製程，不需要驗證 CRC16（因為可能是不完整的條碼）
    if process_code == 'ZZ':
        sku = parsed.get('sku', '')
        # 從 SKU 提取產品線和機種代碼（如果 SKU 存在）
        series_code = ''
        model_code = ''
        if sku and len(sku) >= 5:
            series_code = BarcodeParser.get_series_from_sku(sku)  # 前 2 碼
            model_code = BarcodeParser.get_model_from_sku(sku)   # 後 3 碼
        
        return {
            "success": True,
            "suggested_action": "first",
            "message": "檢測到新工單（ZZ 製程），建議使用首站遷出",
            "data": {
                "barcode": request.barcode,
                "order": parsed['order'].upper(),
                "process": process_code,
                "sku": sku,
                "series_code": series_code,
                "model_code": model_code
            }
        }
    
    # 對於完整條碼，驗證 CRC16 校驗碼
    if not CRC16.verify(request.barcode):
        raise HTTPException(status_code=400, detail="條碼校驗碼錯誤")
    
    # 取得當前站點
    current_station = request.current_station_id.upper()
    barcode_process = process_code.upper()
    
    # ========== 根據 BARCODE_SCAN_LOGIC.md 定義的邏輯 ==========
    # 優先級順序：
    # 1. ZZ 製程 → 首站遷出（已在上面處理）
    # 2. 上一站條碼 + 當前站點或下游站點已有遷出記錄 → 只允許查詢（防止數據錯亂）
    # 3. 當前站點已有遷入記錄 → 遷出
    # 4. 當前站點已有遷出記錄 → 遷出
    # 5. 沒有記錄 → 遷入（根據條碼與站點關係）
    
    # 判斷條碼與當前站點的關係（上一站/本站/下一站）
    station_order = {'P1': 1, 'P2': 2, 'P3': 3, 'P4': 4, 'P5': 5}
    barcode_order = station_order.get(barcode_process, 999)
    current_order = station_order.get(current_station, 999)
    
    # ========== 第二優先級：上一站條碼 + 當前站點或下游站點已有遷出記錄 ==========
    # 防止數據錯亂：如果條碼已經流到下游，不能再遷入或遷出
    if barcode_order < current_order:
        # 這是上一站條碼
        has_out_at_current = sheet_service.has_outbound_record_at_station(request.barcode, current_station)
        has_out_at_downstream = sheet_service.has_outbound_record_at_downstream_stations(request.barcode, current_station)
        
        if has_out_at_current or has_out_at_downstream:
            # 當前站點或下游站點已有遷出記錄 → 只允許查詢
            return {
                "success": True,
                "suggested_action": "trace",
                "message": f"該條碼在當前站點或下游站點已有遷出記錄，為避免數據錯亂，只能進行查詢",
                "data": {
                    "barcode": request.barcode,
                    "order": parsed['order'].upper(),
                    "process": process_code,
                    "sku": parsed['sku']
                }
            }
    
    # ========== 第三優先級：檢查當前站點是否有遷入記錄 ==========
    has_in_at_current = sheet_service.has_inbound_record_at_station(request.barcode, current_station)
    
    if has_in_at_current:
        # 當前站點已有遷入記錄 → 必須先遷出
        return {
            "success": True,
            "suggested_action": "outbound",
            "message": f"該條碼在 {current_station} 站點已有遷入記錄，請使用遷出功能",
            "data": {
                "barcode": request.barcode,
                "order": parsed['order'].upper(),
                "process": process_code,
                "sku": parsed['sku']
            }
        }
    
    # ========== 第四優先級：檢查當前站點是否有遷出記錄 ==========
    has_out_at_current = sheet_service.has_outbound_record_at_station(request.barcode, current_station)
    
    if has_out_at_current:
        # 當前站點已有遷出記錄 → 可以再次遷出（例如：分為良品和不良品）
        return {
            "success": True,
            "suggested_action": "outbound",
            "message": f"該條碼在 {current_station} 站點已有遷出記錄，可以再次遷出",
            "data": {
                "barcode": request.barcode,
                "order": parsed['order'].upper(),
                "process": process_code,
                "sku": parsed['sku']
            }
        }
    
    # ========== 最低優先級：沒有記錄 → 根據條碼與站點關係決定 ==========
    if barcode_order < current_order:
        # 上一站條碼 → 建議遷入（正常流程）
        return {
            "success": True,
            "suggested_action": "inbound",
            "message": f"檢測到 {barcode_process} 製程條碼（上一站），在 {current_station} 站點沒有記錄，建議使用遷入功能",
            "data": {
                "barcode": request.barcode,
                "order": parsed['order'].upper(),
                "process": process_code,
                "sku": parsed['sku']
            }
        }
    elif barcode_order == current_order:
        # 本站條碼 → 建議遷入（可能是異常情況）
        return {
            "success": True,
            "suggested_action": "inbound",
            "message": f"檢測到 {barcode_process} 製程條碼（本站），在 {current_station} 站點沒有記錄，建議使用遷入功能",
            "data": {
                "barcode": request.barcode,
                "order": parsed['order'].upper(),
                "process": process_code,
                "sku": parsed['sku']
            }
        }
    else:
        # 下一站條碼 → 建議遷入（可能是跳站異常）
        return {
            "success": True,
            "suggested_action": "inbound",
            "message": f"檢測到 {barcode_process} 製程條碼（下一站），在 {current_station} 站點沒有記錄，建議使用遷入功能",
            "data": {
                "barcode": request.barcode,
                "order": parsed['order'].upper(),
                "process": process_code,
                "sku": parsed['sku']
            }
        }


@app.get("/api/config/series")
async def get_series_options():
    """
    取得產品線選項列表
    
    返回所有可用的產品線（Series）選項
    """
    series_dict = config_loader.get_section_dict("series", "Series")
    
    # 轉換為列表格式，包含代號和名稱
    series_list = [
        {"code": code, "name": name}
        for code, name in series_dict.items()
    ]
    
    return {
        "success": True,
        "data": series_list
    }


@app.get("/api/config/models")
async def get_model_options():
    """
    取得機種選項列表
    
    返回所有可用的機種（Model）選項
    """
    model_dict = config_loader.get_section_dict("model", "Model")
    
    # 轉換為列表格式，包含代號和名稱
    model_list = [
        {"code": code, "name": name}
        for code, name in model_dict.items()
    ]
    
    return {
        "success": True,
        "data": model_list
    }


@app.get("/api/config/containers")
async def get_container_options():
    """
    取得容器選項列表
    
    返回所有可用的容器（Container）選項
    """
    container_dict = config_loader.get_section_dict("container", "Container")
    
    # 轉換為列表格式，包含代號和容量
    container_list = [
        {"code": code, "capacity": name}
        for code, name in container_dict.items()
    ]
    
    return {
        "success": True,
        "data": container_list
    }


@app.get("/api/config/processes")
async def get_process_options():
    """
    取得製程站點選項列表
    
    返回所有可用的製程站點（Process）選項
    """
    process_dict = config_loader.get_section_dict("process", "Process")
    
    # 轉換為列表格式，包含代號和名稱
    process_list = [
        {"code": code, "name": name}
        for code, name in process_dict.items()
    ]
    
    return {
        "success": True,
        "data": process_list
    }


@app.post("/api/scan/inbound")
async def scan_inbound(request: InboundRequest, background_tasks: BackgroundTasks):
    """
    貨物遷入 API
    
    關鍵邏輯：
    1. 解析條碼
    2. 優先進行流程驗證（防呆檢查）
    3. 若驗證失敗，直接回傳 HTTP 400 錯誤
    4. 若驗證通過，使用 BackgroundTasks 寫入 Google Sheets
    """
    # 解析條碼
    parsed = BarcodeParser.parse(request.barcode)
    if not parsed:
        raise HTTPException(status_code=400, detail="條碼格式錯誤，無法解析")
    
    # 驗證 CRC16 校驗碼
    if not CRC16.verify(request.barcode):
        raise HTTPException(status_code=400, detail="條碼校驗碼錯誤")
    
    # 取得 SKU 和上一站
    sku = parsed['sku']
    prev_station = parsed['process']
    curr_station = request.current_station_id
    
    # 檢查該條碼在當前站點是否已有 IN 記錄
    # 如果該條碼在當前站點已經遷入過，應該使用遷出功能，不能再遷入
    has_in_at_current = sheet_service.has_inbound_record_at_station(request.barcode, curr_station)
    
    if has_in_at_current:
        # 如果當前站點已有 IN 記錄，返回特殊狀態，讓前端切換到遷出
        return {
            "success": False,
            "should_switch_to_outbound": True,
            "message": f"該條碼在 {curr_station} 站點已有遷入記錄，請使用遷出功能",
            "data": {
                "barcode": request.barcode,
                "order": parsed['order'].upper(),
                "sku": sku
            }
        }
    
    # 檢查該條碼在當前站點是否已有 OUT 記錄
    # 如果該條碼在當前站點有遷出記錄，表示已經在當前站點遷出過（可能分為良品和不良品），
    # 應該直接使用遷出功能，不要再遷入
    # 注意：這裡檢查的是「當前站點」的遷出記錄，而不是「任何站點」的遷出記錄
    # 因為上游站點的遷出記錄不應該阻止下游站點的遷入
    has_out_at_current = sheet_service.has_outbound_record_at_station(request.barcode, curr_station)
    
    if has_out_at_current:
        # 如果當前站點已有 OUT 記錄，返回特殊狀態，讓前端切換到遷出
        return {
            "success": False,
            "should_switch_to_outbound": True,
            "message": f"該條碼在 {curr_station} 站點已有遷出記錄，請使用遷出功能",
            "data": {
                "barcode": request.barcode,
                "order": parsed['order'].upper(),
                "sku": sku
            }
        }
    
    # 取得產品系列（前2碼）
    series = BarcodeParser.get_series_from_sku(sku)
    
    # 優先進行流程驗證（防呆檢查）
    is_valid, error_message = validate_process_flow(series, prev_station, curr_station)
    
    if not is_valid:
        # 驗證失敗，直接回傳 HTTP 400 錯誤
        raise HTTPException(status_code=400, detail=error_message)
    
    # 計算工時（遷入時工時為 0）
    cycle_time = 0
    
    # 準備記錄資料（工單號和站點轉換為大寫）
    log_data = {
        "timestamp": datetime.now(),
        "action": "IN",
        "operator": request.operator_id,
        "order": parsed['order'].upper(),
        "process": curr_station.upper(),
        "sku": sku,
        "container": parsed['container'],
        "box_seq": parsed['box_seq'],
        "qty": parsed['qty'],
        "status": parsed['status'],
        "cycle_time": cycle_time,
        "scanned_barcode": request.barcode,
        "new_barcode": ""
    }
    
    # 同步寫入 Google Sheets（檢查是否成功）
    write_success = sheet_service.write_log(log_data)
    
    if not write_success:
        # 寫入失敗，返回錯誤，讓前端顯示錯誤訊息並允許重試
        raise HTTPException(
            status_code=500, 
            detail="寫入 Google Sheets 失敗，請檢查網路連線或 Google Sheets 設定，稍後再試"
        )
    
    # 寫入成功，回傳成功回應
    return {
        "success": True,
        "message": "遷入成功",
        "data": {
            "order": parsed['order'].upper(),
            "sku": sku,
            "current_station": curr_station.upper(),
            "prev_station": prev_station.upper()
        }
    }


@app.post("/api/scan/outbound")
async def scan_outbound(request: OutboundRequest, background_tasks: BackgroundTasks):
    """
    貨物遷出 API
    
    邏輯：
    1. 解析舊條碼
    2. 生成新條碼（更新製程代號）
    3. 計算工時
    4. 寫入 Google Sheets
    """
    # 解析舊條碼
    parsed = BarcodeParser.parse(request.barcode)
    if not parsed:
        raise HTTPException(status_code=400, detail="條碼格式錯誤，無法解析")
    
    # 驗證 CRC16 校驗碼
    if not CRC16.verify(request.barcode):
        raise HTTPException(status_code=400, detail="條碼校驗碼錯誤")
    
    # 生成新條碼
    new_barcode = BarcodeGenerator.generate_from_previous(
        previous_barcode=request.barcode,
        new_process=request.current_station_id,
        new_container=request.container,
        new_box_seq=request.box_seq,
        new_status=request.status,
        new_qty=request.qty
    )
    
    if not new_barcode:
        raise HTTPException(status_code=500, detail="生成新條碼失敗")
    
    # 計算工時（這裡簡化處理，實際應從遷入時間計算）
    # TODO: 從 Google Sheets 查詢上次遷入時間來計算實際工時
    cycle_time = 0
    
    # 取得 domain 設定，並組合成完整的條碼 URL
    domain = config_loader.get_value("settings", "Settings", "domain", "")
    if domain:
        # 移除 domain 末尾的斜線（如果有的話）
        domain = domain.rstrip('/')
        # 組合成完整 URL：domain/b=條碼
        new_barcode_with_domain = f"{domain}/b={new_barcode}"
    else:
        # 如果沒有設定 domain，只使用條碼
        new_barcode_with_domain = new_barcode
    
    # 準備記錄資料（工單號和站點轉換為大寫）
    log_data = {
        "timestamp": datetime.now(),
        "action": "OUT",
        "operator": request.operator_id,
        "order": parsed['order'].upper(),
        "process": request.current_station_id.upper(),
        "sku": parsed['sku'],
        "container": request.container or parsed['container'],
        "box_seq": request.box_seq or parsed['box_seq'],
        "qty": request.qty or parsed['qty'],
        "status": request.status or parsed['status'],
        "cycle_time": cycle_time,
        "scanned_barcode": request.barcode,
        "new_barcode": new_barcode_with_domain
    }
    
    # 同步寫入 Google Sheets（檢查是否成功）
    write_success = sheet_service.write_log(log_data)
    
    if not write_success:
        # 寫入失敗，返回錯誤，讓前端顯示錯誤訊息並允許重試
        raise HTTPException(
            status_code=500, 
            detail="寫入 Google Sheets 失敗，請檢查網路連線或 Google Sheets 設定，稍後再試"
        )
    
    # 取得下一站建議
    series = BarcodeParser.get_series_from_sku(parsed['sku'])
    next_station = get_next_station(series, request.current_station_id)
    
    # 生成 QR Code SVG（使用包含 domain 的完整 URL）
    qr_svg = QRCodeGenerator.generate_simple_svg(new_barcode_with_domain)
    
    # 寫入成功，回傳成功回應
    return {
        "success": True,
        "message": "遷出成功",
        "data": {
            "new_barcode": new_barcode,  # 返回原始條碼（不含 domain）
            "new_barcode_url": new_barcode_with_domain,  # 返回完整 URL（含 domain）
            "order": parsed['order'].upper(),
            "current_station": request.current_station_id.upper(),
            "next_station": next_station.upper() if next_station else None,
            "qr_code_svg": qr_svg
        }
    }


@app.post("/api/scan/trace")
async def scan_trace(request: TraceRequest):
    """
    追溯查詢 API
    
    根據條碼查詢該工單的時間軸與良率統計
    按製程站點分組，計算出入時間、總耗時間、投入數量、產出數量
    """
    from collections import defaultdict
    from datetime import datetime
    
    # 解析條碼
    parsed = BarcodeParser.parse(request.barcode)
    if not parsed:
        raise HTTPException(status_code=400, detail="條碼格式錯誤，無法解析")
    
    # 查詢該工單的所有記錄
    order = parsed['order']
    logs = sheet_service.get_logs_by_order(order)
    
    # 按製程站點分組記錄
    station_logs = defaultdict(lambda: {"in": [], "out": []})
    
    for log in logs:
        process = log.get("process", "").upper()
        action = log.get("action", "").upper()
        timestamp_str = log.get("timestamp", "")
        
        # 解析時間戳記
        try:
            if isinstance(timestamp_str, str) and timestamp_str.strip():
                # 嘗試多種時間格式
                timestamp = None
                for fmt in ["%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S.%f"]:
                    try:
                        timestamp = datetime.strptime(timestamp_str.strip(), fmt)
                        break
                    except:
                        continue
                if timestamp is None:
                    continue  # 如果所有格式都失敗，跳過這筆記錄
            elif isinstance(timestamp_str, datetime):
                timestamp = timestamp_str
            else:
                continue  # 無效的時間戳記，跳過
        except Exception as e:
            print(f"解析時間戳記失敗：{timestamp_str}, 錯誤：{e}")
            continue
        
        log_entry = {
            "timestamp": timestamp,
            "timestamp_str": timestamp_str,
            "operator": log.get("operator", ""),
            "qty": int(log.get("qty", 0) or 0),
            "status": log.get("status", ""),
            "container": log.get("container", ""),
            "box_seq": log.get("box_seq", ""),
            "cycle_time": float(log.get("cycle_time", 0) or 0)
        }
        
        if action == "IN":
            station_logs[process]["in"].append(log_entry)
        elif action == "OUT":
            station_logs[process]["out"].append(log_entry)
    
    # 按時間排序每個站點的記錄
    for process in station_logs:
        station_logs[process]["in"].sort(key=lambda x: x["timestamp"])
        station_logs[process]["out"].sort(key=lambda x: x["timestamp"])
    
    # 定義站點順序（用於確定首站和計算投入數量）
    station_order = {'P1': 1, 'P2': 2, 'P3': 3, 'P4': 4, 'P5': 5}
    
    # 找到首站（第一個有OUT記錄的站點，按站點順序）
    first_station = None
    first_station_order = None
    for process, records in station_logs.items():
        if records["out"]:  # 有遷出記錄
            process_order = station_order.get(process, 999)
            if first_station_order is None or process_order < first_station_order:
                first_station = process
                first_station_order = process_order
    
    # 構建站點時間軸（按站點順序排序，而不是按時間）
    station_timeline = []
    # 按站點順序處理每個站點
    sorted_processes = sorted(station_logs.keys(), key=lambda p: station_order.get(p, 999))
    
    # 用於追蹤上一站的產出良品數量
    previous_station_good_qty = None
    
    for process in sorted_processes:
        records = station_logs[process]
        
        # 找到最早的記錄時間
        earliest_time = None
        if records["in"]:
            earliest_time = records["in"][0]["timestamp"]
        if records["out"]:
            out_time = records["out"][0]["timestamp"]
            if earliest_time is None or out_time < earliest_time:
                earliest_time = out_time
        
        if earliest_time:
            # 計算投入數量：
            # - 如果是首站，使用所有 IN 記錄的數量總和
            # - 如果不是首站，使用上一站的產出良品數量
            if process == first_station:
                # 首站：投入數量 = 所有 IN 記錄的數量總和
                input_qty = sum(r["qty"] for r in records["in"])
            else:
                # 非首站：投入數量 = 上一站的產出良品數量
                input_qty = previous_station_good_qty if previous_station_good_qty is not None else 0
            
            # 計算產出數量（所有 OUT 記錄的數量總和）
            output_qty = sum(r["qty"] for r in records["out"])
            
            # 計算產出良品數量（所有 OUT 記錄中狀態為 G 的數量總和）
            output_good_qty = sum(r["qty"] for r in records["out"] if r["status"].upper() == "G")
            
            # 計算產出不良品數量（所有 OUT 記錄中狀態不是 G 的數量總和）
            output_bad_qty = sum(r["qty"] for r in records["out"] if r["status"].upper() != "G")
            
            # 更新上一站的產出良品數量（用於下一個站點的投入數量計算）
            previous_station_good_qty = output_good_qty
            
            # 計算總耗時間（從最早 IN 到最晚 OUT）
            total_time = None
            if records["in"] and records["out"]:
                first_in = records["in"][0]["timestamp"]
                last_out = records["out"][-1]["timestamp"]
                time_diff = last_out - first_in
                total_seconds = time_diff.total_seconds()
                hours = int(total_seconds // 3600)
                minutes = int((total_seconds % 3600) // 60)
                seconds = int(total_seconds % 60)
                total_time = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            
            # 獲取出入時間
            in_time = records["in"][0]["timestamp_str"] if records["in"] else None
            out_time = records["out"][-1]["timestamp_str"] if records["out"] else None
            
            station_timeline.append({
                "process": process,
                "earliest_time": earliest_time.isoformat() if earliest_time else None,
                "in_time": in_time,
                "out_time": out_time,
                "total_time": total_time,
                "input_qty": input_qty,
                "output_qty": output_qty,
                "output_good_qty": output_good_qty,
                "output_bad_qty": output_bad_qty,
                "in_records": records["in"],
                "out_records": records["out"]
            })
    
    # 按站點順序排序（P1, P2, P3, P4, P5），而不是按時間
    station_timeline.sort(key=lambda x: station_order.get(x["process"], 999))
    
    # ========== 計算統計數據（根據新的邏輯）==========
    # 1. 總數 = 首站遷出的良品與不良品加總
    # 找到首站（第一個有 OUT 記錄的站點，按時間順序）
    first_station = None
    first_station_time = None
    
    # 找到最早有遷出記錄的站點（按時間排序）
    for process, records in station_logs.items():
        if records["out"]:  # 有遷出記錄
            # 找到最早的遷出時間
            earliest_out_time = records["out"][0]["timestamp"]
            
            # 如果這是第一個找到的站點，或者時間更早，則更新首站
            if first_station_time is None or earliest_out_time < first_station_time:
                first_station = process
                first_station_time = earliest_out_time
    
    # 計算首站遷出的總數（良品 + 不良品）
    total_qty = 0
    if first_station and first_station in station_logs:
        for out_record in station_logs[first_station]["out"]:
            total_qty += out_record["qty"]
    
    # 2. 找到最終站（最後一個有 OUT 記錄的站點，按時間順序）
    final_station = None
    final_station_time = None
    
    for process, records in station_logs.items():
        if records["out"]:  # 有遷出記錄
            # 找到最晚的遷出時間
            latest_out_time = records["out"][-1]["timestamp"]
            
            # 如果這是第一個找到的站點，或者時間更晚，則更新最終站
            if final_station_time is None or latest_out_time > final_station_time:
                final_station = process
                final_station_time = latest_out_time
    
    # 3. 計算最終站的良品數量
    final_good_qty = 0
    
    if final_station and final_station in station_logs:
        for out_record in station_logs[final_station]["out"]:
            qty = out_record["qty"]
            status = out_record["status"].upper()
            if status == "G":  # 良品
                final_good_qty += qty
    
    # 4. 計算全製程不良品 = 首站投入總數 - 最終站良品數
    total_defect_qty = total_qty - final_good_qty
    
    # 5. 計算直通率 = 最終站良品數 / 首站投入總數 × 100%
    first_pass_rate = (final_good_qty / total_qty * 100) if total_qty > 0 else 0
    
    # 6. 計算全製程用時（累加各製程的總耗時間）
    total_process_time_seconds = 0
    for station in station_timeline:
        if station.get("total_time"):
            # 解析時間格式 "HH:MM:SS"
            time_parts = station["total_time"].split(":")
            if len(time_parts) == 3:
                hours = int(time_parts[0])
                minutes = int(time_parts[1])
                seconds = int(time_parts[2])
                total_process_time_seconds += hours * 3600 + minutes * 60 + seconds
    
    # 格式化全製程用時
    total_hours = int(total_process_time_seconds // 3600)
    total_minutes = int((total_process_time_seconds % 3600) // 60)
    total_seconds = int(total_process_time_seconds % 60)
    total_process_time = f"{total_hours:02d}:{total_minutes:02d}:{total_seconds:02d}"
    
    # 5. 計算各製程站的良率（產出良品數量 / 投入數量）
    # 注意：當站良率必須基於投入數量計算，而不是產出總數
    station_yield_rates = {}
    for process, records in station_logs.items():
        # 計算投入數量（所有 IN 記錄的數量總和）
        input_qty = sum(r["qty"] for r in records["in"])
        
        # 計算產出良品數量（所有 OUT 記錄中狀態為 G 的數量總和）
        output_good_qty = sum(r["qty"] for r in records["out"] if r["status"].upper() == "G")
        
        # 當站良率 = 產出良品數量 / 投入數量（必須有投入記錄才能計算）
        # 如果沒有投入記錄，則不計算當站良率（避免使用產出總數作為分母）
        if input_qty > 0 and records["out"]:  # 必須同時有投入和產出記錄
            station_yield = (output_good_qty / input_qty * 100)
            station_yield_rates[process] = round(station_yield, 2)
    
    # 從 SKU 提取產品線和機種信息
    sku = parsed['sku']
    series_code = BarcodeParser.get_series_from_sku(sku)  # 前2碼
    model_code = BarcodeParser.get_model_from_sku(sku)    # 後3碼
    
    # 從 INI 檔中查找對應的名稱
    series_dict = config_loader.get_section_dict("series", "Series")
    model_dict = config_loader.get_section_dict("model", "Model")
    
    # 查找產品線名稱（ConfigParser 會將鍵轉為小寫存儲）
    series_name = ""
    if series_code:
        # ConfigParser 會將鍵轉為小寫，所以使用小寫查找
        series_name = series_dict.get(series_code.lower(), series_code)
    
    # 查找機種名稱（處理前導零，例如 001 和 1）
    model_name = ""
    if model_code:
        # ConfigParser 會將鍵轉為小寫，所以使用小寫查找
        # 嘗試直接匹配
        model_name = model_dict.get(model_code.lower(), "")
        
        # 如果找不到，嘗試去除前導零後匹配
        if not model_name:
            model_code_no_zero = model_code.lstrip('0') or '0'
            model_name = model_dict.get(model_code_no_zero.lower(), "")
        
        # 如果還是找不到，使用原始代碼
        if not model_name:
            model_name = model_code
    
    return {
        "success": True,
        "data": {
            "order": order.upper(),
            "sku": sku,
            "series_code": series_code,
            "series_name": series_name,
            "model_code": model_code,
            "model_name": model_name,
            "station_timeline": station_timeline,
            "statistics": {
                "total_qty": total_qty,  # 首站遷出的總數
                "final_good_qty": final_good_qty,  # 最終站的良品數量
                "total_defect_qty": total_defect_qty,  # 全製程不良品 = 首站投入總數 - 最終站良品數
                "first_pass_rate": round(first_pass_rate, 2),  # 直通率 = 最終站良品數 / 首站投入總數 × 100%
                "yield_rate": round((final_good_qty / total_qty * 100) if total_qty > 0 else 0, 2),  # 良率 = 良品/總數
                "total_process_time": total_process_time,  # 全製程用時（累加各製程的總耗時間）
                "station_yield_rates": station_yield_rates  # 各製程站的良率
            }
        }
    }


@app.post("/api/scan/first")
async def scan_first(request: FirstStationRequest, background_tasks: BackgroundTasks):
    """
    首站遷出 API
    
    手動輸入工單資訊，生成第一個條碼
    從產品線代號和機種代號自動組合成 SKU
    """
    # 驗證產品線代號是否存在（ConfigParser 會將鍵轉為小寫）
    series_dict = config_loader.get_section_dict("series", "Series")
    series_code_lower = request.series_code.lower()
    if series_code_lower not in series_dict:
        raise HTTPException(status_code=400, detail=f"無效的產品線代號：{request.series_code}")
    
    # 驗證機種代號是否存在（ConfigParser 會將鍵轉為小寫）
    model_dict = config_loader.get_section_dict("model", "Model")
    if request.model_code not in model_dict:
        raise HTTPException(status_code=400, detail=f"無效的機種代號：{request.model_code}")
    
    # 組合成 SKU：產品線代號（2碼）+ 機種代號（3碼，補零）
    model_code_padded = request.model_code.zfill(3)[:3]
    sku = f"{request.series_code}{model_code_padded}"
    
    # 工單號轉換為大寫
    order_upper = request.order.upper()
    
    # 生成第一個條碼
    barcode = BarcodeGenerator.generate(
        order=order_upper,
        process=request.current_station_id,
        sku=sku,
        container=request.container,
        box_seq=request.box_seq,
        status=request.status,
        qty=request.qty
    )
    
    # 取得 domain 設定，並組合成完整的條碼 URL
    domain = config_loader.get_value("settings", "Settings", "domain", "")
    if domain:
        # 移除 domain 末尾的斜線（如果有的話）
        domain = domain.rstrip('/')
        # 組合成完整 URL：domain/b=條碼
        new_barcode_with_domain = f"{domain}/b={barcode}"
    else:
        # 如果沒有設定 domain，只使用條碼
        new_barcode_with_domain = barcode
    
    # 準備記錄資料（工單號和站點轉換為大寫）
    log_data = {
        "timestamp": datetime.now(),
        "action": "OUT",
        "operator": request.operator_id,
        "order": order_upper,
        "process": request.current_station_id.upper(),
        "sku": sku,
        "container": request.container,
        "box_seq": request.box_seq,
        "qty": request.qty,
        "status": request.status,
        "cycle_time": 0,
        "scanned_barcode": "",
        "new_barcode": new_barcode_with_domain  # 使用包含 domain 的完整 URL
    }
    
    # 同步寫入 Google Sheets（檢查是否成功）
    write_success = sheet_service.write_log(log_data)
    
    if not write_success:
        # 寫入失敗，返回錯誤，讓前端顯示錯誤訊息並允許重試
        raise HTTPException(
            status_code=500, 
            detail="寫入 Google Sheets 失敗，請檢查網路連線或 Google Sheets 設定，稍後再試"
        )
    
    # 取得下一站建議
    next_station = get_next_station(request.series_code, request.current_station_id)
    
    # 生成 QR Code SVG（使用包含 domain 的完整 URL）
    qr_svg = QRCodeGenerator.generate_simple_svg(new_barcode_with_domain)
    
    # 寫入成功，回傳成功回應
    return {
        "success": True,
        "message": "首站遷出成功",
        "data": {
            "barcode": barcode,  # 返回原始條碼（不含 domain）
            "barcode_url": new_barcode_with_domain,  # 返回完整 URL（含 domain）
            "order": order_upper,
            "sku": sku,
            "current_station": request.current_station_id.upper(),
            "next_station": next_station.upper() if next_station else None,
            "qr_code_svg": qr_svg
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

