import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict

class LogEvent(BaseModel):
    timestamp: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))
    service: str
    level: str = "INFO"
    method: Optional[str] = None
    path: Optional[str] = None
    status: Optional[int] = None
    duration_ms: Optional[float] = None
    caller: Optional[str] = None
    downstream: Optional[str] = None
    datastore: Optional[str] = None
    message: str = ""
    raw: str = ""

    model_config = ConfigDict(from_attributes=True)

class ServiceNode(BaseModel):
    name: str
    role: str
    user_facing: bool = False
    evidence: str = ""
    event_count: int = 0
    error_count: int = 0
    p95_latency_ms: Optional[float] = None

class TopologyEdge(BaseModel):
    source: str
    target: str
    protocol: str = "http"
    call_count: int = 1
    failure_count: int = 0
    avg_latency_ms: Optional[float] = None

class DatastoreNode(BaseModel):
    name: str
    type: str  # relational, cache, queue, nosql
    touching_services: List[str] = Field(default_factory=list)
    evidence: str = ""

class FailurePattern(BaseModel):
    pattern_type: str
    service: str
    frequency: int
    summary: str
    evidence_lines: List[str] = Field(default_factory=list)

class ArchitectureResult(BaseModel):
    id: Optional[int] = None
    created_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))
    title: str = "Architecture Analysis"
    log_count: int = 0
    services: List[ServiceNode] = Field(default_factory=list)
    topology: List[TopologyEdge] = Field(default_factory=list)
    datastores: List[DatastoreNode] = Field(default_factory=list)
    failure_patterns: List[FailurePattern] = Field(default_factory=list)
    llm_advisory: Optional[str] = None
    is_llm_assisted: bool = False

class AnalyzeLogRequest(BaseModel):
    logs: str = Field(description="Raw log content (JSON lines, syslog, or nginx)")
    title: Optional[str] = "Log Analysis Run"
    enable_llm_advisory: bool = False

class MetricMapping(BaseModel):
    pattern: str
    metric: str
    metric_type: str  # counter, gauge, histogram
    labels: List[str] = Field(default_factory=list)
    unit: str
    description: str

class PrometheusAlert(BaseModel):
    alert: str
    expr: str
    for_duration: str = "5m"
    severity: str = "warning"
    summary: str
    runbook: str

class AlertGroup(BaseModel):
    name: str
    rules: List[PrometheusAlert]

class BurnRateAlert(BaseModel):
    window: str
    burn_rate: float
    severity: str
    expr: str

class SloDefinition(BaseModel):
    service: str
    target_percentage: float = 99.9
    good_request_expr: str
    total_request_expr: str
    slo_expr: str
    latency_slo: Optional[str] = None
    burn_alerts: List[BurnRateAlert] = Field(default_factory=list)

class GrafanaPanel(BaseModel):
    id: int
    title: str
    type: str
    expr: str
    grid_pos: Dict[str, int]

class GrafanaDashboard(BaseModel):
    title: str
    uid: str
    schema_version: int = 39
    panels: List[GrafanaPanel] = Field(default_factory=list)
    raw_json: Dict[str, Any] = Field(default_factory=dict)

class UserPrincipal(BaseModel):
    sub: str
    username: str
    email: Optional[str] = None
    roles: List[str] = Field(default_factory=list)
    is_demo: bool = False

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 3600
    user: UserPrincipal

class AuditLogItem(BaseModel):
    id: int
    created_at: datetime.datetime
    actor: str
    action: str
    target: str
    details: Dict[str, Any] = Field(default_factory=dict)

class EvaluationReport(BaseModel):
    dataset_name: str
    total_log_lines: int
    precision: float
    recall: float
    f1_score: float
    services_detected: int
    expected_services: int
    edges_detected: int
    expected_edges: int
    failure_patterns_detected: int
    evaluated_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))
    notes: str = ""
