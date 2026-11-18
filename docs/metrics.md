# Metric contract

CareQA preserves source/reference values and calculates comparison signals separately. Metrics are for synthetic benchmark quality analysis only.

| Metric | Calculation | Null / denominator behavior |
|---|---|---|
| Exact match | `expected == actual` | Missing required actual is a `missing` defect. |
| Normalized match | Field-aware canonical comparison | Whitespace/case normalised for text; ISO/slash dates canonicalised; `dosage_mg` uses a documented 0.5 mg tolerance. |
| Completeness | populated required fields / required fields | A missing actual counts as unpopulated. Empty required field sets return 1.0. |
| Entity P/R/F1 | set intersection over expected/predicted entity lists | Empty predicted set has precision 0 when expected is non-empty. Empty expected set has recall 1.0. |
| Defect count | `mismatch` + `missing` field results | Count, not a percentage. |
| Average latency | total recorded adapter milliseconds / predictions | Offline adapter timings are synthetic instrumentation, not an infrastructure benchmark. |

Aggregate field metrics are calculated from persisted field-level denominators; the service does not average percentages per case. Model-judge or human-adjudication scores are not present in this release and must remain separate if added later.


