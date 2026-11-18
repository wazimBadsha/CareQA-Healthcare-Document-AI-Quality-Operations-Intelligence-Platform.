# Validation manifest — 2026-11-18

All evidence below was generated against the local CareQA implementation with synthetic data only. No patient, employer, credential, or external provider data was used.

| Task | Result | Evidence |
|---|---|---|
| Backend lint and unit/API tests | Passed | [01-backend-quality.md](01-backend-quality.md) |
| Frontend type check and production build | Passed | [02-frontend-build.md](02-frontend-build.md) |
| Browser E2E — dashboard load | Passed | [01-dashboard-loaded.png](playwright/01-dashboard-loaded.png) |
| Browser E2E — benchmark run and persisted results | Passed | [02-benchmark-run-and-results.png](playwright/02-benchmark-run-and-results.png) |

## Artifact integrity

| File | SHA-256 |
|---|---|
| `playwright/01-dashboard-loaded.png` | `2313B3E49474025C2427ED5E54E5D3CED7A9B43E1FF8979374D21B9AEB837CF6` |
| `playwright/02-benchmark-run-and-results.png` | `569AE15D554E5E74E3DACA470C1245A54641DC0E4EAAE697437E46D47EF1B731` |
| `playwright/report/index.html` | `08CE0C94DDC037E3E132561958E23D4D892AD3679A512BB10D068DE2434DBF04` |

The Playwright HTML report and its completed-run status are retained under `playwright/`.
