import json

from app.database import get_redis

SHORT_CODE_TTL = 300
RISK_SCORE_TTL = 600


def get_cached_url(short_code):
    """
    Retrieve original URL from Redis cache.
    Returns None if not found or Redis unavailable.
    """
    redis_client = get_redis()
    if not redis_client:
        return None

    try:
        key = f"url:{short_code}"
        return redis_client.get(key)
    except Exception:
        return None


def cache_url(short_code, original_url):
    """
    Cache a short_code -> original_url mapping with 5 minute TTL.
    Silently fails if Redis unavailable.
    """
    redis_client = get_redis()
    if not redis_client:
        return

    try:
        key = f"url:{short_code}"
        redis_client.setex(key, SHORT_CODE_TTL, original_url)
    except Exception:
        pass


def delete_cached_url(short_code):
    """
    Remove a short_code from cache.
    Silently fails if Redis unavailable.
    """
    redis_client = get_redis()
    if not redis_client:
        return

    try:
        key = f"url:{short_code}"
        redis_client.delete(key)
    except Exception:
        pass


def get_cached_risk_score(url_id):
    """
    Retrieve risk score from Redis cache.
    Returns None if not found or Redis unavailable.
    """
    redis_client = get_redis()
    if not redis_client:
        return None

    try:
        key = f"risk:{url_id}"
        data = redis_client.get(key)
        if data:
            return json.loads(data)
        return None
    except Exception:
        return None


def cache_risk_score(url_id, score_data):
    """
    Cache risk score with 10 minute TTL.
    score_data should be a dict with 'score', 'tier', 'signals'.
    Silently fails if Redis unavailable.
    """
    redis_client = get_redis()
    if not redis_client:
        return

    try:
        key = f"risk:{url_id}"
        redis_client.setex(key, RISK_SCORE_TTL, json.dumps(score_data))
    except Exception:
        pass


def delete_cached_risk_score(url_id):
    """
    Remove a risk score from cache.
    Silently fails if Redis unavailable.
    """
    redis_client = get_redis()
    if not redis_client:
        return

    try:
        key = f"risk:{url_id}"
        redis_client.delete(key)
    except Exception:
        pass
