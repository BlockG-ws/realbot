import yaml
from typing import Dict, Any, Optional, Union
from pathlib import Path


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

    def is_feature_enabled(self, feature_name: str, chat_id: Optional[int] = None) -> bool:
        """
        Check if a feature is enabled for a specific chat or globally

        Args:
            feature_name: Name of the feature (e.g., 'actions', 'bitflip', 'link')
            chat_id: Chat ID to check group-specific settings (optional)

        Returns:
            bool: True if feature is enabled, False otherwise
        """
        # Check group-specific settings first
        if chat_id:
            group_config = self.config_data.get(chat_id, {})
            if feature_name in group_config:
                return group_config[feature_name].get('enable', False)

        # Fall back to global settings
        global_features = self.config_data.get('features', {})
        feature_config = global_features.get(feature_name, {})
        return feature_config.get('enable', False)

    def get_feature_config(self, feature_name: str, chat_id: Optional[int] = None) -> Dict[str, Any]:
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
            group_config = self.config_data.get(chat_id, {})
            if feature_name in group_config:
                return group_config[feature_name]

        # Fall back to global settings
        global_features = self.config_data.get('features', {})
        return global_features.get(feature_name, {})


# Global config instance
config = Config()