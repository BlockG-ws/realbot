import logging
from pathlib import Path
from typing import Any, Dict, Optional, Union

import yaml


def _to_int_chat_id(chat_id: Any) -> Optional[int]:
    """Safely convert chat_id to an integer if applicable, else return None."""
    if isinstance(chat_id, int):
        return chat_id
    if isinstance(chat_id, str):
        s = chat_id.strip()
        if s and (s.isdigit() or (s.startswith("-") and s[1:].isdigit())):
            try:
                return int(s)
            except ValueError:
                return None
    return None


def _extract_enable(val: Any) -> Optional[bool]:
    """Extract boolean enable flag from bool or dict."""
    if isinstance(val, bool):
        return val
    if isinstance(val, dict):
        enable_val = val.get("enable")
        if isinstance(enable_val, bool):
            return enable_val
    return None


def _deep_merge(base: Any, override: Any) -> Any:
    """Recursively merge override into base, ignoring None in override."""
    if override is None:
        return base
    if not isinstance(base, dict) or not isinstance(override, dict):
        return override
    merged = dict(base)
    for k, v in override.items():
        if v is None:
            continue
        if k in merged and isinstance(merged[k], dict) and isinstance(v, dict):
            merged[k] = _deep_merge(merged[k], v)
        else:
            merged[k] = v
    return merged


async def _get_db_feature_config(chat_id: Any, feature_name: str) -> Any:
    """Retrieve a feature config from DB if chat_id is numeric."""
    int_id = _to_int_chat_id(chat_id)
    if int_id is None:
        return None
    try:
        from adapters.db.config import get_config_value

        return await get_config_value(int_id, feature_name)
    except Exception as e:
        logging.warning(
            f"Error reading feature {feature_name} from DB for chat {int_id}: {e}"
        )
        return None


async def _get_db_chat_config(chat_id: Any) -> Dict[str, Any]:
    """Retrieve all feature overrides from DB, excluding model metadata columns."""
    int_id = _to_int_chat_id(chat_id)
    if int_id is None:
        return {}
    try:
        from adapters.db.config import get_config

        raw = await get_config(int_id)
        if not isinstance(raw, dict):
            return {}
        return {
            k: v
            for k, v in raw.items()
            if k not in ("id", "chat_id") and v is not None
        }
    except Exception as e:
        logging.warning(f"Error reading DB config for chat {int_id}: {e}")
        return {}


class Config:
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = Path(config_path)
        self.config_data: Dict[Union[str, int], Any] = self._load_config()

    def _load_config(self) -> Dict[Union[str, int], Any]:
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, "r", encoding="utf-8") as file:
                return yaml.safe_load(file) or {}
        except FileNotFoundError:
            return {}
        except yaml.YAMLError as e:
            logging.error(f"Error loading config file {self.config_path}: {e}")
            return {}

    def get_config_value(self, key: str, default: Any = None) -> Any:
        """Get a configuration value using dot notation (e.g. 'matrix.homeserver')."""
        keys = key.split(".")
        value = self.config_data
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def get(self, key: str, default: Any = None) -> Any:
        """Alias for get_config_value."""
        return self.get_config_value(key, default)

    def get_admin_id(self) -> Optional[int]:
        """Get admin user ID."""
        return self.get_config_value("admin")

    def get_developer_id(self) -> Optional[int]:
        """Get developer user ID."""
        return self.get_config_value("dev")

    def _get_yaml_chat_config(self, chat_id: Any) -> Dict[str, Any]:
        """Get chat-specific configuration dictionary from YAML data."""
        if chat_id is None:
            return {}
        if chat_id in self.config_data and isinstance(self.config_data[chat_id], dict):
            return self.config_data[chat_id]
        str_id = str(chat_id)
        if str_id in self.config_data and isinstance(self.config_data[str_id], dict):
            return self.config_data[str_id]
        int_id = _to_int_chat_id(chat_id)
        if (
            int_id is not None
            and int_id in self.config_data
            and isinstance(self.config_data[int_id], dict)
        ):
            return self.config_data[int_id]
        return {}

    def is_global_feature_enabled(self, feature_name: str) -> bool:
        """Check if a feature is enabled globally in YAML."""
        global_features = self.config_data.get("features", {})
        if not isinstance(global_features, dict):
            return False
        val = global_features.get(feature_name)
        en = _extract_enable(val)
        return en if en is not None else False

    async def is_feature_enabled(
        self, feature_name: str, chat_id: Optional[Union[int, str]] = None
    ) -> bool:
        """
        Check if a feature is enabled for a specific chat or globally.
        Precedence:
          1. Global Kill Switch: If the feature exists in global 'features' and is disabled, return False.
          2. DB override (for numeric chat_id)
          3. YAML group override
          4. Global YAML default
        """
        global_features = self.config_data.get("features", {})
        if isinstance(global_features, dict) and feature_name in global_features:
            if not self.is_global_feature_enabled(feature_name):
                return False

        if not chat_id:
            return self.is_global_feature_enabled(feature_name)

        # 1. DB Override
        db_val = await _get_db_feature_config(chat_id, feature_name)
        en = _extract_enable(db_val)
        if en is not None:
            return en

        # 2. YAML Group Override
        yaml_chat = self._get_yaml_chat_config(chat_id)
        if feature_name in yaml_chat:
            en = _extract_enable(yaml_chat[feature_name])
            if en is not None:
                return en

        # 3. Global Fallback
        return self.is_global_feature_enabled(feature_name)

    async def get_feature_config(
        self, feature_name: str, chat_id: Optional[Union[int, str]] = None
    ) -> Dict[str, Any]:
        """
        Get complete configuration for a feature, merged with global defaults.
        Precedence: Global Default <- YAML Group Override <- DB Override.
        """
        global_features = self.config_data.get("features", {})
        base_raw = (
            global_features.get(feature_name, {})
            if isinstance(global_features, dict)
            else {}
        )
        if isinstance(base_raw, bool):
            base_cfg: Dict[str, Any] = {"enable": base_raw}
        elif isinstance(base_raw, dict):
            base_cfg = dict(base_raw)
        else:
            base_cfg = {}

        if not chat_id:
            return base_cfg

        # YAML Group Override
        yaml_chat = self._get_yaml_chat_config(chat_id)
        yaml_feat = yaml_chat.get(feature_name)
        if isinstance(yaml_feat, bool):
            base_cfg["enable"] = yaml_feat
        elif isinstance(yaml_feat, dict):
            base_cfg = _deep_merge(base_cfg, yaml_feat)

        # DB Override
        db_val = await _get_db_feature_config(chat_id, feature_name)
        if isinstance(db_val, bool):
            base_cfg["enable"] = db_val
        elif isinstance(db_val, dict):
            base_cfg = _deep_merge(base_cfg, db_val)

        return base_cfg

    async def get_group_config(self, chat_id: Union[int, str]) -> Dict[str, Any]:
        """
        Get full effective configuration for a group chat.
        Returns a dictionary mapping feature names to their effective config (bool or dict).
        """
        result: Dict[str, Any] = {}

        # 1. Base from global features
        global_features = self.config_data.get("features", {})
        if isinstance(global_features, dict):
            for feat, val in global_features.items():
                if isinstance(val, dict):
                    if set(val.keys()) == {"enable"}:
                        result[feat] = val.get("enable")
                    else:
                        result[feat] = dict(val)
                else:
                    result[feat] = val

        # 2. Merge YAML group config
        yaml_chat = self._get_yaml_chat_config(chat_id)
        for feat, val in yaml_chat.items():
            norm = (
                val.get("enable")
                if isinstance(val, dict) and set(val.keys()) == {"enable"}
                else val
            )
            if feat in result and isinstance(result[feat], dict) and isinstance(norm, dict):
                result[feat] = _deep_merge(result[feat], norm)
            else:
                result[feat] = norm

        # 3. Merge DB config (metadata excluded)
        db_chat = await _get_db_chat_config(chat_id)
        for feat, val in db_chat.items():
            if feat in result and isinstance(result[feat], dict) and isinstance(val, dict):
                result[feat] = _deep_merge(result[feat], val)
            else:
                result[feat] = val

        return result

    async def update_group_feature(
        self,
        chat_id: Union[int, str],
        feature: str,
        value: Union[bool, str, int, dict],
        sub_key: Optional[str] = None,
    ) -> bool:
        """
        Update a group feature's configuration in the database.
        Returns True on success, False otherwise.
        """
        int_id = _to_int_chat_id(chat_id)
        if int_id is None:
            logging.warning(f"Cannot update config for non-numeric chat_id: {chat_id}")
            return False

        # Guard against updating globally disabled features
        global_features = self.config_data.get("features", {})
        if isinstance(global_features, dict) and feature in global_features:
            if not self.is_global_feature_enabled(feature):
                logging.warning(f"Feature {feature} is globally disabled; update denied.")
                return False

        try:
            from adapters.db.config import update_config_value

            await update_config_value(
                chat_id=int_id, feature=feature, key=sub_key, value=value
            )
            return True
        except Exception as e:
            logging.error(f"Failed to update config for chat {int_id}, feature {feature}: {e}")
            return False


# Global config instance
config = Config()
