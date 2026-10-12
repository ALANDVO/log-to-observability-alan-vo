import pytest

def test_full_observability_api_workflow(client, operator_token, admin_token, viewer_token):
    op_headers = {"Authorization": f"Bearer {operator_token}"}
    view_headers = {"Authorization": f"Bearer {viewer_token}"}
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    sample_logs = (
        '{"ts": "2026-10-12T10:00:00Z", "service": "api-gateway", "method": "GET", "path": "/orders", "status": 200, "duration_ms": 30, "downstream": "order-service"}\n'
        '{"ts": "2026-10-12T10:00:01Z", "service": "order-service", "method": "POST", "path": "/orders", "status": 200, "duration_ms": 70, "datastore": "postgres"}\n'
    )

    # 1. Analyze logs
    res = client.post("/api/architecture/analyze", json={"logs": sample_logs, "title": "Test Run"}, headers=op_headers)
    assert res.status_code == 200
    arch_data = res.json()
    run_id = arch_data["id"]
    assert run_id is not None
    assert len(arch_data["services"]) == 2

    # 2. List runs (viewer)
    res = client.get("/api/architecture/runs?limit=10&offset=0", headers=view_headers)
    assert res.status_code == 200
    runs = res.json()
    assert len(runs) >= 1
    assert runs[0]["id"] == run_id

    # 3. Get run details (viewer)
    res = client.get(f"/api/architecture/runs/{run_id}", headers=view_headers)
    assert res.status_code == 200
    assert res.json()["title"] == "Test Run"

    # 4. Generate Dashboard from run (operator)
    res = client.post("/api/observability/dashboards/generate", json={"architecture_id": run_id}, headers=op_headers)
    assert res.status_code == 200
    dash = res.json()
    assert dash["schema_version"] == 39
    assert len(dash["panels"]) >= 4

    # 5. Generate Alerts from run (operator)
    res = client.post("/api/observability/alerts/generate", json={"architecture_id": run_id}, headers=op_headers)
    assert res.status_code == 200
    alerts = res.json()
    assert len(alerts["rules"]) >= 2

    # 6. Calculate SLO (operator)
    res = client.post("/api/observability/slo/calculate", json={"service": "order-service", "target_percentage": 99.9}, headers=op_headers)
    assert res.status_code == 200
    slo = res.json()
    assert slo["service"] == "order-service"
    assert len(slo["burn_alerts"]) == 3

    # 7. Check Audit Logs (admin)
    res = client.get("/api/observability/audit-logs", headers=admin_headers)
    assert res.status_code == 200
    audit_logs = res.json()
    assert len(audit_logs) >= 1
    assert audit_logs[0]["action"] == "ANALYZE_LOGS"

    # 8. Delete run (admin)
    res = client.delete(f"/api/architecture/runs/{run_id}", headers=admin_headers)
    assert res.status_code == 200
    assert res.json()["status"] == "deleted"

    # 9. Verify deletion (viewer)
    res = client.get(f"/api/architecture/runs/{run_id}", headers=view_headers)
    assert res.status_code == 404

def test_health_and_stats_endpoints(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"

    res = client.get("/api/stats")
    assert res.status_code == 200
    assert "version" in res.json()
