import logging

import yaml
from typing import Dict, Any, Optional, Union
from pathlib import Path

from adapters.db.config import get_config_value, get_config


class Config:
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = Path(config_path)
        self.config_data = self._load_config()

    def _load_config(self) ->  Dict[Union[str, int], Any]:
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file) or {}
        except FileNotFoundError:
            return {}
        except yaml.YAMLError as e:
            print(f"Error loading config: {e}")
            return {}

    def get_admin_id(self) -> Optional[int]:
        """Get admin user ID"""
        return self.config_data.get('admin')

    def get_developer_id(self) -> Optional[int]:
        """Get developer user ID"""
        return self.config_data.get('dev')

    def get_config_value(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by key

        Args:
            key: Configuration key to retrieve
            default: Default value if key is not found

        Returns:
            The configuration value or default if not found
        """
        keys = key.split('.')
        value = self.config_data

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def is_global_feature_enabled(self, feature_name: str) -> bool:
        """
        Check if a feature is globally enabled

        Args:
            feature_name: Name of the feature (e.g., 'actions', 'bitflip', 'link')
        Returns:
            bool: True if feature is enabled, False otherwise
        """
        global_features = self.config_data.get('features', {})
        feature_config = global_features.get(feature_name, {})
        return feature_config.get('enable', False)

    async def get_group_config(self, chat_id: int) -> None | dict[str, Any] | dict[Any, Any] | dict:
        """
        Get configuration for a specific group chat

        Args:
            chat_id: Chat ID of the group
        Returns:
            dict: Group configuration
        """

        def _fill_none(primary: Dict[str, Any], fallback: Dict[str, Any]) -> Dict[str, Any]:
            if not isinstance(primary, dict):
                return primary if primary is not None else fallback
            result: Dict[str, Any] = {}
            for k, v in primary.items():
                fb = fallback.get(k) if isinstance(fallback, dict) else None
                if isinstance(v, dict) and isinstance(fb, dict):
                    result[k] = _fill_none(v, fb)
                else:
                    result[k] = v if v is not None else fb
            # include keys only present in fallback
            if isinstance(fallback, dict):
                for k, v in fallback.items():
                    if k not in result:
                        result[k] = v
            return result

        def _normalize_enabled_dicts(cfg: Any) -> Any:
            """
            Convert dicts of the form {'enable': bool} into the bool value,
            and recurse into nested dicts to normalize values.
            """
            if not isinstance(cfg, dict):
                return cfg
            normalized: Dict[Any, Any] = {}
            for k, v in cfg.items():
                if isinstance(v, dict) and set(v.keys()) == {"enable"}:
                    normalized[k] = v.get("enable")
                else:
                    normalized[k] = v
            return normalized

        try:
            db_config = await get_config(chat_id)
            file_cfg = self.config_data.get(chat_id, {}) or self.config_data.get(str(chat_id),{})
            file_cfg = _normalize_enabled_dicts(file_cfg)
            if not db_config:
                if file_cfg:
                    global_features = self.config_data.get('features', {})
                    global_features = _normalize_enabled_dicts(global_features)
                    return _fill_none(file_cfg, global_features)
                # Fallback to global features if neither DB nor file has group config
                return self.config_data.get('features', {})
            else:
                global_features = self.config_data.get('features', {})
                global_features = _normalize_enabled_dicts(global_features)
                if file_cfg:
                    db_config = _fill_none(db_config, file_cfg)
                    db_config = _fill_none(db_config, global_features)
                    return db_config
                else:
                    db_config = _fill_none(db_config, global_features)
            return db_config
        except Exception as e:
            logging.warning(f"获取群组 {chat_id} 配置时出错",e)

    async def is_feature_enabled(self, feature_name: str, chat_id: Optional[int] = None) -> bool:
        """
        Check if a feature is enabled for a specific chat or globally

        Args:
            feature_name: Name of the feature (e.g., 'actions', 'bitflip', 'link')
            chat_id: Chat ID to check group-specific settings (optional)

        Returns:
            bool: True if feature is enabled, False otherwise
        """
        # 先检查全局设置
        if not self.is_global_feature_enabled(feature_name):
            return False
        # Check group-specific settings first
        if chat_id:
            try:
                is_enabled = await get_config_value(chat_id, feature_name)
                if isinstance(is_enabled, bool):
                    return is_enabled
                elif isinstance(is_enabled, dict):
                    return is_enabled.get('enable', False)
            except Exception:
                logging.warning(f"从数据库获取 {feature_name} 配置时出错，使用文件配置作为后备")
            group_config = self.config_data.get(chat_id, {})
            if feature_name in group_config:
                return group_config[feature_name].get('enable', False)
        return False


    async def get_feature_config(self, feature_name: str, chat_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Get complete configuration for a feature

        Args:
            feature_name: Name of the feature
            chat_id: Chat ID to check group-specific settings (optional)

        Returns:
            dict: Feature configuration
        """
        # Check group-specific settings first
        if chat_id:
            db_config = await get_config_value(chat_id, feature_name)
            if isinstance(db_config, dict):
                return db_config
            group_config = self.config_data.get(chat_id, {})
            if feature_name in group_config:
                return group_config[feature_name]

        # Fall back to global settings
        global_features = self.config_data.get('features', {})
        return global_features.get(feature_name, {})


# Global config instance
config = Config()