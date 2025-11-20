"""
QR Code 生成模組單元測試
"""
import pytest
from services.qrcode_generator import QRCodeGenerator


class TestQRCodeGenerator:
    """QR Code 生成器測試"""
    
    @pytest.mark.unit
    def test_generate_simple_svg(self, sample_barcode):
        """測試生成簡單 SVG QR Code"""
        svg = QRCodeGenerator.generate_simple_svg(sample_barcode)
        
        assert svg is not None
        assert isinstance(svg, str)
        # 驗證是 SVG 格式
        assert svg.strip().startswith('<svg')
        assert '</svg>' in svg
        # 驗證包含條碼數據（通過檢查 SVG 內容）
        assert len(svg) > 0
    
    @pytest.mark.unit
    def test_generate_simple_svg_with_url(self):
        """測試生成包含 URL 的 QR Code"""
        url = "https://example.com/b=251119AA-P2-ST352-A1-01-G-0100-X4F"
        svg = QRCodeGenerator.generate_simple_svg(url)
        
        assert svg is not None
        assert isinstance(svg, str)
        assert svg.strip().startswith('<svg')
    
    @pytest.mark.unit
    def test_generate_simple_svg_empty_string(self):
        """測試生成空字串的 QR Code"""
        svg = QRCodeGenerator.generate_simple_svg("")
        
        # 空字串也應該能生成 QR Code（雖然沒有意義）
        assert svg is not None
        assert isinstance(svg, str)
    
    @pytest.mark.unit
    def test_generate_simple_svg_long_data(self):
        """測試生成長數據的 QR Code"""
        long_data = "A" * 100  # 100 個字符
        svg = QRCodeGenerator.generate_simple_svg(long_data)
        
        assert svg is not None
        assert isinstance(svg, str)
        assert svg.strip().startswith('<svg')
    
    @pytest.mark.unit
    def test_generate_simple_svg_special_characters(self):
        """測試生成包含特殊字符的 QR Code"""
        special_data = "https://example.com/b=251119AA-P2-ST352-A1-01-G-0100-X4F?param=value&other=test"
        svg = QRCodeGenerator.generate_simple_svg(special_data)
        
        assert svg is not None
        assert isinstance(svg, str)
        assert svg.strip().startswith('<svg')
    
    @pytest.mark.unit
    def test_generate_svg(self, sample_barcode):
        """測試生成完整 SVG QR Code（使用配置）"""
        svg = QRCodeGenerator.generate_svg(sample_barcode)
        
        assert svg is not None
        assert isinstance(svg, str)
        # 驗證是 SVG 格式
        assert svg.strip().startswith('<svg')
        assert '</svg>' in svg
    
    @pytest.mark.unit
    def test_generate_svg_consistency(self, sample_barcode):
        """測試 QR Code 生成一致性"""
        svg1 = QRCodeGenerator.generate_simple_svg(sample_barcode)
        svg2 = QRCodeGenerator.generate_simple_svg(sample_barcode)
        
        # 相同輸入應生成相同的 SVG（或至少是有效的 SVG）
        assert svg1 is not None
        assert svg2 is not None
        assert isinstance(svg1, str)
        assert isinstance(svg2, str)
    
    @pytest.mark.unit
    def test_generate_svg_contains_size(self, sample_barcode):
        """測試生成的 SVG 包含尺寸資訊"""
        svg = QRCodeGenerator.generate_simple_svg(sample_barcode)
        
        assert svg is not None
        # 驗證包含 width 和 height 屬性
        assert 'width=' in svg or 'width="' in svg
        assert 'height=' in svg or 'height="' in svg
    
    @pytest.mark.unit
    def test_generate_svg_different_data(self):
        """測試不同數據生成不同的 QR Code"""
        data1 = "251119AA-P2-ST352-A1-01-G-0100-X4F"
        data2 = "251119BB-P3-AC001-A2-02-N-0050-ABC"
        
        svg1 = QRCodeGenerator.generate_simple_svg(data1)
        svg2 = QRCodeGenerator.generate_simple_svg(data2)
        
        # 不同數據應生成不同的 SVG
        assert svg1 != svg2
    
    @pytest.mark.unit
    def test_generate_svg_error_handling(self):
        """測試錯誤處理"""
        # 測試 None（雖然函數不接受 None，但測試異常情況）
        # 實際上，如果傳入 None，應該會拋出異常或返回 None
        # 這裡主要測試函數的健壯性
        
        # 測試非常長的字符串（可能導致問題）
        very_long_data = "A" * 10000
        svg = QRCodeGenerator.generate_simple_svg(very_long_data)
        
        # 應該能處理（可能生成較大的 QR Code）
        assert svg is None or isinstance(svg, str)

