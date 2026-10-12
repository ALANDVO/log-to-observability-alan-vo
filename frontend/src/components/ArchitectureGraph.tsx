import React, { useState } from 'react';
import { ArchitectureResult, ServiceNode, DatastoreNode } from '../types';

interface ArchitectureGraphProps {
  architecture: ArchitectureResult | null;
  onRefresh?: () => void;
}

export const ArchitectureGraph: React.FC<ArchitectureGraphProps> = ({ architecture }) => {
  const [selectedNode, setSelectedNode] = useState<ServiceNode | DatastoreNode | null>(null);

  if (!architecture || (!architecture.services.length && !architecture.datastores.length)) {
    return (
      <div className="card empty-state">
        <div className="empty-icon">📊</div>
        <h3>No Architecture Detected Yet</h3>
        <p>Ingest a stream of logs (JSON lines, Syslog, or Nginx) to automatically discover service topology, communication edges, and datastores.</p>
      </div>
    );
  }

  const { services, topology, datastores, failure_patterns } = architecture;

  // Compute node layout positions
  const totalNodes = services.length + datastores.length;
  const radius = Math.min(260, Math.max(160, totalNodes * 28));
  const centerX = 380;
  const centerY = 260;

  const nodePositions: Record<string, { x: number; y: number }> = {};
  const allNodeNames = [
    ...services.map(s => s.name),
    ...datastores.map(d => d.name)
  ];

  allNodeNames.forEach((name, idx) => {
    const angle = (idx / totalNodes) * 2 * Math.PI - Math.PI / 2;
    nodePositions[name] = {
      x: centerX + radius * Math.cos(angle),
      y: centerY + radius * Math.sin(angle)
    };
  });

  return (
    <div className="architecture-view">
      <div className="overview-stats">
        <div className="stat-card">
          <span className="stat-label">Services Discovered</span>
          <span className="stat-value">{services.length}</span>
        </div>
        <div className="stat-card">
          <span className="stat-label">Communication Edges</span>
          <span className="stat-value">{topology.length}</span>
        </div>
        <div className="stat-card">
          <span className="stat-label">Datastores Identified</span>
          <span className="stat-value">{datastores.length}</span>
        </div>
        <div className="stat-card">
          <span className="stat-label">Failure Patterns</span>
          <span className="stat-value text-danger">{failure_patterns.length}</span>
        </div>
      </div>

      <div className="graph-container">
        <div className="graph-svg-wrapper">
          <svg className="topology-svg" viewBox="0 0 760 520">
            <defs>
              <marker
                id="arrow"
                viewBox="0 0 10 10"
                refX="22"
                refY="5"
                markerWidth="6"
                markerHeight="6"
                orient="auto-start-reverse"
              >
                <path d="M 0 0 L 10 5 L 0 10 z" fill="#64748b" />
              </marker>
            </defs>

            {/* Edges */}
            {topology.map((edge, idx) => {
              const src = nodePositions[edge.source];
              const tgt = nodePositions[edge.target];
              if (!src || !tgt) return null;

              return (
                <g key={`edge-${idx}`} className="edge-group">
                  <line
                    x1={src.x}
                    y1={src.y}
                    x2={tgt.x}
                    y2={tgt.y}
                    stroke={edge.failure_count > 0 ? '#ef4444' : '#64748b'}
                    strokeWidth={Math.min(4, Math.max(1.5, Math.log10(edge.call_count + 1) * 2))}
                    markerEnd="url(#arrow)"
                    strokeDasharray={edge.protocol === 'queue' ? '4,4' : undefined}
                  />
                  <text
                    x={(src.x + tgt.x) / 2}
                    y={(src.y + tgt.y) / 2 - 6}
                    className="edge-label"
                    textAnchor="middle"
                  >
                    {edge.protocol.toUpperCase()} ({edge.call_count})
                  </text>
                </g>
              );
            })}

            {/* Service Nodes */}
            {services.map((svc) => {
              const pos = nodePositions[svc.name] || { x: centerX, y: centerY };
              const isSelected = selectedNode?.name === svc.name;
              const isGateway = svc.role === 'gateway';

              return (
                <g
                  key={`svc-${svc.name}`}
                  className={`node-group ${isSelected ? 'selected' : ''}`}
                  onClick={() => setSelectedNode(svc)}
                  style={{ cursor: 'pointer' }}
                >
                  <circle
                    cx={pos.x}
                    cy={pos.y}
                    r={isGateway ? 24 : 20}
                    fill={isGateway ? '#06b6d4' : svc.role === 'worker' ? '#a855f7' : '#3b82f6'}
                    stroke={isSelected ? '#f8fafc' : '#1e293b'}
                    strokeWidth={isSelected ? 3 : 1.5}
                  />
                  <text
                    x={pos.x}
                    y={pos.y + 36}
                    textAnchor="middle"
                    className="node-label"
                  >
                    {svc.name}
                  </text>
                  {svc.error_count > 0 && (
                    <circle cx={pos.x + 14} cy={pos.y - 14} r="8" fill="#ef4444" />
                  )}
                </g>
              );
            })}

            {/* Datastore Nodes */}
            {datastores.map((ds) => {
              const pos = nodePositions[ds.name] || { x: centerX, y: centerY };
              const isSelected = selectedNode?.name === ds.name;

              return (
                <g
                  key={`ds-${ds.name}`}
                  className={`node-group ${isSelected ? 'selected' : ''}`}
                  onClick={() => setSelectedNode(ds)}
                  style={{ cursor: 'pointer' }}
                >
                  <rect
                    x={pos.x - 18}
                    y={pos.y - 18}
                    width="36"
                    height="36"
                    rx="6"
                    fill={ds.type === 'cache' ? '#f59e0b' : ds.type === 'queue' ? '#ec4899' : '#10b981'}
                    stroke={isSelected ? '#f8fafc' : '#1e293b'}
                    strokeWidth={isSelected ? 3 : 1.5}
                  />
                  <text
                    x={pos.x}
                    y={pos.y + 32}
                    textAnchor="middle"
                    className="node-label"
                  >
                    {ds.name}
                  </text>
                </g>
              );
            })}
          </svg>
        </div>

        {/* Selected Node Details or Failure Breakdown */}
        <div className="detail-sidebar">
          {selectedNode ? (
            <div className="card node-detail-card">
              <div className="card-header">
                <h4>{selectedNode.name}</h4>
                <button className="btn-close" onClick={() => setSelectedNode(null)}>✕</button>
              </div>

              {'role' in selectedNode ? (
                <div className="detail-content">
                  <div className="detail-row">
                    <span className="label">Role:</span>
                    <span className="badge">{selectedNode.role.toUpperCase()}</span>
                  </div>
                  <div className="detail-row">
                    <span className="label">User Facing:</span>
                    <span>{selectedNode.user_facing ? 'Yes (Public Ingress)' : 'No (Internal API)'}</span>
                  </div>
                  <div className="detail-row">
                    <span className="label">Processed Events:</span>
                    <span>{selectedNode.event_count}</span>
                  </div>
                  <div className="detail-row">
                    <span className="label">Error Count:</span>
                    <span className={selectedNode.error_count > 0 ? 'text-danger' : ''}>
                      {selectedNode.error_count}
                    </span>
                  </div>
                  {selectedNode.p95_latency_ms !== undefined && selectedNode.p95_latency_ms !== null && (
                    <div className="detail-row">
                      <span className="label">p95 Latency:</span>
                      <span>{selectedNode.p95_latency_ms} ms</span>
                    </div>
                  )}
                  <div className="evidence-box">
                    <strong>Evidence:</strong>
                    <p>{selectedNode.evidence}</p>
                  </div>
                </div>
              ) : (
                <div className="detail-content">
                  <div className="detail-row">
                    <span className="label">Datastore Type:</span>
                    <span className="badge badge-success">{selectedNode.type.toUpperCase()}</span>
                  </div>
                  <div className="detail-row">
                    <span className="label">Referencing Services:</span>
                    <span>{selectedNode.touching_services.join(', ') || 'None'}</span>
                  </div>
                  <div className="evidence-box">
                    <strong>Evidence:</strong>
                    <p>{selectedNode.evidence}</p>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="card failure-card">
              <h4>Failure Patterns Detected</h4>
              {failure_patterns.length === 0 ? (
                <p className="text-muted">No systemic failure patterns detected in this log window.</p>
              ) : (
                <div className="failure-list">
                  {failure_patterns.map((fp, i) => (
                    <div key={i} className="failure-item">
                      <div className="failure-header">
                        <span className="badge badge-danger">{fp.pattern_type}</span>
                        <span className="text-muted">{fp.service} ({fp.frequency}x)</span>
                      </div>
                      <p className="failure-summary">{fp.summary}</p>
                      {fp.evidence_lines.length > 0 && (
                        <pre className="evidence-pre">{fp.evidence_lines[0]}</pre>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {architecture.llm_advisory && (
            <div className="card advisory-card">
              <h4>💡 SRE Advisory Assessment</h4>
              <p className="advisory-text">{architecture.llm_advisory}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
