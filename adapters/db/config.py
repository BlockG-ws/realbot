from typing import Any, Optional, Union
from adapters.db.models import Config


async def get_config(chat_id: int) -> dict:
    """Retrieve configuration for a specific chat_id."""
    config = await Config.get_or_none(chat_id=chat_id).values()
    return config or {}


async def get_config_value(chat_id: int, key: str) -> bool | dict | None:
    """Retrieve a specific configuration value for a chat_id."""
    config = await Config.get_or_none(chat_id=chat_id)
    if config:
        return getattr(config, key, None)
    return None


async def update_config_value(
    chat_id: int,
    feature: str,
    key: Optional[str],
    value: Union[bool, str, int, dict, Any],
) -> None:
    """Update config for a chat_id in database."""
    config, _ = await Config.get_or_create(chat_id=chat_id)
    if not key:
        setattr(config, feature, value)
        await config.save()
        return

    feature_config = getattr(config, feature) or {}
    if isinstance(feature_config, dict):
        new_config = dict(feature_config)
        new_config[key] = value
        setattr(config, feature, new_config)
        await config.save()
