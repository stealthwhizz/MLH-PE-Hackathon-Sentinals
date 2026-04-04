from datetime import datetime

from peewee import BooleanField, CharField, DateTimeField, ForeignKeyField, IntegerField

from app.database import BaseModel


class Url(BaseModel):
    user_id = IntegerField(null=True, index=True)
    short_code = CharField(max_length=10, unique=True, index=True)
    original_url = CharField(max_length=2048)
    title = CharField(max_length=255, null=True)
    is_active = BooleanField(default=True, index=True)
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

    class Meta:
        table_name = "urls"
        indexes = (
            (("user_id", "is_active"), False),
            (("created_at",), False),
        )

    def save(self, *args, **kwargs):
        self.updated_at = datetime.utcnow()
        return super().save(*args, **kwargs)
