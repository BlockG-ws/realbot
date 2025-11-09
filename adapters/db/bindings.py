from adapters.db.models import MinecraftBindings

async def get_mc_binding(chat_id: int) -> dict:
    """Retrieve Minecraft binding for a specific chat_id."""
    binding = await MinecraftBindings.get_or_none(chat_id=chat_id).values()
    return binding

async def update_mc_binding(chat_id: int, server_type: str, address: str | None) -> None:
    """Update Minecraft binding for a specific chat_id."""
    binding, created = await MinecraftBindings.get_or_create(chat_id=chat_id)
    if server_type == 'java':
        binding.java_server = address
    elif server_type == 'bedrock':
        binding.bedrock_server = address
    await binding.save()