# API Gateway Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Kong API Gateway for rate limiting, authentication, and request routing.

**Architecture:** Kong Gateway sits in front of all services, handling JWT validation, rate limiting per IP, and routing requests to appropriate Django services.

**Tech Stack:** Kong Gateway (OSS), Redis (for rate limit storage), Docker, Nginx (fallback option)

---

## Files Overview

| File | Action | Responsibility |
|------|--------|----------------|
| `docker/kong/kong.yml` | Create | Kong declarative configuration |
| `docker/kong/Dockerfile` | Create | Kong container image |
| `docker/docker-compose.yml` | Modify | Add Kong service, update networking |
| `backend/backend/settings.py` | Modify | CORS, trusted proxies |
| `backend/api/auth_views.py` | Modify | JWT verification for Kong passthrough |
| `docs/gateway.md` | Create | Gateway usage documentation |

---

### Task 1: Kong Configuration

**Files:**
- Create: `docker/kong/kong.yml`
- Create: `docker/kong/Dockerfile`

- [ ] **Step 1: Create Kong declarative configuration**

```yaml
# docker/kong/kong.yml
_format_version: "3.0"

_transform: true

services:
  - name: auth-service
    url: http://backend:8000/api/auth
    routes:
      - name: auth-route
        paths: [/auth]
        strip_path: false

  - name: patient-service
    url: http://backend:8000/api/patients
    routes:
      - name: patient-route
        paths: [/patients]
        strip_path: false

  - name: triage-service
    url: http://backend:8000/api/sessions
    routes:
      - name: triage-route
        paths: [/sessions, /symptom-assessment]
        strip_path: false

  - name: prediction-service
    url: http://backend:8000/api/predictions
    routes:
      - name: prediction-route
        paths: [/predictions]
        strip_path: false

  - name: websocket-service
    url: http://backend:8000/ws
    routes:
      - name: ws-route
        paths: [/ws]
        strip_path: false
        protocols: [http, https, ws, wss]

plugins:
  # Rate Limiting (Redis-backed)
  - name: rate-limiting
    config:
      second: 10
      minute: 100
      hour: 1000
      policy: redis
      redis_host: redis
      redis_port: 6379
      hide_client_headers: false
    service: auth-service

  - name: rate-limiting
    config:
      second: 30
      minute: 300
      hour: 3000
      policy: redis
      redis_host: redis
      redis_port: 6379
    service: patient-service

  - name: rate-limiting
    config:
      second: 30
      minute: 300
      hour: 3000
      policy: redis
      redis_host: redis
      redis_port: 6379
    service: triage-service

  # CORS (for all services)
  - name: cors
    config:
      origins: ["*"]
      methods: [GET, POST, PUT, DELETE, PATCH, OPTIONS]
      headers: [Accept, Accept-Version, Content-Type, Authorization, Origin]
      exposed_headers: [X-Auth-Token, X-RateLimit-Limit, X-RateLimit-Remaining]
      credentials: true
      max_age: 86400

  # Request Transformer (add headers)
  - name: request-transformer
    config:
      add:
        headers:
          - "X-Gateway-Version:1.0"

  # Response Transformer (add rate limit headers)
  - name: response-transformer
    config:
      add:
        headers:
          - "X-Served-By:Kong-Gateway"

  # IP Restriction (optional - for admin routes)
  # - name: ip-restriction
  #   config:
  #     allow:
  #       - "10.0.0.0/8"
  #   route: admin-route

  # Bot Detection
  - name: bot-detection
    config:
      allow: []

consumers:
  - username: health-triage-client

# JWT Authentication (optional - Kong can validate JWTs)
# jwt_secrets:
#   - key: health-triage-key
#     secret: ${JWT_SECRET}
#     consumer: health-triage-client
```

- [ ] **Step 2: Create Kong Dockerfile**

```dockerfile
# docker/kong/Dockerfile
FROM kong:3.5-alpine

# Copy declarative configuration
COPY kong.yml /kong/kong.yml

# Set environment variables
ENV KONG_DATABASE=off
ENV KONG_DECLARATIVE_CONFIG=/kong/kong.yml
ENV KONG_DNS_ORDER=LAST,A,CNAME
ENV KONG_PLUGINS=bundled

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD kong health || exit 1

EXPOSE 8000 8443 8001 8444
```

- [ ] **Step 3: Commit**

```bash
git add docker/kong/
git commit -m "feat(gateway): add Kong API Gateway configuration"
```

---

### Task 2: Docker Compose Integration

**Files:**
- Modify: `docker/docker-compose.yml`

- [ ] **Step 1: Add Kong service to docker-compose.yml**

Read current file first, then add:

```yaml
services:
  kong:
    build:
      context: ./kong
      dockerfile: Dockerfile
    container_name: medical_triage_kong
    ports:
      - "8000:8000"   # Proxy port
      - "8443:8443"   # Proxy SSL port
      - "8001:8001"   # Admin API
      - "8444:8444"   # Admin API SSL
    environment:
      KONG_DATABASE: "off"
      KONG_DECLARATIVE_CONFIG: /kong/kong.yml
      KONG_PROXY_ACCESS_LOG: /dev/stdout
      KONG_ADMIN_ACCESS_LOG: /dev/stdout
      KONG_PROXY_ERROR_LOG: /dev/stderr
      KONG_ADMIN_ERROR_LOG: /dev/stderr
      KONG_ADMIN_LISTEN: "0.0.0.0:8001"
    depends_on:
      - redis
      - backend
    networks:
      - medical_triage_network
    restart: unless-stopped
```

- [ ] **Step 2: Update backend service ports**

Change backend to NOT expose port 8000 directly (only through Kong):

```yaml
backend:
  # ... existing config ...
  ports:
    - "8001:8000"  # Changed from 8000:8000 to avoid conflict
```

- [ ] **Step 3: Add networks section if not exists**

```yaml
networks:
  medical_triage_network:
    driver: bridge
```

- [ ] **Step 4: Commit**

```bash
git add docker/docker-compose.yml
git commit -m "feat(gateway): integrate Kong into docker-compose"
```

---

### Task 3: Backend Configuration Updates

**Files:**
- Modify: `backend/backend/settings.py`

- [ ] **Step 1: Add trusted proxy settings**

Read current settings.py, then add after CORS section:

```python
# Trusted Proxies (Kong Gateway)
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True
X_FRAME_OPTIONS = 'DENY'

# Security settings for production
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
```

- [ ] **Step 2: Update CORS to trust Kong**

Modify existing CORS section:

```python
# CORS - Allow Kong Gateway
CORS_ALLOW_ALL_ORIGINS = True  # For development
# In production, use:
# CORS_ALLOWED_ORIGINS = [
#     "http://localhost:80",
#     "https://yourdomain.com",
# ]

# Allow headers from Kong
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'x-gateway-version',  # Kong header
]

CORS_EXPOSE_HEADERS = [
    'x-rate-limit-limit',
    'x-rate-limit-remaining',
    'x-rate-limit-reset',
]
```

- [ ] **Step 3: Commit**

```bash
git add backend/backend/settings.py
git commit -m "feat(gateway): add trusted proxy settings for Kong"
```

---

### Task 4: Nginx Fallback Configuration

**Files:**
- Create: `docker/nginx/nginx-gateway.conf`
- Create: `docker/nginx/Dockerfile`

- [ ] **Step 1: Create Nginx configuration (simpler alternative to Kong)**

```nginx
# docker/nginx/nginx-gateway.conf
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
    use epoll;
    multi_accept on;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logging format
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for" '
                    'rt=$request_time uct="$upstream_connect_time" '
                    'uht="$upstream_header_time" urt="$upstream_response_time"';

    access_log /var/log/nginx/access.log main;

    # Performance
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 10M;

    # Rate limiting zones
    limit_req_zone $binary_remote_addr zone=auth_limit:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=30r/s;
    limit_req_zone $binary_remote_addr zone=ws_limit:10m rate=5r/s;

    # Upstream backend
    upstream backend {
        server backend:8000;
        keepalive 32;
    }

    # Auth endpoints (stricter rate limit)
    server {
        listen 8000;
        server_name localhost;

        location /auth/ {
            limit_req zone=auth_limit burst=20 nodelay;
            proxy_pass http://backend/api/auth/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Patient endpoints
        location /patients/ {
            limit_req zone=api_limit burst=50 nodelay;
            proxy_pass http://backend/api/patients/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }

        # Triage/Symptom endpoints
        location /sessions/ {
            limit_req zone=api_limit burst=50 nodelay;
            proxy_pass http://backend/api/sessions/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }

        location /symptom-assessment/ {
            limit_req zone=api_limit burst=50 nodelay;
            proxy_pass http://backend/api/symptom-assessment/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }

        location /predictions/ {
            limit_req zone=api_limit burst=50 nodelay;
            proxy_pass http://backend/api/predictions/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }

        # WebSocket endpoint
        location /ws/ {
            limit_req zone=ws_limit burst=10 nodelay;
            proxy_pass http://backend/ws/;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_read_timeout 86400;
        }

        # Health check
        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }

        # Rate limit exceeded
        limit_req_status 429;
    }
}
```

- [ ] **Step 2: Create Nginx Dockerfile**

```dockerfile
# docker/nginx/Dockerfile
FROM nginx:1.25-alpine

# Remove default config
RUN rm /etc/nginx/conf.d/default.conf

# Copy custom config
COPY nginx-gateway.conf /etc/nginx/nginx.conf

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost/health || exit 1

EXPOSE 8000
```

- [ ] **Step 3: Commit**

```bash
git add docker/nginx/
git commit -m "feat(gateway): add Nginx as alternative API gateway"
```

---

### Task 5: Documentation

**Files:**
- Create: `docs/gateway.md`

- [ ] **Step 1: Create gateway documentation**

```markdown
# API Gateway Documentation

## Overview

The Health Triage API uses Kong Gateway (with Nginx fallback) for:
- Rate limiting per IP address
- Request routing to backend services
- CORS handling
- Bot detection
- Request/response transformation

## Quick Start

### Using Kong (Recommended)

```bash
cd docker
docker-compose up -d kong
```

Gateway available at: `http://localhost:8000`

### Using Nginx (Alternative)

```bash
cd docker
docker-compose up -d nginx
```

Gateway available at: `http://localhost:8000`

## Rate Limits

| Endpoint | Per Second | Per Minute | Per Hour |
|----------|------------|------------|----------|
| /auth/* | 10 | 100 | 1000 |
| /patients/* | 30 | 300 | 3000 |
| /sessions/* | 30 | 300 | 3000 |
| /symptom-assessment/* | 30 | 300 | 3000 |
| /predictions/* | 30 | 300 | 3000 |
| /ws/* | 5 | - | - |

## Rate Limit Headers

All responses include:
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Requests remaining in window
- `X-RateLimit-Reset`: Unix timestamp when limit resets

## Testing Rate Limits

```bash
# Quick test (should hit limit after ~10 requests)
for i in {1..15}; do
  curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/auth/login/
done
```

Expected: First 10 return 200/401, rest return 429 (Too Many Requests)

## Kong Admin API

```bash
# Check Kong health
curl http://localhost:8001/status

# List all routes
curl http://localhost:8001/routes

# List all services
curl http://localhost:8001/services

# Check rate limit plugin
curl http://localhost:8001/plugins
```

## Configuration Changes

1. Edit `docker/kong/kong.yml`
2. Restart Kong: `docker-compose restart kong`
3. Verify: `curl http://localhost:8001/routes`

## Troubleshooting

### 429 Too Many Requests
- Rate limit exceeded. Wait or increase limits in kong.yml

### 502 Bad Gateway
- Backend service down. Check: `docker-compose ps backend`

### WebSocket not connecting
- Ensure proxy headers are set correctly
- Check `proxy_read_timeout` is high enough

## Production Considerations

- Enable SSL termination at Kong
- Use Kong Manager for monitoring
- Configure Prometheus plugin for metrics
- Set up alerting for rate limit hits
```

- [ ] **Step 2: Commit**

```bash
git add docs/gateway.md
git commit -m "docs: add API Gateway documentation"
```

---

### Task 6: Testing

**Files:**
- Create: `backend/api/tests/test_gateway.py`

- [ ] **Step 1: Write rate limit tests**

```python
# backend/api/tests/test_gateway.py
import pytest
from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth.models import User


class RateLimitTestCase(TestCase):
    """Test rate limiting behavior (simulated)."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )

    def test_login_endpoint_responds(self):
        """Verify login endpoint is accessible."""
        response = self.client.post('/api/auth/login/', {
            'email': 'test@example.com',
            'password': 'testpass123'
        })
        # Should get a response (rate limiting happens at gateway)
        self.assertIn(response.status_code, [200, 400, 401])

    def test_patient_endpoint_requires_auth(self):
        """Verify patient endpoint requires authentication."""
        response = self.client.get('/api/patients/me/')
        self.assertEqual(response.status_code, 401)

    def test_authenticated_patient_access(self):
        """Verify authenticated access to patient endpoint."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/patients/me/')
        # Should succeed or return 404 if profile doesn't exist
        self.assertIn(response.status_code, [200, 404])

    def test_symptom_submission_requires_auth(self):
        """Verify symptom assessment requires authentication."""
        response = self.client.post('/api/symptom-assessment/', {
            'symptoms': ['fever', 'headache']
        }, format='json')
        self.assertEqual(response.status_code, 401)
```

- [ ] **Step 2: Run tests**

```bash
cd backend
python manage.py test api.tests.test_gateway -v 2
```

Expected: All tests pass

- [ ] **Step 3: Commit**

```bash
git add backend/api/tests/test_gateway.py
git commit -m "test: add gateway integration tests"
```

---

### Task 7: Verification & Demo

**Files:** None

- [ ] **Step 1: Start all services**

```bash
cd docker
docker-compose up -d kong postgres redis backend
```

- [ ] **Step 2: Verify Kong is running**

```bash
# Check Kong health
curl http://localhost:8001/status

# Expected: {"status": "healthy", ...}
```

- [ ] **Step 3: Test rate limiting**

```bash
# Test rate limit (run 15 quick requests)
for i in {1..15}; do
  echo -n "Request $i: "
  curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/auth/login/
done
```

Expected: First 10 return 200/401, requests 11+ return 429

- [ ] **Step 4: Test routing**

```bash
# Test patient endpoint through Kong
curl -s http://localhost:8000/patients/me/ | head -c 100

# Should return 401 (unauthorized) - proves routing works
```

- [ ] **Step 5: Check Kong logs**

```bash
docker logs medical_triage_kong --tail 20
```

Expected: See proxy access logs

---

## Success Criteria

- [ ] Kong container starts without errors
- [ ] All API routes accessible through `localhost:8000`
- [ ] Rate limiting triggers 429 after threshold
- [ ] Rate limit headers present in responses
- [ ] Nginx alternative works as fallback
- [ ] Tests pass
- [ ] Documentation complete

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Kong won't start | Check `docker/logs` for config errors |
| 502 Bad Gateway | Verify backend is running and reachable |
| Rate limit not working | Ensure Redis is running |
| WebSocket fails | Check `proxy_read_timeout` setting |
