# Distributed ML Scale Architecture Design

**Date:** 2026-03-29
**Author:** Health Triage Assistant Team
**Status:** Approved

---

## 1. Executive Summary

This document describes the architecture for scaling the Health Triage Assistant from a Django monolith to a distributed ML system capable of handling 1000+ requests per second with sub-200ms latency.

**Goals:**
- Horizontal scaling via service decomposition
- Production ML infrastructure (MLflow, A/B testing, drift detection)
- Enterprise-grade observability (metrics, logging, tracing)
- Kubernetes-native deployment with auto-scaling

**Non-Goals:**
- Mobile app development (web-first)
- Direct healthcare provider integrations (regulatory scope)
- Multi-region deployment (single-region sufficient for resume project)

---

## 2. Current State

### 2.1 Existing Architecture

```
┌─────────────┐     ┌─────────────────────────────────────┐     ┌─────────────┐
│   React     │────▶│         Django Monolith             │────▶│  PostgreSQL │
│  Frontend   │     │  - REST API                         │     │             │
│             │◀────│  - WebSocket (Channels)             │     │             │
└─────────────┘     │  - ML Inference (inline)            │     └─────────────┘
                    │  - LangChain Agent                  │
                    │  - Celery Workers                   │
                    └─────────────────────────────────────┘
                              │
                              ▼
                        ┌─────────────┐
                        │    Redis    │
                        │ (Cache+MQ)  │
                        └─────────────┘
```

### 2.2 Current Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 18 + TypeScript + Tailwind |
| Backend | Django 5 + DRF + Channels |
| ML | XGBoost + scikit-learn |
| Agent | LangChain + LangGraph + Gemini 2.5 Flash |
| Database | PostgreSQL 16 |
| Cache/Queue | Redis 7 |
| Async | Celery 5 |

---

## 3. Target Architecture

### 3.1 System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                           CLIENT LAYER                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │
│  │   Web App   │  │  Mobile App │  │  API Clients│                 │
│  │   (React)   │  │   (Future)  │  │  (External) │                 │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘                 │
└─────────┼────────────────┼────────────────┼─────────────────────────┘
          │                │                │
          ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      API GATEWAY (Kong)                             │
│         Rate Limiting │ JWT Auth │ Request Routing │ Caching       │
│         Global Rate Limit: 1000 req/min per IP                      │
└─────────────────────────────────────────────────────────────────────┘
          │                │                │
          ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        SERVICE MESH                                 │
│  ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐    │
│  │   Auth Service   │ │  Triage Service  │ │  Patient Service │    │
│  │   :8001          │ │    :8002         │ │    :8003         │    │
│  │   (JWT + OAuth)  │ │  (REST + WS)     │ │   (CRUD + Hist)  │    │
│  └──────────────────┘ └──────────────────┘ └──────────────────┘    │
│                                                                     │
│  ┌──────────────────┐ ┌──────────────────┐                         │
│  │ Inference Svc    │ │   Agent Service  │                         │
│  │    :8004         │ │    :8005         │                         │
│  │  (ML Model API)  │ │ (LangChain+LCEL) │                         │
│  └──────────────────┘ └──────────────────┘                         │
└─────────────────────────────────────────────────────────────────────┘
          │                │                │
          ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      MESSAGE BROKER (Kafka)                         │
│    Topics: triage-requests, inference-jobs, async-events, audit    │
│    Partitions: 3 per topic | Replication: 2x                       │
└─────────────────────────────────────────────────────────────────────┘
          │                │                │
          ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      WORKER LAYER (Celery)                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │
│  │Email Worker │  │ PDF Worker   │  │Cleanup Worker│               │
│  │  (Scale: 2) │  │  (Scale: 1)  │  │  (Scale: 1)  │               │
│  └─────────────┘  └─────────────┘  └─────────────┘                 │
└─────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       DATA LAYER                                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │
│  │ PostgreSQL  │  │  Redis      │  │   MLflow    │                 │
│  │ Primary:5432│  │ Cache:6379  │  │  Registry   │                 │
│  │ Replicas: 2 │  │ Cluster: 3  │  │  :5000      │                 │
│  └─────────────┘  └─────────────┘  └─────────────┘                 │
│                                                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │
│  │ Prometheus  │  │   Grafana   │  │    ELK      │                 │
│  │  :9090      │  │   :3000     │  │  :9200      │                 │
│  │  Metrics    │  │  Dashboards │  │  Logging    │                 │
│  └─────────────┘  └─────────────┘  └─────────────┘                 │
│                                                                     │
│  ┌─────────────┐                                                    │
│  │   Jaeger    │                                                    │
│  │   :16686    │                                                    │
│  │  Tracing    │                                                    │
│  └─────────────┘                                                    │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 Service Decomposition

| Service | Port | Responsibility | Scale Target |
|---------|------|----------------|--------------|
| **Auth Service** | 8001 | JWT issuance, OAuth, session management | 2 replicas |
| **Triage Service** | 8002 | Symptom submission, session management, WebSocket hub | 4 replicas |
| **Patient Service** | 8003 | Patient CRUD, history, profile management | 2 replicas |
| **Inference Service** | 8004 | ML model serving, batching, caching | 4 replicas (auto-scale) |
| **Agent Service** | 8005 | LangChain agent, tool orchestration, streaming | 4 replicas (auto-scale) |

---

## 4. Component Specifications

### 4.1 API Gateway (Kong)

**Purpose:** Single entry point, rate limiting, authentication, request routing.

**Configuration:**
```yaml
rate_limiting:
  policy: redis
  second: 100
  minute: 1000
  hour: 10000

jwt_auth:
  key_claim_name: iss
  secret_claim_based_verification: true

routes:
  - name: auth
    paths: [/auth]
    services: auth-service
  - name: triage
    paths: [/triage, /ws]
    services: triage-service
  - name: patients
    paths: [/patients]
    services: patient-service
  - name: inference
    paths: [/inference]
    services: inference-service
  - name: agent
    paths: [/agent, /chat]
    services: agent-service
```

**Health Check:** `GET /health` → 200 OK

---

### 4.2 Auth Service

**Purpose:** Centralized authentication and authorization.

**Endpoints:**
- `POST /auth/register` - User registration
- `POST /auth/login` - JWT token issuance
- `POST /auth/refresh` - Token refresh
- `POST /auth/logout` - Token invalidation
- `GET /auth/verify` - Token verification

**Dependencies:** PostgreSQL (users table), Redis (token blacklist)

---

### 4.3 Triage Service

**Purpose:** Symptom assessment session management, WebSocket hub.

**Endpoints:**
- `POST /triage/sessions` - Create new session
- `GET /triage/sessions/{id}` - Get session details
- `GET /triage/sessions` - List user sessions
- `WS /ws/triage/{session_id}` - Real-time chat

**Kafka Producers:**
- `triage-requests` - New assessment requests
- `audit-logs` - All triage decisions

**Dependencies:** PostgreSQL, Redis, Agent Service (gRPC)

---

### 4.4 Patient Service

**Purpose:** Patient profile and history management.

**Endpoints:**
- `GET /patients/me` - Get current patient profile
- `PUT /patients/me` - Update profile
- `GET /patients/history` - Get triage history
- `GET /patients/reports` - Get generated reports

**Dependencies:** PostgreSQL, Inference Service (for predictions)

---

### 4.5 Inference Service

**Purpose:** ML model serving with batching and caching.

**Endpoints:**
- `POST /inference/predict` - Single prediction
- `POST /inference/batch` - Batch predictions
- `GET /inference/model` - Model metadata
- `GET /inference/health` - Model health check

**Cache Strategy:**
```
Key: symptom_hash:{md5(sorted_symptoms)}
TTL: 24 hours
Hit: Return cached prediction
Miss: Run inference, cache result
```

**Batching:**
- Window: 100ms
- Max batch size: 32
- Fallback: Immediate inference if batch not full

**MLflow Integration:**
- Model registry: Track versions
- A/B testing: Route traffic by model version
- Metrics: Log latency, accuracy per prediction

---

### 4.6 Agent Service

**Purpose:** LangChain agent orchestration with streaming.

**Endpoints:**
- `POST /agent/chat` - Single turn (non-streaming)
- `POST /agent/chat/stream` - Streaming SSE response
- `WS /ws/agent/{session_id}` - Full-duplex WebSocket

**Agent Tools:**
1. `symptom_classifier` - Calls Inference Service
2. `get_patient_history` - Calls Patient Service
3. `get_triage_recommendation` - Internal logic
4. `generate_triage_report` - Triggers PDF worker
5. `trigger_escalation_alert` - Kafka event

**Streaming Protocol:**
```
Event: message
Data: {"chunk": "Hello, I'm your health assistant..."}

Event: tool_call
Data: {"tool": "symptom_classifier", "input": {"symptoms": [...]}}

Event: complete
Data: {"final_response": "..."}
```

---

### 4.7 Message Broker (Kafka)

**Topic Configuration:**

| Topic | Partitions | Replication | Retention |
|-------|------------|-------------|-----------|
| triage-requests | 6 | 2 | 7 days |
| inference-jobs | 6 | 2 | 1 day |
| async-events | 3 | 2 | 3 days |
| audit-logs | 6 | 2 | 90 days |

**Consumer Groups:**
- `triage-consumers` - Agent Service
- `inference-consumers` - Inference Service workers
- `async-consumers` - Celery workers

---

### 4.8 Observability Stack

#### Prometheus Metrics

**Inference Service:**
```
inference_requests_total{status, model_version}
inference_latency_seconds{quantile}
inference_cache_hits_total
inference_batch_size{quantile}
model_accuracy{model_version}
```

**Agent Service:**
```
agent_requests_total{status}
agent_latency_seconds{quantile}
agent_tool_calls_total{tool_name, status}
agent_stream_duration_seconds
```

**Triage Service:**
```
triage_sessions_total{status}
triage_websocket_connections
triage_session_duration_seconds{quantile}
```

#### Grafana Dashboards

1. **System Overview** - Request rate, error rate, latency (RED method)
2. **ML Performance** - Accuracy, latency, cache hit rate, batch efficiency
3. **Agent Performance** - Tool usage, conversation length, escalation rate
4. **Resource Utilization** - CPU, memory, disk per service
5. **Kafka Health** - Lag per consumer group, throughput

#### ELK Logging

**Log Format (JSON):**
```json
{
  "timestamp": "2026-03-29T10:00:00Z",
  "level": "INFO",
  "service": "inference-service",
  "trace_id": "abc123",
  "span_id": "def456",
  "message": "Prediction completed",
  "context": {
    "model_version": "v2.1",
    "latency_ms": 45,
    "cache_hit": false,
    "symptoms_count": 5
  }
}
```

#### Jaeger Tracing

**Trace Propagation:** W3C Trace Context headers

**Key Spans:**
1. API Gateway → Service
2. Service → Kafka (produce)
3. Kafka (consume) → Worker
4. Service → Service (gRPC/HTTP)
5. Service → Database

---

## 5. Data Flow

### 5.1 Symptom Assessment Flow

```
1. User submits symptoms via Web App
2. API Gateway validates JWT, rate limits
3. Triage Service creates session
4. Triage Service → Kafka (triage-requests topic)
5. Agent Service consumes from Kafka
6. Agent invokes symptom_classifier tool
7. Inference Service → Redis cache check
8. Cache miss → XGBoost inference
9. Inference Service → logs to Prometheus, MLflow
10. Agent receives prediction
11. Agent generates response via LLM
12. Response streamed via WebSocket
13. Triage Service persists to PostgreSQL
14. Audit log → Kafka (audit-logs topic)
```

### 5.2 Caching Flow

```
1. Inference Service receives prediction request
2. Compute cache key: md5(sorted(symptoms))
3. Redis GET cache_key
4. If HIT: Return cached result (latency: ~5ms)
5. If MISS:
   a. Load model from MLflow registry
   b. Run XGBoost inference
   c. Redis SET cache_key result EX 86400
   d. Return result (latency: ~50ms)
```

### 5.3 A/B Testing Flow

```
1. Inference Service receives request
2. Determine model version:
   - 90% traffic → model_v2.1 (champion)
   - 10% traffic → model_v2.2 (challenger)
3. Run inference with assigned model
4. Log to MLflow: model_version, prediction, latency
5. Log to Prometheus: inference_requests_total{model_version}
6. Grafana compares accuracy/latency across versions
```

---

## 6. Failure Mode Analysis

### 6.1 Failure Scenarios

| Failure | Detection | Mitigation | Recovery |
|---------|-----------|------------|----------|
| Inference Service down | Health check fails | Circuit breaker opens, queue backlog | Kubernetes restarts pod |
| Redis cluster failure | Connection timeout | Fallback to direct DB, disable caching | Redis Sentinel failover |
| Kafka broker down | Producer timeout | Retry with backoff, local buffer | Kafka controller election |
| PostgreSQL primary fails | Replication lag alert | Promote replica, update connection string | Patroni automatic failover |
| MLflow unavailable | HTTP 5xx | Use last-known-good model version | Restart MLflow service |
| Gemini API rate limited | HTTP 429 | Exponential backoff, queue requests | Wait for rate limit reset |
| High latency (>500ms P99) | Prometheus alert | Scale up replicas, enable caching | HPA auto-scales |

### 6.2 Circuit Breaker Configuration

```yaml
circuit_breaker:
  failure_threshold: 5        # Failures before opening
  recovery_timeout: 30s       # Time before half-open
  half_open_requests: 3       # Test requests before closing
  services: [inference, agent, patient]
```

### 6.3 Retry Policy

```yaml
retry:
  max_attempts: 3
  backoff: exponential
  initial_interval: 100ms
  max_interval: 5s
  retryable_status: [502, 503, 504, 429]
```

---

## 7. Deployment Architecture

### 7.1 Kubernetes Resources

| Resource | Name | Replicas | CPU | Memory |
|----------|------|----------|-----|--------|
| Deployment | auth-service | 2 | 250m | 512Mi |
| Deployment | triage-service | 4 | 500m | 1Gi |
| Deployment | patient-service | 2 | 250m | 512Mi |
| Deployment | inference-service | 4 (HPA: 2-8) | 1000m | 2Gi |
| Deployment | agent-service | 4 (HPA: 2-8) | 500m | 1Gi |
| Deployment | celery-worker | 3 | 500m | 1Gi |
| StatefulSet | postgres | 3 (1 primary) | 1000m | 4Gi |
| StatefulSet | redis | 3 (cluster) | 500m | 1Gi |
| StatefulSet | kafka | 3 | 1000m | 2Gi |
| Deployment | mlflow | 2 | 500m | 1Gi |
| Deployment | prometheus | 2 | 500m | 2Gi |
| Deployment | grafana | 1 | 250m | 512Mi |
| Deployment | elasticsearch | 3 | 1000m | 4Gi |
| Deployment | jaeger | 1 | 500m | 1Gi |

### 7.2 Horizontal Pod Autoscaling

```yaml
# Inference Service HPA
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: inference-service-hpa
spec:
  minReplicas: 2
  maxReplicas: 8
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Pods
    pods:
      metric:
        name: inference_requests_per_second
      target:
        type: AverageValue
        averageValue: 100
```

### 7.3 Ingress Configuration

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: health-triage-ingress
  annotations:
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/rate-limit-window: "1m"
spec:
  rules:
  - host: triage.example.com
    http:
      paths:
      - path: /auth
        backend: auth-service
      - path: /triage
        backend: triage-service
      - path: /ws
        backend: triage-service
      - path: /patients
        backend: patient-service
      - path: /inference
        backend: inference-service
      - path: /agent
        backend: agent-service
```

---

## 8. Testing Strategy

### 8.1 Test Pyramid

```
        ┌───┐
       │ E2E │         10 tests
      │─────│        (Full flow, user journeys)
     │─────────│
    │ Integration │     50 tests
   │─────────────│    (Service contracts, Kafka)
  │─────────────────│
 │      Unit         │  200 tests
 │───────────────────│ (Functions, classes, utilities)
```

### 8.2 Load Testing Targets

| Service | Target RPS | P99 Latency | Error Rate |
|---------|------------|-------------|------------|
| Auth | 500 | <50ms | <0.1% |
| Triage | 1000 | <100ms | <0.5% |
| Patient | 500 | <50ms | <0.1% |
| Inference | 2000 | <200ms | <1% |
| Agent | 500 | <500ms | <1% |

**Tool:** k6 or Locust

---

## 9. Security Considerations

### 9.1 Data Protection

- **Encryption at rest:** PostgreSQL TDE, encrypted PVCs
- **Encryption in transit:** TLS 1.3 everywhere (mTLS for service mesh)
- **PII handling:** Patient data anonymization in logs
- **Secrets management:** Kubernetes Secrets + external vault

### 9.2 API Security

- **Rate limiting:** Per-IP and per-user
- **Input validation:** Pydantic schemas, max length limits
- **SQL injection:** ORM parameterized queries only
- **XSS/CSRF:** CORS headers, CSRF tokens for state-changing ops

### 9.3 Compliance

- **HIPAA considerations:** Audit logs, access controls, data retention
- **GDPR considerations:** Right to deletion, data portability
- **Audit trail:** All triage decisions logged with timestamp, model version, user

---

## 10. Implementation Phases

| Phase | Name | Duration | Key Deliverables |
|-------|------|----------|------------------|
| 9 | API Gateway | 1 week | Kong setup, rate limiting, routing |
| 10 | Service Decomposition | 2 weeks | Split monolith, gRPC contracts |
| 11 | Kafka Integration | 1 week | Topics, producers, consumers |
| 12 | Inference Service | 2 weeks | Model serving, caching, batching |
| 13 | MLflow Integration | 1 week | Model registry, A/B testing |
| 14 | Observability | 2 weeks | Prometheus, Grafana, ELK, Jaeger |
| 15 | Kubernetes | 2 weeks | Manifests, Helm charts, HPA |

---

## 11. Success Metrics

| Metric | Baseline | Target | Measurement |
|--------|----------|--------|-------------|
| Max Throughput | ~100 RPS | 1000+ RPS | k6 load test |
| P99 Latency | ~500ms | <200ms | Prometheus histogram |
| Cache Hit Rate | 0% | >85% | Redis INFO stats |
| Model Accuracy | 86.7% F1 | >88% F1 | MLflow metrics |
| Uptime | N/A | 99.9% | Uptime monitoring |
| Deployment Frequency | Manual | Daily | GitHub Actions |

---

## 12. Open Questions

| Question | Decision Needed | Owner |
|----------|-----------------|-------|
| Kong vs Nginx Plus? | Gateway selection | Architecture |
| Self-hosted vs managed Kafka? | Infrastructure complexity | DevOps |
| MLflow vs Weights & Biases? | Experiment tracking tool | ML |
| Self-hosted K8s vs managed (GKE/EKS)? | Operational overhead | DevOps |

---

## 13. Appendix

### 13.1 Glossary

| Term | Definition |
|------|------------|
| HPA | Horizontal Pod Autoscaler |
| RED | Rate, Errors, Duration (metrics method) |
| LCEL | LangChain Expression Language |
| mTLS | Mutual TLS (service-to-service auth) |
| PVC | Persistent Volume Claim (K8s storage) |

### 13.2 References

- [Kong Documentation](https://docs.konghq.com/)
- [Kafka Documentation](https://kafka.apache.org/documentation/)
- [MLflow Documentation](https://mlflow.org/docs/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Kubernetes HPA](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/)
