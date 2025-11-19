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

app = FastAPI(title="工廠製程物流追溯與分析系統", version="0.0.5")

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
    
    # 判斷邏輯：
    # 1. 如果條碼的製程代號不等於當前站點（例如：P1 條碼在 P2 站點）
    #    檢查該條碼在當前站點（P2）是否有遷出記錄
    #    - 如果沒有，建議使用遷入功能（從上游站點遷入）
    #    - 如果有，建議使用遷出功能（已經遷入過，可以再次遷出）
    # 2. 如果條碼的製程代號等於當前站點（例如：P2 條碼在 P2 站點）
    #    檢查該條碼是否有任何遷出記錄
    #    - 如果有，建議使用遷出功能（可以再次遷出，例如分為良品和不良品）
    #    - 如果沒有，可能是異常情況，建議使用遷入功能
    
    if barcode_process != current_station:
        # 條碼的製程代號不等於當前站點（從上游站點來的條碼）
        # 檢查該條碼在當前站點是否有遷出記錄
        has_out_at_current = sheet_service.has_outbound_record_at_station(request.barcode, current_station)
        
        if has_out_at_current:
            # 該條碼在當前站點已有遷出記錄，建議使用遷出功能
            return {
                "success": True,
                "suggested_action": "outbound",
                "message": f"該條碼在 {current_station} 站點已有遷出記錄，建議使用遷出功能",
                "data": {
                    "barcode": request.barcode,
                    "order": parsed['order'].upper(),
                    "process": process_code,
                    "sku": parsed['sku']
                }
            }
        else:
            # 該條碼在當前站點沒有遷出記錄，建議使用遷入功能
            return {
                "success": True,
                "suggested_action": "inbound",
                "message": f"檢測到 {barcode_process} 製程條碼，在 {current_station} 站點沒有遷出記錄，建議使用遷入功能",
                "data": {
                    "barcode": request.barcode,
                    "order": parsed['order'].upper(),
                    "process": process_code,
                    "sku": parsed['sku']
                }
            }
    else:
        # 條碼的製程代號等於當前站點（可能是同站點的條碼）
        # 檢查該條碼是否有任何遷出記錄
        has_out_record = sheet_service.has_outbound_record(request.barcode)
        
        if has_out_record:
            # 如果有 OUT 記錄，建議使用遷出功能
            return {
                "success": True,
                "suggested_action": "outbound",
                "message": "該條碼已有遷出記錄，建議使用遷出功能",
                "data": {
                    "barcode": request.barcode,
                    "order": parsed['order'].upper(),
                    "process": process_code,
                    "sku": parsed['sku']
                }
            }
        else:
            # 如果沒有 OUT 記錄，建議使用遷入功能
            return {
                "success": True,
                "suggested_action": "inbound",
                "message": "該條碼可以進行遷入",
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
    
    # 準備記錄資料（工單號轉換為大寫）
    log_data = {
        "timestamp": datetime.now(),
        "action": "IN",
        "operator": request.operator_id,
        "order": parsed['order'].upper(),
        "process": curr_station,
        "sku": sku,
        "container": parsed['container'],
        "box_seq": parsed['box_seq'],
        "qty": parsed['qty'],
        "status": parsed['status'],
        "cycle_time": cycle_time,
        "scanned_barcode": request.barcode,
        "new_barcode": ""
    }
    
    # 使用 BackgroundTasks 寫入 Google Sheets（非阻塞）
    background_tasks.add_task(write_to_sheet, log_data)
    
    # 立即回傳成功回應
    return {
        "success": True,
        "message": "遷入成功",
        "data": {
            "order": parsed['order'].upper(),
            "sku": sku,
            "current_station": curr_station,
            "prev_station": prev_station
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
    
    # 準備記錄資料（工單號轉換為大寫）
    log_data = {
        "timestamp": datetime.now(),
        "action": "OUT",
        "operator": request.operator_id,
        "order": parsed['order'].upper(),
        "process": request.current_station_id,
        "sku": parsed['sku'],
        "container": request.container or parsed['container'],
        "box_seq": request.box_seq or parsed['box_seq'],
        "qty": request.qty or parsed['qty'],
        "status": request.status or parsed['status'],
        "cycle_time": cycle_time,
        "scanned_barcode": request.barcode,
        "new_barcode": new_barcode_with_domain
    }
    
    # 使用 BackgroundTasks 寫入 Google Sheets
    background_tasks.add_task(write_to_sheet, log_data)
    
    # 取得下一站建議
    series = BarcodeParser.get_series_from_sku(parsed['sku'])
    next_station = get_next_station(series, request.current_station_id)
    
    # 生成 QR Code SVG（使用包含 domain 的完整 URL）
    qr_svg = QRCodeGenerator.generate_simple_svg(new_barcode_with_domain)
    
    # 立即回傳成功回應
    return {
        "success": True,
        "message": "遷出成功",
        "data": {
            "new_barcode": new_barcode,  # 返回原始條碼（不含 domain）
            "new_barcode_url": new_barcode_with_domain,  # 返回完整 URL（含 domain）
            "order": parsed['order'].upper(),
            "current_station": request.current_station_id,
            "next_station": next_station,
            "qr_code_svg": qr_svg
        }
    }


@app.post("/api/scan/trace")
async def scan_trace(request: TraceRequest):
    """
    追溯查詢 API
    
    根據條碼查詢該工單的時間軸與良率統計
    """
    # 解析條碼
    parsed = BarcodeParser.parse(request.barcode)
    if not parsed:
        raise HTTPException(status_code=400, detail="條碼格式錯誤，無法解析")
    
    # 查詢該工單的所有記錄
    order = parsed['order']
    logs = sheet_service.get_logs_by_order(order)
    
    # 計算良率統計
    total_qty = 0
    good_qty = 0
    for log in logs:
        qty = int(log.get("qty", 0))
        status = log.get("status", "")
        total_qty += qty
        if status == "G":  # 良品
            good_qty += qty
    
    yield_rate = (good_qty / total_qty * 100) if total_qty > 0 else 0
    
    return {
        "success": True,
        "data": {
            "order": order.upper(),
            "sku": parsed['sku'],
            "logs": logs,
            "statistics": {
                "total_qty": total_qty,
                "good_qty": good_qty,
                "yield_rate": round(yield_rate, 2)
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
    # 驗證產品線代號是否存在
    series_dict = config_loader.get_section_dict("series", "Series")
    if request.series_code not in series_dict:
        raise HTTPException(status_code=400, detail=f"無效的產品線代號：{request.series_code}")
    
    # 驗證機種代號是否存在
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
    
    # 準備記錄資料（工單號轉換為大寫）
    log_data = {
        "timestamp": datetime.now(),
        "action": "OUT",
        "operator": request.operator_id,
        "order": order_upper,
        "process": request.current_station_id,
        "sku": sku,
        "container": request.container,
        "box_seq": request.box_seq,
        "qty": request.qty,
        "status": request.status,
        "cycle_time": 0,
        "scanned_barcode": "",
        "new_barcode": new_barcode_with_domain  # 使用包含 domain 的完整 URL
    }
    
    # 使用 BackgroundTasks 寫入 Google Sheets
    background_tasks.add_task(write_to_sheet, log_data)
    
    # 取得下一站建議
    next_station = get_next_station(request.series_code, request.current_station_id)
    
    # 生成 QR Code SVG（使用包含 domain 的完整 URL）
    qr_svg = QRCodeGenerator.generate_simple_svg(new_barcode_with_domain)
    
    return {
        "success": True,
        "message": "首站遷出成功",
        "data": {
            "barcode": barcode,  # 返回原始條碼（不含 domain）
            "barcode_url": new_barcode_with_domain,  # 返回完整 URL（含 domain）
            "order": order_upper,
            "sku": sku,
            "current_station": request.current_station_id,
            "next_station": next_station,
            "qr_code_svg": qr_svg
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

