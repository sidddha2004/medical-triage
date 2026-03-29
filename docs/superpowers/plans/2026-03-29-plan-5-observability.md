# Observability Stack Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add comprehensive observability with Prometheus metrics, Grafana dashboards, ELK logging, and Jaeger distributed tracing.

**Architecture:** Each service exports Prometheus metrics, logs are structured JSON sent to ELK stack, and distributed tracing via Jaeger provides end-to-end request visibility.

**Tech Stack:** Prometheus, Grafana, Elasticsearch, Logstash, Kibana, Jaeger, OpenTelemetry

---

## Files Overview

| File | Action | Responsibility |
|------|--------|----------------|
| `docker/prometheus/prometheus.yml` | Create | Prometheus config |
| `docker/grafana/provisioning/` | Create | Grafana dashboards |
| `docker/elasticsearch/` | Create | ELK stack config |
| `docker/jaeger/` | Create | Jaeger config |
| `backend/observability/` | Create | Metrics, logging, tracing |
| `docker/docker-compose.yml` | Modify | Add observability services |

---

### Task 1: Prometheus Configuration

**Files:**
- Create: `docker/prometheus/prometheus.yml`
- Create: `docker/prometheus/Dockerfile`
- Create: `docker/prometheus/alerts.yml`

- [ ] **Step 1: Create Prometheus config**

```yaml
# docker/prometheus/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: 'medical-triage'
    environment: 'development'

# Alertmanager configuration
alerting:
  alertmanagers:
    - static_configs:
        - targets: []

# Load alert rules
rule_files:
  - "alerts.yml"

# Scrape configurations
scrape_configs:
  # Prometheus self-monitoring
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
        labels:
          service: 'prometheus'

  # API Gateway (Kong)
  - job_name: 'kong'
    static_configs:
      - targets: ['kong:8001']
        labels:
          service: 'gateway'

  # Backend Services
  - job_name: 'backend'
    static_configs:
      - targets: ['backend:8000']
        labels:
          service: 'backend'

  # Inference Service
  - job_name: 'inference-service'
    static_configs:
      - targets: ['inference-service:8004']
        labels:
          service: 'inference'

  # Agent Service
  - job_name: 'agent-service'
    static_configs:
      - targets: ['agent-service:8005']
        labels:
          service: 'agent'

  # Auth Service
  - job_name: 'auth-service'
    static_configs:
      - targets: ['auth-service:50051']
        labels:
          service: 'auth'

  # Patient Service
  - job_name: 'patient-service'
    static_configs:
      - targets: ['patient-service:50052']
        labels:
          service: 'patient'

  # Triage Service
  - job_name: 'triage-service'
    static_configs:
      - targets: ['triage-service:8002']
        labels:
          service: 'triage'

  # Node Exporter (host metrics)
  - job_name: 'node'
    static_configs:
      - targets: ['node-exporter:9100']
        labels:
          service: 'node'

  # Redis Exporter
  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']
        labels:
          service: 'redis'

  # PostgreSQL Exporter
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']
        labels:
          service: 'postgres'

  # Kafka Exporter
  - job_name: 'kafka'
    static_configs:
      - targets: ['kafka-exporter:9308']
        labels:
          service: 'kafka'
```

- [ ] **Step 2: Create alert rules**

```yaml
# docker/prometheus/alerts.yml
groups:
  - name: service_alerts
    rules:
      # High error rate
      - alert: HighErrorRate
        expr: sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m])) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value | humanizePercentage }} over the last 5 minutes"

      # High latency
      - alert: HighLatency
        expr: histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, service)) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High latency detected"
          description: "P95 latency is {{ $value }}s for service {{ $labels.service }}"

      # Service down
      - alert: ServiceDown
        expr: up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Service {{ $labels.job }} is down"
          description: "{{ $labels.instance }} has been down for more than 1 minute"

      # Inference service specific
      - alert: InferenceHighLatency
        expr: histogram_quantile(0.95, sum(rate(inference_latency_seconds_bucket[5m])) by (le)) > 0.5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Inference latency too high"
          description: "P95 inference latency is {{ $value }}s"

      - alert: InferenceErrorRate
        expr: sum(rate(inference_requests_total{status="error"}[5m])) / sum(rate(inference_requests_total[5m])) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High inference error rate"
          description: "Inference error rate is {{ $value | humanizePercentage }}"

      # Cache hit rate too low
      - alert: LowCacheHitRate
        expr: sum(rate(inference_cache_hits_total[5m])) / sum(rate(inference_requests_total[5m])) < 0.5
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Low cache hit rate"
          description: "Cache hit rate is {{ $value | humanizePercentage }}"

      # Kafka consumer lag
      - alert: KafkaConsumerLag
        expr: kafka_consumer_group_lag > 10000
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Kafka consumer lag detected"
          description: "Consumer group {{ $labels.consumer_group }} has lag of {{ $value }}"

      # Memory usage high
      - alert: HighMemoryUsage
        expr: (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes > 0.85
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage"
          description: "Memory usage is {{ $value | humanizePercentage }}"

      # Disk usage high
      - alert: HighDiskUsage
        expr: (node_filesystem_size_bytes - node_filesystem_free_bytes) / node_filesystem_size_bytes > 0.85
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High disk usage"
          description: "Disk usage is {{ $value | humanizePercentage }}"
```

- [ ] **Step 3: Create Prometheus Dockerfile**

```dockerfile
# docker/prometheus/Dockerfile
FROM prom/prometheus:v2.48.0

# Copy configuration
COPY prometheus.yml /etc/prometheus/prometheus.yml
COPY alerts.yml /etc/prometheus/alerts.yml

# Create data directory
RUN mkdir -p /prometheus/data && \
    chown -R nobody:nobody /prometheus/data

# Health check
HEALTHCHECK --interval=30s --timeout=3s \
  CMD wget -q -O /dev/null http://localhost:9090/-/healthy || exit 1

EXPOSE 9090
```

- [ ] **Step 4: Commit**

```bash
git add docker/prometheus/
git commit -m "infra: add Prometheus configuration with alerting rules"
```

---

### Task 2: Grafana Dashboards

**Files:**
- Create: `docker/grafana/provisioning/datasources/datasources.yml`
- Create: `docker/grafana/provisioning/dashboards/dashboards.yml`
- Create: `docker/grafana/provisioning/dashboards/system-overview.json`
- Create: `docker/grafana/provisioning/dashboards/ml-performance.json`
- Create: `docker/grafana/Dockerfile`

- [ ] **Step 1: Create Grafana datasource provisioning**

```yaml
# docker/grafana/provisioning/datasources/datasources.yml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
    jsonData:
      httpMethod: POST
      timeInterval: 15s

  - name: Loki
    type: loki
    access: proxy
    url: http://loki:3100
    editable: true
    jsonData:
      maxLines: 1000

  - name: Jaeger
    type: jaeger
    access: proxy
    url: http://jaeger:16686
    editable: true
```

- [ ] **Step 2: Create dashboard provisioning config**

```yaml
# docker/grafana/provisioning/dashboards/dashboards.yml
apiVersion: 1

providers:
  - name: 'Medical Triage Dashboards'
    orgId: 1
    folder: ''
    folderUid: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 30
    allowUiUpdates: true
    options:
      path: /etc/grafana/provisioning/dashboards
```

- [ ] **Step 3: Create System Overview Dashboard**

```json
{
  "dashboard": {
    "id": null,
    "title": "System Overview",
    "tags": ["medical-triage", "overview"],
    "timezone": "browser",
    "refresh": "10s",
    "panels": [
      {
        "id": 1,
        "type": "stat",
        "title": "Total Requests",
        "gridPos": {"x": 0, "y": 0, "w": 6, "h": 4},
        "targets": [
          {
            "expr": "sum(rate(http_requests_total[5m]))",
            "legendFormat": "req/s"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "reqps",
            "decimals": 2
          }
        }
      },
      {
        "id": 2,
        "type": "stat",
        "title": "Error Rate",
        "gridPos": {"x": 6, "y": 0, "w": 6, "h": 4},
        "targets": [
          {
            "expr": "sum(rate(http_requests_total{status=~\"5..\"}[5m])) / sum(rate(http_requests_total[5m])) * 100",
            "legendFormat": "%"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "percent",
            "thresholds": {
              "mode": "absolute",
              "steps": [
                {"value": 0, "color": "green"},
                {"value": 1, "color": "yellow"},
                {"value": 5, "color": "red"}
              ]
            }
          }
        }
      },
      {
        "id": 3,
        "type": "stat",
        "title": "P95 Latency",
        "gridPos": {"x": 12, "y": 0, "w": 6, "h": 4},
        "targets": [
          {
            "expr": "histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))",
            "legendFormat": "P95"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "s",
            "thresholds": {
              "mode": "absolute",
              "steps": [
                {"value": 0, "color": "green"},
                {"value": 0.5, "color": "yellow"},
                {"value": 1, "color": "red"}
              ]
            }
          }
        }
      },
      {
        "id": 4,
        "type": "stat",
        "title": "Active Services",
        "gridPos": {"x": 18, "y": 0, "w": 6, "h": 4},
        "targets": [
          {
            "expr": "count(up == 1)",
            "legendFormat": "services"
          }
        ]
      },
      {
        "id": 5,
        "type": "timeseries",
        "title": "Request Rate by Service",
        "gridPos": {"x": 0, "y": 4, "w": 12, "h": 8},
        "targets": [
          {
            "expr": "sum(rate(http_requests_total[5m])) by (service)",
            "legendFormat": "{{service}}"
          }
        ]
      },
      {
        "id": 6,
        "type": "timeseries",
        "title": "Error Rate by Service",
        "gridPos": {"x": 12, "y": 4, "w": 12, "h": 8},
        "targets": [
          {
            "expr": "sum(rate(http_requests_total{status=~\"5..\"}[5m])) by (service) / sum(rate(http_requests_total[5m])) by (service) * 100",
            "legendFormat": "{{service}}"
          }
        ]
      },
      {
        "id": 7,
        "type": "heatmap",
        "title": "Latency Distribution",
        "gridPos": {"x": 0, "y": 12, "w": 12, "h": 8},
        "targets": [
          {
            "expr": "sum(rate(http_request_duration_seconds_bucket[5m])) by (le, service)",
            "format": "heatmap",
            "legendFormat": "{{service}}"
          }
        ]
      },
      {
        "id": 8,
        "type": "table",
        "title": "Service Health",
        "gridPos": {"x": 12, "y": 12, "w": 12, "h": 8},
        "targets": [
          {
            "expr": "up",
            "format": "table",
            "instant": true
          }
        ],
        "transformations": [
          {
            "id": "organize",
            "options": {
              "renameByName": {
                "Time": "",
                "Value": "Status",
                "job": "Service"
              }
            }
          }
        ]
      }
    ],
    "time": {"from": "now-1h", "to": "now"},
    "timepicker": {}
  }
}
```

- [ ] **Step 4: Create ML Performance Dashboard**

```json
{
  "dashboard": {
    "id": null,
    "title": "ML Performance",
    "tags": ["medical-triage", "ml"],
    "panels": [
      {
        "id": 1,
        "type": "stat",
        "title": "Total Predictions",
        "gridPos": {"x": 0, "y": 0, "w": 6, "h": 4},
        "targets": [
          {
            "expr": "sum(inference_requests_total)",
            "legendFormat": "predictions"
          }
        ]
      },
      {
        "id": 2,
        "type": "stat",
        "title": "Cache Hit Rate",
        "gridPos": {"x": 6, "y": 0, "w": 6, "h": 4},
        "targets": [
          {
            "expr": "sum(rate(inference_cache_hits_total[5m])) / sum(rate(inference_requests_total[5m])) * 100",
            "legendFormat": "%"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "percent",
            "thresholds": {
              "steps": [
                {"value": 0, "color": "red"},
                {"value": 50, "color": "yellow"},
                {"value": 80, "color": "green"}
              ]
            }
          }
        }
      },
      {
        "id": 3,
        "type": "stat",
        "title": "P95 Inference Latency",
        "gridPos": {"x": 12, "y": 0, "w": 6, "h": 4},
        "targets": [
          {
            "expr": "histogram_quantile(0.95, sum(rate(inference_latency_seconds_bucket[5m])) by (le))",
            "legendFormat": "P95"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "s"
          }
        }
      },
      {
        "id": 4,
        "type": "stat",
        "title": "Model Version",
        "gridPos": {"x": 18, "y": 0, "w": 6, "h": 4},
        "targets": [
          {
            "expr": "model_version_info",
            "legendFormat": "{{version}}"
          }
        ]
      },
      {
        "id": 5,
        "type": "timeseries",
        "title": "Predictions by Disease",
        "gridPos": {"x": 0, "y": 4, "w": 12, "h": 8},
        "targets": [
          {
            "expr": "sum(rate(model_predictions_total[5m])) by (disease)",
            "legendFormat": "{{disease}}"
          }
        ]
      },
      {
        "id": 6,
        "type": "timeseries",
        "title": "Inference Latency by Model Version",
        "gridPos": {"x": 12, "y": 4, "w": 12, "h": 8},
        "targets": [
          {
            "expr": "histogram_quantile(0.95, sum(rate(inference_latency_seconds_bucket[5m])) by (le, model_version))",
            "legendFormat": "{{model_version}}"
          }
        ]
      }
    ]
  }
}
```

- [ ] **Step 5: Create Grafana Dockerfile**

```dockerfile
# docker/grafana/Dockerfile
FROM grafana/grafana:10.2.0

# Install plugins
USER root
RUN grafana-cli plugins install grafana-piechart-panel && \
    grafana-cli plugins install grafana-worldmap-panel

USER grafana

# Copy provisioning
COPY provisioning/ /etc/grafana/provisioning/
COPY dashboards/ /etc/grafana/provisioning/dashboards/

# Environment variables
ENV GF_SECURITY_ADMIN_USER=admin
ENV GF_SECURITY_ADMIN_PASSWORD=admin
ENV GF_USERS_ALLOW_SIGN_UP=false

EXPOSE 3000
```

- [ ] **Step 6: Commit**

```bash
git add docker/grafana/
git commit -m "infra: add Grafana dashboards and provisioning"
```

---

### Task 3: ELK Stack Logging

**Files:**
- Create: `docker/elasticsearch/docker-compose.yml`
- Create: `docker/logstash/pipeline.conf`
- Create: `docker/logstash/Dockerfile`
- Create: `docker/kibana/Dockerfile`

- [ ] **Step 1: Add Elasticsearch to docker-compose**

```yaml
# docker/docker-compose.yml (add to services)

  # Elasticsearch
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    container_name: medical_triage_elasticsearch
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    ports:
      - "9200:9200"
      - "9300:9300"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data
    networks:
      - medical_triage_network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9200/_cluster/health"]
      interval: 30s
      timeout: 10s
      retries: 5

  # Logstash
  logstash:
    build:
      context: ./logstash
      dockerfile: Dockerfile
    container_name: medical_triage_logstash
    environment:
      - LS_JAVA_OPTS=-Xmx256m -Xms256m
    volumes:
      - ./logstash/pipeline.conf:/usr/share/logstash/pipeline/logstash.conf
    depends_on:
      - elasticsearch
    networks:
      - medical_triage_network

  # Kibana
  kibana:
    image: docker.elastic.co/kibana/kibana:8.11.0
    container_name: medical_triage_kibana
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    ports:
      - "5601:5601"
    depends_on:
      - elasticsearch
    networks:
      - medical_triage_network

  # Loki (alternative to ELK)
  loki:
    image: grafana/loki:2.9.0
    container_name: medical_triage_loki
    ports:
      - "3100:3100"
    command: -config.file=/etc/loki/local-config.yaml
    networks:
      - medical_triage_network

volumes:
  elasticsearch_data:
```

- [ ] **Step 2: Create Logstash pipeline**

```conf
# docker/logstash/pipeline.conf
input {
  # TCP input for application logs
  tcp {
    port => 5000
    codec => json_lines
  }

  # Beats input (Filebeat, Metricbeat)
  beats {
    port => 5044
  }

  # HTTP input
  http {
    port => 8080
    codec => json
  }
}

filter {
  # Parse JSON logs
  if [message] =~ /^\{.*\}$/ {
    json {
      source => "message"
    }
  }

  # Add timestamp if missing
  if ![timestamp] {
    date {
      match => ["@timestamp", "ISO8601"]
      target => "timestamp"
    }
  }

  # Filter by service
  if [service] == "backend" {
    mutate {
      add_tag => ["django"]
    }
  }

  if [service] == "inference" {
    mutate {
      add_tag => ["ml", "inference"]
    }
  }

  # Parse log levels
  if [level] in ["ERROR", "error", "ERROR"] {
    mutate {
      add_tag => ["error"]
    }
  }

  if [level] in ["WARN", "WARNING", "warn", "warning"] {
    mutate {
      add_tag => ["warning"]
    }
  }

  # Remove unnecessary fields
  mutate {
    remove_field => ["host", "@version"]
  }

  # Add environment tag
  mutate {
    add_field => {
      "environment" => "development"
      "application" => "medical-triage"
    }
  }
}

output {
  # Send to Elasticsearch
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "medical-triage-%{+YYYY.MM.dd}"
    template_name => "medical-triage"
  }

  # Debug output (optional)
  stdout {
    codec => rubydebug
  }
}
```

- [ ] **Step 3: Create Logstash Dockerfile**

```dockerfile
# docker/logstash/Dockerfile
FROM docker.elastic.co/logstash/logstash:8.11.0

# Install any needed plugins
# RUN logstash-plugin install logstash-input-kafka

# Expose ports
EXPOSE 5000 5044 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s \
  CMD curl -f http://localhost:9600/_node/stats || exit 1
```

- [ ] **Step 4: Commit**

```bash
git add docker/elasticsearch/ docker/logstash/ docker/kibana/
git commit -m "infra: add ELK stack for centralized logging"
```

---

### Task 4: Jaeger Distributed Tracing

**Files:**
- Create: `docker/jaeger/docker-compose.yml`
- Create: `backend/observability/tracing.py`

- [ ] **Step 1: Add Jaeger to docker-compose**

```yaml
# docker/docker-compose.yml (add to services)

  # Jaeger (all-in-one for development)
  jaeger:
    image: jaegertracing/all-in-one:1.53
    container_name: medical_triage_jaeger
    environment:
      - COLLECTOR_OTLP_ENABLED=true
      - COLLECTOR_ZIPKIN_HOST_PORT=:9411
    ports:
      - "5775:5775/udp"    # Agent - accept compact Thrift UDP
      - "6831:6831/udp"    # Agent - accept jaeger.thrift over UDP
      - "6832:6832/udp"    # Agent - accept jaeger.thrift over UDP
      - "5778:5778"        # Agent - serve configs
      - "16686:16686"      # UI
      - "14268:14268"      # Collector - accept jaeger.thrift directly
      - "14250:14250"      # Collector - accept model.proto
      - "9411:9411"        # Collector - Zipkin compatible API
    networks:
      - medical_triage_network
    restart: unless-stopped

  # Jaeger Collector (for production)
  jaeger-collector:
    image: jaegertracing/jaeger-collector:1.53
    container_name: medical_triage_jaeger_collector
    environment:
      - COLLECTOR_OTLP_ENABLED=true
    ports:
      - "14268:14268"
      - "4317:4317"
      - "4318:4318"
    depends_on:
      - jaeger
    networks:
      - medical_triage_network
    profiles:
      - production
```

- [ ] **Step 2: Create tracing module**

```python
# backend/observability/tracing.py
"""
Distributed Tracing with Jaeger/OpenTelemetry.
"""

import os
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.django import DjangoInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
import logging

logger = logging.getLogger(__name__)


def setup_tracing(service_name: str = 'medical-triage-backend'):
    """Setup OpenTelemetry tracing with Jaeger exporter."""

    # Set up the tracer provider
    tracer_provider = TracerProvider()
    trace.set_tracer_provider(tracer_provider)

    # Configure Jaeger exporter
    jaeger_endpoint = os.getenv('JAEGER_ENDPOINT', 'http://jaeger:14268/api/traces')
    jaeger_agent_host = os.getenv('JAEGER_AGENT_HOST', 'jaeger')
    jaeger_agent_port = int(os.getenv('JAEGER_AGENT_PORT', 6831))

    jaeger_exporter = JaegerExporter(
        agent_host_name=jaeger_agent_host,
        agent_port=jaeger_agent_port,
        endpoint=jaeger_endpoint,
    )

    # Add batch span processor
    span_processor = BatchSpanProcessor(jaeger_exporter)
    tracer_provider.add_span_processor(span_processor)

    # Instrument Django
    DjangoInstrumentor().instrument()
    logger.info('Django instrumentation enabled')

    # Instrument requests library
    RequestsInstrumentor().instrument()
    logger.info('Requests instrumentation enabled')

    # Instrument Redis
    RedisInstrumentor().instrument()
    logger.info('Redis instrumentation enabled')

    logger.info(f'Tracing setup complete for service: {service_name}')

    return trace.get_tracer(service_name)


# Context manager for custom spans
from contextlib import contextmanager


@contextmanager
def trace_span(tracer, span_name: str, **attributes):
    """Context manager for creating trace spans."""
    with tracer.start_as_current_span(span_name) as span:
        for key, value in attributes.items():
            span.set_attribute(key, value)
        yield span


# Decorator for tracing functions
def traced_function(tracer, span_name: str):
    """Decorator to trace function execution."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            with trace_span(tracer, span_name, function=func.__name__):
                return func(*args, **kwargs)
        return wrapper
    return decorator
```

- [ ] **Step 3: Commit**

```bash
git add docker/jaeger/ backend/observability/tracing.py
git commit -m "infra: add Jaeger distributed tracing"
```

---

### Task 5: Application Instrumentation

**Files:**
- Create: `backend/observability/logging.py`
- Create: `backend/observability/metrics.py`
- Modify: `backend/backend/settings.py`

- [ ] **Step 1: Create structured logging module**

```python
# backend/observability/logging.py
"""
Structured Logging for Health Triage.

JSON logging format for ELK stack ingestion.
"""

import logging
import json
import sys
from datetime import datetime
from typing import Dict, Any


class JSONFormatter(logging.Formatter):
    """JSON log formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = {
                'type': str(record.exc_info[0].__name__),
                'message': str(record.exc_info[1]),
                'traceback': self.formatException(record.exc_info)
            }

        # Add custom fields
        if hasattr(record, 'custom_fields'):
            log_data.update(record.custom_fields)

        # Add request context if available
        try:
            from django.utils.deprecation import MiddlewareMixin
            # Add user ID, request ID, etc. if available
        except:
            pass

        return json.dumps(log_data)


class RequestContextFilter(logging.Filter):
    """Add request context to log records."""

    def __init__(self, request=None):
        self.request = request

    def filter(self, record: logging.LogRecord) -> bool:
        # Add request-specific fields
        if self.request:
            record.request_id = getattr(self.request, 'request_id', 'unknown')
            record.user_id = getattr(self.request.user, 'id', 'anonymous') if hasattr(self.request, 'user') else 'anonymous'
            record.path = getattr(self.request, 'path', 'unknown')
            record.method = getattr(self.request, 'method', 'unknown')

        return True


def get_logger(name: str) -> logging.Logger:
    """Get a logger with JSON formatting."""
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    return logger
```

- [ ] **Step 2: Create metrics module**

```python
# backend/observability/metrics.py
"""
Prometheus Metrics for Health Triage.
"""

from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin
import time
import re


# HTTP Metrics
HTTP_REQUESTS = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status', 'service']
)

HTTP_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint', 'service'],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

HTTP_REQUESTS_IN_PROGRESS = Gauge(
    'http_requests_in_progress',
    'HTTP requests currently being processed',
    ['method', 'endpoint', 'service']
)

# Database Metrics
DB_QUERIES = Counter(
    'database_queries_total',
    'Total database queries',
    ['model', 'operation']
)

DB_QUERY_LATENCY = Histogram(
    'database_query_duration_seconds',
    'Database query latency',
    ['model', 'operation'],
    buckets=[0.0001, 0.0005, 0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0]
)

# WebSocket Metrics
WS_CONNECTIONS = Gauge(
    'websocket_connections',
    'Active WebSocket connections',
    ['service']
)

WS_MESSAGES = Counter(
    'websocket_messages_total',
    'Total WebSocket messages',
    ['direction', 'service']
)


class PrometheusMiddleware(MiddlewareMixin):
    """Middleware to record HTTP metrics."""

    def process_request(self, request):
        request._start_time = time.time()
        request._endpoint = self._get_endpoint(request.path)

        HTTP_REQUESTS_IN_PROGRESS.labels(
            method=request.method,
            endpoint=request._endpoint,
            service='backend'
        ).inc()

    def process_response(self, request, response):
        endpoint = getattr(request, '_endpoint', 'unknown')
        start_time = getattr(request, '_start_time', time.time())

        latency = time.time() - start_time

        HTTP_REQUESTS.labels(
            method=request.method,
            endpoint=endpoint,
            status=response.status_code,
            service='backend'
        ).inc()

        HTTP_LATENCY.labels(
            method=request.method,
            endpoint=endpoint,
            service='backend'
        ).observe(latency)

        HTTP_REQUESTS_IN_PROGRESS.labels(
            method=request.method,
            endpoint=endpoint,
            service='backend'
        ).dec()

        return response

    def _get_endpoint(self, path: str) -> str:
        """Normalize path by replacing IDs with placeholders."""
        # Replace numeric IDs
        normalized = re.sub(r'/\d+', '/{id}', path)
        # Replace UUIDs
        normalized = re.sub(r'/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', '/{uuid}', normalized, flags=re.IGNORECASE)
        return normalized


def metrics_endpoint(request):
    """Expose Prometheus metrics endpoint."""
    return HttpResponse(generate_latest(), content_type=CONTENT_TYPE_LATEST)
```

- [ ] **Step 3: Update Django settings**

```python
# backend/backend/settings.py (add to end)

# Observability
INSTALLED_APPS += [
    'django_prometheus',
]

MIDDLEWARE = [
    'django_prometheus.middleware.PrometheusBeforeMiddleware',
    *MIDDLEWARE,
    'django_prometheus.middleware.PrometheusAfterMiddleware',
]

# Update ROOT_URLCONF to include metrics
# In backend/urls.py:
# from django_prometheus import urls as prometheus_urls
# path('metrics/', include(prometheus_urls.urls)),

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': 'observability.logging.JSONFormatter',
        },
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'logs/app.log',
            'formatter': 'json',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}
```

- [ ] **Step 4: Commit**

```bash
git add backend/observability/ backend/backend/settings.py
git commit -m "feat: add application instrumentation for metrics and logging"
```

---

### Task 6: Testing & Verification

**Files:**
- Create: `scripts/test_observability.py`

- [ ] **Step 1: Create verification script**

```python
#!/usr/bin/env python
"""Test Observability Stack."""

import requests
import time

PROMETHEUS_URL = 'http://localhost:9090'
GRAFANA_URL = 'http://localhost:3000'
JAEGER_URL = 'http://localhost:16686'
KIBANA_URL = 'http://localhost:5601'
ELASTICSEARCH_URL = 'http://localhost:9200'


def check_service(name, url, timeout=10):
    """Check if a service is healthy."""
    try:
        response = requests.get(url, timeout=timeout)
        status = "✓" if response.status_code == 200 else "✗"
        print(f"{status} {name}: {response.status_code}")
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        print(f"✗ {name}: {e}")
        return False


def test_prometheus():
    """Test Prometheus."""
    print('\n=== Testing Prometheus ===')
    check_service('Prometheus Health', f'{PROMETHEUS_URL}/-/healthy')
    check_service('Prometheus Targets', f'{PROMETHEUS_URL}/api/v1/targets')
    check_service('Prometheus Metrics', f'{PROMETHEUS_URL}/api/v1/metrics')


def test_grafana():
    """Test Grafana."""
    print('\n=== Testing Grafana ===')
    check_service('Grafana Login', f'{GRAFANA_URL}/login')
    check_service('Grafana Health', f'{GRAFANA_URL}/api/health')


def test_jaeger():
    """Test Jaeger."""
    print('\n=== Testing Jaeger ===')
    check_service('Jaeger UI', f'{JAEGER_URL}/')
    check_service('Jaeger Services', f'{JAEGER_URL}/api/services')


def test_elasticsearch():
    """Test Elasticsearch."""
    print('\n=== Testing Elasticsearch ===')
    check_service('Elasticsearch', f'{ELASTICSEARCH_URL}/_cluster/health')
    check_service('Elasticsearch Indices', f'{ELASTICSEARCH_URL}/_cat/indices')


def test_kibana():
    """Test Kibana."""
    print('\n=== Testing Kibana ===')
    check_service('Kibana', f'{KIBANA_URL}/app/home')


def test_metrics_endpoint():
    """Test application metrics endpoint."""
    print('\n=== Testing Application Metrics ===')
    check_service('Backend Metrics', 'http://localhost:8000/metrics')
    check_service('Inference Metrics', 'http://localhost:8004/metrics')


def test_logging():
    """Test logging by making requests."""
    print('\n=== Testing Logging ===')
    try:
        # Make some requests to generate logs
        requests.get('http://localhost:8000/api/health', timeout=5)
        print("✓ Requests made - check Kibana for logs")
    except Exception as e:
        print(f"✗ Error making requests: {e}")


if __name__ == '__main__':
    print('Observability Stack Verification')
    print('=' * 50)

    test_prometheus()
    test_grafana()
    test_jaeger()
    test_elasticsearch()
    test_kibana()
    test_metrics_endpoint()
    test_logging()

    print('\n' + '=' * 50)
    print('\nAccess URLs:')
    print(f'  Prometheus:  {PROMETHEUS_URL}')
    print(f'  Grafana:     {GRAFANA_URL} (admin/admin)')
    print(f'  Jaeger:      {JAEGER_URL}')
    print(f'  Kibana:      {KIBANA_URL}')
    print(f'  Elasticsearch: {ELASTICSEARCH_URL}')
```

- [ ] **Step 2: Run verification**

```bash
# Start all observability services
cd docker
docker-compose up -d prometheus grafana jaeger elasticsearch logstash kibana

# Wait for services to start
sleep 30

# Run verification
cd ..
python scripts/test_observability.py
```

- [ ] **Step 3: Commit**

```bash
git add scripts/test_observability.py
git commit -m "test: add observability verification script"
```

---

## Success Criteria

- [ ] Prometheus scraping all services
- [ ] Grafana dashboards displaying metrics
- [ ] Logs visible in Kibana
- [ ] Traces visible in Jaeger
- [ ] Alert rules loaded in Prometheus
- [ ] Metrics endpoint accessible at `/metrics`
- [ ] All verification tests pass

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Prometheus not scraping | Check targets at `/api/v1/targets` |
| Grafana shows no data | Verify datasource URL is `http://prometheus:9090` |
| No logs in Kibana | Create index pattern `medical-triage-*` |
| No traces in Jaeger | Make requests, wait 30s for flush |
| Elasticsearch won't start | Increase `vm.max_map_count`: `sysctl -w vm.max_map_count=262144` |
