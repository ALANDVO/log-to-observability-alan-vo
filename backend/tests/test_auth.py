import pytest
from fastapi import HTTPException
from app.core.config import Settings
from app.core.auth import create_demo_token, decode_token

def test_unauthenticated_rejection(client):
    res = client.post("/api/architecture/analyze", json={"logs": '{"service": "test"}'})
    assert res.status_code == 401

def test_role_denial_for_viewer(client, viewer_token):
    headers = {"Authorization": f"Bearer {viewer_token}"}
    res = client.post("/api/architecture/analyze", json={"logs": '{"service": "test"}'}, headers=headers)
    assert res.status_code == 403
    assert "Access denied" in res.json()["detail"]

def test_operator_role_permitted(client, operator_token):
    headers = {"Authorization": f"Bearer {operator_token}"}
    res = client.post("/api/architecture/analyze", json={"logs": '{"service": "test"}'}, headers=headers)
    assert res.status_code == 200

def test_production_refuses_demo_mode():
    with pytest.raises(RuntimeError) as exc_info:
        s = Settings(ENVIRONMENT="production", DEMO_MODE=True)
        s.validate_production_safety()
    assert "Demo mode is prohibited in production" in str(exc_info.value)

def test_demo_token_creation_and_decoding():
    token = create_demo_token("analyst-1", "operator")
    principal = decode_token(token)
    assert principal.username == "analyst-1"
    assert "operator" in principal.roles
    assert principal.is_demo is True
