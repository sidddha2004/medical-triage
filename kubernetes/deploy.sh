#!/bin/bash
# kubernetes/deploy.sh
# Deploy Medical Triage to Kubernetes

set -e

NAMESPACE="medical-triage"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "========================================"
echo "Medical Triage Kubernetes Deployment"
echo "========================================"

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "Error: kubectl is not installed"
    exit 1
fi

# Check cluster connection
echo ""
echo "Checking cluster connection..."
if ! kubectl cluster-info &> /dev/null; then
    echo "Error: Cannot connect to Kubernetes cluster"
    echo "Make sure you have configured kubectl correctly"
    exit 1
fi

echo "Connected to cluster: $(kubectl config current-context)"

# Create namespace
echo ""
echo "Creating namespace: $NAMESPACE"
kubectl apply -f "$SCRIPT_DIR/namespace.yaml"

# Apply ConfigMap and Secrets
echo ""
echo "Creating ConfigMap..."
kubectl apply -f "$SCRIPT_DIR/configmap.yaml"

echo ""
echo "Creating Secrets (using defaults - CHANGE IN PRODUCTION)..."
kubectl apply -f "$SCRIPT_DIR/secrets.yaml"

# Apply infrastructure services
echo ""
echo "Deploying infrastructure services..."
kubectl apply -f "$SCRIPT_DIR/postgres-statefulset.yaml"
kubectl apply -f "$SCRIPT_DIR/redis-deployment.yaml"
kubectl apply -f "$SCRIPT_DIR/kafka-deployment.yaml"
kubectl apply -f "$SCRIPT_DIR/mlflow-deployment.yaml"

# Apply observability stack
echo ""
echo "Deploying observability stack..."
kubectl apply -f "$SCRIPT_DIR/prometheus-deployment.yaml"
kubectl apply -f "$SCRIPT_DIR/grafana-deployment.yaml"
kubectl apply -f "$SCRIPT_DIR/jaeger-deployment.yaml"
kubectl apply -f "$SCRIPT_DIR/loki-deployment.yaml"

# Apply application services
echo ""
echo "Deploying application services..."
kubectl apply -f "$SCRIPT_DIR/backend-deployment.yaml"
kubectl apply -f "$SCRIPT_DIR/inference-deployment.yaml"
kubectl apply -f "$SCRIPT_DIR/grpc-services.yaml"

# Apply API Gateway
echo ""
echo "Deploying Kong API Gateway..."
kubectl apply -f "$SCRIPT_DIR/kong-deployment.yaml"

# Apply Ingress
echo ""
echo "Configuring Ingress..."
kubectl apply -f "$SCRIPT_DIR/ingress.yaml"

# Wait for deployments
echo ""
echo "Waiting for deployments to be ready..."
kubectl wait --for=condition=available deployment --all -n $NAMESPACE --timeout=300s || true

# Show status
echo ""
echo "========================================"
echo "Deployment Complete!"
echo "========================================"
echo ""
echo "Service Endpoints:"
kubectl get svc -n $NAMESPACE
echo ""
echo "Pod Status:"
kubectl get pods -n $NAMESPACE
echo ""
echo "To access services:"
echo "  kubectl port-forward -n $NAMESPACE svc/kong 8000:80"
echo "  kubectl port-forward -n $NAMESPACE svc/grafana 3000:3000"
echo "  kubectl port-forward -n $NAMESPACE svc/prometheus 9090:9090"
echo "  kubectl port-forward -n $NAMESPACE svc/jaeger 16686:16686"
echo ""
