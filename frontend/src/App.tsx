import React, { useState, useEffect } from 'react';
import { ArchitectureResult } from './types';
import { api } from './api/client';
import { Header } from './components/Header';
import { ArchitectureGraph } from './components/ArchitectureGraph';
import { DashboardViewer } from './components/DashboardViewer';
import { AlertRuleViewer } from './components/AlertRuleViewer';
import { SloCalculator } from './components/SloCalculator';
import { EvaluationView } from './components/EvaluationView';
import { LogIngestionModal } from './components/LogIngestionModal';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>('architecture');
  const [currentArchitecture, setCurrentArchitecture] = useState<ArchitectureResult | null>(null);
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadInitialData = async () => {
      try {
        const runs = await api.listRuns(1, 0);
        if (runs.length > 0) {
          setCurrentArchitecture(runs[0]);
        }
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : 'Failed to load initial runs');
      } finally {
        setLoading(false);
      }
    };
    loadInitialData();
  }, []);

  const handleIngestSuccess = (result: ArchitectureResult) => {
    setCurrentArchitecture(result);
    setActiveTab('architecture');
  };

  return (
    <div className="app-container">
      <Header
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onOpenIngest={() => setIsModalOpen(true)}
      />

      <main className="main-content">
        {error && <div className="alert alert-danger">{error}</div>}

        {loading ? (
          <div className="card empty-state">Loading application data...</div>
        ) : (
          <>
            {activeTab === 'architecture' && (
              <ArchitectureGraph architecture={currentArchitecture} />
            )}
            {activeTab === 'dashboards' && (
              <DashboardViewer architecture={currentArchitecture} />
            )}
            {activeTab === 'alerts' && (
              <AlertRuleViewer architecture={currentArchitecture} />
            )}
            {activeTab === 'slo' && (
              <SloCalculator architecture={currentArchitecture} />
            )}
            {activeTab === 'evaluation' && (
              <EvaluationView />
            )}
          </>
        )}
      </main>

      <footer className="footer">
        <p>
          <strong>log-to-observability-alan-vo</strong> &bull; Built by Alan Vo (&lt;alanvo@gmail.com&gt;) &bull; AI, Machine Learning & Observability
        </p>
      </footer>

      <LogIngestionModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSuccess={handleIngestSuccess}
      />
    </div>
  );
};

export default App;
