"""
QR Code 生成器
根據 config/qrcode.ini 設定生成 QR Code SVG
"""
import qrcode
from qrcode.image.svg import SvgPathImage
from typing import Optional
from services.config_loader import config_loader


class QRCodeGenerator:
    """QR Code 生成器類別"""
    
    @staticmethod
    def generate_svg(data: str) -> Optional[str]:
        """
        生成 QR Code SVG 字串
        
        Args:
            data: 要編碼的資料（通常是條碼字串）
        
        Returns:
            SVG 字串，若失敗則返回 None
        """
        try:
            # 從設定檔讀取配置
            size = int(config_loader.get_value("qrcode", "QRCode", "size", "300"))
            error_correction_str = config_loader.get_value("qrcode", "QRCode", "error_correction", "M")
            finder_pattern = config_loader.get_value("qrcode", "QRCode", "finder_pattern", "square")
            logo_ratio = float(config_loader.get_value("qrcode", "QRCode", "logo_ratio", "0.0"))
            
            # 轉換容錯率字串為常數
            error_correction_map = {
                "L": qrcode.constants.ERROR_CORRECT_L,
                "M": qrcode.constants.ERROR_CORRECT_M,
                "Q": qrcode.constants.ERROR_CORRECT_Q,
                "H": qrcode.constants.ERROR_CORRECT_H
            }
            error_correction = error_correction_map.get(error_correction_str.upper(), qrcode.constants.ERROR_CORRECT_M)
            
            # 創建 QR Code 實例
            qr = qrcode.QRCode(
                version=1,
                error_correction=error_correction,
                box_size=10,  # 內部使用，最終大小由 size 控制
                border=4,
            )
            
            # 添加資料
            qr.add_data(data)
            qr.make(fit=True)
            
            # 生成 SVG
            # 使用 SvgPathImage 生成更簡潔的 SVG
            img = qr.make_image(image_factory=SvgPathImage)
            
            # 取得 SVG 字串
            svg_string = img.to_string()
            
            # 調整 SVG 大小
            # 找到 width 和 height 屬性並替換
            import re
            # 計算實際的 box 數量
            matrix_size = qr.modules_count
            # 計算 scale
            scale = size / (matrix_size * 10)  # 10 是 box_size
            
            # 替換 SVG 中的尺寸
            svg_string = re.sub(
                r'width="[^"]*"',
                f'width="{size}"',
                svg_string
            )
            svg_string = re.sub(
                r'height="[^"]*"',
                f'height="{size}"',
                svg_string
            )
            
            # 添加 transform scale（如果需要）
            if scale != 1.0:
                # 在 <svg> 標籤後添加 transform
                svg_string = svg_string.replace(
                    '<svg',
                    f'<svg transform="scale({scale})" transform-origin="0 0"'
                )
            
            # 處理定位點形狀（如果需要）
            if finder_pattern != "square":
                # 這裡可以添加自訂定位點形狀的邏輯
                # 由於 qrcode 庫的限制，我們主要調整 SVG 的樣式
                pass
            
            # 處理 logo（如果需要）
            if logo_ratio > 0:
                # 這裡可以添加 logo 的邏輯
                # 需要額外的圖片處理
                pass
            
            return svg_string
            
        except Exception as e:
            print(f"生成 QR Code SVG 失敗：{e}")
            return None
    
    @staticmethod
    def generate_simple_svg(data: str) -> Optional[str]:
        """
        生成 QR Code SVG
        
        Args:
            data: 要編碼的資料
        
        Returns:
            SVG 字串
        """
        try:
            # 從設定檔讀取配置
            error_correction_str = config_loader.get_value("qrcode", "QRCode", "error_correction", "M")
            size = int(config_loader.get_value("qrcode", "QRCode", "size", "300"))
            
            # 轉換容錯率
            error_correction_map = {
                "L": qrcode.constants.ERROR_CORRECT_L,
                "M": qrcode.constants.ERROR_CORRECT_M,
                "Q": qrcode.constants.ERROR_CORRECT_Q,
                "H": qrcode.constants.ERROR_CORRECT_H
            }
            error_correction = error_correction_map.get(error_correction_str.upper(), qrcode.constants.ERROR_CORRECT_M)
            
            # 計算 box_size（根據目標大小動態調整）
            # 先創建一個臨時 QR code 來獲取模組數量
            temp_qr = qrcode.QRCode(
                version=1,
                error_correction=error_correction,
                box_size=1,
                border=4,
            )
            temp_qr.add_data(data)
            temp_qr.make(fit=True)
            matrix_size = temp_qr.modules_count
            
            # 計算合適的 box_size（考慮 border）
            # border 會增加 4*2 = 8 個模組
            total_modules = matrix_size + 8
            box_size = max(1, size // total_modules)
            
            # 創建實際的 QR Code
            qr = qrcode.QRCode(
                version=None,  # 自動選擇版本
                error_correction=error_correction,
                box_size=box_size,
                border=4,
            )
            qr.add_data(data)
            qr.make(fit=True)
            
            # 生成 SVG
            img = qr.make_image(image_factory=SvgPathImage)
            svg_string = img.to_string()
            
            # 計算實際生成的尺寸
            actual_matrix_size = qr.modules_count
            actual_size = actual_matrix_size * box_size
            
            # 調整 SVG 的 width 和 height
            import re
            svg_string = re.sub(
                r'width="[^"]*"',
                f'width="{size}"',
                svg_string
            )
            svg_string = re.sub(
                r'height="[^"]*"',
                f'height="{size}"',
                svg_string
            )
            
            # 確保有 viewBox
            if 'viewBox' not in svg_string:
                svg_string = svg_string.replace(
                    '<svg',
                    f'<svg viewBox="0 0 {actual_size} {actual_size}"'
                )
            else:
                svg_string = re.sub(
                    r'viewBox="[^"]*"',
                    f'viewBox="0 0 {actual_size} {actual_size}"',
                    svg_string
                )
            
            return svg_string
            
        except Exception as e:
            print(f"生成 QR Code SVG 失敗：{e}")
            import traceback
            traceback.print_exc()
            return None

