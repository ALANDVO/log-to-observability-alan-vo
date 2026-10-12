import React, { useState } from 'react';
import { AlertGroup, ArchitectureResult } from '../types';
import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';

interface AlertRuleViewerProps {
  architecture: ArchitectureResult | null;
}

export const AlertRuleViewer: React.FC<AlertRuleViewerProps> = ({ architecture }) => {
  const { role } = useAuth();
  const [alertGroup, setAlertGroup] = useState<AlertGroup | null>(null);
  const [filterSeverity, setFilterSeverity] = useState<string>('all');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleGenerate = async () => {
    if (!architecture?.id && !architecture?.services.length) {
      setError('Please analyze logs first to generate alert rules.');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await api.generateAlerts({
        architecture_id: architecture.id || undefined
      });
      setAlertGroup(res);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Alert rule generation failed');
    } finally {
      setLoading(false);
    }
  };

  const handleExportYaml = () => {
    if (!alertGroup) return;
    const yamlLines = [
      'groups:',
      `  - name: ${alertGroup.name}`,
      '    interval: 30s',
      '    rules:'
    ];
    alertGroup.rules.forEach((r) => {
      yamlLines.push(`      - alert: ${r.alert}`);
      yamlLines.push(`        expr: ${r.expr}`);
      yamlLines.push(`        for: ${r.for_duration}`);
      yamlLines.push(`        labels:`);
      yamlLines.push(`          severity: ${r.severity}`);
      yamlLines.push(`        annotations:`);
      yamlLines.push(`          summary: "${r.summary}"`);
      yamlLines.push(`          runbook_url: "${r.runbook}"`);
    });

    const blob = new Blob([yamlLines.join('\n')], { type: 'text/yaml' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'prometheus-alerts.yaml';
    a.click();
    URL.revokeObjectURL(url);
  };

  const canGenerate = role === 'operator' || role === 'admin';
  const rules = alertGroup?.rules || [];
  const filteredRules = filterSeverity === 'all'
    ? rules
    : rules.filter(r => r.severity.toLowerCase() === filterSeverity.toLowerCase());

  return (
    <div className="alert-viewer">
      <div className="view-header">
        <div>
          <h2>Prometheus Alert Rules</h2>
          <p className="text-muted">Auto-generates Prometheus & Alertmanager rule definitions with threshold triggers and runbooks.</p>
        </div>
        <div className="header-buttons">
          <button
            className="btn btn-primary"
            onClick={handleGenerate}
            disabled={loading || !canGenerate}
            title={!canGenerate ? 'Requires operator or admin role' : ''}
          >
            {loading ? 'Generating...' : '⚡ Generate Prometheus Rules'}
          </button>
          {alertGroup && (
            <button className="btn btn-secondary" onClick={handleExportYaml}>
              💾 Export YAML
            </button>
          )}
        </div>
      </div>

      {error && <div className="alert alert-danger">{error}</div>}

      {!alertGroup ? (
        <div className="card empty-state">
          <div className="empty-icon">🚨</div>
          <h3>No Alert Rules Generated</h3>
          <p>Generate rules based on detected services, latency degradation, error spikes, and database pool saturation.</p>
        </div>
      ) : (
        <div className="alerts-content">
          <div className="filter-bar">
            <span>Filter by Severity:</span>
            <button
              className={`filter-btn ${filterSeverity === 'all' ? 'active' : ''}`}
              onClick={() => setFilterSeverity('all')}
            >
              All ({rules.length})
            </button>
            <button
              className={`filter-btn ${filterSeverity === 'critical' ? 'active' : ''}`}
              onClick={() => setFilterSeverity('critical')}
            >
              Critical ({rules.filter(r => r.severity === 'critical').length})
            </button>
            <button
              className={`filter-btn ${filterSeverity === 'warning' ? 'active' : ''}`}
              onClick={() => setFilterSeverity('warning')}
            >
              Warning ({rules.filter(r => r.severity === 'warning').length})
            </button>
          </div>

          <div className="rules-table-container card">
            <table className="rules-table">
              <thead>
                <tr>
                  <th>Alert Name</th>
                  <th>Severity</th>
                  <th>For</th>
                  <th>PromQL Expression</th>
                  <th>Summary & Runbook</th>
                </tr>
              </thead>
              <tbody>
                {filteredRules.map((rule, idx) => (
                  <tr key={idx}>
                    <td className="font-mono font-bold">{rule.alert}</td>
                    <td>
                      <span className={`badge badge-${rule.severity === 'critical' ? 'danger' : 'warning'}`}>
                        {rule.severity.toUpperCase()}
                      </span>
                    </td>
                    <td>{rule.for_duration}</td>
                    <td className="query-cell">
                      <code>{rule.expr}</code>
                    </td>
                    <td>
                      <p className="rule-summary">{rule.summary}</p>
                      <small className="text-muted">📖 {rule.runbook}</small>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
