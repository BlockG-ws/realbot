from adapters.db.models import MatrixSyncTokens

async def get_sync_token(user_id: str) -> str:
    """Retrieve sync token for a user."""
    token = await MatrixSyncTokens.get_or_none(matrix_id=user_id).values()
    return token.get('sync_token')

async def update_sync_token(user_id: str, token: str) -> None:
    """Update sync token for a user."""
    data, created = await MatrixSyncTokens.get_or_create(matrix_id=user_id)
    data.sync_token = token
    await data.save()