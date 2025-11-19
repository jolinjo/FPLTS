"""
流程驗證器
負責驗證產品從上一站移動到當前站點是否合法
"""
from typing import Tuple, Optional
from services.config_loader import config_loader


def validate_process_flow(sku: str, prev_station: str, curr_station: str) -> Tuple[bool, Optional[str]]:
    """
    驗證產品從上一站移動到當前站點是否合法
    
    Args:
        sku: 產品 SKU（前2碼，例如 'ST', 'AC', 'MD'）
        prev_station: 上一站製程代號（例如 'P1', 'P2'）
        curr_station: 當前站製程代號（例如 'P2', 'P3'）
    
    Returns:
        Tuple[bool, Optional[str]]: 
            - 第一個值：驗證是否通過（True=合法, False=不合法）
            - 第二個值：錯誤訊息（若驗證失敗）
    """
    # 讀取 flow.ini
    flow_config = config_loader.get_config('flow')
    if not flow_config:
        return False, "無法讀取流程設定檔 flow.ini"
    
    # 取得該 SKU 的流程清單，若不存在則使用 DEFAULT
    flow_section = flow_config.get('Flow', sku, fallback=None)
    if not flow_section:
        flow_section = flow_config.get('Flow', 'DEFAULT', fallback='')
    
    if not flow_section:
        return False, f"找不到 SKU {sku} 的流程定義，且無預設流程"
    
    # 統一轉換為大寫進行比較
    prev_station_upper = prev_station.upper()
    curr_station_upper = curr_station.upper()
    
    # 解析流程清單（例如 "P1, P2, P3, P4, P5"），並統一轉換為大寫
    flow_list = [station.strip().upper() for station in flow_section.split(',')]
    
    # 檢查上一站是否在流程清單中
    if prev_station_upper not in flow_list:
        return False, f"上一站 {prev_station} 不在 SKU {sku} 的流程清單中"
    
    # 取得上一站在流程清單中的索引
    prev_index = flow_list.index(prev_station_upper)
    
    # 檢查當前站是否為上一站的合法下一站
    if prev_index + 1 >= len(flow_list):
        # 上一站已經是最後一站
        return False, f"上一站 {prev_station} 已經是流程的最後一站，無法繼續移動"
    
    expected_next_station = flow_list[prev_index + 1]
    
    if curr_station_upper != expected_next_station:
        # 跳站或錯誤的站點
        return False, f"錯誤！{prev_station} 後續應為 {expected_next_station}，不可跳至 {curr_station}"
    
    # 驗證通過
    return True, None


def get_next_station(sku: str, current_station: str) -> Optional[str]:
    """
    取得指定 SKU 和當前站點的下一個站點
    
    Args:
        sku: 產品 SKU（前2碼）
        current_station: 當前站製程代號
    
    Returns:
        下一個站點代號，若不存在則返回 None
    """
    flow_config = config_loader.get_config('flow')
    if not flow_config:
        return None
    
    # 取得該 SKU 的流程清單
    flow_section = flow_config.get('Flow', sku, fallback=None)
    if not flow_section:
        flow_section = flow_config.get('Flow', 'DEFAULT', fallback='')
    
    if not flow_section:
        return None
    
    # 統一轉換為大寫進行比較
    current_station_upper = current_station.upper()
    
    # 解析流程清單，並統一轉換為大寫
    flow_list = [station.strip().upper() for station in flow_section.split(',')]
    
    # 檢查當前站在流程清單中的位置
    if current_station_upper not in flow_list:
        return None
    
    current_index = flow_list.index(current_station_upper)
    
    # 取得下一站
    if current_index + 1 < len(flow_list):
        return flow_list[current_index + 1]
    
    return None

