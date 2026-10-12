import React, { useState, useEffect } from 'react';
import { EvaluationReport } from '../types';
import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';

export const EvaluationView: React.FC = () => {
  const { role } = useAuth();
  const [report, setReport] = useState<EvaluationReport | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [running, setRunning] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchBenchmark = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getBenchmark();
      setReport(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to fetch evaluation report');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBenchmark();
  }, []);

  const handleRunEvaluation = async () => {
    setRunning(true);
    setError(null);
    try {
      const data = await api.runBenchmark();
      setReport(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to run evaluation benchmark');
    } finally {
      setRunning(false);
    }
  };

  const canRun = role === 'operator' || role === 'admin';

  return (
    <div className="evaluation-view">
      <div className="view-header">
        <div>
          <h2>AI & Machine Learning Evaluation</h2>
          <p className="text-muted">Rigorous, reproducible evaluation metrics against labeled microservice topology baselines.</p>
        </div>
        <button
          className="btn btn-primary"
          onClick={handleRunEvaluation}
          disabled={running || !canRun}
          title={!canRun ? 'Requires operator or admin role' : ''}
        >
          {running ? 'Running Benchmark...' : '🔄 Run Evaluation Benchmark'}
        </button>
      </div>

      {error && <div className="alert alert-danger">{error}</div>}

      {loading ? (
        <div className="card empty-state">Loading evaluation benchmark...</div>
      ) : report ? (
        <div className="evaluation-content">
          <div className="metric-tiles">
            <div className="metric-tile card">
              <span className="metric-title">Composite F1 Score</span>
              <span className="metric-value font-mono">{(report.f1_score * 100).toFixed(1)}%</span>
              <span className="metric-subtitle">Harmonic mean of topology & edge discovery</span>
            </div>
            <div className="metric-tile card">
              <span className="metric-title">Precision</span>
              <span className="metric-value font-mono text-success">{(report.precision * 100).toFixed(1)}%</span>
              <span className="metric-subtitle">True services & edges discovered</span>
            </div>
            <div className="metric-tile card">
              <span className="metric-title">Recall</span>
              <span className="metric-value font-mono text-info">{(report.recall * 100).toFixed(1)}%</span>
              <span className="metric-subtitle">Coverage against labeled ground truth</span>
            </div>
            <div className="metric-tile card">
              <span className="metric-title">Failure Modes</span>
              <span className="metric-value font-mono">{report.failure_patterns_detected}</span>
              <span className="metric-subtitle">Injected anomalies classified</span>
            </div>
          </div>

          <div className="card benchmark-details-card mt-4">
            <h3>Benchmark Provenance & Baseline Details</h3>
            <div className="table-responsive">
              <table className="eval-table">
                <tbody>
                  <tr>
                    <td><strong>Dataset</strong></td>
                    <td><code>{report.dataset_name}</code> (Synthetic e-commerce microservices)</td>
                  </tr>
                  <tr>
                    <td><strong>Log Lines Processed</strong></td>
                    <td>{report.total_log_lines} multi-service events</td>
                  </tr>
                  <tr>
                    <td><strong>Services Discovered</strong></td>
                    <td>{report.services_detected} / {report.expected_services} expected services</td>
                  </tr>
                  <tr>
                    <td><strong>Communication Edges</strong></td>
                    <td>{report.edges_detected} / {report.expected_edges} expected dependencies</td>
                  </tr>
                  <tr>
                    <td><strong>Evaluation Timestamp</strong></td>
                    <td>{new Date(report.evaluated_at).toLocaleString()}</td>
                  </tr>
                  <tr>
                    <td><strong>Evaluation Notes</strong></td>
                    <td>{report.notes}</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div className="limitations-box mt-4">
              <h4>Limitations and Boundary Conditions</h4>
              <ul>
                <li><strong>Log Coverage:</strong> Unobserved communication paths during low-traffic windows cannot be inferred without corresponding trace records.</li>
                <li><strong>Ephemeral IPs:</strong> Dynamic container IPs require structured caller tags or reverse proxy headers for cross-host edge inference.</li>
                <li><strong>Advisory LLM Independence:</strong> Core evaluation metrics are computed offline deterministically; opt-in LLM advisory analysis is strictly supplementary.</li>
              </ul>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
};
