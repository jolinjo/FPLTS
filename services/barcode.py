"""
條碼處理模組
負責 34 碼條碼的解析、CRC16 校驗以及新條碼生成
"""
import re
from typing import Optional, Dict, Tuple
from datetime import datetime


class BarcodeParser:
    """條碼解析器"""
    
    # 條碼格式：[工單8]-[製程2]-[SKU5]-[容器2]-[箱號2]-[貨態1]-[數量4]-[校驗3]
    BARCODE_PATTERN = re.compile(
        r'^([A-Z0-9]{8})-([A-Z0-9]{2})-([A-Z0-9]{5})-([A-Z0-9]{2})-([0-9]{2})-([A-Z])-([0-9]{4})-([A-Z0-9]{3})$'
    )
    
    @staticmethod
    def parse(barcode: str) -> Optional[Dict[str, str]]:
        """
        解析 34 碼條碼
        
        Args:
            barcode: 34 碼條碼字串
        
        Returns:
            解析後的字典，包含：
            - order: 工單號 (8碼)
            - process: 製程代號 (2碼)
            - sku: SKU (5碼，前2碼為系列，後3碼為機型)
            - container: 容器代號 (2碼)
            - box_seq: 箱號 (2碼)
            - status: 貨態 (1碼)
            - qty: 數量 (4碼)
            - crc: 校驗碼 (3碼)
            若解析失敗則返回 None
        """
        match = BarcodeParser.BARCODE_PATTERN.match(barcode.strip())
        if not match:
            return None
        
        return {
            'order': match.group(1),
            'process': match.group(2),
            'sku': match.group(3),
            'container': match.group(4),
            'box_seq': match.group(5),
            'status': match.group(6),
            'qty': match.group(7),
            'crc': match.group(8)
        }
    
    @staticmethod
    def parse_partial(barcode: str) -> Optional[Dict[str, str]]:
        """
        解析部分條碼（至少包含工單號、製程代號和 SKU）
        用於處理不完整的條碼，特別是 ZZ 製程（新工單）
        
        新工單格式：工單號-ZZ-SKU（例如：251119AB-ZZ-AC001）
        後續欄位（容器、箱號、貨態、數量、校驗碼）為空
        
        Args:
            barcode: 條碼字串（可能不完整，可能包含 b= 前綴）
        
        Returns:
            解析後的字典，至少包含 order、process 和 sku
            其他欄位如果不存在則為空字串
        """
        barcode = barcode.strip()
        
        # 清理可能的 b= 前綴（來自 URL 參數）
        if barcode.startswith('b='):
            barcode = barcode[2:].strip()
        
        # 嘗試用 - 分割
        parts = barcode.split('-')
        
        if len(parts) < 2:
            return None
        
        # 至少要有工單號和製程代號
        order = parts[0].strip()
        process = parts[1].strip()
        
        if not order or not process:
            return None
        
        # 新工單（ZZ 製程）至少需要工單號、製程代號和 SKU
        # 但如果只有工單號和製程代號，也允許（SKU 為空）
        
        # 確保工單號是 8 碼（補零或截斷）
        order = order.upper().ljust(8, '0')[:8]
        # 確保製程代號是 2 碼（但保持 ZZ 為 ZZ，不補零）
        process = process.upper()
        if len(process) < 2:
            process = process.ljust(2, '0')
        elif len(process) > 2:
            process = process[:2]
        
        result = {
            'order': order,
            'process': process,
            'sku': parts[2] if len(parts) > 2 else '',
            'container': parts[3] if len(parts) > 3 else '',
            'box_seq': parts[4] if len(parts) > 4 else '',
            'status': parts[5] if len(parts) > 5 else '',
            'qty': parts[6] if len(parts) > 6 else '',
            'crc': parts[7] if len(parts) > 7 else ''
        }
        
        return result
    
    @staticmethod
    def get_series_from_sku(sku: str) -> str:
        """
        從 SKU 取得產品系列（前2碼）
        
        Args:
            sku: SKU 字串（5碼）
        
        Returns:
            產品系列代號（2碼）
        """
        return sku[:2] if len(sku) >= 2 else ""
    
    @staticmethod
    def get_model_from_sku(sku: str) -> str:
        """
        從 SKU 取得產品機型（後3碼）
        
        Args:
            sku: SKU 字串（5碼）
        
        Returns:
            產品機型代號（3碼）
        """
        return sku[2:5] if len(sku) >= 5 else ""


class CRC16:
    """CRC16 校驗計算"""
    
    @staticmethod
    def calculate(data: str) -> str:
        """
        計算 CRC16 校驗碼
        
        Args:
            data: 要計算校驗碼的資料字串
        
        Returns:
            3碼十六進位校驗碼（大寫）
        """
        # 簡化的 CRC16 計算（使用標準多項式 0x1021）
        crc = 0xFFFF
        polynomial = 0x1021
        
        for byte in data.encode('utf-8'):
            crc ^= (byte << 8)
            for _ in range(8):
                if crc & 0x8000:
                    crc = (crc << 1) ^ polynomial
                else:
                    crc <<= 1
                crc &= 0xFFFF
        
        # 轉換為 3 碼十六進位字串（大寫）
        crc_hex = format(crc, 'X')
        # 確保是 3 碼，不足補 0
        return crc_hex.zfill(3)[-3:]
    
    @staticmethod
    def verify(barcode: str) -> bool:
        """
        驗證條碼的 CRC16 校驗碼
        
        Args:
            barcode: 完整的 34 碼條碼
        
        Returns:
            驗證是否通過
        """
        parsed = BarcodeParser.parse(barcode)
        if not parsed:
            return False
        
        # 取得不含校驗碼的部分（前31碼）
        data_part = barcode[:-4]  # 移除最後的 "-" 和 3碼校驗碼
        calculated_crc = CRC16.calculate(data_part)
        
        return calculated_crc == parsed['crc']


class BarcodeGenerator:
    """條碼生成器"""
    
    @staticmethod
    def generate(
        order: str,
        process: str,
        sku: str,
        container: str,
        box_seq: str,
        status: str,
        qty: str
    ) -> str:
        """
        生成新的 34 碼條碼
        
        Args:
            order: 工單號 (8碼)
            process: 製程代號 (2碼)
            sku: SKU (5碼)
            container: 容器代號 (2碼)
            box_seq: 箱號 (2碼)
            status: 貨態 (1碼)
            qty: 數量 (4碼)
        
        Returns:
            完整的 34 碼條碼字串
        """
        # 格式化各欄位
        order = order.upper().ljust(8, '0')[:8]
        process = process.upper().ljust(2, '0')[:2]
        sku = sku.upper().ljust(5, '0')[:5]
        container = container.upper().ljust(2, '0')[:2]
        box_seq = box_seq.zfill(2)[:2]
        status = status.upper()[:1]
        qty = qty.zfill(4)[:4]
        
        # 組合不含校驗碼的部分
        data_part = f"{order}-{process}-{sku}-{container}-{box_seq}-{status}-{qty}"
        
        # 計算 CRC16 校驗碼
        crc = CRC16.calculate(data_part)
        
        # 組合完整條碼
        barcode = f"{data_part}-{crc}"
        
        return barcode
    
    @staticmethod
    def generate_from_previous(
        previous_barcode: str,
        new_process: str,
        new_container: Optional[str] = None,
        new_box_seq: Optional[str] = None,
        new_status: Optional[str] = None,
        new_qty: Optional[str] = None
    ) -> Optional[str]:
        """
        從舊條碼生成新條碼（遷出時使用）
        
        Args:
            previous_barcode: 舊條碼
            new_process: 新製程代號
            new_container: 新容器代號（若為 None 則沿用舊值）
            new_box_seq: 新箱號（若為 None 則沿用舊值）
            new_status: 新貨態（若為 None 則沿用舊值）
            new_qty: 新數量（若為 None 則沿用舊值）
        
        Returns:
            新條碼字串，若解析失敗則返回 None
        """
        parsed = BarcodeParser.parse(previous_barcode)
        if not parsed:
            return None
        
        return BarcodeGenerator.generate(
            order=parsed['order'],
            process=new_process,
            sku=parsed['sku'],
            container=new_container or parsed['container'],
            box_seq=new_box_seq or parsed['box_seq'],
            status=new_status or parsed['status'],
            qty=new_qty or parsed['qty']
        )

