#!/bin/bash
# scripts/generate_protos.sh
# Generate Python gRPC code from Protocol Buffer definitions

set -e

PROTO_DIR="protos"
PYTHON_OUT_DIR="services"

echo "Generating Python gRPC code..."

# Create output directories
mkdir -p services/auth_service
mkdir -p services/patient_service
mkdir -p services/triage_service
mkdir -p services/inference_service
mkdir -p services/agent_service

# Generate Python code for each proto
for proto_file in $PROTO_DIR/*.proto; do
    echo "Processing $proto_file..."
    python -m grpc_tools.protoc \
        -I$PROTO_DIR \
        --python_out=$PYTHON_OUT_DIR \
        --grpc_python_out=$PYTHON_OUT_DIR \
        $proto_file
done

echo "Done! Generated files:"
find $PYTHON_OUT_DIR -name "*_pb2*.py" 2>/dev/null | head -20 || echo "Note: Run with Python environment that has grpcio-tools installed"
