"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
type MetricMap = Record<string, number>;
type Dataset = { id: string; name: string; version: string; case_count: number; content_hash: string };
type Run = { id: string; dataset_id: string; status: string; prompt_version: string; evaluator_version: string; random_seed: number; created_at?: string };
type Result = { case_key: string; field_path: string; expected: unknown; actual: unknown; outcome: string; latency_ms: number };
type Overview = { run_count: number; completed_run_count: number; latest_run_id: string | null; metrics: MetricMap; status_counts: Record<string, number> };

function percent(value?: number) { return value === undefined ? "—" : `${(value * 100).toFixed(1)}%`; }
function number(value?: number, digits = 0) { return value === undefined ? "—" : value.toFixed(digits); }
function apiPath(path: string) { return `${API}${path}`; }

export default function Home() {
  const [overview, setOverview] = useState<Overview | null>(null);
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [runs, setRuns] = useState<Run[]>([]);
  const [selectedRun, setSelectedRun] = useState<string | null>(null);
  const [results, setResults] = useState<Result[]>([]);
  const [notice, setNotice] = useState("Loading connected workspace…");
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    try {
      const [overviewResponse, datasetsResponse, runsResponse] = await Promise.all([
        fetch(apiPath("/api/v1/overview"), { cache: "no-store" }),
        fetch(apiPath("/api/v1/datasets"), { cache: "no-store" }),
        fetch(apiPath("/api/v1/runs"), { cache: "no-store" })
      ]);
      if (![overviewResponse, datasetsResponse, runsResponse].every(response => response.ok)) throw new Error("The API returned an error.");
      const nextOverview = await overviewResponse.json() as Overview;
      const nextDatasets = await datasetsResponse.json() as Dataset[];
      const nextRuns = await runsResponse.json() as Run[];
      setOverview(nextOverview); setDatasets(nextDatasets); setRuns(nextRuns);
      setSelectedRun(current => current || nextOverview.latest_run_id || nextRuns[0]?.id || null);
      setNotice("Live data · synthetic workspace");
    } catch {
      setNotice("API unavailable — start the CareQA stack to load real evaluation data.");
    }
  }, []);

  useEffect(() => { void load(); }, [load]);
  useEffect(() => {
    if (!selectedRun) return;
    fetch(apiPath(`/api/v1/runs/${selectedRun}/results?limit=32`)).then(response => response.ok ? response.json() : Promise.reject()).then(data => setResults(data.items)).catch(() => setResults([]));
  }, [selectedRun]);

  const runDemo = async () => {
    const dataset = datasets[0];
    if (!dataset) return setNotice("No dataset is available yet.");
    setBusy(true); setNotice("Running deterministic evaluation…");
    try {
      const response = await fetch(apiPath("/api/v1/runs"), { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ dataset_id: dataset.id, seed: 2026 }) });
      if (!response.ok) throw new Error();
      const run = await response.json() as Run;
      setSelectedRun(run.id); setNotice("Run completed and persisted."); await load();
    } catch { setNotice("Run could not be created. Check the API service."); }
    finally { setBusy(false); }
  };

  const defectRows = useMemo(() => results.filter(result => result.outcome !== "exact_match"), [results]);
  const metrics = overview?.metrics;
  return <main className="shell">
    <header className="topbar">
      <div className="brand"><span className="brand-mark" aria-hidden="true">CQ</span><span>CareQA</span></div>
      <div className="header-right"><span className="env">SYNTHETIC DATA ONLY</span><span className="status"><i />{notice}</span></div>
    </header>

    <section className="hero">
      <div><p className="eyebrow">QUALITY OPERATIONS INTELLIGENCE</p><h1>Evidence for every<br/><em>AI extraction.</em></h1><p>CareQA measures structured-output quality on reproducible, synthetic document benchmarks. It does not provide clinical decision support.</p></div>
      <aside className="hero-card"><p className="eyebrow">OFFLINE BASELINE</p><strong>Deterministic</strong><span>No API key · no patient data</span><button onClick={runDemo} disabled={busy || !datasets.length}>{busy ? "Evaluating…" : "Run benchmark"}</button></aside>
    </section>

    <section className="section-heading"><div><p className="eyebrow">EXECUTIVE OVERVIEW</p><h2>Quality snapshot</h2></div><button className="quiet-button" onClick={() => void load()}>Refresh data</button></section>
    <section className="metric-grid" aria-label="Evaluation metrics">
      <Metric label="NORMALIZED ACCURACY" value={percent(metrics?.field_normalized_accuracy)} detail="Field comparisons after safe normalization" />
      <Metric label="COMPLETENESS" value={percent(metrics?.completeness)} detail="Required output fields populated" />
      <Metric label="ENTITY F1" value={percent(metrics?.entity_f1)} detail="Set-valued care action extraction" />
      <Metric label="DETECTED DEFECTS" value={number(metrics?.defect_count)} detail={`Across ${overview?.completed_run_count ?? 0} completed runs`} tone="amber" />
    </section>

    <section className="content-grid">
      <article className="panel"><div className="panel-head"><div><p className="eyebrow">BENCHMARKS</p><h3>Versioned datasets</h3></div><span className="tag">{datasets.length} ACTIVE</span></div>
        {datasets.length ? datasets.map(dataset => <div className="row" key={dataset.id}><div><strong>{dataset.name}</strong><small>v{dataset.version} · {dataset.case_count} cases</small></div><code>{dataset.content_hash.slice(0, 10)}…</code></div>) : <Empty text="No datasets loaded." />}
      </article>
      <article className="panel"><div className="panel-head"><div><p className="eyebrow">OPERATIONS</p><h3>Run lifecycle</h3></div></div>
        <div className="run-summary"><span>All runs</span><strong>{overview?.run_count ?? "—"}</strong><span>Completed</span><strong>{overview?.completed_run_count ?? "—"}</strong><span>Mean latency</span><strong>{number(metrics?.average_latency_ms)} ms</strong></div>
        <p className="muted">Runs record dataset, prompt, evaluator and seed metadata. Offline runs complete synchronously while retaining a worker-ready boundary.</p>
      </article>
    </section>

    <section className="section-heading history-heading"><div><p className="eyebrow">RUN HISTORY</p><h2>Inspectable evidence</h2></div><span className="muted">Select a run to view persisted field outcomes.</span></section>
    <section className="evidence-grid">
      <article className="panel run-panel"><div className="run-list">{runs.length ? runs.map(run => <button key={run.id} onClick={() => setSelectedRun(run.id)} className={run.id === selectedRun ? "run active" : "run"}><span className={`dot ${run.status}`} /><span><strong>{run.prompt_version}</strong><small>{run.id.slice(0, 8)} · seed {run.random_seed}</small></span><em>{run.status}</em></button>) : <Empty text="Create a benchmark run to populate history." />}</div></article>
      <article className="panel"><div className="panel-head"><div><p className="eyebrow">FIELD RESULTS</p><h3>Recent outcomes</h3></div><span className="tag">{results.length} SHOWN</span></div>
        <div className="table-wrap"><table><thead><tr><th>Case / field</th><th>Expected</th><th>Actual</th><th>Outcome</th></tr></thead><tbody>{results.map((result, index) => <tr key={`${result.case_key}-${result.field_path}-${index}`}><td><strong>{result.case_key}</strong><small>{result.field_path}</small></td><td>{show(result.expected)}</td><td>{show(result.actual)}</td><td><span className={result.outcome === "exact_match" ? "badge pass" : "badge fail"}>{result.outcome.replace("_", " ")}</span></td></tr>)}</tbody></table>{!results.length && <Empty text="No field-level results selected." />}</div>
      </article>
    </section>
    {defectRows.length > 0 && <p className="defect-note">Showing {defectRows.length} non-exact results in the current evidence set. These are controlled synthetic defects used to demonstrate measurable evaluation behavior.</p>}
    <footer><span>CareQA · independent portfolio demonstration</span><span>No real patient data · Not a medical device · No compliance claim</span></footer>
  </main>;
}

function Metric({ label, value, detail, tone = "" }: { label: string; value: string; detail: string; tone?: string }) { return <article className={`metric ${tone}`}><p>{label}</p><strong>{value}</strong><small>{detail}</small></article>; }
function Empty({ text }: { text: string }) { return <p className="empty">{text}</p>; }
function show(value: unknown) { return value === null || value === undefined ? "—" : Array.isArray(value) ? value.join(", ") : String(value); }
