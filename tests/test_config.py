import asyncio
import os
import tempfile
import unittest
import yaml
from pathlib import Path
from tortoise import Tortoise

from adapters.db.models import Config as DbConfig
from config import Config, config as global_config
from unittest.mock import AsyncMock, MagicMock
from core.cfg import handle_config_command


TEST_CONFIG_YAML = """
admin: 123456789
dev: 616760897

start_telegram_bot: true
also_start_matrix_bot: false

matrix:
  homeserver: "https://matrix.org"
  user_id: "@bot:matrix.org"

features:
  actions:
    enable: true
  bitflip:
    enable: true
  link:
    enable: true
  unpin:
    enable: true
    regex: "#default"
  welcome:
    enable: true
    message: "欢迎新人"
  disabled_feature:
    enable: false

-1001111111111:
  actions:
    enable: false
  unpin:
    regex: "#group_pin"

"!test_room:matrix.org":
  copy_notice_event: true
  actions: false
"""


class TestConfig(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # Set up a temporary yaml config file
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_path = Path(self.temp_dir.name) / "test_config.yaml"
        with open(self.config_path, "w", encoding="utf-8") as f:
            f.write(TEST_CONFIG_YAML)

        # Initialize Tortoise DB in memory
        await Tortoise.init(
            db_url="sqlite://:memory:",
            modules={"models": ["adapters.db.models"]},
        )
        await Tortoise.generate_schemas()

        # Instantiate Config
        self.config = Config(config_path=str(self.config_path))

    async def asyncTearDown(self):
        await Tortoise.close_connections()
        self.temp_dir.cleanup()

    def test_basic_values(self):
        self.assertEqual(self.config.get_admin_id(), 123456789)
        self.assertEqual(self.config.get_developer_id(), 616760897)
        self.assertEqual(self.config.get_config_value("matrix.homeserver"), "https://matrix.org")
        self.assertEqual(self.config.get_config_value("nonexistent.key", 999), 999)
        self.assertTrue(self.config.get_config_value("start_telegram_bot"))

    def test_is_global_feature_enabled(self):
        self.assertTrue(self.config.is_global_feature_enabled("actions"))
        self.assertTrue(self.config.is_global_feature_enabled("welcome"))
        self.assertFalse(self.config.is_global_feature_enabled("disabled_feature"))
        self.assertFalse(self.config.is_global_feature_enabled("nonexistent"))

    async def test_is_feature_enabled_global_fallback(self):
        # Default global feature without chat_id or in group without override
        self.assertTrue(await self.config.is_feature_enabled("actions"))
        self.assertTrue(await self.config.is_feature_enabled("actions", chat_id=12345))
        # Globally disabled feature remains disabled
        self.assertFalse(await self.config.is_feature_enabled("disabled_feature", chat_id=12345))

    async def test_is_feature_enabled_yaml_group_override(self):
        # In YAML, -1001111111111 has actions: enable: false
        self.assertFalse(await self.config.is_feature_enabled("actions", chat_id=-1001111111111))
        self.assertFalse(await self.config.is_feature_enabled("actions", chat_id="-1001111111111"))

    async def test_is_feature_enabled_matrix_room(self):
        # Matrix room string ID
        room_id = "!test_room:matrix.org"
        self.assertFalse(await self.config.is_feature_enabled("actions", chat_id=room_id))
        self.assertTrue(await self.config.is_feature_enabled("copy_notice_event", chat_id=room_id))

    async def test_is_feature_enabled_db_override(self):
        chat_id = -1002222222222
        # Default is true
        self.assertTrue(await self.config.is_feature_enabled("bitflip", chat_id=chat_id))

        # Add DB override
        await DbConfig.create(chat_id=chat_id, bitflip=False)
        self.assertFalse(await self.config.is_feature_enabled("bitflip", chat_id=chat_id))

    async def test_get_feature_config(self):
        # Global default
        cfg = await self.config.get_feature_config("unpin")
        self.assertEqual(cfg.get("regex"), "#default")
        self.assertEqual(cfg.get("enable"), True)

        # YAML group override: unpin has regex: "#group_pin" but retains enable: True
        group_cfg = await self.config.get_feature_config("unpin", chat_id=-1001111111111)
        self.assertEqual(group_cfg.get("regex"), "#group_pin")
        self.assertEqual(group_cfg.get("enable"), True)

    async def test_get_group_config_no_leak(self):
        chat_id = -1003333333333
        await DbConfig.create(chat_id=chat_id, bitflip=False, welcome={"enable": True, "message": "hello"})
        group_cfg = await self.config.get_group_config(chat_id)

        # Must not leak db metadata columns
        self.assertNotIn("id", group_cfg)
        self.assertNotIn("chat_id", group_cfg)

        # Values should be merged
        self.assertEqual(group_cfg.get("bitflip"), False)
        self.assertIn("welcome", group_cfg)
        self.assertEqual(group_cfg["welcome"].get("message"), "hello")

    async def test_update_group_feature(self):
        chat_id = -1004444444444
        # Initially actions is enabled globally
        self.assertTrue(await self.config.is_feature_enabled("actions", chat_id=chat_id))

        # Update boolean feature
        success = await self.config.update_group_feature(chat_id, "actions", False)
        self.assertTrue(success)
        self.assertFalse(await self.config.is_feature_enabled("actions", chat_id=chat_id))

        # Update nested feature subkey
        success = await self.config.update_group_feature(chat_id, "welcome", "新欢迎词", sub_key="message")
        self.assertTrue(success)
        feat_cfg = await self.config.get_feature_config("welcome", chat_id=chat_id)
        self.assertEqual(feat_cfg.get("message"), "新欢迎词")

        # Refuse update for globally disabled feature
        success = await self.config.update_group_feature(chat_id, "disabled_feature", True)
        self.assertFalse(success)

    async def test_handle_config_command(self):
        # Sync test config data to global_config singleton
        original_config_data = global_config.config_data
        global_config.config_data = self.config.config_data
        try:
            chat_id = -1005555555555
            chat_mock = MagicMock()
            chat_mock.type = "supergroup"
            chat_mock.id = chat_id
            member_mock = MagicMock()
            member_mock.status = "administrator"
            chat_mock.get_member = AsyncMock(return_value=member_mock)

            msg = MagicMock()
            msg.chat = chat_mock
            msg.from_user = MagicMock(id=999)
            msg.sender_chat = None
            msg.reply = AsyncMock()

            # 1. View config
            msg.text = "/config"
            await handle_config_command(msg)
            msg.reply.assert_called()
            reply_text = msg.reply.call_args[0][0]
            self.assertIn("当前配置：", reply_text)
            self.assertIn("actions: True", reply_text)
            self.assertNotIn("id:", reply_text)

            # 2. Toggle boolean feature to false
            msg.reply.reset_mock()
            msg.text = "/config actions off"
            await handle_config_command(msg)
            msg.reply.assert_called_with("功能 actions 已关闭")
            self.assertFalse(await global_config.is_feature_enabled("actions", chat_id=chat_id))

            # 3. Update nested feature subkey
            msg.reply.reset_mock()
            msg.text = "/config welcome message 欢迎新群友"
            await handle_config_command(msg)
            msg.reply.assert_called_with("配置项 welcome.message 已更新为 欢迎新群友")
            feat_cfg = await global_config.get_feature_config("welcome", chat_id=chat_id)
            self.assertEqual(feat_cfg.get("message"), "欢迎新群友")

            # 4. Attempt to update globally disabled feature
            msg.reply.reset_mock()
            msg.text = "/config disabled_feature on"
            await handle_config_command(msg)
            msg.reply.assert_called_with("该功能已经在全局配置中禁用")

            # 5. Non-existent feature
            msg.reply.reset_mock()
            msg.text = "/config unknown_feature on"
            await handle_config_command(msg)
            msg.reply.assert_called_with("不存在该功能，请检查后重试")
        finally:
            global_config.config_data = original_config_data


if __name__ == "__main__":
    unittest.main()
