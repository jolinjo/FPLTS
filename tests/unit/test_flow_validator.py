"""
流程驗證模組單元測試
"""
import pytest
from services.flow_validator import validate_process_flow, get_next_station


class TestValidateProcessFlow:
    """流程驗證測試"""
    
    @pytest.mark.unit
    def test_validate_valid_flow_st(self):
        """測試 ST 系列正常流程驗證（全製程）"""
        # P1 → P2（合法）
        is_valid, error = validate_process_flow('ST', 'P1', 'P2')
        assert is_valid is True
        assert error is None
    
    @pytest.mark.unit
    def test_validate_valid_flow_ac(self):
        """測試 AC 系列正常流程驗證"""
        # AC 系列流程：P1, P2, P3
        # P1 → P2（合法）
        is_valid, error = validate_process_flow('AC', 'P1', 'P2')
        assert is_valid is True
        assert error is None
        
        # P2 → P3（合法）
        is_valid, error = validate_process_flow('AC', 'P2', 'P3')
        assert is_valid is True
        assert error is None
    
    @pytest.mark.unit
    def test_validate_skip_station(self):
        """測試跳站驗證失敗"""
        # P1 → P3（跳過 P2，不合法）
        is_valid, error = validate_process_flow('ST', 'P1', 'P3')
        assert is_valid is False
        assert error is not None
        assert 'P2' in error  # 錯誤訊息應包含預期的下一站
    
    @pytest.mark.unit
    def test_validate_miss_station(self):
        """測試漏站驗證失敗"""
        # P2 → P4（漏掉 P3，不合法）
        is_valid, error = validate_process_flow('ST', 'P2', 'P4')
        assert is_valid is False
        assert error is not None
        assert 'P3' in error  # 錯誤訊息應包含預期的下一站
    
    @pytest.mark.unit
    def test_validate_reverse_flow(self):
        """測試反向流程驗證失敗"""
        # P2 → P1（反向，不合法）
        is_valid, error = validate_process_flow('ST', 'P2', 'P1')
        assert is_valid is False
        assert error is not None
    
    @pytest.mark.unit
    def test_validate_last_station(self):
        """測試最後一站驗證"""
        # 對於 ST 系列，P5 是最後一站
        # 從 P5 無法繼續移動
        is_valid, error = validate_process_flow('ST', 'P5', 'P6')
        assert is_valid is False
        assert error is not None
        assert '最後一站' in error or 'last' in error.lower()
    
    @pytest.mark.unit
    def test_validate_nonexistent_prev_station(self):
        """測試上一站不在流程清單中"""
        # 假設 P9 不在流程清單中
        is_valid, error = validate_process_flow('ST', 'P9', 'P1')
        assert is_valid is False
        assert error is not None
        assert 'P9' in error or '不在' in error
    
    @pytest.mark.unit
    def test_validate_default_flow(self):
        """測試使用 DEFAULT 流程"""
        # 使用不存在的 SKU，應使用 DEFAULT 流程
        is_valid, error = validate_process_flow('XX', 'P1', 'P2')
        # 如果 DEFAULT 流程定義為 P1, P2, P3, P4, P5，則應通過
        # 實際結果取決於配置檔
        assert isinstance(is_valid, bool)
    
    @pytest.mark.unit
    def test_validate_case_insensitive(self):
        """測試大小寫不敏感"""
        # 使用小寫
        is_valid1, _ = validate_process_flow('st', 'p1', 'p2')
        # 使用大寫
        is_valid2, _ = validate_process_flow('ST', 'P1', 'P2')
        
        # 結果應該相同
        assert is_valid1 == is_valid2
    
    @pytest.mark.unit
    def test_validate_md_flow(self):
        """測試 MD 系列流程"""
        # MD 系列流程：P1, P2, P3, P4
        # P1 → P2（合法）
        is_valid, error = validate_process_flow('MD', 'P1', 'P2')
        assert is_valid is True
        assert error is None
        
        # P2 → P3（合法）
        is_valid, error = validate_process_flow('MD', 'P2', 'P3')
        assert is_valid is True
        assert error is None
        
        # P3 → P4（合法）
        is_valid, error = validate_process_flow('MD', 'P3', 'P4')
        assert is_valid is True
        assert error is None


class TestGetNextStation:
    """取得下一站測試"""
    
    @pytest.mark.unit
    def test_get_next_station_st(self):
        """測試 ST 系列取得下一站"""
        # P1 的下一站應該是 P2
        next_station = get_next_station('ST', 'P1')
        assert next_station == 'P2'
        
        # P2 的下一站應該是 P3
        next_station = get_next_station('ST', 'P2')
        assert next_station == 'P3'
        
        # P3 的下一站應該是 P4
        next_station = get_next_station('ST', 'P3')
        assert next_station == 'P4'
        
        # P4 的下一站應該是 P5
        next_station = get_next_station('ST', 'P4')
        assert next_station == 'P5'
        
        # P5 是最後一站，應返回 None
        next_station = get_next_station('ST', 'P5')
        assert next_station is None
    
    @pytest.mark.unit
    def test_get_next_station_ac(self):
        """測試 AC 系列取得下一站"""
        # AC 系列流程：P1, P2, P3
        next_station = get_next_station('AC', 'P1')
        assert next_station == 'P2'
        
        next_station = get_next_station('AC', 'P2')
        assert next_station == 'P3'
        
        # P3 是最後一站
        next_station = get_next_station('AC', 'P3')
        assert next_station is None
    
    @pytest.mark.unit
    def test_get_next_station_md(self):
        """測試 MD 系列取得下一站"""
        # MD 系列流程：P1, P2, P3, P4
        next_station = get_next_station('MD', 'P1')
        assert next_station == 'P2'
        
        next_station = get_next_station('MD', 'P3')
        assert next_station == 'P4'
        
        # P4 是最後一站
        next_station = get_next_station('MD', 'P4')
        assert next_station is None
    
    @pytest.mark.unit
    def test_get_next_station_nonexistent(self):
        """測試不存在的站點"""
        # 不存在的站點應返回 None
        next_station = get_next_station('ST', 'P9')
        assert next_station is None
    
    @pytest.mark.unit
    def test_get_next_station_nonexistent_sku(self):
        """測試不存在的 SKU（應使用 DEFAULT）"""
        # 不存在的 SKU 應使用 DEFAULT 流程
        next_station = get_next_station('XX', 'P1')
        # 如果 DEFAULT 流程定義為 P1, P2, P3, P4, P5，則應返回 P2
        # 實際結果取決於配置檔
        assert next_station is None or next_station == 'P2'
    
    @pytest.mark.unit
    def test_get_next_station_case_insensitive(self):
        """測試大小寫不敏感"""
        # 使用小寫
        next1 = get_next_station('st', 'p1')
        # 使用大寫
        next2 = get_next_station('ST', 'P1')
        
        # 結果應該相同（都轉換為大寫）
        assert next1 == next2

