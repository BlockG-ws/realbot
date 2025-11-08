from tortoise import fields, models

class Stats(models.Model):
    chat_id = fields.BigIntField(index=True,unique=True)
    chat_title = fields.CharField(null=True,max_length=1024)
    total_messages = fields.IntField(default=0)
    messages_24h = fields.JSONField(null=True,default=dict)
    users = fields.JSONField(null=True,default=dict)
    messages = fields.JSONField(null=True,default=dict)

    class Meta:
        table = "stats"

class MinecraftBindings(models.Model):
    chat_id = fields.BigIntField(index=True,unique=True)
    java_server = fields.CharField(max_length=255,null=True)
    bedrock_server = fields.CharField(max_length=255,null=True)
    class Meta:
        table = "minecraft_bindings"

class Config(models.Model):
    chat_id = fields.BigIntField(index=True)
    config = fields.JSONField(null=True,default=dict)
    class Meta:
        table = "config"

class FediSecrets(models.Model):
    instance_domain = fields.CharField(max_length=255,unique=True)
    is_misskey = fields.BooleanField(default=False)
    client_id = fields.CharField(max_length=255)
    client_secret = fields.CharField(max_length=255)
    class Meta:
        table = "fedi_clients"

class FediTokens(models.Model):
    user_id = fields.BigIntField(index=True)
    instance_domain = fields.CharField(max_length=255)
    access_token = fields.CharField(max_length=1024)
    class Meta:
        table = "fedi_tokens"
        unique_together = (("user_id", "instance_domain"),)

class Lottery(models.Model):
    id = fields.CharField(max_length=255,pk=True)
    chat_id = fields.BigIntField(index=True)
    title = fields.CharField(max_length=1024)
    description = fields.TextField(null=True)
    participants = fields.JSONField(null=True,default=list)
    is_ended = fields.BooleanField(default=False)

    class Meta:
        table = "lottery"