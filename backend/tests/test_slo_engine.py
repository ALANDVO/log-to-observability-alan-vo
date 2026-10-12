import pytest
from app.services.slo_engine import SloEngine

def test_slo_multi_window_burn_rates():
    slo = SloEngine.calculate_slo("payment-service", target_percentage=99.9, latency_threshold_ms=250.0)

    assert slo.service == "payment-service"
    assert slo.target_percentage == 99.9
    assert len(slo.burn_alerts) == 3

    # Check 1h, 6h, 24h windows
    windows = {b.window: b.burn_rate for b in slo.burn_alerts}
    assert windows["1h"] == 14.4
    assert windows["6h"] == 6.0
    assert windows["24h"] == 1.0

    # Verify PromQL expressions
    assert "rate(http_requests_total" in slo.good_request_expr
    assert "payment-service" in slo.slo_expr
    assert slo.latency_slo is not None
    assert "0.25" in slo.latency_slo
