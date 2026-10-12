export interface ServiceNode {
  name: string;
  role: string;
  user_facing: boolean;
  evidence: string;
  event_count: number;
  error_count: number;
  p95_latency_ms?: number | null;
}

export interface TopologyEdge {
  source: string;
  target: string;
  protocol: string;
  call_count: number;
  failure_count: number;
  avg_latency_ms?: number | null;
}

export interface DatastoreNode {
  name: string;
  type: string;
  touching_services: string[];
  evidence: string;
}

export interface FailurePattern {
  pattern_type: string;
  service: string;
  frequency: number;
  summary: string;
  evidence_lines: string[];
}

export interface ArchitectureResult {
  id?: number | null;
  created_at: string;
  title: string;
  log_count: number;
  services: ServiceNode[];
  topology: TopologyEdge[];
  datastores: DatastoreNode[];
  failure_patterns: FailurePattern[];
  llm_advisory?: string | null;
  is_llm_assisted: boolean;
}

export interface GrafanaPanel {
  id: number;
  title: string;
  type: string;
  expr: string;
  grid_pos: { h: number; w: number; x: number; y: number };
}

export interface GrafanaDashboard {
  title: string;
  uid: string;
  schema_version: number;
  panels: GrafanaPanel[];
  raw_json: Record<string, unknown>;
}

export interface PrometheusAlert {
  alert: string;
  expr: string;
  for_duration: string;
  severity: string;
  summary: string;
  runbook: string;
}

export interface AlertGroup {
  name: string;
  rules: PrometheusAlert[];
}

export interface BurnRateAlert {
  window: string;
  burn_rate: number;
  severity: string;
  expr: string;
}

export interface SloDefinition {
  service: string;
  target_percentage: number;
  good_request_expr: string;
  total_request_expr: string;
  slo_expr: string;
  latency_slo?: string | null;
  burn_alerts: BurnRateAlert[];
}

export interface UserPrincipal {
  sub: string;
  username: string;
  email?: string | null;
  roles: string[];
  is_demo: boolean;
}

export interface EvaluationReport {
  dataset_name: string;
  total_log_lines: number;
  precision: number;
  recall: number;
  f1_score: number;
  services_detected: number;
  expected_services: number;
  edges_detected: number;
  expected_edges: number;
  failure_patterns_detected: number;
  evaluated_at: string;
  notes: string;
}
