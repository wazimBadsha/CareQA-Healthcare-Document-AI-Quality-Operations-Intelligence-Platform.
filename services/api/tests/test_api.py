def test_health_and_seeded_dataset(client):
    assert client.get("/health/live").json() == {"status": "ok"}
    assert client.get("/health/ready").json() == {"status": "ready"}
    datasets = client.get("/api/v1/datasets").json()
    assert len(datasets) == 1
    assert datasets[0]["case_count"] == 24


def test_run_persists_item_results_and_metrics(client):
    dataset = client.get("/api/v1/datasets").json()[0]
    created = client.post("/api/v1/runs", json={"dataset_id": dataset["id"], "seed": 7})
    assert created.status_code == 201
    run = created.json()
    assert run["status"] == "completed"
    metrics = {item["metric_name"]: item["metric_value"] for item in client.get(f"/api/v1/runs/{run['id']}/metrics").json()}
    assert 0 <= metrics["field_normalized_accuracy"] <= 1
    assert metrics["defect_count"] > 0
    results = client.get(f"/api/v1/runs/{run['id']}/results?limit=500").json()["items"]
    assert len(results) == 24 * 8
    assert {item["outcome"] for item in results} >= {"exact_match", "mismatch"}


def test_compare_requires_compatible_runs(client):
    dataset = client.get("/api/v1/datasets").json()[0]
    first = client.post("/api/v1/runs", json={"dataset_id": dataset["id"], "seed": 1}).json()
    second = client.post("/api/v1/runs", json={"dataset_id": dataset["id"], "seed": 2}).json()
    comparison = client.get("/api/v1/compare", params={"baseline": first["id"], "candidate": second["id"]})
    assert comparison.status_code == 200
    assert any(item["metric_name"] == "defect_count" for item in comparison.json()["deltas"])


def test_tenant_scope_and_synthetic_document_ingest(client):
    rejected = client.get("/api/v1/datasets", headers={"X-Tenant-Id": "unknown"})
    assert rejected.status_code == 404
    document = client.post("/api/v1/documents", json={"storage_key": "synthetic/case.txt", "extracted_text": "Synthetic only."})
    assert document.status_code == 201
    detail = client.get(f"/api/v1/documents/{document.json()['id']}")
    assert detail.json()["extracted_text"] == "Synthetic only."
