import React from 'react';
import { useAuth } from '../context/AuthContext';

interface HeaderProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  onOpenIngest: () => void;
}

export const Header: React.FC<HeaderProps> = ({ activeTab, setActiveTab, onOpenIngest }) => {
  const { user, role, loginDemo, logout } = useAuth();

  const handleRoleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    loginDemo(e.target.value);
  };

  return (
    <header className="header">
      <div className="header-brand">
        <span className="brand-logo">🔭</span>
        <div>
          <h1 className="brand-title">Log to Observability</h1>
          <span className="brand-sub">Alan Vo | AI & Machine Learning Pipeline</span>
        </div>
      </div>

      <nav className="header-nav">
        <button
          className={`nav-btn ${activeTab === 'architecture' ? 'active' : ''}`}
          onClick={() => setActiveTab('architecture')}
        >
          Topology & Architecture
        </button>
        <button
          className={`nav-btn ${activeTab === 'dashboards' ? 'active' : ''}`}
          onClick={() => setActiveTab('dashboards')}
        >
          Grafana Dashboards
        </button>
        <button
          className={`nav-btn ${activeTab === 'alerts' ? 'active' : ''}`}
          onClick={() => setActiveTab('alerts')}
        >
          Alert Rules
        </button>
        <button
          className={`nav-btn ${activeTab === 'slo' ? 'active' : ''}`}
          onClick={() => setActiveTab('slo')}
        >
          SLO Engine
        </button>
        <button
          className={`nav-btn ${activeTab === 'evaluation' ? 'active' : ''}`}
          onClick={() => setActiveTab('evaluation')}
        >
          AI/ML Evaluation
        </button>
      </nav>

      <div className="header-actions">
        <button className="btn btn-primary" onClick={onOpenIngest}>
          + Ingest Logs
        </button>

        <div className="auth-pill">
          <span className="demo-badge">DEMO MODE</span>
          <select className="role-select" value={role} onChange={handleRoleChange} title="Switch demo role">
            <option value="viewer">Viewer (Read-Only)</option>
            <option value="operator">Operator (Analyze/Export)</option>
            <option value="admin">Admin (Full Control)</option>
          </select>
          <span className="user-name">{user?.username || 'Guest'}</span>
          <button className="btn-logout" onClick={() => logout()} title="Logout">✕</button>
        </div>
      </div>
    </header>
  );
};
