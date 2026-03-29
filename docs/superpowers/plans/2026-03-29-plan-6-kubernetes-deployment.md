# Kubernetes Deployment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deploy the Health Triage system to Kubernetes with auto-scaling, high availability, and production-grade configuration.

**Architecture:** All services deployed as Kubernetes Deployments with Horizontal Pod Autoscaling (HPA), Services for networking, Ingress for external access, ConfigMaps/Secrets for configuration, and Helm charts for package management.

**Tech Stack:** Kubernetes, Helm, Nginx Ingress, Cert-Manager (TLS), Horizontal Pod Autoscaler, Kubernetes Secrets

---

## Files Overview

| File | Action | Responsibility |
|------|--------|----------------|
| `k8s/namespaces.yml` | Create | Namespace definition |
| `k8s/configmaps.yml` | Create | Application configuration |
| `k8s/secrets.yml` | Create | Sensitive configuration |
| `k8s/postgres-statefulset.yml` | Create | PostgreSQL deployment |
| `k8s/redis-deployment.yml` | Create | Redis deployment |
| `k8s/backend-deployment.yml` | Create | Backend service deployment |
| `k8s/inference-deployment.yml` | Create | Inference service deployment |
| `k8s/ingress.yml` | Create | Ingress routing |
| `k8s/hpa.yml` | Create | Auto-scaling configuration |
| `charts/medical-triage/` | Create | Helm chart |

---

### Task 1: Namespace and Base Configuration

**Files:**
- Create: `k8s/namespaces.yml`
- Create: `k8s/configmaps.yml`
- Create: `k8s/secrets.yml`

- [ ] **Step 1: Create namespace**

```yaml
# k8s/namespaces.yml
apiVersion: v1
kind: Namespace
metadata:
  name: medical-triage
  labels:
    name: medical-triage
    environment: production
    team: health-platform
---
# Resource quota for the namespace
apiVersion: v1
kind: ResourceQuota
metadata:
  name: medical-triage-quota
  namespace: medical-triage
spec:
  hard:
    requests.cpu: "10"
    requests.memory: 20Gi
    limits.cpu: "20"
    limits.memory: 40Gi
    pods: "50"
    services: "20"
    secrets: "20"
    configmaps: "20"
---
# Limit range for default resource constraints
apiVersion: v1
kind: LimitRange
metadata:
  name: medical-triage-limits
  namespace: medical-triage
spec:
  limits:
  - default:
      cpu: 500m
      memory: 512Mi
    defaultRequest:
      cpu: 100m
      memory: 128Mi
    type: Container
```

- [ ] **Step 2: Create ConfigMaps**

```yaml
# k8s/configmaps.yml
apiVersion: v1
kind: ConfigMap
metadata:
  name: backend-config
  namespace: medical-triage
data:
  DEBUG: "false"
  ALLOWED_HOSTS: "medical-triage.example.com,api.medical-triage.example.com"
  DB_NAME: "medical_triage"
  DB_USER: "postgres"
  DB_HOST: "postgres-service"
  DB_PORT: "5432"
  REDIS_URL: "redis://redis-service:6379/0"
  KAFKA_BOOTSTRAP_SERVERS: "kafka-service:9092"
  MLFLOW_TRACKING_URI: "http://mlflow-service:5000"
  LOG_LEVEL: "INFO"
  CELERY_BROKER_URL: "redis://redis-service:6379/0"
  CELERY_RESULT_BACKEND: "redis://redis-service:6379/0"
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: inference-config
  namespace: medical-triage
data:
  MLFLOW_TRACKING_URI: "http://mlflow-service:5000"
  REDIS_HOST: "redis-service"
  REDIS_PORT: "6379"
  MODEL_PATH: "/app/models/classifier.joblib"
  CACHE_TTL: "86400"
  AB_TEST_ENABLED: "true"
  AB_TEST_CHAMPION_VERSION: "v1.0"
  AB_TEST_CHALLENGER_VERSION: "v2.0"
  AB_TEST_CHALLENGER_TRAFFIC: "10"
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: agent-config
  namespace: medical-triage
data:
  GEMINI_MODEL: "gemini-2.5-flash"
  GEMINI_TEMPERATURE: "0.3"
  MAX_CONVERSATION_HISTORY: "20"
  STREAMING_ENABLED: "true"
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: nginx-config
  namespace: medical-triage
data:
  proxy-body-size: "10m"
  proxy-read-timeout: "600"
  proxy-send-timeout: "600"
  ssl-protocols: "TLSv1.2 TLSv1.3"
  rate-limit: "100"
  rate-limit-window: "1m"
```

- [ ] **Step 3: Create Secrets template**

```yaml
# k8s/secrets.yml
# IMPORTANT: In production, use external-secrets or sealed-secrets
# This is a template - replace values with actual secrets

apiVersion: v1
kind: Secret
metadata:
  name: backend-secrets
  namespace: medical-triage
type: Opaque
stringData:
  # Generate with: echo -n 'your-secret' | base64
  SECRET_KEY: "change-me-in-production"
  DB_PASSWORD: "postgres-password-change-me"
  JWT_SECRET: "jwt-secret-change-me"
  GOOGLE_API_KEY: "your-gemini-api-key-here"
  AWS_ACCESS_KEY_ID: "your-aws-key"
  AWS_SECRET_ACCESS_KEY: "your-aws-secret"
---
apiVersion: v1
kind: Secret
metadata:
  name: postgres-secrets
  namespace: medical-triage
type: Opaque
stringData:
  POSTGRES_PASSWORD: "postgres-password-change-me"
  POSTGRES_USER: "postgres"
  POSTGRES_DB: "medical_triage"
---
apiVersion: v1
kind: Secret
metadata:
  name: redis-secrets
  namespace: medical-triage
type: Opaque
stringData:
  REDIS_PASSWORD: "redis-password-change-me"
```

- [ ] **Step 4: Commit**

```bash
git add k8s/namespaces.yml k8s/configmaps.yml k8s/secrets.yml
git commit -m "k8s: add namespace, configmaps, and secrets"
```

---

### Task 2: Database StatefulSet

**Files:**
- Create: `k8s/postgres-statefulset.yml`
- Create: `k8s/postgres-service.yml`
- Create: `k8s/postgres-pvc.yml`

- [ ] **Step 1: Create PostgreSQL StatefulSet**

```yaml
# k8s/postgres-statefulset.yml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: medical-triage
  labels:
    app: postgres
    component: database
spec:
  serviceName: postgres-service
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:16-alpine
        ports:
        - containerPort: 5432
          name: postgres
        env:
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-secrets
              key: POSTGRES_PASSWORD
        - name: POSTGRES_USER
          valueFrom:
            secretKeyRef:
              name: postgres-secrets
              key: POSTGRES_USER
        - name: POSTGRES_DB
          valueFrom:
            secretKeyRef:
              name: postgres-secrets
              key: POSTGRES_DB
        - name: PGDATA
          value: /var/lib/postgresql/data/pgdata
        resources:
          requests:
            cpu: 500m
            memory: 1Gi
          limits:
            cpu: 2000m
            memory: 4Gi
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
        livenessProbe:
          exec:
            command:
            - pg_isready
            - -U
            - $(POSTGRES_USER)
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          exec:
            command:
            - pg_isready
            - -U
            - $(POSTGRES_USER)
          initialDelaySeconds: 5
          periodSeconds: 5
      securityContext:
        fsGroup: 999  # postgres user
  volumeClaimTemplates:
  - metadata:
      name: postgres-storage
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 10Gi
      storageClassName: standard
```

- [ ] **Step 2: Create PostgreSQL Service**

```yaml
# k8s/postgres-service.yml
apiVersion: v1
kind: Service
metadata:
  name: postgres-service
  namespace: medical-triage
  labels:
    app: postgres
spec:
  type: ClusterIP
  ports:
  - port: 5432
    targetPort: 5432
    name: postgres
  selector:
    app: postgres
---
# Headless service for StatefulSet
apiVersion: v1
kind: Service
metadata:
  name: postgres-headless
  namespace: medical-triage
  labels:
    app: postgres
spec:
  clusterIP: None
  ports:
  - port: 5432
    targetPort: 5432
    name: postgres
  selector:
    app: postgres
```

- [ ] **Step 3: Commit**

```bash
git add k8s/postgres-statefulset.yml k8s/postgres-service.yml
git commit -m "k8s: add PostgreSQL StatefulSet and service"
```

---

### Task 3: Redis Deployment

**Files:**
- Create: `k8s/redis-deployment.yml`
- Create: `k8s/redis-service.yml`

- [ ] **Step 1: Create Redis Deployment**

```yaml
# k8s/redis-deployment.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: medical-triage
  labels:
    app: redis
    component: cache
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
          name: redis
        command:
        - redis-server
        - --appendonly
        - "yes"
        - --requirepass
        - $(REDIS_PASSWORD)
        env:
        - name: REDIS_PASSWORD
          valueFrom:
            secretKeyRef:
              name: redis-secrets
              key: REDIS_PASSWORD
        resources:
          requests:
            cpu: 250m
            memory: 512Mi
          limits:
            cpu: 1000m
            memory: 2Gi
        volumeMounts:
        - name: redis-storage
          mountPath: /data
        livenessProbe:
          exec:
            command:
            - redis-cli
            - ping
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          exec:
            command:
            - redis-cli
            - ping
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: redis-storage
        emptyDir: {}  # Use persistent volume in production
```

- [ ] **Step 2: Create Redis Service**

```yaml
# k8s/redis-service.yml
apiVersion: v1
kind: Service
metadata:
  name: redis-service
  namespace: medical-triage
  labels:
    app: redis
spec:
  type: ClusterIP
  ports:
  - port: 6379
    targetPort: 6379
    name: redis
  selector:
    app: redis
```

- [ ] **Step 3: Commit**

```bash
git add k8s/redis-deployment.yml k8s/redis-service.yml
git commit -m "k8s: add Redis deployment and service"
```

---

### Task 4: Backend Deployment

**Files:**
- Create: `k8s/backend-deployment.yml`
- Create: `k8s/backend-service.yml`
- Create: `k8s/backend-hpa.yml`

- [ ] **Step 1: Create Backend Deployment**

```yaml
# k8s/backend-deployment.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  namespace: medical-triage
  labels:
    app: backend
    component: api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8000"
        prometheus.io/path: "/metrics"
    spec:
      containers:
      - name: backend
        image: medical-triage-backend:latest
        imagePullPolicy: Always
        ports:
        - containerPort: 8000
          name: http
          protocol: TCP
        envFrom:
        - configMapRef:
            name: backend-config
        - secretRef:
            name: backend-secrets
        resources:
          requests:
            cpu: 250m
            memory: 512Mi
          limits:
            cpu: 1000m
            memory: 2Gi
        livenessProbe:
          httpGet:
            path: /api/health/
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/health/
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
        lifecycle:
          preStop:
            exec:
              command: ["kill", "-SIGTERM", "1"]
      imagePullSecrets:
      - name: registry-secret  # Create this for private registry
---
# Migration job (runs once before deployment)
apiVersion: batch/v1
kind: Job
metadata:
  name: backend-migrations
  namespace: medical-triage
spec:
  template:
    spec:
      containers:
      - name: migrations
        image: medical-triage-backend:latest
        command: ["python", "manage.py", "migrate"]
        envFrom:
        - configMapRef:
            name: backend-config
        - secretRef:
            name: backend-secrets
      restartPolicy: OnFailure
  backoffLimit: 3
```

- [ ] **Step 2: Create Backend Service**

```yaml
# k8s/backend-service.yml
apiVersion: v1
kind: Service
metadata:
  name: backend-service
  namespace: medical-triage
  labels:
    app: backend
spec:
  type: ClusterIP
  ports:
  - port: 8000
    targetPort: 8000
    name: http
    protocol: TCP
  selector:
    app: backend
---
# WebSocket service (same deployment, different service for clarity)
apiVersion: v1
kind: Service
metadata:
  name: backend-ws-service
  namespace: medical-triage
  labels:
    app: backend
spec:
  type: ClusterIP
  ports:
  - port: 8000
    targetPort: 8000
    name: ws
    protocol: TCP
  selector:
    app: backend
```

- [ ] **Step 3: Create Backend HPA**

```yaml
# k8s/backend-hpa.yml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-hpa
  namespace: medical-triage
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  - type: Pods
    pods:
      metric:
        name: http_requests_per_second
      target:
        type: AverageValue
        averageValue: "100"
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 60
      - type: Pods
        value: 4
        periodSeconds: 60
      selectPolicy: Max
```

- [ ] **Step 4: Commit**

```bash
git add k8s/backend-deployment.yml k8s/backend-service.yml k8s/backend-hpa.yml
git commit -m "k8s: add Backend deployment with HPA"
```

---

### Task 5: Inference Service Deployment

**Files:**
- Create: `k8s/inference-deployment.yml`
- Create: `k8s/inference-service.yml`
- Create: `k8s/inference-hpa.yml`

- [ ] **Step 1: Create Inference Deployment**

```yaml
# k8s/inference-deployment.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: inference-service
  namespace: medical-triage
  labels:
    app: inference-service
    component: ml
spec:
  replicas: 2
  selector:
    matchLabels:
      app: inference-service
  template:
    metadata:
      labels:
        app: inference-service
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8004"
        prometheus.io/path: "/metrics"
    spec:
      containers:
      - name: inference
        image: medical-triage-inference:latest
        imagePullPolicy: Always
        ports:
        - containerPort: 8004
          name: http
          protocol: TCP
        - containerPort: 50053
          name: grpc
          protocol: TCP
        envFrom:
        - configMapRef:
            name: inference-config
        resources:
          requests:
            cpu: 500m
            memory: 1Gi
          limits:
            cpu: 2000m
            memory: 4Gi
        volumeMounts:
        - name: model-storage
          mountPath: /app/models
          readOnly: true
        livenessProbe:
          httpGet:
            path: /health
            port: 8004
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8004
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: model-storage
        configMap:
          name: model-files-config
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: model-files-config
  namespace: medical-triage
data:
  # Placeholder - mount actual model files via PVC or init container
  classifier.joblib: |
    # Model file mounted from external source
```

- [ ] **Step 2: Create Inference Service**

```yaml
# k8s/inference-service.yml
apiVersion: v1
kind: Service
metadata:
  name: inference-service
  namespace: medical-triage
  labels:
    app: inference-service
spec:
  type: ClusterIP
  ports:
  - port: 8004
    targetPort: 8004
    name: http
    protocol: TCP
  - port: 50053
    targetPort: 50053
    name: grpc
    protocol: TCP
  selector:
    app: inference-service
```

- [ ] **Step 3: Create Inference HPA**

```yaml
# k8s/inference-hpa.yml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: inference-service-hpa
  namespace: medical-triage
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: inference-service
  minReplicas: 2
  maxReplicas: 8
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 60
  - type: Pods
    pods:
      metric:
        name: inference_requests_per_second
      target:
        type: AverageValue
        averageValue: "50"
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 60
```

- [ ] **Step 4: Commit**

```bash
git add k8s/inference-deployment.yml k8s/inference-service.yml k8s/inference-hpa.yml
git commit -m "k8s: add Inference Service deployment with HPA"
```

---

### Task 6: Ingress and Network Policies

**Files:**
- Create: `k8s/ingress.yml`
- Create: `k8s/network-policy.yml`
- Create: `k8s/certificate.yml`

- [ ] **Step 1: Create Ingress**

```yaml
# k8s/ingress.yml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: medical-triage-ingress
  namespace: medical-triage
  annotations:
    kubernetes.io/ingress.class: nginx
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/rate-limit-window: "1m"
    nginx.ingress.kubernetes.io/connection-proxy-header: "keep-alive"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "600"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "600"
    nginx.ingress.kubernetes.io/proxy-body-size: "10m"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - medical-triage.example.com
    - api.medical-triage.example.com
    secretName: medical-triage-tls
  rules:
  - host: medical-triage.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend-service
            port:
              number: 80
  - host: api.medical-triage.example.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: backend-service
            port:
              number: 8000
      - path: /ws
        pathType: Prefix
        backend:
          service:
            name: backend-ws-service
            port:
              number: 8000
      - path: /inference
        pathType: Prefix
        backend:
          service:
            name: inference-service
            port:
              number: 8004
      - path: /metrics
        pathType: Prefix
        backend:
          service:
            name: backend-service
            port:
              number: 8000
```

- [ ] **Step 2: Create Network Policy**

```yaml
# k8s/network-policy.yml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: backend-network-policy
  namespace: medical-triage
spec:
  podSelector:
    matchLabels:
      app: backend
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    - podSelector:
        matchLabels:
          app: inference-service
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: postgres
    ports:
    - protocol: TCP
      port: 5432
  - to:
    - podSelector:
        matchLabels:
          app: redis
    ports:
    - protocol: TCP
      port: 6379
  - to:
    - namespaceSelector: {}
    ports:
    - protocol: TCP
      port: 443  # Allow HTTPS for external APIs
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: postgres-network-policy
  namespace: medical-triage
spec:
  podSelector:
    matchLabels:
      app: postgres
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: backend
    ports:
    - protocol: TCP
      port: 5432
```

- [ ] **Step 3: Create Certificate (cert-manager)**

```yaml
# k8s/certificate.yml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@example.com
    privateKeySecretRef:
      name: letsencrypt-prod-key
    solvers:
    - http01:
        ingress:
          class: nginx
---
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: medical-triage-cert
  namespace: medical-triage
spec:
  secretName: medical-triage-tls
  duration: 2160h  # 90 days
  renewBefore: 360h  # 15 days before expiry
  subject:
    organizations:
    - Health Triage Team
  commonName: medical-triage.example.com
  isCA: false
  dnsNames:
  - medical-triage.example.com
  - api.medical-triage.example.com
  issuerRef:
    name: letsencrypt-prod
    kind: ClusterIssuer
```

- [ ] **Step 4: Commit**

```bash
git add k8s/ingress.yml k8s/network-policy.yml k8s/certificate.yml
git commit -m "k8s: add Ingress, Network Policies, and TLS certificates"
```

---

### Task 7: Helm Chart

**Files:**
- Create: `charts/medical-triage/Chart.yaml`
- Create: `charts/medical-triage/values.yaml`
- Create: `charts/medical-triage/templates/`

- [ ] **Step 1: Create Chart.yaml**

```yaml
# charts/medical-triage/Chart.yaml
apiVersion: v2
name: medical-triage
description: Health Triage Assistant - AI-powered symptom assessment
type: application
version: 1.0.0
appVersion: "1.0.0"
keywords:
  - health
  - triage
  - ml
  - ai
maintainers:
  - name: Your Name
    email: your.email@example.com
dependencies:
  - name: postgresql
    version: 12.x.x
    repository: https://charts.bitnami.com/bitnami
    condition: postgresql.enabled
  - name: redis
    version: 17.x.x
    repository: https://charts.bitnami.com/bitnami
    condition: redis.enabled
  - name: nginx-ingress
    version: 4.x.x
    repository: https://kubernetes.github.io/ingress-nginx
    condition: ingress.enabled
```

- [ ] **Step 2: Create values.yaml**

```yaml
# charts/medical-triage/values.yaml
replicaCount: 3

image:
  repository: medical-triage-backend
  tag: latest
  pullPolicy: Always

nameOverride: ""
fullnameOverride: ""

serviceAccount:
  create: true
  name: medical-triage-sa

podSecurityContext:
  fsGroup: 1000

securityContext:
  runAsNonRoot: true
  runAsUser: 1000

service:
  type: ClusterIP
  port: 8000

ingress:
  enabled: true
  className: nginx
  annotations:
    nginx.ingress.kubernetes.io/rate-limit: "100"
  hosts:
    - host: medical-triage.example.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: medical-triage-tls
      hosts:
        - medical-triage.example.com

resources:
  requests:
    cpu: 250m
    memory: 512Mi
  limits:
    cpu: 1000m
    memory: 2Gi

autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
  targetMemoryUtilizationPercentage: 80

# External service configuration
postgresql:
  enabled: true
  auth:
    existingSecret: postgres-secrets

redis:
  enabled: true
  auth:
    existingSecret: redis-secrets

# Feature flags
features:
  kafkaEnabled: false
  mlflowEnabled: true
  observabilityEnabled: true

# Monitoring
monitoring:
  prometheusScrape: true
  serviceMonitor:
    enabled: true
    interval: 15s
```

- [ ] **Step 3: Create deployment template**

```yaml
# charts/medical-triage/templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "medical-triage.fullname" . }}
  labels:
    {{- include "medical-triage.labels" . | nindent 4 }}
spec:
  {{- if not .Values.autoscaling.enabled }}
  replicas: {{ .Values.replicaCount }}
  {{- end }}
  selector:
    matchLabels:
      {{- include "medical-triage.selectorLabels" . | nindent 6 }}
  template:
    metadata:
      labels:
        {{- include "medical-triage.selectorLabels" . | nindent 8 }}
      annotations:
        prometheus.io/scrape: "{{ .Values.monitoring.prometheusScrape }}"
        prometheus.io/port: "8000"
    spec:
      serviceAccountName: {{ include "medical-triage.serviceAccountName" . }}
      securityContext:
        {{- toYaml .Values.podSecurityContext | nindent 8 }}
      containers:
        - name: {{ .Chart.Name }}
          securityContext:
            {{- toYaml .Values.securityContext | nindent 12 }}
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          ports:
            - name: http
              containerPort: 8000
              protocol: TCP
          livenessProbe:
            httpGet:
              path: /api/health/
              port: http
            initialDelaySeconds: 30
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /api/health/
              port: http
            initialDelaySeconds: 5
            periodSeconds: 5
          resources:
            {{- toYaml .Values.resources | nindent 12 }}
      {{- with .Values.nodeSelector }}
      nodeSelector:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      {{- with .Values.affinity }}
      affinity:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      {{- with .Values.tolerations }}
      tolerations:
        {{- toYaml . | nindent 8 }}
      {{- end }}
```

- [ ] **Step 4: Commit**

```bash
git add charts/medical-triage/
git commit -m "k8s: add Helm chart for medical-triage"
```

---

### Task 8: Deployment Scripts

**Files:**
- Create: `scripts/deploy-k8s.sh`
- Create: `scripts/destroy-k8s.sh`

- [ ] **Step 1: Create deploy script**

```bash
#!/bin/bash
# scripts/deploy-k8s.sh

set -e

NAMESPACE="medical-triage"
CONTEXT="${K8S_CONTEXT:-docker-desktop}"

echo "Deploying Medical Triage to Kubernetes..."
echo "Context: $CONTEXT"
echo "Namespace: $NAMESPACE"

# Set context
kubectl config use-context $CONTEXT

# Create namespace
echo "Creating namespace..."
kubectl apply -f k8s/namespaces.yml

# Apply secrets (ensure you've created real secrets first)
echo "Applying secrets..."
kubectl apply -f k8s/secrets.yml -n $NAMESPACE

# Apply configmaps
echo "Applying configmaps..."
kubectl apply -f k8s/configmaps.yml -n $NAMESPACE

# Deploy infrastructure
echo "Deploying PostgreSQL..."
kubectl apply -f k8s/postgres-statefulset.yml -f k8s/postgres-service.yml -n $NAMESPACE

echo "Deploying Redis..."
kubectl apply -f k8s/redis-deployment.yml -f k8s/redis-service.yml -n $NAMESPACE

# Wait for infrastructure
echo "Waiting for PostgreSQL to be ready..."
kubectl wait --for=condition=ready pod -l app=postgres -n $NAMESPACE --timeout=120s

echo "Waiting for Redis to be ready..."
kubectl wait --for=condition=ready pod -l app=redis -n $NAMESPACE --timeout=60s

# Run migrations
echo "Running database migrations..."
kubectl apply -f k8s/backend-deployment.yml -n $NAMESPACE
kubectl wait --for=condition=complete job/backend-migrations -n $NAMESPACE --timeout=120s

# Deploy services
echo "Deploying Backend..."
kubectl apply -f k8s/backend-deployment.yml -f k8s/backend-service.yml -f k8s/backend-hpa.yml -n $NAMESPACE

echo "Deploying Inference Service..."
kubectl apply -f k8s/inference-deployment.yml -f k8s/inference-service.yml -f k8s/inference-hpa.yml -n $NAMESPACE

# Deploy networking
echo "Deploying Ingress and Network Policies..."
kubectl apply -f k8s/ingress.yml -f k8s/network-policy.yml -f k8s/certificate.yml -n $NAMESPACE

# Wait for deployments
echo "Waiting for deployments to be ready..."
kubectl wait --for=condition=available deployment/backend -n $NAMESPACE --timeout=300s
kubectl wait --for=condition=available deployment/inference-service -n $NAMESPACE --timeout=300s

echo ""
echo "Deployment complete!"
echo ""
echo "Access URLs:"
echo "  API: https://api.medical-triage.example.com"
echo "  Frontend: https://medical-triage.example.com"
echo "  Metrics: https://api.medical-triage.example.com/metrics"
echo ""
echo "Useful commands:"
echo "  kubectl get pods -n $NAMESPACE"
echo "  kubectl logs -l app=backend -n $NAMESPACE"
echo "  kubectl describe ingress medical-triage-ingress -n $NAMESPACE"
```

- [ ] **Step 2: Create destroy script**

```bash
#!/bin/bash
# scripts/destroy-k8s.sh

set -e

NAMESPACE="medical-triage"

echo "WARNING: This will delete all Medical Triage resources!"
echo "Namespace: $NAMESPACE"
read -p "Are you sure? (yes to confirm): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Aborted."
    exit 1
fi

# Delete namespace (removes everything)
echo "Deleting namespace..."
kubectl delete namespace $NAMESPACE --wait=false

echo "Resources are being deleted in the background."
echo "Use 'kubectl get namespace $NAMESPACE' to check progress."
```

- [ ] **Step 3: Make scripts executable**

```bash
chmod +x scripts/deploy-k8s.sh scripts/destroy-k8s.sh
```

- [ ] **Step 4: Commit**

```bash
git add scripts/deploy-k8s.sh scripts/destroy-k8s.sh
git commit -m "k8s: add deployment and cleanup scripts"
```

---

### Task 9: Testing & Verification

**Files:**
- Create: `scripts/test-k8s-deployment.sh`

- [ ] **Step 1: Create verification script**

```bash
#!/bin/bash
# scripts/test-k8s-deployment.sh

NAMESPACE="medical-triage"

echo "Medical Triage Kubernetes Deployment Verification"
echo "=" * 60

# Check namespace
echo -e "\n=== Checking Namespace ==="
kubectl get namespace $NAMESPACE

# Check pods
echo -e "\n=== Checking Pods ==="
kubectl get pods -n $NAMESPACE

# Check deployments
echo -e "\n=== Checking Deployments ==="
kubectl get deployments -n $NAMESPACE

# Check services
echo -e "\n=== Checking Services ==="
kubectl get services -n $NAMESPACE

# Check HPA
echo -e "\n=== Checking HPA ==="
kubectl get hpa -n $NAMESPACE

# Check ingress
echo -e "\n=== Checking Ingress ==="
kubectl get ingress -n $NAMESPACE

# Check pod logs
echo -e "\n=== Checking Backend Logs (last 10 lines) ==="
kubectl logs -l app=backend -n $NAMESPACE --tail=10

# Test backend health
echo -e "\n=== Testing Backend Health ==="
BACKEND_POD=$(kubectl get pod -l app=backend -n $NAMESPACE -o jsonpath='{.items[0].metadata.name}')
kubectl exec $BACKEND_POD -n $NAMESPACE -- curl -s http://localhost:8000/api/health/

# Test inference health
echo -e "\n=== Testing Inference Health ==="
INFERENCE_POD=$(kubectl get pod -l app=inference-service -n $NAMESPACE -o jsonpath='{.items[0].metadata.name}')
kubectl exec $INFERENCE_POD -n $NAMESPACE -- curl -s http://localhost:8004/health

echo -e "\n" + "=" * 60
echo "Verification complete!"
```

- [ ] **Step 2: Commit**

```bash
git add scripts/test-k8s-deployment.sh
git commit -m "k8s: add deployment verification script"
```

---

## Success Criteria

- [ ] All pods running and ready
- [ ] PostgreSQL StatefulSet healthy
- [ ] Redis deployment healthy
- [ ] Backend HPA active with 2+ replicas
- [ ] Inference HPA active with 2+ replicas
- [ ] Ingress routing working
- [ ] Health endpoints responding
- [ ] Deploy script completes without errors
- [ ] Helm chart installs successfully

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Pods in CrashLoopBackOff | Check logs: `kubectl logs <pod> -n medical-triage` |
| Pending pods | Check resources: `kubectl describe pod <pod> -n medical-triage` |
| Ingress not working | Verify ingress controller: `kubectl get pods -n ingress-nginx` |
| Database connection failed | Check secrets: `kubectl get secret backend-secrets -n medical-triage -o yaml` |
| HPA not scaling | Check metrics: `kubectl top pods -n medical-triage` |
