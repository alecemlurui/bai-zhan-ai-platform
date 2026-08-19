"""
models.py

Tortoise ORM 模型定义。
"""

from enum import Enum

from tortoise import fields, models


class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"


class User(models.Model):
    id = fields.IntField(primary_key=True)
    username = fields.CharField(max_length=128, unique=True)
    email = fields.CharField(max_length=256, null=True)
    password_hash = fields.CharField(max_length=256)
    role = fields.CharEnumField(UserRole, default=UserRole.USER)
    is_active = fields.BooleanField(default=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    topics: fields.ReverseRelation["Topic"]
    media: fields.ReverseRelation["Media"]
    materials: fields.ReverseRelation["Material"]

    class Meta:
        table = "users"


class Bot(models.Model):
    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=128)
    owner = fields.ForeignKeyField("models.User", related_name="bots")
    config = fields.JSONField(default=dict)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "bots"


class TopicStatus(str, Enum):
    CREATED = "created"
    GENERATING_TITLES = "generating_titles"
    COMPLETED = "completed"


class Topic(models.Model):
    id = fields.IntField(primary_key=True)
    user = fields.ForeignKeyField("models.User", related_name="topics")
    title = fields.CharField(max_length=256)
    params = fields.JSONField(default=dict)
    status = fields.CharEnumField(TopicStatus, default=TopicStatus.CREATED)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    titles: fields.ReverseRelation["Title"]

    class Meta:
        table = "topics"


class Title(models.Model):
    id = fields.IntField(primary_key=True)
    topic = fields.ForeignKeyField("models.Topic", related_name="titles")
    text = fields.TextField()
    score = fields.FloatField(null=True)
    is_selected = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)

    articles: fields.ReverseRelation["Article"]

    class Meta:
        table = "titles"


class ArticleStatus(str, Enum):
    DRAFT = "draft"
    GENERATING = "generating"
    COMPLETED = "completed"
    PUBLISHED = "published"


class Article(models.Model):
    id = fields.IntField(primary_key=True)
    title = fields.ForeignKeyField("models.Title", related_name="articles")
    content = fields.TextField()
    status = fields.CharEnumField(ArticleStatus, default=ArticleStatus.DRAFT)
    metadata = fields.JSONField(default=dict)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    publish_records: fields.ReverseRelation["PublishRecord"]

    class Meta:
        table = "articles"


class MediaType(str, Enum):
    IMAGE = "image"
    VIDEO = "video"


class Media(models.Model):
    id = fields.IntField(primary_key=True)
    owner = fields.ForeignKeyField("models.User", related_name="media")
    url = fields.CharField(max_length=2048)
    type = fields.CharEnumField(MediaType, default=MediaType.IMAGE)
    width = fields.IntField(null=True)
    height = fields.IntField(null=True)
    size_bytes = fields.IntField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "media"


class MaterialType(str, Enum):
    TEXT = "text"
    IMAGE = "image"


class Material(models.Model):
    id = fields.IntField(primary_key=True)
    owner = fields.ForeignKeyField("models.User", related_name="materials")
    type = fields.CharEnumField(MaterialType, default=MaterialType.TEXT)
    content = fields.TextField(null=True)
    url = fields.CharField(max_length=2048, null=True)
    tags = fields.JSONField(default=list)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "materials"


class PublishStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"


class PublishRecord(models.Model):
    id = fields.IntField(primary_key=True)
    article = fields.ForeignKeyField("models.Article", related_name="publish_records")
    platform = fields.CharField(max_length=64)
    status = fields.CharEnumField(PublishStatus, default=PublishStatus.PENDING)
    ext_id = fields.CharField(max_length=256, null=True)
    error_message = fields.TextField(null=True)
    result = fields.JSONField(default=dict)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "publish_records"


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class Task(models.Model):
    id = fields.IntField(primary_key=True)
    type = fields.CharField(max_length=64)
    payload = fields.JSONField(default=dict)
    status = fields.CharEnumField(TaskStatus, default=TaskStatus.PENDING)
    attempts = fields.IntField(default=0)
    max_attempts = fields.IntField(default=3)
    result = fields.JSONField(null=True)
    logs = fields.JSONField(default=list)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "tasks"
