from adapters.db.models import Config
from adapters.db.models import ChannelWhiteList

async def get_config(chat_id: int) -> dict:
    """Retrieve configuration for a specific chat_id."""
    config = await Config.get_or_none(chat_id=chat_id).values()
    return config

async def get_config_value(chat_id: int, key: str) -> bool | dict | None:
    """Retrieve a specific configuration value for a chat_id."""
    config = await Config.get_or_none(chat_id=chat_id)
    if config:
        return getattr(config, key, None)
    return None

async def update_config_value(chat_id: int, feature: str, key: str | None, value: bool | str) -> None:
    """Update config for a chat_id."""
    config, created = await Config.get_or_create(chat_id=chat_id)
    if not key and isinstance(value, bool):
        setattr(config, feature, value)
        await config.save()
        return
    elif key and isinstance(value, (bool, str)):
        feature_config = getattr(config, feature) or {}
        if isinstance(feature_config, dict):
            feature_config[key] = value
            setattr(config, feature, feature_config)
            await config.save()
            return