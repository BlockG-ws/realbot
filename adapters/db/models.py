from tortoise import fields, models


class Config(models.Model):
    chat_id = fields.BigIntField(index=True)
    actions = fields.BooleanField(null=True, default=None)
    bitflip = fields.BooleanField(null=True, default=None)
    link = fields.BooleanField(null=True, default=None)
    fedi = fields.BooleanField(null=True, default=None)
    repeater = fields.BooleanField(null=True, default=None)
    promote = fields.BooleanField(null=True, default=None)
    stats = fields.BooleanField(null=True, default=None)
    unpin = fields.JSONField(
        null=True, default=lambda: {"enable": False, "regex": None}
    )
    welcome = fields.JSONField(
        null=True, default=lambda: {"enable": False, "message": None}
    )
    anti_anonymous = fields.BooleanField(null=True, default=None)

    class Meta:
        table = "config"


class MatrixSyncTokens(models.Model):
    matrix_id = fields.CharField(index=True, unique=True, max_length=1024)
    sync_token = fields.CharField(max_length=256)

    class Meta:
        table = "matrix_sync_tokens"


class Stats(models.Model):
    chat_id = fields.BigIntField(index=True, unique=True)
    chat_title = fields.CharField(null=True, max_length=1024)
    total_messages = fields.IntField(default=0)
    messages_24h = fields.JSONField(null=True, default=dict)
    users = fields.JSONField(null=True, default=dict)
    messages = fields.JSONField(null=True, default=dict)

    class Meta:
        table = "stats"


class MinecraftBindings(models.Model):
    chat_id = fields.BigIntField(index=True, unique=True)
    java_server = fields.CharField(max_length=255, null=True)
    bedrock_server = fields.CharField(max_length=255, null=True)

    class Meta:
        table = "minecraft_bindings"


class FediClients(models.Model):
    instance_domain = fields.CharField(max_length=255, unique=True)
    is_misskey = fields.BooleanField(default=False)
    client_id = fields.CharField(max_length=255)
    client_secret = fields.CharField(max_length=255)

    class Meta:
        table = "fedi_clients"


class FediUserTokens(models.Model):
    user_id = fields.BigIntField(index=True)
    instance_domain = fields.CharField(max_length=255)
    access_token = fields.CharField(max_length=1024)

    class Meta:
        table = "fedi_tokens"
        unique_together = (("user_id", "instance_domain"),)


class ChannelWhiteList(models.Model):
    chat_id = fields.BigIntField(index=True)
    linked_info = fields.JSONField(
        null=True, default=lambda: {"id": None, "fullname": None, "username": None}
    )
    whitelist = fields.JSONField(null=True, default=list)
    also_ban = fields.BooleanField(default=False)

    class Meta:
        table = "channel_whitelist"


class Lottery(models.Model):
    chat_id = fields.BigIntField(index=True)
    type = fields.CharField(max_length=50)
    winner_count = fields.IntField(default=1)
    max_participants = fields.IntField(null=True)
    end_time = fields.DatetimeField(null=True)
    title = fields.CharField(max_length=1024)
    description = fields.TextField(null=True)
    creator = fields.JSONField(null=True, default=dict)
    token = fields.CharField(max_length=1024, null=True)
    participants = fields.JSONField(null=True, default=list)
    winners = fields.JSONField(null=True, default=list)
    is_ended = fields.BooleanField(default=False)

    class Meta:
        table = "lottery"


class NoDupState(models.Model):

    # 群组 ID（按群分别记录）
    chat_id = fields.BigIntField(index=True)
    # 追踪的链接（频道链接或URL）
    link = fields.CharField(index=True, max_length=2048)
    # 该链接被转发的次数（在该群内）
    count = fields.IntField(default=1)
    # 首次看到的时间
    first_seen_at = fields.DatetimeField(auto_now_add=True)
    # 最后一次看到的时间
    last_seen_at = fields.DatetimeField(auto_now=True)
    # 该链接在群内被转发过的消息记录
    forwarded_messages = fields.JSONField(null=True, default=list)

    class Meta:
        table = "no_dup_state"
        # (chat_id, link) 组合作为唯一键，确保每个群有独立的去重记录
        unique_together = (("chat_id", "link"),)
