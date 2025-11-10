from adapters.db.models import FediUserTokens, FediClients

async def fedi_instance_is_misskey(instance_domain: str) -> bool | None:
    """Retrieve Fediverse instance client info by instance_domain."""
    is_misskey = await FediClients.get_or_none(instance_domain=instance_domain).values("is_misskey")
    return is_misskey[0] if is_misskey else None

async def get_fedi_client_info(instance_domain: str) -> dict:
    """Retrieve Fediverse instance client info by instance_domain."""
    client_id, client_secret = await FediClients.get_or_none(instance_domain=instance_domain).values("client_id", "client_secret")
    return {
        "client_id": client_id,
        "client_secret": client_secret
    }

async def get_fedi_user_instance_domains(user_id: int) -> list[str]:
    """Retrieve all Fediverse instance domains associated with a user_id."""
    tokens = await FediUserTokens.filter(user_id=user_id).values_list("instance_domain", flat=True)
    return list(tokens)

async def get_fedi_user_cred(instance_domain: str, user_id: int) -> str:
    """Retrieve Fediverse user credential by instance_domain and user_id."""
    token = await FediUserTokens.get_or_none(instance_domain=instance_domain, user_id=user_id)
    return getattr(token, "access_token", "") or ""

async def update_fedi_user_cred(instance_domain: str, user_id: int, access_token: str) -> None:
    """Update Fediverse user credential by instance_domain and user_id."""
    token_obj, _ = await FediUserTokens.get_or_create(instance_domain=instance_domain, user_id=user_id)
    token_obj.access_token = access_token
    await token_obj.save()

async def update_fedi_client_info(instance_domain: str, is_misskey: bool,client_id: str, client_secret: str) -> None:
    """Update Fediverse instance client info by instance_domain."""
    obj, _ = await FediClients.get_or_create(
        instance_domain=instance_domain,
        defaults={'client_id': client_id, 'client_secret': client_secret, 'is_misskey': False}
    )
    obj.is_misskey = is_misskey
    if client_id and client_secret:
        obj.client_id = client_id
        obj.client_secret = client_secret
    await obj.save()

