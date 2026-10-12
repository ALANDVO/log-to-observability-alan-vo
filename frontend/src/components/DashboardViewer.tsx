import React, { useState } from 'react';
import { GrafanaDashboard, ArchitectureResult } from '../types';
import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';

interface DashboardViewerProps {
  architecture: ArchitectureResult | null;
}

export const DashboardViewer: React.FC<DashboardViewerProps> = ({ architecture }) => {
  const { role } = useAuth();
  const [dashboard, setDashboard] = useState<GrafanaDashboard | null>(null);
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleGenerate = async () => {
    if (!architecture?.id && !architecture?.services.length) {
      setError('Please analyze logs first to generate a dashboard.');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await api.generateDashboard({
        architecture_id: architecture.id || undefined,
        title: `${architecture.title} Dashboard`
      });
      setDashboard(res);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Dashboard generation failed');
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = () => {
    if (!dashboard) return;
    navigator.clipboard.writeText(JSON.stringify(dashboard.raw_json, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    if (!dashboard) return;
    const blob = new Blob([JSON.stringify(dashboard.raw_json, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${dashboard.uid || 'grafana-dashboard'}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const canGenerate = role === 'operator' || role === 'admin';

  return (
    <div className="dashboard-viewer">
      <div className="view-header">
        <div>
          <h2>Grafana Dashboard Generator</h2>
          <p className="text-muted">Auto-generates complete Grafana dashboard JSON (schemaVersion 39+) with RED/USE PromQL panels.</p>
        </div>
        <div className="header-buttons">
          <button
            className="btn btn-primary"
            onClick={handleGenerate}
            disabled={loading || !canGenerate}
            title={!canGenerate ? 'Requires operator or admin role' : ''}
          >
            {loading ? 'Generating...' : '⚡ Generate Grafana Dashboard'}
          </button>
        </div>
      </div>

      {error && <div className="alert alert-danger">{error}</div>}

      {!dashboard ? (
        <div className="card empty-state">
          <div className="empty-icon">📈</div>
          <h3>No Dashboard Generated Yet</h3>
          <p>Click "Generate Grafana Dashboard" to construct PromQL queries for request rates, 5xx error percentages, latency percentiles, and datastore saturation.</p>
        </div>
      ) : (
        <div className="dashboard-content">
          <div className="card dashboard-meta-card">
            <div className="meta-info">
              <h3>{dashboard.title}</h3>
              <span className="badge">UID: {dashboard.uid}</span>
              <span className="badge">Schema: v{dashboard.schema_version}</span>
            </div>
            <div className="meta-actions">
              <button className="btn btn-secondary" onClick={handleCopy}>
                {copied ? '✓ Copied JSON' : '📋 Copy JSON'}
              </button>
              <button className="btn btn-secondary" onClick={handleDownload}>
                💾 Download File
              </button>
            </div>
          </div>

          <div className="panels-grid">
            {dashboard.panels.map((panel) => (
              <div key={panel.id} className="card panel-card">
                <div className="panel-header">
                  <h4>{panel.title}</h4>
                  <span className="badge badge-info">{panel.type}</span>
                </div>
                <div className="query-box">
                  <span className="query-label">PromQL:</span>
                  <code>{panel.expr}</code>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
