import os

from tortoise import Tortoise

async def init_db():
    db_path = "db.sqlite3"
    if os.getenv("DB_FILE"):
        db_path = os.getenv("DB_FILE")
    await Tortoise.init(
        db_url=f'sqlite://{db_path}',
        modules={'models': ['adapters.db.models']}
    )
    await Tortoise.generate_schemas()

async def close_db():
    await Tortoise.close_connections()