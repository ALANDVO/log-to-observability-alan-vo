import re
from typing import List, Dict, Any, Set, Tuple, Optional
from collections import defaultdict
from app.models.schemas import (
    LogEvent,
    ServiceNode,
    TopologyEdge,
    DatastoreNode,
    FailurePattern,
    ArchitectureResult
)

class ArchitectureDetector:
    @classmethod
    def detect(cls, events: List[LogEvent], title: str = "Architecture Analysis") -> ArchitectureResult:
        if not events:
            return ArchitectureResult(
                title=title,
                log_count=0,
                services=[],
                topology=[],
                datastores=[],
                failure_patterns=[]
            )

        # 1. Group events by service
        service_events: Dict[str, List[LogEvent]] = defaultdict(list)
        for ev in events:
            service_events[ev.service].append(ev)

        # 2. Extract services
        services: List[ServiceNode] = []
        user_facing_services: Set[str] = set()

        for svc_name, ev_list in sorted(service_events.items()):
            count = len(ev_list)
            errors = sum(1 for e in ev_list if e.level in {"ERROR", "FATAL", "CRITICAL"} or (e.status and e.status >= 500))
            latencies = [e.duration_ms for e in ev_list if e.duration_ms is not None]
            latencies.sort()
            p95 = latencies[int(len(latencies) * 0.95)] if latencies else None

            # Infer role & user facing
            is_gateway = any(
                k in svc_name.lower()
                for k in ["gateway", "ingress", "router", "proxy", "frontend", "edge"]
            ) or any(e.caller and ("127.0.0.1" in e.caller or "10." in e.caller or "192." in e.caller) for e in ev_list)

            is_worker = any(k in svc_name.lower() for k in ["worker", "consumer", "cron", "job", "batch"])

            if is_gateway:
                role = "gateway"
                user_facing = True
                user_facing_services.add(svc_name)
            elif is_worker:
                role = "worker"
                user_facing = False
            else:
                role = "api"
                user_facing = any(e.path and e.path.startswith("/api") for e in ev_list)
                if user_facing:
                    user_facing_services.add(svc_name)

            evidence = f"Identified {count} events across {len(set(e.path for e in ev_list if e.path))} unique paths"

            services.append(ServiceNode(
                name=svc_name,
                role=role,
                user_facing=user_facing,
                evidence=evidence,
                event_count=count,
                error_count=errors,
                p95_latency_ms=round(p95, 2) if p95 is not None else None
            ))

        # 3. Detect Topology Edges
        edge_map: Dict[Tuple[str, str, str], Dict[str, Any]] = defaultdict(
            lambda: {"count": 0, "failures": 0, "latencies": []}
        )

        for ev in events:
            # Explicit caller -> service
            if ev.caller and ev.caller in service_events and ev.caller != ev.service:
                key = (ev.caller, ev.service, "http")
                edge_map[key]["count"] += 1
                if (ev.status and ev.status >= 500) or ev.level == "ERROR":
                    edge_map[key]["failures"] += 1
                if ev.duration_ms is not None:
                    edge_map[key]["latencies"].append(ev.duration_ms)

            # Explicit service -> downstream
            if ev.downstream and ev.downstream in service_events and ev.downstream != ev.service:
                protocol = "http"
                if "kafka" in ev.downstream or "rabbit" in ev.downstream:
                    protocol = "queue"
                key = (ev.service, ev.downstream, protocol)
                edge_map[key]["count"] += 1
                if (ev.status and ev.status >= 500) or ev.level == "ERROR":
                    edge_map[key]["failures"] += 1
                if ev.duration_ms is not None:
                    edge_map[key]["latencies"].append(ev.duration_ms)

        # Fallback topology heuristic: Gateway connects to other business services if no explicit edges
        if not edge_map and len(services) > 1:
            gateways = [s.name for s in services if s.role == "gateway"]
            targets = [s.name for s in services if s.role != "gateway"]
            for gw in gateways:
                for tgt in targets:
                    key = (gw, tgt, "http")
                    edge_map[key]["count"] += max(1, service_events[tgt].__len__() // 2)

        topology: List[TopologyEdge] = []
        for (src, tgt, proto), stats in sorted(edge_map.items()):
            lats = stats["latencies"]
            avg_lat = round(sum(lats) / len(lats), 2) if lats else None
            topology.append(TopologyEdge(
                source=src,
                target=tgt,
                protocol=proto,
                call_count=stats["count"],
                failure_count=stats["failures"],
                avg_latency_ms=avg_lat
            ))

        # 4. Detect Datastores
        datastore_map: Dict[str, Set[str]] = defaultdict(set)
        for ev in events:
            if ev.datastore:
                datastore_map[ev.datastore].add(ev.service)

        datastores: List[DatastoreNode] = []
        for ds_name, touching in sorted(datastore_map.items()):
            ds_type = "relational"
            if ds_name in ["redis", "memcached"]:
                ds_type = "cache"
            elif ds_name in ["kafka", "rabbitmq"]:
                ds_type = "queue"
            elif ds_name in ["mongodb", "elasticsearch", "cassandra"]:
                ds_type = "nosql"

            datastores.append(DatastoreNode(
                name=ds_name,
                type=ds_type,
                touching_services=sorted(list(touching)),
                evidence=f"Referenced by services: {', '.join(sorted(touching))}"
            ))

        # 5. Detect Failure Patterns
        failure_patterns: List[FailurePattern] = []
        pattern_groups: Dict[Tuple[str, str], List[LogEvent]] = defaultdict(list)

        for ev in events:
            is_err = ev.level in {"ERROR", "FATAL", "CRITICAL"} or (ev.status and ev.status >= 500)
            if not is_err:
                continue

            msg_lower = (ev.message or ev.raw).lower()
            if any(w in msg_lower for w in ["timeout", "timed out", "deadline"]):
                pattern_type = "timeout_spike"
            elif any(w in msg_lower for w in ["pool", "connection pool", "near limit", "exhausted"]):
                pattern_type = "resource_exhaustion"
            elif any(w in msg_lower for w in ["auth", "unauthorized", "forbidden", "token", "jwt", "401", "403"]):
                pattern_type = "auth_failure"
            elif any(w in msg_lower for w in ["rate limit", "429", "quota", "too many"]):
                pattern_type = "rate_limit_exceeded"
            elif ev.status == 502 or "bad gateway" in msg_lower:
                pattern_type = "upstream_unavailable"
            else:
                pattern_type = "unhandled_exception"

            pattern_groups[(pattern_type, ev.service)].append(ev)

        for (p_type, svc), err_evs in sorted(pattern_groups.items(), key=lambda x: len(x[1]), reverse=True):
            sample_lines = [e.raw for e in err_evs[:3]]
            summary = f"Detected {len(err_evs)} {p_type.replace('_', ' ')} incidents in {svc}"
            failure_patterns.append(FailurePattern(
                pattern_type=p_type,
                service=svc,
                frequency=len(err_evs),
                summary=summary,
                evidence_lines=sample_lines
            ))

        return ArchitectureResult(
            title=title,
            log_count=len(events),
            services=services,
            topology=topology,
            datastores=datastores,
            failure_patterns=failure_patterns,
            is_llm_assisted=False
        )
