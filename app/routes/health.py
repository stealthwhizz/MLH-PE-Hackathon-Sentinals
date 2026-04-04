from flask import Blueprint, Response, jsonify
from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram, generate_latest

from app.database import db, get_redis
from app.models.health_check import HealthCheck
from app.models.risk_score import RiskScore
from app.models.url import Url

health_bp = Blueprint("health", __name__)

registry = CollectorRegistry()

urls_created_total = Counter(
    "urls_created_total", "Total number of URLs created", registry=registry
)

url_redirects_total = Counter(
    "url_redirects_total",
    "Total number of URL redirects",
    ["short_code"],
    registry=registry,
)

redirect_latency_seconds = Histogram(
    "redirect_latency_seconds",
    "Redirect response time in seconds",
    registry=registry,
)

ghost_probes_total = Counter(
    "ghost_probes_total", "Total hits on inactive URLs", registry=registry
)

destination_dead_total = Counter(
    "destination_dead_total",
    "Total number of dead destination detections",
    registry=registry,
)

risk_score_threats_total = Gauge(
    "risk_score_threats_total", "Number of URLs with risk score > 70", registry=registry
)

urls_active_total = Gauge(
    "urls_active_total", "Total number of active URLs", registry=registry
)

urls_inactive_total = Gauge(
    "urls_inactive_total", "Total number of inactive URLs", registry=registry
)


@health_bp.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint with DB and Redis status."""
    status = {"status": "ok"}

    try:
        db.execute_sql("SELECT 1")
        status["db"] = "ok"
    except Exception as e:
        status["status"] = "degraded"
        status["db"] = "error"
        return jsonify(status), 503

    redis_client = get_redis()
    if redis_client:
        try:
            redis_client.ping()
            status["redis"] = "ok"
        except Exception:
            status["redis"] = "error"
    else:
        status["redis"] = "unavailable"

    return jsonify(status), 200


@health_bp.route("/metrics", methods=["GET"])
def metrics():
    """Prometheus metrics endpoint."""
    active_count = Url.select().where(Url.is_active == True).count()
    inactive_count = Url.select().where(Url.is_active == False).count()

    urls_active_total.set(active_count)
    urls_inactive_total.set(inactive_count)

    threat_count = RiskScore.select().where(RiskScore.score > 70).count()
    risk_score_threats_total.set(threat_count)

    dead_count = HealthCheck.select().where(HealthCheck.health_status == "DEAD").count()
    destination_dead_total._value._value = dead_count

    return Response(generate_latest(registry), mimetype="text/plain")


def increment_urls_created():
    """Helper to increment URLs created counter."""
    urls_created_total.inc()


def increment_url_redirects(short_code):
    """Helper to increment redirect counter for a short code."""
    url_redirects_total.labels(short_code=short_code).inc()


def record_redirect_latency(seconds):
    """Helper to record redirect latency."""
    redirect_latency_seconds.observe(seconds)


def increment_ghost_probes():
    """Helper to increment ghost probe counter."""
    ghost_probes_total.inc()


def increment_destination_dead():
    """Helper to increment dead destination counter."""
    destination_dead_total.inc()
