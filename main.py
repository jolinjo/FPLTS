"""
FastAPI 應用程式入口
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import os
from dotenv import load_dotenv

from services.barcode import BarcodeParser, BarcodeGenerator, CRC16
from services.flow_validator import validate_process_flow, get_next_station
from services.sheet import sheet_service
from services.config_loader import config_loader

load_dotenv()

app = FastAPI(title="工廠製程物流追溯與分析系統", version="0.0.1")

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
        "new_barcode": new_barcode
    }
    
    # 使用 BackgroundTasks 寫入 Google Sheets
    background_tasks.add_task(write_to_sheet, log_data)
    
    # 取得下一站建議
    series = BarcodeParser.get_series_from_sku(parsed['sku'])
    next_station = get_next_station(series, request.current_station_id)
    
    # 立即回傳成功回應
    return {
        "success": True,
        "message": "遷出成功",
        "data": {
            "new_barcode": new_barcode,
            "order": parsed['order'].upper(),
            "current_station": request.current_station_id,
            "next_station": next_station
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
        "new_barcode": barcode
    }
    
    # 使用 BackgroundTasks 寫入 Google Sheets
    background_tasks.add_task(write_to_sheet, log_data)
    
    # 取得下一站建議
    next_station = get_next_station(request.series_code, request.current_station_id)
    
    return {
        "success": True,
        "message": "首站遷出成功",
        "data": {
            "barcode": barcode,
            "order": order_upper,
            "sku": sku,
            "current_station": request.current_station_id,
            "next_station": next_station
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

