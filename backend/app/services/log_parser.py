import re
import json
import datetime
from typing import List, Dict, Any, Optional
from app.models.schemas import LogEvent

# Regex for Nginx/Apache Combined Access Log:
# 127.0.0.1 - - [10/Oct/2026:13:55:36 +0000] "GET /orders HTTP/1.1" 200 2326 "-" "Mozilla/5.0"
NGINX_PATTERN = re.compile(
    r'^(?P<ip>\S+)\s+\S+\s+(?P<user>\S+)\s+\[(?P<time>[^\]]+)\]\s+"(?P<method>[A-Z]+)\s+(?P<path>\S+)[^"]*"\s+(?P<status>\d{3})\s+(?P<bytes>\d+)(?:\s+"(?P<referrer>[^"]*)"\s+"(?P<agent>[^"]*)")?'
)

# Regex for Syslog RFC 5424/3164:
# <134>1 2026-10-12T14:00:00Z web01 api-gateway 1234 - - msg...
# or Oct 12 14:00:00 web01 api-gateway[1234]: msg...
SYSLOG_PATTERN = re.compile(
    r'^(?:<\d+>(?:1\s+)?(?P<time>\S+)\s+\S+\s+)?(?P<service>[a-zA-Z0-9_\-]+)(?:\[\d+\])?:\s+(?P<message>.*)$'
)

# Common datastore keywords to detect
DATASTORE_KEYWORDS = {
    "postgres": "postgresql",
    "postgresql": "postgresql",
    "mysql": "mysql",
    "redis": "redis",
    "mongodb": "mongodb",
    "mongo": "mongodb",
    "kafka": "kafka",
    "rabbitmq": "rabbitmq",
    "elasticsearch": "elasticsearch",
    "sqlite": "sqlite",
    "cassandra": "cassandra",
    "dynamodb": "dynamodb"
}

HTTP_METHODS = {"GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"}

class LogParser:
    @classmethod
    def parse_text(cls, content: str) -> List[LogEvent]:
        events: List[LogEvent] = []
        for line in content.splitlines():
            line_str = line.strip()
            if not line_str:
                continue
            event = cls.parse_line(line_str)
            if event:
                events.append(event)
        return events

    @classmethod
    def parse_line(cls, line: str) -> Optional[LogEvent]:
        # 1. Attempt JSON Lines
        if line.startswith("{") and line.endswith("}"):
            try:
                data = json.loads(line)
                return cls._from_json_dict(data, line)
            except json.JSONDecodeError:
                pass

        # 2. Attempt Nginx Access Log
        nginx_match = NGINX_PATTERN.match(line)
        if nginx_match:
            return cls._from_nginx(nginx_match.groupdict(), line)

        # 3. Attempt Syslog
        syslog_match = SYSLOG_PATTERN.match(line)
        if syslog_match:
            return cls._from_syslog(syslog_match.groupdict(), line)

        # 4. Fallback unstructured / generic line
        return cls._from_generic(line)

    @classmethod
    def _from_json_dict(cls, data: Dict[str, Any], raw: str) -> LogEvent:
        # Extract timestamp
        ts_val = data.get("timestamp") or data.get("ts") or data.get("time") or data.get("@timestamp")
        timestamp = cls._parse_timestamp(ts_val)

        # Extract service name
        service = (
            data.get("service")
            or data.get("app")
            or data.get("service_name")
            or data.get("component")
            or "unknown-service"
        )

        level = (data.get("level") or data.get("severity") or "INFO").upper()
        method = (data.get("method") or data.get("http_method") or "").upper() or None
        path = data.get("path") or data.get("uri") or data.get("url") or None
        status = data.get("status") or data.get("status_code") or data.get("code")
        if status is not None:
            try:
                status = int(status)
            except (ValueError, TypeError):
                status = None

        duration = data.get("duration_ms") or data.get("latency_ms") or data.get("ms") or data.get("duration")
        if duration is not None:
            try:
                duration = float(duration)
            except (ValueError, TypeError):
                duration = None

        caller = data.get("caller") or data.get("client") or data.get("source_service") or None
        downstream = data.get("downstream") or data.get("target_service") or data.get("target") or None
        msg = data.get("msg") or data.get("message") or ""

        # Extract datastore if mentioned in text or fields
        raw_ds = data.get("datastore") or data.get("database")
        if raw_ds:
            datastore = DATASTORE_KEYWORDS.get(str(raw_ds).lower(), str(raw_ds))
        else:
            datastore = cls._extract_datastore(msg)
        if not downstream:
            downstream = cls._extract_downstream_call(msg)

        return LogEvent(
            timestamp=timestamp,
            service=str(service),
            level=level,
            method=method,
            path=path,
            status=status,
            duration_ms=duration,
            caller=caller,
            downstream=downstream,
            datastore=datastore,
            message=str(msg),
            raw=raw
        )

    @classmethod
    def _from_nginx(cls, groups: Dict[str, str], raw: str) -> LogEvent:
        method = groups.get("method", "GET")
        path = groups.get("path", "/")
        status = int(groups.get("status", 200))
        time_str = groups.get("time", "")
        # Common Nginx time format: 10/Oct/2026:13:55:36 +0000
        timestamp = cls._parse_timestamp(time_str)

        return LogEvent(
            timestamp=timestamp,
            service="nginx-ingress",
            level="INFO" if status < 400 else ("WARN" if status < 500 else "ERROR"),
            method=method,
            path=path,
            status=status,
            duration_ms=None,
            caller=groups.get("ip"),
            downstream=cls._infer_service_from_path(path),
            message=f"{method} {path} HTTP {status}",
            raw=raw
        )

    @classmethod
    def _from_syslog(cls, groups: Dict[str, str], raw: str) -> LogEvent:
        service = groups.get("service") or "syslog-service"
        msg = groups.get("message") or ""
        time_str = groups.get("time")
        timestamp = cls._parse_timestamp(time_str)

        level = "INFO"
        if any(w in msg.upper() for w in ["ERR", "ERROR", "FAIL", "FATAL", "EXCEPTION"]):
            level = "ERROR"
        elif any(w in msg.upper() for w in ["WARN", "WARNING"]):
            level = "WARN"

        datastore = cls._extract_datastore(msg)
        downstream = cls._extract_downstream_call(msg)

        return LogEvent(
            timestamp=timestamp,
            service=service,
            level=level,
            datastore=datastore,
            downstream=downstream,
            message=msg,
            raw=raw
        )

    @classmethod
    def _from_generic(cls, raw: str) -> LogEvent:
        # Check for service token: [service-name] or service:
        service = "app-service"
        svc_match = re.search(r'\[([a-zA-Z0-9_\-]+)\]', raw)
        if svc_match:
            service = svc_match.group(1)

        level = "INFO"
        for candidate in ["ERROR", "FATAL", "CRITICAL", "WARN", "WARNING", "DEBUG"]:
            if candidate in raw.upper():
                level = "ERROR" if candidate in ["ERROR", "FATAL", "CRITICAL"] else candidate
                break

        status = None
        status_match = re.search(r'\bstatus[=:\s]+(\d{3})\b|\bHTTP\s+(\d{3})\b', raw, re.IGNORECASE)
        if status_match:
            status = int(status_match.group(1) or status_match.group(2))

        duration = None
        duration_match = re.search(r'\b(\d+(?:\.\d+)?)\s*(?:ms|milliseconds)\b', raw, re.IGNORECASE)
        if duration_match:
            duration = float(duration_match.group(1))

        return LogEvent(
            timestamp=datetime.datetime.now(datetime.timezone.utc),
            service=service,
            level=level,
            status=status,
            duration_ms=duration,
            datastore=cls._extract_datastore(raw),
            downstream=cls._extract_downstream_call(raw),
            message=raw,
            raw=raw
        )

    @staticmethod
    def _parse_timestamp(val: Any) -> datetime.datetime:
        if isinstance(val, (int, float)):
            try:
                return datetime.datetime.fromtimestamp(val, tz=datetime.timezone.utc)
            except Exception:
                pass
        if isinstance(val, str):
            try:
                # ISO 8601
                return datetime.datetime.fromisoformat(val.replace("Z", "+00:00"))
            except Exception:
                pass
            try:
                # Nginx format: 10/Oct/2026:13:55:36 +0000
                return datetime.datetime.strptime(val.split()[0], "%d/%b/%Y:%H:%M:%S").replace(tzinfo=datetime.timezone.utc)
            except Exception:
                pass
        return datetime.datetime.now(datetime.timezone.utc)

    @classmethod
    def _extract_datastore(cls, text: str) -> Optional[str]:
        lower = text.lower()
        for kw, canonical in DATASTORE_KEYWORDS.items():
            if re.search(rf'\b{kw}\b', lower):
                return canonical
        return None

    @classmethod
    def _extract_downstream_call(cls, text: str) -> Optional[str]:
        # Examples: "calling order-service", "forwarding to http://payment-service:8080"
        match = re.search(r'(?:call|calling|forwarding|to|upstream|request\s+to)\s+(?:https?://)?([a-zA-Z0-9_\-]+)(?::\d+)?', text, re.IGNORECASE)
        if match:
            candidate = match.group(1).lower()
            if candidate not in {"the", "a", "endpoint", "url", "service", "upstream", "localhost"}:
                return candidate
        return None

    @classmethod
    def _infer_service_from_path(cls, path: str) -> Optional[str]:
        parts = [p for p in path.split("/") if p and p not in {"api", "v1", "v2"}]
        if parts:
            first = parts[0].rstrip("s")
            return f"{first}-service"
        return None
