import React, { useState } from 'react';
import { api } from '../api/client';
import { ArchitectureResult } from '../types';
import { useAuth } from '../context/AuthContext';

interface LogIngestionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (result: ArchitectureResult) => void;
}

const SAMPLE_JSON_LOGS = `{"ts": "2026-10-12T10:00:00Z", "service": "api-gateway", "method": "GET", "path": "/api/v1/orders", "status": 200, "duration_ms": 42, "caller": "192.168.1.10", "downstream": "order-service", "msg": "forwarded to order-service"}
{"ts": "2026-10-12T10:00:01Z", "service": "order-service", "method": "POST", "path": "/orders", "status": 200, "duration_ms": 115, "caller": "api-gateway", "downstream": "payment-service", "datastore": "postgres", "msg": "saved order in postgres"}
{"ts": "2026-10-12T10:00:02Z", "service": "payment-service", "method": "POST", "path": "/charge", "status": 200, "duration_ms": 85, "caller": "order-service", "datastore": "redis", "msg": "cached charge token in redis"}
{"ts": "2026-10-12T10:00:03Z", "service": "order-service", "level": "WARN", "msg": "db pool near limit: 94% postgres connections in use", "datastore": "postgres"}
{"ts": "2026-10-12T10:00:04Z", "service": "api-gateway", "level": "ERROR", "method": "POST", "path": "/api/v1/orders", "status": 504, "duration_ms": 3200, "downstream": "order-service", "msg": "gateway timeout waiting for order-service"}`;

const SAMPLE_NGINX_LOGS = `192.168.1.100 - - [12/Oct/2026:10:00:00 +0000] "GET /api/v1/users HTTP/1.1" 200 1420 "-" "Mozilla/5.0"
192.168.1.101 - - [12/Oct/2026:10:00:01 +0000] "POST /api/v1/orders HTTP/1.1" 201 320 "-" "curl/7.88"
192.168.1.102 - - [12/Oct/2026:10:00:02 +0000] "POST /api/v1/payments HTTP/1.1" 502 210 "-" "Mozilla/5.0"`;

export const LogIngestionModal: React.FC<LogIngestionModalProps> = ({ isOpen, onClose, onSuccess }) => {
  const { role } = useAuth();
  const [title, setTitle] = useState('E-Commerce Cluster Logs');
  const [logs, setLogs] = useState(SAMPLE_JSON_LOGS);
  const [enableLlm, setEnableLlm] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!logs.trim()) {
      setError('Please provide log data to analyze.');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const result = await api.analyzeLogs(logs, title, enableLlm);
      onSuccess(result);
      onClose();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Analysis failed');
    } finally {
      setLoading(false);
    }
  };

  const canIngest = role === 'operator' || role === 'admin';

  return (
    <div className="modal-backdrop">
      <div className="modal-content card">
        <div className="modal-header">
          <h3>Ingest & Analyze Logs</h3>
          <button className="btn-close" onClick={onClose}>✕</button>
        </div>

        {error && <div className="alert alert-danger">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Analysis Run Title:</label>
            <input
              type="text"
              className="form-control"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Production Cluster Logs"
              required
            />
          </div>

          <div className="sample-buttons">
            <span className="text-muted text-sm">Presets:</span>
            <button type="button" className="btn-preset" onClick={() => setLogs(SAMPLE_JSON_LOGS)}>
              Microservice JSON Lines
            </button>
            <button type="button" className="btn-preset" onClick={() => setLogs(SAMPLE_NGINX_LOGS)}>
              Nginx Access Logs
            </button>
          </div>

          <div className="form-group mt-2">
            <label>Raw Log Content (Multi-line):</label>
            <textarea
              className="form-control font-mono"
              rows={8}
              value={logs}
              onChange={(e) => setLogs(e.target.value)}
              placeholder="Paste raw log lines here..."
              required
            />
          </div>

          <div className="checkbox-group mt-3">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={enableLlm}
                onChange={(e) => setEnableLlm(e.target.checked)}
              />
              <span>Enable Opt-In LLM Advisory Assessment (Requires operator configured key)</span>
            </label>
            <small className="text-muted block ml-5">
              Deterministic offline topology, metric mappings, and alert rules run without any LLM key.
            </small>
          </div>

          <div className="modal-footer mt-4">
            <button type="button" className="btn btn-secondary" onClick={onClose}>
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={loading || !canIngest}
              title={!canIngest ? 'Requires operator or admin role' : ''}
            >
              {loading ? 'Analyzing...' : 'Run Architecture Detection'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
