import React, { useState } from 'react';
import { SloDefinition, ArchitectureResult } from '../types';
import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';

interface SloCalculatorProps {
  architecture: ArchitectureResult | null;
}

export const SloCalculator: React.FC<SloCalculatorProps> = ({ architecture }) => {
  const { role } = useAuth();
  const services = architecture?.services || [];
  const defaultService = services[0]?.name || 'api-gateway';

  const [selectedService, setSelectedService] = useState<string>(defaultService);
  const [targetPercentage, setTargetPercentage] = useState<number>(99.9);
  const [latencyThreshold, setLatencyThreshold] = useState<number>(250);
  const [sloResult, setSloResult] = useState<SloDefinition | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleCalculate = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.calculateSlo(selectedService, targetPercentage, latencyThreshold);
      setSloResult(res);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'SLO calculation failed');
    } finally {
      setLoading(false);
    }
  };

  const canCalculate = role === 'operator' || role === 'admin';

  return (
    <div className="slo-view">
      <div className="view-header">
        <div>
          <h2>SLO & Error Budget Burn Rate Engine</h2>
          <p className="text-muted">Calculates availability targets and multi-window burn rate alert thresholds using Google SRE methodology.</p>
        </div>
      </div>

      {error && <div className="alert alert-danger">{error}</div>}

      <div className="slo-layout">
        <div className="card slo-input-card">
          <h3>SLO Target Configuration</h3>

          <div className="form-group">
            <label>Service Target:</label>
            {services.length > 0 ? (
              <select
                className="form-control"
                value={selectedService}
                onChange={(e) => setSelectedService(e.target.value)}
              >
                {services.map((s) => (
                  <option key={s.name} value={s.name}>
                    {s.name} ({s.role})
                  </option>
                ))}
              </select>
            ) : (
              <input
                type="text"
                className="form-control"
                value={selectedService}
                onChange={(e) => setSelectedService(e.target.value)}
              />
            )}
          </div>

          <div className="form-group">
            <label>Availability Target (%):</label>
            <div className="slider-row">
              <input
                type="range"
                min="95"
                max="99.99"
                step="0.01"
                value={targetPercentage}
                onChange={(e) => setTargetPercentage(parseFloat(e.target.value))}
              />
              <span className="slider-val">{targetPercentage.toFixed(2)}%</span>
            </div>
          </div>

          <div className="form-group">
            <label>p99 Latency Threshold (ms):</label>
            <input
              type="number"
              className="form-control"
              value={latencyThreshold}
              onChange={(e) => setLatencyThreshold(parseInt(e.target.value, 10))}
            />
          </div>

          <button
            className="btn btn-primary btn-block"
            onClick={handleCalculate}
            disabled={loading || !canCalculate}
            title={!canCalculate ? 'Requires operator or admin role' : ''}
          >
            {loading ? 'Calculating...' : 'Compute Multi-Window Burn Rates'}
          </button>
        </div>

        <div className="slo-results-pane">
          {!sloResult ? (
            <div className="card empty-state">
              <div className="empty-icon">🎯</div>
              <h3>Configure Target & Compute</h3>
              <p>Configure availability percentage and latency targets to calculate multi-window error budget burn rate alert triggers.</p>
            </div>
          ) : (
            <div className="card slo-details-card">
              <div className="slo-summary-header">
                <h3>{sloResult.service} Availability SLO: {sloResult.target_percentage}%</h3>
                <span className="badge badge-success">30-Day Rolling Window</span>
              </div>

              <div className="slo-expressions">
                <div className="expr-block">
                  <strong>Good Request Definition:</strong>
                  <code>{sloResult.good_request_expr}</code>
                </div>
                <div className="expr-block">
                  <strong>Total Requests:</strong>
                  <code>{sloResult.total_request_expr}</code>
                </div>
                <div className="expr-block">
                  <strong>SLI Ratio Formula:</strong>
                  <code>{sloResult.slo_expr}</code>
                </div>
                {sloResult.latency_slo && (
                  <div className="expr-block">
                    <strong>Latency SLI (p99):</strong>
                    <code>{sloResult.latency_slo}</code>
                  </div>
                )}
              </div>

              <h4 className="mt-4">Google SRE Multi-Window Burn Rate Alerts</h4>
              <table className="burn-table">
                <thead>
                  <tr>
                    <th>Window</th>
                    <th>Burn Rate</th>
                    <th>Budget Consumed</th>
                    <th>Severity</th>
                    <th>PromQL Alert Condition</th>
                  </tr>
                </thead>
                <tbody>
                  {sloResult.burn_alerts.map((b, i) => (
                    <tr key={i}>
                      <td className="font-bold">{b.window}</td>
                      <td>{b.burn_rate}x</td>
                      <td>{b.burn_rate === 14.4 ? '2% in 1 hour' : b.burn_rate === 6 ? '5% in 6 hours' : '100% in 30 days'}</td>
                      <td>
                        <span className={`badge badge-${b.severity === 'critical' ? 'danger' : b.severity === 'warning' ? 'warning' : 'info'}`}>
                          {b.severity.toUpperCase()}
                        </span>
                      </td>
                      <td className="query-cell"><code>{b.expr}</code></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
