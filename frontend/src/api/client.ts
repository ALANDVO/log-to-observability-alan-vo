import {
  ArchitectureResult,
  GrafanaDashboard,
  AlertGroup,
  SloDefinition,
  UserPrincipal,
  EvaluationReport
} from '../types';

let inMemoryToken: string | null = null;

export const setAuthToken = (token: string | null) => {
  inMemoryToken = token;
};

export const getAuthToken = (): string | null => {
  return inMemoryToken;
};

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers || {});
  headers.set('Content-Type', 'application/json');

  if (inMemoryToken) {
    headers.set('Authorization', `Bearer ${inMemoryToken}`);
  }

  const response = await fetch(endpoint, {
    ...options,
    headers
  });

  if (!response.ok) {
    let errorMsg = `HTTP Error ${response.status}`;
    try {
      const errJson = await response.json();
      if (errJson && errJson.detail) {
        errorMsg = errJson.detail;
      }
    } catch {
      // Use fallback error message
    }
    throw new Error(errorMsg);
  }

  return response.json() as Promise<T>;
}

export const api = {
  // Auth
  async loginDemo(username: string, role: string): Promise<{ access_token: string; user: UserPrincipal }> {
    const data = await request<{ access_token: string; user: UserPrincipal }>('/api/auth/demo-token', {
      method: 'POST',
      body: JSON.stringify({ username, role })
    });
    setAuthToken(data.access_token);
    return data;
  },

  async getMe(): Promise<UserPrincipal> {
    return request<UserPrincipal>('/api/auth/me');
  },

  async logout(): Promise<void> {
    try {
      await request('/api/auth/logout', { method: 'POST' });
    } finally {
      setAuthToken(null);
    }
  },

  // Architecture Detection
  async analyzeLogs(logs: string, title?: string, enableLlmAdvisory: boolean = false): Promise<ArchitectureResult> {
    return request<ArchitectureResult>('/api/architecture/analyze', {
      method: 'POST',
      body: JSON.stringify({ logs, title, enable_llm_advisory: enableLlmAdvisory })
    });
  },

  async listRuns(limit: number = 20, offset: number = 0): Promise<ArchitectureResult[]> {
    return request<ArchitectureResult[]>(`/api/architecture/runs?limit=${limit}&offset=${offset}`);
  },

  async getRun(id: number): Promise<ArchitectureResult> {
    return request<ArchitectureResult>(`/api/architecture/runs/${id}`);
  },

  async deleteRun(id: number): Promise<{ status: string; id: number }> {
    return request<{ status: string; id: number }>(`/api/architecture/runs/${id}`, {
      method: 'DELETE'
    });
  },

  // Observability Generation
  async generateDashboard(params: { architecture_id?: number; logs?: string; title?: string }): Promise<GrafanaDashboard> {
    return request<GrafanaDashboard>('/api/observability/dashboards/generate', {
      method: 'POST',
      body: JSON.stringify(params)
    });
  },

  async generateAlerts(params: { architecture_id?: number; logs?: string }): Promise<AlertGroup> {
    return request<AlertGroup>('/api/observability/alerts/generate', {
      method: 'POST',
      body: JSON.stringify(params)
    });
  },

  async calculateSlo(service: string, targetPercentage: number = 99.9, latencyThresholdMs: number = 250): Promise<SloDefinition> {
    return request<SloDefinition>('/api/observability/slo/calculate', {
      method: 'POST',
      body: JSON.stringify({
        service,
        target_percentage: targetPercentage,
        latency_threshold_ms: latencyThresholdMs
      })
    });
  },

  // Evaluation
  async getBenchmark(): Promise<EvaluationReport> {
    return request<EvaluationReport>('/api/evaluation/benchmark');
  },

  async runBenchmark(customLogs?: string): Promise<EvaluationReport> {
    return request<EvaluationReport>('/api/evaluation/run', {
      method: 'POST',
      body: JSON.stringify({ custom_logs: customLogs })
    });
  }
};
