# Medical Triage Assistant - Kubernetes Deployment

## Prerequisites

- Kubernetes cluster 1.25+ (kind, minikube, EKS, GKE, AKS)
- kubectl configured
- Helm 3.x (optional, for Helm-based deployment)
- PersistentVolume provisioner (for stateful services)

## Quick Start

### Option 1: kubectl apply (Recommended for development)

```bash
# 1. Create namespace and all resources
kubectl apply -f kubernetes/namespace.yaml
kubectl apply -f kubernetes/

# 2. Wait for all pods to be ready
kubectl get pods -n medical-triage -w

# 3. Access services
kubectl port-forward -n medical-triage svc/kong 8000:80
kubectl port-forward -n medical-triage svc/grafana 3000:3000
kubectl port-forward -n medical-triage svc/prometheus 9090:9090
kubectl port-forward -n medical-triage svc/jaeger 16686:16686
```

### Option 2: Helm (Recommended for production)

```bash
# 1. Add values overrides (optional)
cp kubernetes/helm/values.yaml my-values.yaml
# Edit my-values.yaml with your configuration

# 2. Install chart
helm install medical-triage kubernetes/helm/ -f my-values.yaml

# 3. Check status
helm status medical-triage
helm list
```

## Access URLs

After deployment, access the services:

| Service | URL | Credentials |
|---------|-----|-------------|
| API Gateway | http://localhost:8000 | - |
| Grafana | http://localhost:3000 | admin / admin-password-change-me |
| Prometheus | http://localhost:9090 | - |
| Jaeger Tracing | http://localhost:16686 | - |
| Kafka UI | http://localhost:8080 | - |
| MLflow | http://localhost:5000 | - |

## Production Configuration

### 1. Update Secrets

```bash
# Generate strong secrets
kubectl create secret generic app-secrets \
  --from-literal=DB_PASSWORD=$(openssl rand -base64 32) \
  --from-literal=SECRET_KEY=$(openssl rand -base64 32) \
  --from-literal=JWT_SECRET=$(openssl rand -base64 32) \
  --from-literal=GOOGLE_API_KEY=your-api-key \
  -n medical-triage --dry-run=client -o yaml | kubectl apply -f -
```

### 2. Configure Ingress

Update `kubernetes/ingress.yaml` with your domain:

```yaml
spec:
  rules:
    - host: api.yourdomain.com
```

### 3. Enable TLS

```yaml
spec:
  tls:
    - hosts:
        - api.yourdomain.com
      secretName: medical-triage-tls
```

## Scaling

### Manual Scaling

```bash
kubectl scale deployment backend -n medical-triage --replicas=5
kubectl scale deployment inference-service -n medical-triage --replicas=10
```

### Auto-Scaling (HPA)

HPA is pre-configured in deployment manifests:

- Backend: 3-10 replicas based on CPU/memory
- Inference: 2-20 replicas based on CPU

## Monitoring

### Check Pod Status

```bash
kubectl get pods -n medical-triage
kubectl describe pod <pod-name> -n medical-triage
```

### View Logs

```bash
kubectl logs -f deployment/backend -n medical-triage
kubectl logs -f deployment/inference-service -n medical-triage
```

### Port Forward All Services

```bash
# Run in separate terminals
kubectl port-forward -n medical-triage svc/kong 8000:80
kubectl port-forward -n medical-triage svc/grafana 3000:3000
kubectl port-forward -n medical-triage svc/prometheus 9090:9090
kubectl port-forward -n medical-triage svc/jaeger 16686:16686
kubectl port-forward -n medical-triage svc/kafka-ui 8080:8080
kubectl port-forward -n medical-triage svc/mlflow 5000:5000
```

## Troubleshooting

### Pod Not Starting

```bash
# Check events
kubectl get events -n medical-triage --sort-by='.lastTimestamp'

# Check logs
kubectl logs <pod-name> -n medical-triage
```

### Database Connection Issues

```bash
# Check postgres is running
kubectl get pods -n medical-triage -l app=postgres

# Test connection from backend pod
kubectl exec -it deployment/backend -n medical-triage -- \
  psql -h postgres -U postgres -d medical_triage -c "SELECT 1"
```

### Service Discovery Issues

```bash
# Check services
kubectl get svc -n medical-triage

# Test DNS resolution
kubectl run -it --rm dns-test --image=busybox:1.28 --restart=Never -- \
  nslookup backend.medical-triage.svc.cluster.local
```

## Uninstall

### kubectl

```bash
kubectl delete namespace medical-triage
```

### Helm

```bash
helm uninstall medical-triage
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Kubernetes Cluster                       │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              medical-triage Namespace                 │   │
│  │                                                       │   │
│  │  ┌─────────────┐    ┌─────────────┐    ┌──────────┐  │   │
│  │  │   Kong      │    │   Backend   │    │Inference │  │   │
│  │  │  Gateway    │───▶│  (x3 pods)  │───▶│ (x2 pod) │  │   │
│  │  │  (x2 pods)  │    │  :8000      │    │ :50053   │  │   │
│  │  └─────────────┘    └─────────────┘    └──────────┘  │   │
│  │         │                                          │   │
│  │         ▼                                          │   │
│  │  ┌────────────────────────────────────────────┐    │   │
│  │  │  Observability Stack                        │    │   │
│  │  │  - Prometheus (metrics)                     │    │   │
│  │  │  - Grafana (dashboards)                     │    │   │
│  │  │  - Jaeger (tracing)                         │    │   │
│  │  │  - Loki (logging)                           │    │   │
│  │  └────────────────────────────────────────────┘    │   │
│  │                                                       │   │
│  │  ┌─────────────┐    ┌─────────────┐                  │   │
│  │  │  PostgreSQL │    │    Redis    │                  │   │
│  │  │  (Stateful) │    │  (Cache)    │                  │   │
│  │  └─────────────┘    └─────────────┘                  │   │
│  │                                                       │   │
│  │  ┌─────────────┐    ┌─────────────┐                  │   │
│  │  │    Kafka    │    │   MLflow    │                  │   │
│  │  │  (Streaming)│    │ (Registry)  │                  │   │
│  │  └─────────────┘    └─────────────┘                  │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```
