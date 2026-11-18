async function getOverview() {
  const base = process.env.CAREQA_API_URL ?? "http://localhost:8000";
  try {
    const response = await fetch(`${base}/api/v1/overview?cases=24&seed=42`, { cache: "no-store" });
    if (!response.ok) throw new Error(`API returned ${response.status}`);
    return await response.json();
  } catch {
    return null;
  }
}
function pct(value?: number) { return value === undefined ? "—" : `${(value * 100).toFixed(1)}%`; }
export default async function Home() {
  const data = await getOverview();
  const metrics = data?.metrics;
  return <main className="shell">
    <header className="topbar"><div className="brand"><span className="brand-mark">CQ</span><span>CareQA</span></div><span className="environment">SYNTHETIC DEMO · OFFLINE EVALUATION</span></header>
    <section className="hero"><div><p className="eyebrow">HEALTHCARE DOCUMENT INTELLIGENCE</p><h1>Quality you can<br/><em>measure.</em></h1><p className="lead">Evaluate structured extraction, expose quality defects and compare repeatable AI evaluation runs — without sending patient data to an external service.</p></div><div className="hero-note"><span className="pulse"/> <strong>Deterministic benchmark</strong><small>Seed 42 · 24 synthetic claim cases</small><small>Provider: offline-mock</small></div></section>
    {!data && <div className="notice">API unavailable. Start the CareQA API to view live evaluation metrics.</div>}
    <section className="section-head"><div><p className="eyebrow">EXECUTIVE OVERVIEW</p><h2>Evaluation snapshot</h2></div><span className="live">● {data ? "API CONNECTED" : "OFFLINE"}</span></section>
    <section className="metric-grid">
      <Metric label="FIELD ACCURACY" value={pct(metrics?.field_accuracy)} detail="Correct fields / compared fields" />
      <Metric label="COMPLETENESS" value={pct(metrics?.completeness)} detail="Required fields populated" />
      <Metric label="F1 SCORE" value={pct(metrics?.f1)} detail="Micro-aggregated field score" />
      <Metric label="DEFECTS FOUND" value={metrics?.defect_count?.toString() ?? "—"} detail="False positives + false negatives" />
    </section>
    <section className="content-grid"><article className="panel"><div className="panel-title"><div><p className="eyebrow">BENCHMARK</p><h3>Run configuration</h3></div><span className="tag">REPRODUCIBLE</span></div><div className="rows"><DataRow label="Dataset" value={data?.dataset?.name ?? "Synthetic Claims Benchmark"}/><DataRow label="Dataset version" value={data?.dataset?.version ?? "1.0.0"}/><DataRow label="Cases evaluated" value={metrics?.case_count?.toString() ?? "—"}/><DataRow label="Model adapter" value={data?.model?.provider ?? "offline-mock"}/><DataRow label="Random seed" value={data?.dataset?.seed?.toString() ?? "42"}/><DataRow label="Evaluation" value="Deterministic · field-level"/></div></article><article className="panel"><p className="eyebrow">QUALITY SIGNALS</p><h3>Metric interpretation</h3><div className="signal"><span className="signal-dot green"/><div><strong>Field accuracy</strong><p>Normalised field comparison against verified synthetic reference values.</p></div></div><div className="signal"><span className="signal-dot blue"/><div><strong>Completeness</strong><p>Percentage of required reference fields that are populated in model output.</p></div></div><div className="signal"><span className="signal-dot amber"/><div><strong>Defects</strong><p>Incorrect, missing or unexpected extracted values in the benchmark.</p></div></div></article></section>
    <footer><span>CareQA · Portfolio engineering demonstration</span><span>No real patient data · Not a clinical product</span></footer>
  </main>;
}
function Metric({label,value,detail}:{label:string;value:string;detail:string}) { return <article className="metric"><p>{label}</p><strong>{value}</strong><small>{detail}</small></article>; }
function DataRow({label,value}:{label:string;value:string}) { return <div className="data-row"><span>{label}</span><strong>{value}</strong></div>; }
