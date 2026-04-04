# Failure and Edge Case Handling

This note explains how GhostLink handles API failures, degraded dependencies, and common edge cases in production.

## Design Goals

- Fail closed for risky traffic (quarantined or inactive short codes).
- Fail open for non-critical cache paths (continue serving when Redis is unavailable).
- Keep responses explicit with stable HTTP status codes and JSON error payloads where app logic handles the error.

## API Failure Matrix

| Endpoint | Scenario | Status | Behavior |
|---|---|---:|---|
| `POST /shorten` | Missing JSON body | `400` | Returns `{"error": "Missing request body", "code": 400}` |
| `POST /shorten` | Missing `original_url` | `400` | Returns `{"error": "Missing original_url", "code": 400}` |
| `POST /shorten` | Invalid URL format | `422` | Returns `{"error": "Invalid URL", "code": 422}` |
| `POST /shorten` | Custom code already exists | `409` | Returns `{"error": "Short code exists", "code": 409}` |
| `POST /shorten` | Generator cannot allocate code | `500` | Returns `{"error": "Failed to generate short code", "code": 500}` |
| `GET /<short_code>` | Code quarantined | `410` | Returns quarantine JSON and records blocked fingerprint |
| `GET /<short_code>` | Code unknown | `404` | Returns `{"error": "Not found", "code": 404}` and records invalid hit |
| `GET /<short_code>` | Code inactive (soft deleted) | `410` | Returns `{"error": "Link inactive", "code": 410}` and emits ghost probe event |
| `GET /<short_code>` | Code valid and active | `302` | Redirects to destination URL |
| `PATCH /urls/<id>` | Missing JSON body | `400` | Returns `{"error": "Missing request body", "code": 400}` |
| `PATCH /urls/<id>` | URL id not found | `404` | Returns `{"error": "Not found", "code": 404}` |
| `PATCH /urls/<id>` | Invalid `original_url` | `422` | Returns `{"error": "Invalid URL", "code": 422}` |
| `DELETE /urls/<id>` | URL id not found | `404` | Returns `{"error": "Not found", "code": 404}` |
| `GET /urls/<id>/risk` | URL id not found | `404` | Returns `{"error": "Not found", "code": 404}` |
| `GET /urls/<id>/risk` | Risk record unavailable | `404` | Returns `{"error": "Risk score unavailable", "code": 404}` |
| `GET /health` | Database probe fails | `503` | Returns degraded health payload |

## Dependency Degradation Behavior

### Redis Unavailable

- Cache operations are best-effort and wrapped in exception handling.
- Redirect and risk scoring still work through database-backed logic.
- Health endpoint reports `redis: "unavailable"` or `redis: "error"` while still returning `200` when DB is healthy.

### Database Unavailable

- `GET /health` returns `503` and marks service degraded.
- Most API routes and `/metrics` depend on DB and will fail without it.

## Security and Abuse Edge Cases

### Quarantined Short Codes

- Source of truth: `nginx/blocked_codes.conf`.
- App-layer guard also checks quarantine before any redirect path.
- Response is a deterministic `410` JSON payload.

### Stale Cache Entries for Inactive URLs

- Redirect path validates current DB state even when cache returns a destination.
- If cache hit points to an inactive or missing record, cache is deleted and request falls back to DB checks.
- This prevents incorrect `302` responses for deactivated links.

### Invalid or High-Volume Probes

- Invalid short-code hits and inactive-link hits are fingerprinted.
- Aggregations feed suspicious client metrics (`ghostlink_suspicious_*`, blocked/invalid counters).

## HTTP Framework Defaults (Expected)

- Unknown routes not explicitly handled by blueprints return Flask default `404` page.
- Unsupported methods on existing routes return Flask default `405` page.

## Operational Notes

- Quarantine helpers:
  - `scripts/quarantine_code.sh`
  - `scripts/unquarantine_code.sh`
- Incident workflows are documented in `docs/RUNBOOK.md`.
- Capacity and chaos validation guidance is in `docs/CAPACITY.md`.

## Test Coverage for Edge Cases

Relevant tests include:

- redirect for inactive links and quarantined links
- stale cache behavior for inactive links
- not-found and validation error responses
- health and metrics endpoint assertions

See `app/tests/test_integration.py` and `app/tests/test_unit.py`.