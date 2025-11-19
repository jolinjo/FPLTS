"""
設定檔載入器
負責讀取 config/ 目錄下的所有 INI 設定檔
"""
import configparser
import os
from pathlib import Path
from typing import Dict, Optional

# 取得專案根目錄
BASE_DIR = Path(__file__).parent.parent
CONFIG_DIR = BASE_DIR / "config"


class ConfigLoader:
    """設定檔載入器類別"""
    
    def __init__(self):
        self.configs: Dict[str, configparser.ConfigParser] = {}
        self._load_all_configs()
    
    def _load_all_configs(self):
        """載入所有 INI 設定檔"""
        config_files = [
            "process.ini",
            "series.ini",
            "model.ini",
            "flow.ini",
            "container.ini",
            "status.ini",
            "qrcode.ini"
        ]
        
        for config_file in config_files:
            config_path = CONFIG_DIR / config_file
            if config_path.exists():
                parser = configparser.ConfigParser()
                parser.read(config_path, encoding='utf-8')
                # 使用檔案名稱（不含副檔名）作為 key
                key = config_file.replace('.ini', '')
                self.configs[key] = parser
            else:
                print(f"警告：找不到設定檔 {config_path}")
    
    def get_config(self, config_name: str) -> Optional[configparser.ConfigParser]:
        """
        取得指定的設定檔
        
        Args:
            config_name: 設定檔名稱（不含 .ini 副檔名）
        
        Returns:
            ConfigParser 物件，若不存在則返回 None
        """
        return self.configs.get(config_name)
    
    def get_value(self, config_name: str, section: str, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        取得設定檔中的特定值
        
        Args:
            config_name: 設定檔名稱（不含 .ini 副檔名）
            section: 區段名稱
            key: 鍵值
            default: 預設值
        
        Returns:
            設定值，若不存在則返回 default
        """
        config = self.get_config(config_name)
        if config and config.has_option(section, key):
            return config.get(section, key)
        return default
    
    def get_section_dict(self, config_name: str, section: str) -> Dict[str, str]:
        """
        取得設定檔中整個區段的字典
        
        Args:
            config_name: 設定檔名稱（不含 .ini 副檔名）
            section: 區段名稱
        
        Returns:
            區段的所有鍵值對字典
        """
        config = self.get_config(config_name)
        if config and config.has_section(section):
            return dict(config.items(section))
        return {}


# 全域單例實例
config_loader = ConfigLoader()

