# 03 — Playwright end-to-end workflow

## Environment

- Playwright `1.65.1`, Chromium
- API: `http://localhost:8000`
- Dashboard: `http://localhost:3000`
- API readiness: `GET /health/ready` returned `{"status":"ready"}`

## Executed command

```text
npm run test:e2e

Running 2 tests using 1 worker
  ok 01 — dashboard loads seeded API-backed workspace
  ok 02 — analyst runs benchmark and inspects persisted field evidence
2 passed (6.1s)
```

## Assertions exercised

1. The dashboard hydrates with live API data, exposes the seeded synthetic benchmark, and renders the quality overview.
2. An analyst starts the offline benchmark through the UI, then sees a persisted run and field-level result rows.

The initial exploratory run exposed that a test base URL of `127.0.0.1` was outside the local API's documented CORS allowlist (`localhost:3000`). The test was corrected to use the documented local host. A second assertion was changed from a transient completion notice to durable persisted-results behavior. The final passing run and screenshots are the authoritative evidence.
