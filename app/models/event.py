from datetime import datetime

from peewee import CharField, DateTimeField, IntegerField

from app.database import BaseModel


class Event(BaseModel):
    url_id = IntegerField(index=True)
    user_id = IntegerField(null=True, index=True)
    event_type = CharField(max_length=50, index=True)
    timestamp = DateTimeField(default=datetime.utcnow, index=True)

    class Meta:
        table_name = "events"
        indexes = (
            (("url_id", "timestamp"), False),
            (("user_id", "timestamp"), False),
        )
