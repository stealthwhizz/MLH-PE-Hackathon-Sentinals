from datetime import datetime

from peewee import CharField, DateTimeField, IntegerField, TextField

from app.database import BaseModel


class RiskScore(BaseModel):
    url_id = IntegerField(unique=True, index=True)
    score = IntegerField(default=0, index=True)
    signals = TextField(default="{}")
    computed_at = DateTimeField(default=datetime.utcnow)
    tier = CharField(max_length=20, index=True)

    class Meta:
        table_name = "risk_scores"
