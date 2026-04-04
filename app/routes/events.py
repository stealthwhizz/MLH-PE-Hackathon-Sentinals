import json

from flask import Blueprint, jsonify, request
from playhouse.shortcuts import model_to_dict

from app.models.event import Event

events_bp = Blueprint("events", __name__)


def _coerce_positive_int(value, default):
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def _encode_details(details):
    if details is None:
        return None
    if isinstance(details, str):
        return details

    try:
        return json.dumps(details)
    except (TypeError, ValueError):
        return str(details)


def _decode_details(raw_details):
    if raw_details in (None, ""):
        return None

    try:
        return json.loads(raw_details)
    except (TypeError, ValueError):
        return raw_details


def _serialize_event(event):
    payload = model_to_dict(event)
    payload["details"] = _decode_details(payload.get("details"))
    return payload


@events_bp.route("/events", methods=["GET"])
def list_events():
    query = Event.select().order_by(Event.id)

    url_id = request.args.get("url_id", type=int)
    user_id = request.args.get("user_id", type=int)
    event_type = request.args.get("event_type")

    if url_id is not None:
        query = query.where(Event.url_id == url_id)
    if user_id is not None:
        query = query.where(Event.user_id == user_id)
    if event_type:
        query = query.where(Event.event_type == event_type)

    page = _coerce_positive_int(request.args.get("page", 1), 1)
    per_page = _coerce_positive_int(request.args.get("per_page", 100), 100)

    events = [_serialize_event(event) for event in query.paginate(page, per_page)]
    return jsonify(events), 200


@events_bp.route("/events", methods=["POST"])
def create_event():
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "Missing request body", "code": 400}), 400

    event_type = (data.get("event_type") or "").strip()
    if not event_type:
        return jsonify({"error": "Missing event_type", "code": 400}), 400

    url_id = data.get("url_id")
    if url_id is None:
        return jsonify({"error": "Missing url_id", "code": 400}), 400

    try:
        url_id = int(url_id)
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid url_id", "code": 400}), 400

    user_id = data.get("user_id")
    if user_id is not None:
        try:
            user_id = int(user_id)
        except (TypeError, ValueError):
            return jsonify({"error": "Invalid user_id", "code": 400}), 400

    payload = {
        "url_id": url_id,
        "user_id": user_id,
        "event_type": event_type,
        "details": _encode_details(data.get("details")),
    }

    timestamp = data.get("timestamp")
    if timestamp:
        payload["timestamp"] = timestamp

    event = Event.create(**payload)
    return jsonify(_serialize_event(event)), 201
