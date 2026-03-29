# Service Decomposition Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Split Django monolith into 5 independent services with gRPC communication.

**Architecture:** Extract functionality from monolith into separate deployable services. Each service owns its database tables, has independent scaling, and communicates via gRPC for sync calls and Kafka for async events.

**Tech Stack:** gRPC (inter-service communication), Protocol Buffers, Django (per service), Docker, service discovery via DNS

---

## Files Overview

| File | Action | Responsibility |
|------|--------|----------------|
| `services/auth-service/` | Create directory | Auth service code |
| `services/patient-service/` | Create directory | Patient service code |
| `services/triage-service/` | Create directory | Triage session service |
| `services/inference-service/` | Create directory | ML inference service |
| `services/agent-service/` | Create directory | LangChain agent service |
| `protos/*.proto` | Create | Protocol Buffer definitions |
| `docker/docker-compose.yml` | Modify | Add all services |
| `backend/` | Modify | Become shared library |

---

### Task 1: Protocol Buffer Definitions

**Files:**
- Create: `protos/auth.proto`
- Create: `protos/patient.proto`
- Create: `protos/triage.proto`
- Create: `protos/inference.proto`
- Create: `protos/agent.proto`

- [ ] **Step 1: Create auth service proto**

```protobuf
// protos/auth.proto
syntax = "proto3";

package auth;

service AuthService {
  rpc Register (RegisterRequest) returns (AuthResponse);
  rpc Login (LoginRequest) returns (AuthResponse);
  rpc Verify (VerifyRequest) returns (VerifyResponse);
  rpc Refresh (RefreshRequest) returns (AuthResponse);
}

message RegisterRequest {
  string email = 1;
  string password = 2;
}

message LoginRequest {
  string email = 1;
  string password = 2;
}

message VerifyRequest {
  string token = 1;
}

message RefreshRequest {
  string refresh_token = 1;
}

message AuthResponse {
  bool success = 1;
  string access_token = 2;
  string refresh_token = 3;
  string error = 4;
  int32 user_id = 5;
  string email = 6;
}

message VerifyResponse {
  bool valid = 1;
  int32 user_id = 2;
  string email = 3;
  string error = 4;
}
```

- [ ] **Step 2: Create patient service proto**

```protobuf
// protos/patient.proto
syntax = "proto3";

package patient;

service PatientService {
  rpc GetPatient (GetPatientRequest) returns (PatientResponse);
  rpc CreatePatient (CreatePatientRequest) returns (PatientResponse);
  rpc UpdatePatient (UpdatePatientRequest) returns (PatientResponse);
  rpc GetPatientHistory (GetHistoryRequest) returns (HistoryResponse);
}

message GetPatientRequest {
  int32 user_id = 1;
}

message CreatePatientRequest {
  int32 user_id = 2;
  string date_of_birth = 3;
  string gender = 4;
  string blood_type = 5;
}

message UpdatePatientRequest {
  int32 patient_id = 1;
  string date_of_birth = 2;
  string gender = 3;
  string blood_type = 4;
}

message PatientResponse {
  bool success = 1;
  int32 patient_id = 2;
  int32 user_id = 3;
  string email = 4;
  string date_of_birth = 5;
  string gender = 6;
  string blood_type = 7;
  string created_at = 8;
  string error = 9;
}

message GetHistoryRequest {
  int32 patient_id = 1;
  int32 limit = 2;
}

message HistoryEntry {
  int32 session_id = 1;
  string started_at = 2;
  string status = 3;
  string triage_level = 4;
  repeated string symptoms = 5;
  string disease = 6;
  float confidence = 7;
}

message HistoryResponse {
  bool success = 1;
  repeated HistoryEntry entries = 2;
  string error = 3;
}
```

- [ ] **Step 3: Create triage service proto**

```protobuf
// protos/triage.proto
syntax = "proto3";

package triage;

service TriageService {
  rpc CreateSession (CreateSessionRequest) returns (SessionResponse);
  rpc GetSession (GetSessionRequest) returns (SessionResponse);
  rpc UpdateSession (UpdateSessionRequest) returns (SessionResponse);
  rpc EndSession (EndSessionRequest) returns (SessionResponse);
  rpc SaveMessage (SaveMessageRequest) returns (MessageResponse);
  rpc GetMessages (GetMessagesRequest) returns (MessagesResponse);
}

message CreateSessionRequest {
  int32 patient_id = 1;
  repeated string symptoms = 2;
  string notes = 3;
}

message GetSessionRequest {
  int32 session_id = 1;
}

message UpdateSessionRequest {
  int32 session_id = 1;
  string status = 2;
  string triage_level = 3;
}

message EndSessionRequest {
  int32 session_id = 1;
}

message SessionResponse {
  bool success = 1;
  int32 session_id = 2;
  int32 patient_id = 3;
  string started_at = 4;
  string ended_at = 5;
  string status = 6;
  string triage_level = 7;
  repeated string symptoms = 8;
  string error = 9;
}

message SaveMessageRequest {
  int32 session_id = 1;
  string role = 2;
  string content = 3;
}

message MessageResponse {
  bool success = 1;
  int32 message_id = 2;
  string error = 3;
}

message GetMessagesRequest {
  int32 session_id = 1;
  int32 limit = 2;
}

message Message {
  string role = 1;
  string content = 2;
  string timestamp = 3;
}

message MessagesResponse {
  bool success = 1;
  repeated Message messages = 2;
  string error = 3;
}
```

- [ ] **Step 4: Create inference service proto**

```protobuf
// protos/inference.proto
syntax = "proto3";

package inference;

service InferenceService {
  rpc Predict (PredictRequest) returns (PredictResponse);
  rpc BatchPredict (BatchPredictRequest) returns (BatchPredictResponse);
  rpc GetModelStatus (ModelStatusRequest) returns (ModelStatusResponse);
}

message PredictRequest {
  repeated string symptoms = 1;
  string model_version = 2;
}

message PredictResponse {
  bool success = 1;
  string disease = 2;
  float confidence = 3;
  repeated string matched_symptoms = 4;
  repeated string precautions = 5;
  string model_version = 6;
  float latency_ms = 7;
  bool cache_hit = 8;
  string error = 9;
}

message BatchPredictRequest {
  repeated PredictRequest requests = 1;
}

message BatchPredictResponse {
  bool success = 1;
  repeated PredictResponse predictions = 2;
  string error = 3;
}

message ModelStatusRequest {}

message ModelStatusResponse {
  bool loaded = 1;
  string model_version = 2;
  int32 total_diseases = 3;
  int32 total_symptoms = 4;
  string last_trained = 5;
  string error = 6;
}
```

- [ ] **Step 5: Create agent service proto**

```protobuf
// protos/agent.proto
syntax = "proto3";

package agent;

service AgentService {
  rpc Chat (ChatRequest) returns (ChatResponse);
  rpc ChatStream (ChatRequest) returns (stream ChatResponse);
}

message ChatRequest {
  string message = 1;
  int32 session_id = 2;
  int32 patient_id = 3;
  repeated ChatMessage history = 4;
}

message ChatMessage {
  string role = 1;
  string content = 2;
}

message ChatResponse {
  string content = 1;
  bool is_complete = 2;
  string tool_name = 3;
  string tool_input = 4;
  string error = 5;
}
```

- [ ] **Step 6: Commit**

```bash
git add protos/
git commit -m "proto: define gRPC service contracts"
```

---

### Task 2: Generate Python gRPC Code

**Files:**
- Create: `requirements-dev.txt`
- Create: `scripts/generate_protos.sh`

- [ ] **Step 1: Add gRPC dependencies**

Create `backend/requirements-grpc.txt`:

```txt
# gRPC dependencies
grpcio>=1.60.0
grpcio-tools>=1.60.0
protobuf>=4.25.0
```

- [ ] **Step 2: Create proto generation script**

```bash
#!/bin/bash
# scripts/generate_protos.sh

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
find $PYTHON_OUT_DIR -name "*_pb2*.py" | head -20
```

- [ ] **Step 3: Make script executable and run**

```bash
chmod +x scripts/generate_protos.sh
./scripts/generate_protos.sh
```

Expected output: Generated `*_pb2.py` and `*_pb2_grpc.py` files

- [ ] **Step 4: Commit**

```bash
git add scripts/ backend/requirements-grpc.txt
git commit -m "build: add gRPC code generation script"
```

---

### Task 3: Auth Service Implementation

**Files:**
- Create: `services/auth-service/main.py`
- Create: `services/auth-service/service.py`
- Create: `services/auth-service/Dockerfile`
- Create: `services/auth-service/requirements.txt`

- [ ] **Step 1: Create auth service requirements**

```txt
# services/auth-service/requirements.txt
Django>=5.0
djangorestframework>=3.15
djangorestframework-simplejwt>=5.3
grpcio>=1.60.0
psycopg2-binary>=2.9
python-decouple>=3.8
```

- [ ] **Step 2: Create auth service gRPC server**

```python
# services/auth-service/service.py
import grpc
from concurrent import futures
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auth_service.settings')
django.setup()

from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
import auth_pb2
import auth_pb2_grpc


class AuthServiceServicer(auth_pb2_grpc.AuthServiceServicer):
    """gRPC Auth Service implementation."""

    def Register(self, request, context):
        try:
            # Check if user exists
            if User.objects.filter(email=request.email).exists():
                context.set_details('User already exists')
                context.set_code(grpc.StatusCode.ALREADY_EXISTS)
                return auth_pb2.AuthResponse(
                    success=False,
                    error='User with this email already exists'
                )

            # Create user
            user = User.objects.create_user(
                email=request.email,
                password=request.password,
                username=request.email  # Django requires username
            )

            # Generate tokens
            refresh = RefreshToken.for_user(user)

            return auth_pb2.AuthResponse(
                success=True,
                access_token=str(refresh.access_token),
                refresh_token=str(refresh),
                user_id=user.id,
                email=user.email
            )

        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            return auth_pb2.AuthResponse(
                success=False,
                error=str(e)
            )

    def Login(self, request, context):
        try:
            user = authenticate(
                username=request.email,
                password=request.password
            )

            if not user:
                context.set_details('Invalid credentials')
                context.set_code(grpc.StatusCode.UNAUTHENTICATED)
                return auth_pb2.AuthResponse(
                    success=False,
                    error='Invalid email or password'
                )

            refresh = RefreshToken.for_user(user)

            return auth_pb2.AuthResponse(
                success=True,
                access_token=str(refresh.access_token),
                refresh_token=str(refresh),
                user_id=user.id,
                email=user.email
            )

        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            return auth_pb2.AuthResponse(
                success=False,
                error=str(e)
            )

    def Verify(self, request, context):
        try:
            from rest_framework_simplejwt.tokens import AccessToken

            try:
                token = AccessToken(request.token)
                return auth_pb2.VerifyResponse(
                    valid=True,
                    user_id=token.get('user_id'),
                    email=User.objects.get(id=token.get('user_id')).email
                )
            except Exception:
                return auth_pb2.VerifyResponse(
                    valid=False,
                    error='Invalid or expired token'
                )

        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            return auth_pb2.VerifyResponse(
                valid=False,
                error=str(e)
            )

    def Refresh(self, request, context):
        try:
            refresh = RefreshToken(request.refresh_token)
            access_token = refresh.access_token

            return auth_pb2.AuthResponse(
                success=True,
                access_token=str(access_token),
                refresh_token=str(refresh)
            )

        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.UNAUTHENTICATED)
            return auth_pb2.AuthResponse(
                success=False,
                error=str(e)
            )


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    auth_pb2_grpc.add_AuthServiceServicer_to_server(
        AuthServiceServicer(), server
    )
    server.add_insecure_port('[::]:50051')
    server.start()
    print('Auth Service started on port 50051')
    server.wait_for_termination()


if __name__ == '__main__':
    serve()
```

- [ ] **Step 3: Create auth service main entrypoint**

```python
# services/auth-service/main.py
#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auth_service.settings')
django.setup()

from service import serve

if __name__ == '__main__':
    serve()
```

- [ ] **Step 4: Create auth service Dockerfile**

```dockerfile
# services/auth-service/Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy code
COPY . .

# Expose gRPC port
EXPOSE 50051

# Health check
HEALTHCHECK --interval=30s --timeout=3s CMD grpc_health_probe -addr=:50051 || exit 1

# Run service
CMD ["python", "main.py"]
```

- [ ] **Step 5: Commit**

```bash
git add services/auth-service/
git commit -m "feat(auth): implement auth service with gRPC"
```

---

### Task 4: Patient Service Implementation

**Files:**
- Create: `services/patient-service/service.py`
- Create: `services/patient-service/Dockerfile`
- Create: `services/patient-service/requirements.txt`

- [ ] **Step 1: Create patient service requirements**

```txt
# services/patient-service/requirements.txt
Django>=5.0
djangorestframework>=3.15
grpcio>=1.60.0
psycopg2-binary>=2.9
python-decouple>=3.8
```

- [ ] **Step 2: Create patient service gRPC server**

```python
# services/patient-service/service.py
import grpc
from concurrent import futures
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'patient_service.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import Patient, TriageSession, Prediction
import patient_pb2
import patient_pb2_grpc
from datetime import datetime


class PatientServiceServicer(patient_pb2_grpc.PatientServiceServicer):
    """gRPC Patient Service implementation."""

    def GetPatient(self, request, context):
        try:
            patient = Patient.objects.get(user_id=request.user_id)
            return patient_pb2.PatientResponse(
                success=True,
                patient_id=patient.id,
                user_id=patient.user.id,
                email=patient.user.email,
                date_of_birth=str(patient.date_of_birth) if patient.date_of_birth else '',
                gender=patient.gender,
                blood_type=patient.blood_type or '',
                created_at=patient.created_at.isoformat()
            )

        except Patient.DoesNotExist:
            return patient_pb2.PatientResponse(
                success=False,
                error='Patient profile not found'
            )
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            return patient_pb2.PatientResponse(
                success=False,
                error=str(e)
            )

    def CreatePatient(self, request, context):
        try:
            user = User.objects.get(id=request.user_id)
            patient = Patient.objects.create(
                user=user,
                date_of_birth=request.date_of_birth if request.date_of_birth else None,
                gender=request.gender or 'prefer_not_to_say',
                blood_type=request.blood_type or None
            )

            return patient_pb2.PatientResponse(
                success=True,
                patient_id=patient.id,
                user_id=patient.user.id,
                email=patient.user.email,
                gender=patient.gender,
                blood_type=patient.blood_type or '',
                created_at=patient.created_at.isoformat()
            )

        except User.DoesNotExist:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            return patient_pb2.PatientResponse(
                success=False,
                error='User not found'
            )
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            return patient_pb2.PatientResponse(
                success=False,
                error=str(e)
            )

    def UpdatePatient(self, request, context):
        try:
            patient = Patient.objects.get(id=request.patient_id)

            if request.date_of_birth:
                patient.date_of_birth = request.date_of_birth
            if request.gender:
                patient.gender = request.gender
            if request.blood_type:
                patient.blood_type = request.blood_type

            patient.save()

            return patient_pb2.PatientResponse(
                success=True,
                patient_id=patient.id,
                user_id=patient.user.id,
                email=patient.user.email,
                gender=patient.gender,
                blood_type=patient.blood_type or '',
                updated_at=datetime.now().isoformat()
            )

        except Patient.DoesNotExist:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            return patient_pb2.PatientResponse(
                success=False,
                error='Patient not found'
            )
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            return patient_pb2.PatientResponse(
                success=False,
                error=str(e)
            )

    def GetPatientHistory(self, request, context):
        try:
            sessions = TriageSession.objects.filter(
                patient_id=request.patient_id
            ).order_by('-started_at')[:request.limit]

            entries = []
            for session in sessions:
                predictions = Prediction.objects.filter(session=session).first()
                entries.append(patient_pb2.HistoryEntry(
                    session_id=session.id,
                    started_at=session.started_at.isoformat(),
                    status=session.status,
                    triage_level=session.triage_level or '',
                    symptoms=session.primary_symptoms or [],
                    disease=predictions.disease if predictions else '',
                    confidence=predictions.confidence if predictions else 0.0
                ))

            return patient_pb2.HistoryResponse(
                success=True,
                entries=entries
            )

        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            return patient_pb2.HistoryResponse(
                success=False,
                error=str(e)
            )


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    patient_pb2_grpc.add_PatientServiceServicer_to_server(
        PatientServiceServicer(), server
    )
    server.add_insecure_port('[::]:50052')
    server.start()
    print('Patient Service started on port 50052')
    server.wait_for_termination()


if __name__ == '__main__':
    serve()
```

- [ ] **Step 3: Create patient service Dockerfile**

```dockerfile
# services/patient-service/Dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 50052

HEALTHCHECK --interval=30s --timeout=3s CMD grpc_health_probe -addr=:50052 || exit 1

CMD ["python", "service.py"]
```

- [ ] **Step 4: Commit**

```bash
git add services/patient-service/
git commit -m "feat(patient): implement patient service with gRPC"
```

---

### Task 5: Inference Service Implementation

**Files:**
- Create: `services/inference-service/service.py`
- Create: `services/inference-service/Dockerfile`
- Create: `services/inference-service/requirements.txt`

- [ ] **Step 1: Create inference service requirements**

```txt
# services/inference-service/requirements.txt
grpcio>=1.60.0
scikit-learn>=1.5
xgboost>=2.1
pandas>=2.2
numpy>=1.26
joblib>=1.4
redis>=5.0
```

- [ ] **Step 2: Create inference service with caching**

```python
# services/inference-service/service.py
import grpc
from concurrent import futures
import hashlib
import json
import time
import os

import inference_pb2
import inference_pb2_grpc


class InferenceServiceServicer(inference_pb2_grpc.InferenceServiceServicer):
    """gRPC Inference Service with caching."""

    def __init__(self):
        self.model = None
        self.encoder = None
        self.loaded_version = None
        self.cache = {}  # In-memory cache (use Redis in production)
        self.load_model()

    def load_model(self):
        """Load ML model from disk."""
        import joblib
        model_path = os.environ.get('MODEL_PATH', 'ml_pipeline/models/classifier.joblib')
        encoder_path = os.environ.get('ENCODER_PATH', 'ml_pipeline/models/encoder.joblib')

        try:
            self.model = joblib.load(model_path)
            self.encoder = joblib.load(encoder_path)
            self.loaded_version = 'v1.0'
            print(f'Model loaded: {model_path}')
        except Exception as e:
            print(f'Error loading model: {e}')
            self.model = None

    def _get_cache_key(self, symptoms):
        """Generate cache key from sorted symptoms."""
        sorted_symptoms = sorted(symptoms)
        key_str = '|'.join(sorted_symptoms)
        return hashlib.md5(key_str.encode()).hexdigest()

    def Predict(self, request, context):
        start_time = time.time()

        try:
            # Check cache first
            cache_key = self._get_cache_key(request.symptoms)
            if cache_key in self.cache:
                cached = self.cache[cache_key]
                return inference_pb2.PredictResponse(
                    success=True,
                    disease=cached['disease'],
                    confidence=cached['confidence'],
                    matched_symptoms=cached['matched_symptoms'],
                    precautions=cached['precautions'],
                    model_version=cached['model_version'],
                    latency_ms=(time.time() - start_time) * 1000,
                    cache_hit=True
                )

            # Run inference
            if self.model is None:
                context.set_code(grpc.StatusCode.UNAVAILABLE)
                return inference_pb2.PredictResponse(
                    success=False,
                    error='Model not loaded'
                )

            # Encode symptoms
            symptom_vector = self.encoder.transform([request.symptoms])

            # Predict
            prediction = self.model.predict(symptom_vector)[0]
            probabilities = self.model.predict_proba(symptom_vector)[0]
            confidence = float(max(probabilities))

            # Cache result (24 hour TTL in production)
            result = {
                'disease': prediction,
                'confidence': confidence,
                'matched_symptoms': list(request.symptoms),
                'precautions': self._get_precautions(prediction),
                'model_version': self.loaded_version
            }
            self.cache[cache_key] = result

            return inference_pb2.PredictResponse(
                success=True,
                disease=prediction,
                confidence=confidence,
                matched_symptoms=list(request.symptoms),
                precautions=result['precautions'],
                model_version=self.loaded_version,
                latency_ms=(time.time() - start_time) * 1000,
                cache_hit=False
            )

        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            return inference_pb2.PredictResponse(
                success=False,
                error=str(e)
            )

    def BatchPredict(self, request, context):
        try:
            predictions = []
            for req in request.requests:
                pred = self.Predict(req, context)
                predictions.append(pred)

            return inference_pb2.BatchPredictResponse(
                success=True,
                predictions=predictions
            )

        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            return inference_pb2.BatchPredictResponse(
                success=False,
                error=str(e)
            )

    def GetModelStatus(self, request, context):
        try:
            return inference_pb2.ModelStatusResponse(
                loaded=self.model is not None,
                model_version=self.loaded_version or '',
                total_diseases=len(self.model.classes_) if self.model else 0,
                total_symptoms=len(self.encoder.categories_[0]) if self.encoder else 0,
                last_trained='2026-03-28'  # Would come from model metadata
            )

        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            return inference_pb2.ModelStatusResponse(
                loaded=False,
                error=str(e)
            )

    def _get_precautions(self, disease):
        """Get precautions for a disease (simplified)."""
        precautions_map = {
            'Flu': ['Rest', 'Hydrate', 'Isolate'],
            'Migraine': ['Rest in dark room', 'Hydrate', 'Avoid triggers'],
            'Common Cold': ['Rest', 'Hydrate', 'Over-the-counter medication'],
        }
        return precautions_map.get(disease, ['Consult a healthcare provider'])


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    inference_pb2_grpc.add_InferenceServiceServicer_to_server(
        InferenceServiceServicer(), server
    )
    server.add_insecure_port('[::]:50053')
    server.start()
    print('Inference Service started on port 50053')
    server.wait_for_termination()


if __name__ == '__main__':
    serve()
```

- [ ] **Step 3: Create inference service Dockerfile**

```dockerfile
# services/inference-service/Dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY ../backend/ml_pipeline ./ml_pipeline

EXPOSE 50053

HEALTHCHECK --interval=30s --timeout=3s CMD grpc_health_probe -addr=:50053 || exit 1

CMD ["python", "service.py"]
```

- [ ] **Step 4: Commit**

```bash
git add services/inference-service/
git commit -m "feat(inference): implement ML inference service with caching"
```

---

### Task 6: Update Docker Compose

**Files:**
- Modify: `docker/docker-compose.yml`

- [ ] **Step 1: Add all services to docker-compose**

Read current file, then add:

```yaml
services:
  # ... existing postgres, redis, backend, etc ...

  # Auth Service
  auth-service:
    build:
      context: ../services/auth-service
      dockerfile: Dockerfile
    container_name: medical_triage_auth
    ports:
      - "50051:50051"
    environment:
      - DB_NAME=medical_triage
      - DB_USER=postgres
      - DB_PASSWORD=postgres
      - DB_HOST=postgres
    depends_on:
      - postgres
    networks:
      - medical_triage_network

  # Patient Service
  patient-service:
    build:
      context: ../services/patient-service
      dockerfile: Dockerfile
    container_name: medical_triage_patient
    ports:
      - "50052:50052"
    environment:
      - DB_NAME=medical_triage
      - DB_USER=postgres
      - DB_PASSWORD=postgres
      - DB_HOST=postgres
    depends_on:
      - postgres
    networks:
      - medical_triage_network

  # Inference Service
  inference-service:
    build:
      context: ../services/inference-service
      dockerfile: Dockerfile
    container_name: medical_triage_inference
    ports:
      - "50053:50053"
    volumes:
      - ../backend/ml_pipeline:/app/ml_pipeline
    depends_on:
      - postgres
    networks:
      - medical_triage_network
```

- [ ] **Step 2: Commit**

```bash
git add docker/docker-compose.yml
git commit -m "infra: add microservices to docker-compose"
```

---

### Task 7: Testing gRPC Communication

**Files:**
- Create: `scripts/test_grpc.py`

- [ ] **Step 1: Create gRPC test script**

```python
#!/usr/bin/env python
# scripts/test_grpc.py
"""Test gRPC services locally."""

import grpc
import sys
sys.path.insert(0, 'services')

import auth_pb2
import auth_pb2_grpc
import patient_pb2
import patient_pb2_grpc
import inference_pb2
import inference_pb2_grpc


def test_auth_service():
    """Test Auth Service."""
    print('\n=== Testing Auth Service ===')

    channel = grpc.insecure_channel('localhost:50051')
    stub = auth_pb2_grpc.AuthServiceStub(channel)

    # Test Register
    try:
        response = stub.Register(auth_pb2.RegisterRequest(
            email='grpc-test@example.com',
            password='testpass123'
        ))
        print(f'Register: success={response.success}, user_id={response.user_id}')
    except grpc.RpcError as e:
        print(f'Register error: {e.details()}')

    # Test Login
    try:
        response = stub.Login(auth_pb2.LoginRequest(
            email='grpc-test@example.com',
            password='testpass123'
        ))
        print(f'Login: success={response.success}')
        return response.access_token
    except grpc.RpcError as e:
        print(f'Login error: {e.details()}')
        return None


def test_inference_service():
    """Test Inference Service."""
    print('\n=== Testing Inference Service ===')

    channel = grpc.insecure_channel('localhost:50053')
    stub = inference_pb2_grpc.InferenceServiceStub(channel)

    # Test Predict
    try:
        response = stub.Predict(inference_pb2.PredictRequest(
            symptoms=['fever', 'headache', 'fatigue']
        ))
        print(f'Predict: disease={response.disease}, confidence={response.confidence:.2%}')
        print(f'  Cache hit: {response.cache_hit}, Latency: {response.latency_ms:.2f}ms')
    except grpc.RpcError as e:
        print(f'Predict error: {e.details()}')

    # Test Model Status
    try:
        response = stub.GetModelStatus(inference_pb2.ModelStatusRequest())
        print(f'Model Status: loaded={response.loaded}, version={response.model_version}')
    except grpc.RpcError as e:
        print(f'Model status error: {e.details()}')


if __name__ == '__main__':
    print('gRPC Service Tests')
    print('=' * 50)

    # Test services
    test_auth_service()
    test_inference_service()

    print('\n' + '=' * 50)
    print('Tests complete!')
```

- [ ] **Step 2: Run tests**

```bash
# Start services first
cd docker
docker-compose up -d auth-service patient-service inference-service

# Run test script
cd ..
python scripts/test_grpc.py
```

Expected: Successful gRPC calls with responses

- [ ] **Step 3: Commit**

```bash
git add scripts/test_grpc.py
git commit -m "test: add gRPC service test script"
```

---

## Success Criteria

- [ ] All 5 services defined with gRPC contracts
- [ ] Protocol Buffer code generated successfully
- [ ] Auth service handles register/login via gRPC
- [ ] Patient service CRUD operations work
- [ ] Inference service returns predictions with caching
- [ ] Docker Compose starts all services
- [ ] gRPC test script passes
- [ ] Services have independent health checks

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `protoc` not found | Run `pip install grpcio-tools` |
| Service won't start | Check Django settings module |
| gRPC connection refused | Verify service is running: `docker ps` |
| Model not found | Ensure ml_pipeline volume is mounted |
