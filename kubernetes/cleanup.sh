#!/bin/bash
# kubernetes/cleanup.sh
# Remove Medical Triage from Kubernetes

set -e

NAMESPACE="medical-triage"

echo "========================================"
echo "Medical Triage Kubernetes Cleanup"
echo "========================================"

# Confirm deletion
echo ""
echo "This will delete the entire '$NAMESPACE' namespace and all resources."
read -p "Are you sure? (y/N): " confirm

if [[ ! $confirm =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

# Delete namespace
echo ""
echo "Deleting namespace: $NAMESPACE"
kubectl delete namespace $NAMESPACE --ignore-not-found

echo ""
echo "Cleanup complete!"
