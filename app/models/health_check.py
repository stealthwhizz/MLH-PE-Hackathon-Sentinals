from datetime import datetime

from peewee import CharField, DateTimeField, IntegerField

from app.database import BaseModel


class HealthCheck(BaseModel):
    url_id = IntegerField(index=True)
    checked_at = DateTimeField(default=datetime.utcnow, index=True)
    status_code = IntegerField(null=True)
    latency_ms = IntegerField(null=True)
    health_status = CharField(max_length=20, index=True)
    redirect_chain_length = IntegerField(default=0)

    class Meta:
        table_name = "health_checks"
        indexes = (
            (("url_id", "checked_at"), False),
        )
