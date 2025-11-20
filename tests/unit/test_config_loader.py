"""
配置載入模組單元測試
"""
import pytest
from services.config_loader import config_loader


class TestConfigLoader:
    """配置載入器測試"""
    
    @pytest.mark.unit
    def test_load_all_configs(self):
        """測試所有配置檔載入"""
        # 驗證主要配置檔都已載入
        assert config_loader.get_config('process') is not None
        assert config_loader.get_config('series') is not None
        assert config_loader.get_config('model') is not None
        assert config_loader.get_config('flow') is not None
        assert config_loader.get_config('container') is not None
        assert config_loader.get_config('status') is not None
        assert config_loader.get_config('qrcode') is not None
        assert config_loader.get_config('settings') is not None
    
    @pytest.mark.unit
    def test_get_config_nonexistent(self):
        """測試取得不存在的配置檔"""
        result = config_loader.get_config('nonexistent')
        assert result is None
    
    @pytest.mark.unit
    def test_get_value_process(self):
        """測試讀取製程配置值"""
        value = config_loader.get_value('process', 'Process', 'P1')
        assert value is not None
        assert isinstance(value, str)
    
    @pytest.mark.unit
    def test_get_value_series(self):
        """測試讀取產品系列配置值"""
        value = config_loader.get_value('series', 'Series', 'ST')
        assert value is not None
        assert isinstance(value, str)
    
    @pytest.mark.unit
    def test_get_value_model(self):
        """測試讀取機種配置值"""
        value = config_loader.get_value('model', 'Model', '350')
        assert value is not None
        assert isinstance(value, str)
    
    @pytest.mark.unit
    def test_get_value_flow(self):
        """測試讀取流程配置值"""
        value = config_loader.get_value('flow', 'Flow', 'ST')
        assert value is not None
        # 流程應該是逗號分隔的站點列表
        assert ',' in value
    
    @pytest.mark.unit
    def test_get_value_default(self):
        """測試讀取不存在的鍵值時返回預設值"""
        default_value = "DEFAULT_VALUE"
        result = config_loader.get_value(
            'process', 'Process', 'NONEXISTENT', default=default_value
        )
        assert result == default_value
    
    @pytest.mark.unit
    def test_get_section_dict_process(self):
        """測試取得製程區段字典"""
        process_dict = config_loader.get_section_dict('process', 'Process')
        assert isinstance(process_dict, dict)
        assert len(process_dict) > 0
        # 驗證包含常見的製程站點
        assert 'P1' in process_dict or 'p1' in process_dict
    
    @pytest.mark.unit
    def test_get_section_dict_series(self):
        """測試取得產品系列區段字典"""
        series_dict = config_loader.get_section_dict('series', 'Series')
        assert isinstance(series_dict, dict)
        assert len(series_dict) > 0
    
    @pytest.mark.unit
    def test_get_section_dict_model(self):
        """測試取得機種區段字典"""
        model_dict = config_loader.get_section_dict('model', 'Model')
        assert isinstance(model_dict, dict)
        assert len(model_dict) > 0
    
    @pytest.mark.unit
    def test_get_section_dict_flow(self):
        """測試取得流程區段字典"""
        flow_dict = config_loader.get_section_dict('flow', 'Flow')
        assert isinstance(flow_dict, dict)
        assert len(flow_dict) > 0
        # 驗證包含 DEFAULT（注意：ConfigParser 會將鍵轉為小寫）
        assert 'DEFAULT' in flow_dict or 'default' in flow_dict
    
    @pytest.mark.unit
    def test_get_section_dict_container(self):
        """測試取得容器區段字典"""
        container_dict = config_loader.get_section_dict('container', 'Container')
        assert isinstance(container_dict, dict)
        assert len(container_dict) > 0
    
    @pytest.mark.unit
    def test_get_section_dict_status(self):
        """測試取得貨態區段字典"""
        status_dict = config_loader.get_section_dict('status', 'Status')
        assert isinstance(status_dict, dict)
        assert len(status_dict) > 0
        # 驗證包含常見的貨態
        assert 'G' in status_dict or 'g' in status_dict
    
    @pytest.mark.unit
    def test_get_section_dict_nonexistent(self):
        """測試取得不存在的區段字典"""
        result = config_loader.get_section_dict('nonexistent', 'Section')
        assert result == {}
    
    @pytest.mark.unit
    def test_get_section_dict_nonexistent_config(self):
        """測試從不存在的配置檔取得區段字典"""
        result = config_loader.get_section_dict('nonexistent', 'Section')
        assert result == {}
    
    @pytest.mark.unit
    def test_qrcode_config(self):
        """測試 QR Code 配置"""
        size = config_loader.get_value('qrcode', 'QRCode', 'size', '300')
        assert size is not None
        # 驗證是數字字串
        assert size.isdigit()
        
        error_correction = config_loader.get_value('qrcode', 'QRCode', 'error_correction', 'M')
        assert error_correction is not None
        assert error_correction.upper() in ['L', 'M', 'Q', 'H']
    
    @pytest.mark.unit
    def test_settings_config(self):
        """測試設定檔配置"""
        # settings.ini 可能包含 domain 等設定
        domain = config_loader.get_value('settings', 'Settings', 'domain', '')
        # domain 可能是空字串或有效 URL
        assert isinstance(domain, str)

