# GhostLink API Reference

This document is a quick endpoint reference for app consumers and evaluators.

## Base URL

- Local (through Nginx): `http://localhost`
- Direct app replicas:
  - `http://localhost:5001`
  - `http://localhost:5002`

## Authentication

No authentication is required in the current hackathon implementation.

## Content Type

- Request body: `application/json`
- Metrics endpoint: `text/plain`

## Endpoints

### POST /shorten

Create a short URL.

Example:

```bash
curl -X POST http://localhost/shorten \
  -H "Content-Type: application/json" \
  -d '{
    "original_url": "https://example.com/path",
    "title": "Example",
    "user_id": 1
  }'
```

Successful response (`201`):

```json
{
  "id": 123,
  "short_code": "abc123"
}
```

Error responses:

- `400` missing body or `original_url`
- `409` short code already exists
- `422` invalid URL format
- `500` short code generation failure

### GET /{short_code}

Resolve a short code.

Example:

```bash
curl -i http://localhost/abc123
```

Response behavior:

- `302` redirect to destination URL
- `404` unknown short code
- `410` inactive short code
- `410` quarantined short code

### GET /urls

List URLs. Optional filter by `user_id`.

Examples:

```bash
curl http://localhost/urls
curl "http://localhost/urls?user_id=1"
```

Successful response (`200`): JSON array of URL records.

### PATCH /urls/{id}

Update URL fields.

Example:

```bash
curl -X PATCH http://localhost/urls/123 \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Updated title",
    "original_url": "https://example.org/new-path",
    "is_active": true
  }'
```

Successful response (`200`):

```json
{"message": "updated"}
```

Error responses:

- `400` missing body
- `404` URL not found
- `422` invalid URL

### DELETE /urls/{id}

Soft delete URL (sets `is_active=false`).

Example:

```bash
curl -X DELETE http://localhost/urls/123
```

Successful response (`200`):

```json
{"message": "deleted"}
```

Error responses:

- `404` URL not found

### GET /urls/{id}/risk

Get risk score for a URL.

Example:

```bash
curl http://localhost/urls/123/risk
```

Typical response (`200`):

```json
{
  "url_id": 123,
  "score": 35,
  "tier": "WATCHLIST",
  "signals": {
    "long_redirect_chain": true
  }
}
```

Error responses:

- `404` URL not found
- `404` risk score unavailable

### GET /health

Service health (DB + Redis view).

Example:

```bash
curl http://localhost/health
```

Response (`200`):

```json
{
  "status": "ok",
  "db": "ok",
  "redis": "ok"
}
```

Response (`503`) when DB probe fails:

```json
{
  "status": "degraded",
  "db": "error"
}
```

### GET /metrics

Prometheus metrics.

Example:

```bash
curl http://localhost/metrics
```

Response (`200`): Prometheus exposition text.

### Canary Endpoints

Synthetic canary routes exposed for monitoring:

- `GET /health-demo`
- `GET /promo-demo`
- `GET /checkout-demo`
- `GET /dashboard-demo`
- `GET /support-demo`

Example:

```bash
curl http://localhost/health-demo
```

Response (`200`):

```json
{"status": "ok", "canary": "health-demo"}
```

## Linked References

- Operational docs: `docs/README.md`
- Failure handling: `docs/FAILURE_EDGE_CASES.md`
- Incident steps: `docs/RUNBOOK.md`
