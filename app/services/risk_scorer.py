import json
from datetime import datetime, timedelta

import whois
from peewee import fn

from app.models.event import Event
from app.models.health_check import HealthCheck
from app.models.risk_score import RiskScore
from app.models.url import Url
from app.services import cache


def compute_risk_score(url_id):
    """
    Compute a 0-100 risk score for a URL based on multiple signals.

    Scoring rules:
    - +35: inactive URL with hit count > 5 (ghost probe detection)
    - +25: dead destination (4xx/5xx status)
    - +20: user deletion spike (>3 deletes in 1 hour)
    - +10: redirect chain > 2
    - +10: domain registered < 30 days ago

    Tiers: 0-30 SAFE, 31-60 SUSPICIOUS, 61-100 THREAT
    """
    url = Url.select().where(Url.id == url_id).first()
    if not url:
        return None

    score = 0
    signals = {}

    if not url.is_active:
        hit_count = Event.select().where(
            (Event.url_id == url_id) & (Event.event_type == "redirect")
        ).count()
        if hit_count > 5:
            score += 35
            signals["ghost_probe"] = True
            signals["hit_count"] = hit_count

    latest_health = (
        HealthCheck.select()
        .where(HealthCheck.url_id == url_id)
        .order_by(HealthCheck.checked_at.desc())
        .first()
    )

    if latest_health:
        if latest_health.status_code and (
            400 <= latest_health.status_code < 600
        ):
            score += 25
            signals["dead_destination"] = True
            signals["status_code"] = latest_health.status_code

        if latest_health.redirect_chain_length > 2:
            score += 10
            signals["long_redirect_chain"] = True
            signals["chain_length"] = latest_health.redirect_chain_length

    if url.user_id:
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        delete_count = (
            Event.select()
            .where(
                (Event.user_id == url.user_id)
                & (Event.event_type == "deleted")
                & (Event.timestamp >= one_hour_ago)
            )
            .count()
        )
        if delete_count > 3:
            score += 20
            signals["deletion_spike"] = True
            signals["deletes_last_hour"] = delete_count

    try:
        from urllib.parse import urlparse
        domain = urlparse(url.original_url).netloc
        if domain:
            domain_info = whois.whois(domain)
            if domain_info and domain_info.creation_date:
                creation_date = domain_info.creation_date
                if isinstance(creation_date, list):
                    creation_date = creation_date[0]

                age_days = (datetime.utcnow() - creation_date).days
                if age_days < 30:
                    score += 10
                    signals["new_domain"] = True
                    signals["domain_age_days"] = age_days
    except Exception:
        pass

    score = min(score, 100)

    if score <= 30:
        tier = "SAFE"
    elif score <= 60:
        tier = "SUSPICIOUS"
    else:
        tier = "THREAT"

    risk_data = {
        "url_id": url_id,
        "score": score,
        "signals": json.dumps(signals),
        "tier": tier,
        "computed_at": datetime.utcnow(),
    }

    RiskScore.insert(**risk_data).on_conflict(
        conflict_target=[RiskScore.url_id],
        update={
            RiskScore.score: score,
            RiskScore.signals: json.dumps(signals),
            RiskScore.tier: tier,
            RiskScore.computed_at: datetime.utcnow(),
        },
    ).execute()

    cache_data = {"score": score, "tier": tier, "signals": signals}
    cache.cache_risk_score(url_id, cache_data)

    return risk_data


def get_risk_score(url_id):
    """
    Get risk score for a URL.
    Checks cache first, then database, computes if missing.
    """
    cached = cache.get_cached_risk_score(url_id)
    if cached:
        return cached

    risk = RiskScore.select().where(RiskScore.url_id == url_id).first()
    if risk:
        data = {
            "score": risk.score,
            "tier": risk.tier,
            "signals": json.loads(risk.signals) if risk.signals else {},
        }
        cache.cache_risk_score(url_id, data)
        return data

    return compute_risk_score(url_id)
