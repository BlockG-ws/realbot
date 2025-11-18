import asyncio
import os
from pathlib import Path
from tortoise import Tortoise
from adapters.db.models import Stats, MinecraftBindings, FediClients, FediUserTokens
import json

# message_stats.json 迁移到数据库
async def migrate_stats() -> None:
    """Migrate stats from JSON file to database"""
    try:
        with open('../message_stats.json', 'r', encoding='utf-8') as f:
            all_stats = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print("No stats to migrate. Skipping.")
        return

    for chat_id_str, stats_data in all_stats.items():
        chat_id = int(chat_id_str)
        stats_obj, created = await Stats.get_or_create(chat_id=chat_id)
        stats_obj.chat_title = stats_data.get('chat_title')
        stats_obj.total_messages = stats_data.get('total_messages', 0)
        # 使用 json.dumps 将字典转换为 JSON 字符串，以确保不会转义
        stats_obj.messages_24h = json.dumps(stats_data.get('messages_24h', {}),ensure_ascii=False)
        stats_obj.users = json.dumps(stats_data.get('users', {}), ensure_ascii=False)
        stats_obj.messages = json.dumps(stats_data.get('messages', {}),ensure_ascii=False)
        await stats_obj.save()

# mc_bindings.json 迁移到数据库
async def migrate_mc_bindings() -> None:
    """Migrate Minecraft bindings from JSON file to database"""
    try:
        with open('../mc_bindings.json', 'r', encoding='utf-8') as f:
            all_bindings = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print("No Minecraft bindings to migrate. Skipping.")
        return

    for chat_id_str, binding_data in all_bindings.items():
        chat_id = int(chat_id_str)
        binding_obj, created = await MinecraftBindings.get_or_create(chat_id=chat_id)
        binding_obj.java_server = binding_data.get('java')
        binding_obj.bedrock_server = binding_data.get('bedrock')
        await binding_obj.save()

# fediverse 账户的信息、客户端机密迁移到数据库
async def migrate_fedi() -> None:
    """Migrate Fediverse secrets and client infomation from files in secrets/"""
    secrets_file_path = Path("../secrets")
    if not secrets_file_path.exists() or not secrets_file_path.is_dir():
        print("No Fediverse secrets to migrate. Skipping.")
        return
    import re
    for secret_file in secrets_file_path.iterdir():
        if secret_file.is_file():
            for secret_file in secrets_file_path.iterdir():
                    if secret_file.is_file():
                        name = secret_file.name
                        # user credential files: realbot_{instance}_{user_id}_usercred.secret
                        usercred = re.match(r"^realbot_(?P<instance>.+)_(?P<user_id>\d+)_usercred\.secret$", name)
                        if usercred:
                            instance = usercred.group("instance")
                            user_id = int(usercred.group("user_id"))
                            try:
                                with secret_file.open('r', encoding='utf-8') as sf:
                                    access_token = sf.readline().strip()
                            except Exception:
                                print(f"Failed to read ` {secret_file} `")
                                continue
                            token_obj, _ = await FediUserTokens.get_or_create(instance_domain=instance, user_id=user_id, access_token=access_token)
                            token_obj.access_token = access_token
                            await token_obj.save()
                            continue
                        # client credential files: realbot_{instance}_clientcred.secret
                        client_cred = re.match(r"^realbot_(?P<instance>.+)_clientcred\.secret$", name)
                        if client_cred:
                            instance = client_cred.group("instance")
                            try:
                                with secret_file.open('r', encoding='utf-8') as sf:
                                    client_id = sf.readline().strip()
                                    client_secret = sf.readline().strip()
                            except Exception:
                                print(f"Failed to read ` {secret_file} `")
                                continue
                            secret_obj, _ = await FediClients.get_or_create(
                                instance_domain=instance,
                                defaults={'client_id': client_id, 'client_secret': client_secret}
                            )
                            secret_obj.client_id = client_id
                            secret_obj.client_secret = client_secret
                            await secret_obj.save()
                            continue

# 主迁移函数
async def migrate() -> None:
    project_root = Path(__file__).resolve().parent.parent
    db_path = project_root / "db.sqlite3"
    env_db_file = os.getenv("DB_FILE")
    if env_db_file:
        db_file_path = Path(env_db_file)
        db_path = db_file_path if db_file_path.is_absolute() else project_root / env_db_file
    await Tortoise.init(
        db_url=f"sqlite://{str(db_path)}",
        modules={'models': ['adapters.db.models']}
    )
    await Tortoise.generate_schemas()
    resp1 = input("Migrate `message_stats.json`? [y/N]: ").strip().lower()
    if resp1 in ("y", "yes"):
        print("Migrating stats...")
        await migrate_stats()
    else:
        print("Skipping stats migration.")
    resp2 = input("Migrate `mc_bindings.json`? [y/N]: ").strip().lower()
    if resp2 in ("y", "yes"):
        print("Migrating mc bindings...")
        await migrate_mc_bindings()
    else:
        print("Skipping mc bindings migration.")
    resp3 = input("Migrate `secrets/` files? [y/N]: ").strip().lower()
    if resp3 in ("y", "yes"):
        print("Migrating fediverse secrets...")
        await migrate_fedi()
    else:
        print("Skipping fediverse migration.")
    print("Migration complete! You can now delete the old JSON files and secrets directory if desired.")
    await Tortoise.close_connections()

if __name__ == '__main__':
    resp = input("This will overwrite existing data in the database. Continue? [y/N]: ").strip().lower()
    if resp in ("y", "yes"):
        asyncio.run(migrate())
    else:
        print("Migration aborted.")