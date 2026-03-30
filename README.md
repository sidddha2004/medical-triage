# Health Triage Assistant

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Django 5.0+](https://img.shields.io/badge/django-5.0+-green.svg)](https://www.djangoproject.com/)
[![React 18+](https://img.shields.io/badge/react-18+-61dafb.svg)](https://reactjs.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An AI-powered health triage system that combines machine learning with conversational AI to provide accurate symptom assessments and personalized triage recommendations.

![Health Triage Dashboard](images/image.png)

---

## 🌟 Features

### For Users

| Feature | Description |
|---------|-------------|
| **🤖 AI Health Chat** | Conversational symptom assessment via real-time WebSocket chat with an AI assistant powered by Gemini 2.5 Flash |
| **🧠 ML Predictions** | XGBoost classifier trained on medical dataset with 88.5% accuracy across 41 diseases and 131 symptoms |
| **📊 Triage Recommendations** | Personalized care level guidance: Self-Care, GP Visit, Urgent Care, or Emergency |
| **📋 Health History** | Track all your triage sessions with interactive visualizations using Recharts |
| **📄 PDF Reports** | Generate structured triage reports for your medical records |
| **🔐 Secure Authentication** | JWT-based authentication with secure session management |

### For Developers

| Feature | Description |
|---------|-------------|
| **🚀 Real-time WebSocket** | Django Channels for streaming AI responses |
| **📡 RESTful API** | Fully documented REST API with Swagger/OpenAPI specs |
| **🤖 LangChain Agent** | Custom AI agent with specialized tools (symptom classifier, history retriever, triage recommender, report generator, escalation alert) |
| **📈 MLflow Integration** | Model registry, experiment tracking, and A/B testing |
| **🔭 Observability** | Prometheus metrics, Grafana dashboards, Loki logging, Jaeger distributed tracing |
| **🐳 Docker Ready** | Full Docker Compose setup for local development |

---

## 🏗️ Architecture

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
│                      NGINX REVERSE PROXY                            │
│         Static Files │ API Proxy │ WebSocket Upgrade               │
└─────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      DJANGO MONOLITH                                │
│  ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐    │
│  │   REST API       │ │  WebSocket API   │ │  Celery Worker   │    │
│  │   (DRF)          │ │  (Channels)      │ │  (Async Tasks)   │    │
│  └──────────────────┘ └──────────────────┘ └──────────────────┘    │
│  ┌──────────────────┐ ┌──────────────────┐                         │
│  │ ML Pipeline      │ │   LangChain      │                         │
│  │  (XGBoost)       │ │   Agent          │                         │
│  └──────────────────┘ └──────────────────┘                         │
└─────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       DATA LAYER                                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │
│  │ PostgreSQL  │  │    Redis    │  │   MLflow    │                 │
│  │ (Primary DB)│  │ (Cache+MQ)  │  │(Model Reg)  │                 │
│  └─────────────┘  └─────────────┘  └─────────────┘                 │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.12+**
- **Node.js 20+**
- **Docker + Docker Compose**

### Option 1: Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/medical-triage.git
cd medical-triage/docker

# Start all services
docker-compose up -d

# Access the application
# Frontend: http://localhost:80
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/api/docs/
# MLflow UI: http://localhost:5000
# Grafana: http://localhost:3000
# Prometheus: http://localhost:9090
# Jaeger: http://localhost:16686
```

### Option 2: Local Development

```bash
# Backend Setup
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver

# Frontend Setup
cd frontend
npm install
npm run dev

# Infrastructure (PostgreSQL + Redis)
cd docker
docker-compose up -d postgres redis
```

---

## 📁 Project Structure

```
medical-triage/
├── backend/                    # Django backend (monolith)
│   ├── api/                   # REST API endpoints
│   │   ├── views.py          # Patient, Session, Prediction views
│   │   ├── auth_views.py     # JWT auth views
│   │   └── urls.py           # API routing
│   ├── agent/                 # AI agent + WebSocket handlers
│   │   ├── langchain_agent.py # LangChain agent with tools
│   │   ├── consumers.py      # WebSocket consumers
│   │   └── tools.py          # Custom agent tools
│   ├── ml_pipeline/           # ML model training + prediction
│   │   ├── train.py          # XGBoost training script
│   │   ├── api.py            # Model serving API
│   │   └── mlflow_tracking.py # MLflow integration
│   ├── core/                  # Shared utilities
│   │   └── models.py         # Django models
│   ├── data/                  # Training datasets
│   ├── backend/               # Django settings
│   └── manage.py
│
├── frontend/                   # React frontend
│   ├── src/
│   │   ├── pages/            # Page components
│   │   │   ├── Login.tsx     # Login page
│   │   │   ├── Dashboard.tsx # Dashboard with session table
│   │   │   ├── Chat.tsx      # Real-time chat UI
│   │   │   ├── Results.tsx   # Prediction results
│   │   │   └── History.tsx   # Health history with charts
│   │   ├── store/            # Zustand state management
│   │   ├── lib/              # API client, utilities
│   │   └── components/       # Reusable components
│   └── package.json
│
├── docker/                     # Docker configuration
│   ├── docker-compose.yml     # All services orchestration
│   ├── Dockerfile.backend     # Backend container
│   ├── Dockerfile.frontend    # Frontend container
│   ├── mlflow/                # MLflow tracking server
│   ├── prometheus/            # Prometheus metrics
│   └── grafana/               # Grafana dashboards
│
├── docs/                       # Documentation
│   ├── superpowers/
│   │   ├── specs/            # Architecture specs
│   │   └── plans/            # Implementation plans
│   └── screenshots/           # UI screenshots
│
└── .planning/                  # Project planning
    ├── PROJECT.md             # Project overview & requirements
    ├── ROADMAP.md             # Phase roadmap
    └── STATE.md               # Current project state
```

**Removed in cleanup:**
- `services/` - gRPC microservices (disabled, using monolithic Django)
- `protos/` - Protocol Buffer definitions (gRPC disabled)
- `kubernetes/`, `k8s/` - K8s manifests (not actively used)
- `docker/kafka/`, `docker/kong/` - Disabled services

---

## 🔌 API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register/` | Register new user |
| POST | `/api/auth/login/` | Login with JWT token |
| POST | `/api/auth/refresh/` | Refresh access token |

### Patient Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/patients/me/` | Get current patient profile |
| POST | `/api/patients/` | Create patient profile |
| PUT | `/api/patients/{id}/` | Update patient profile |

### Triage & Symptoms

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/symptom-assessment/` | Submit symptoms, get ML prediction |
| GET | `/api/sessions/` | List triage sessions |
| GET | `/api/sessions/{id}/` | Get session details |
| POST | `/api/sessions/{id}/end_session/` | End a session |

### Predictions

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/predictions/` | List predictions |
| POST | `/api/predictions/` | Create prediction |

### WebSocket

| Endpoint | Description |
|----------|-------------|
| `WS /ws/triage/{session_id}/` | Real-time chat with AI agent |

### API Documentation

| Endpoint | Description |
|----------|-------------|
| `/api/docs/` | Swagger UI (interactive API docs) |
| `/api/redoc/` | ReDoc (beautiful API docs) |

---

## 🧠 ML Model

### Model Details

- **Algorithm:** XGBoost Classifier
- **Training Data:** DiseaseAndSymptoms.csv
- **Classes:** 41 diseases
- **Features:** 131 symptoms
- **Performance:**
  - Accuracy: 88.5%
  - F1 Score: 86.7% (weighted)

### MLflow Integration

✅ **Active** - Model is registered in MLflow as `health-triage-classifier` v1

- Model artifacts stored in MLflow registry
- Experiment tracking enabled
- Access the MLflow UI at http://localhost:5000

### Supported Diseases (Sample)

| Disease | Common Symptoms |
|---------|-----------------|
| Flu | Fever, headache, fatigue, body aches |
| Migraine | Headache, nausea, light sensitivity |
| Common Cold | Runny nose, sneezing, sore throat |
| Allergy | Itching, sneezing, watery eyes |
| Pneumonia | Fever, cough, shortness of breath |

### Triage Levels

| Level | Description | Action |
|-------|-------------|--------|
| 🟢 Self-Care | Minor conditions | Rest at home, OTC medication |
| 🟡 GP Visit | Non-urgent conditions | Schedule doctor appointment |
| 🟠 Urgent Care | Potentially serious | Seek care within 24 hours |
| 🔴 Emergency | Life-threatening | Call emergency services immediately |

---

## 🛠️ Tech Stack

### Backend

| Technology | Version | Purpose |
|------------|---------|---------|
| Django | 5.0+ | Web framework |
| Django REST Framework | 3.15+ | REST API |
| Django Channels | 4.0+ | WebSocket support |
| Celery | 5.4+ | Async task queue |
| XGBoost | 2.1+ | ML classifier |
| LangChain | 0.2+ | AI agent framework |
| LangGraph | 0.2+ | Agent orchestration |

### Frontend

| Technology | Version | Purpose |
|------------|---------|---------|
| React | 18+ | UI framework |
| TypeScript | 5+ | Type safety |
| Tailwind CSS | 3+ | Styling |
| React Query | 5+ | Data fetching |
| Recharts | 2+ | Data visualization |
| Zustand | 4+ | State management |
| Axios | 1+ | HTTP client |

### Infrastructure

| Technology | Version | Purpose |
|------------|---------|---------|
| PostgreSQL | 16 | Primary database |
| Redis | 7 | Cache + message broker |
| MLflow | 2.10+ | ML lifecycle management |
| Prometheus | - | Metrics collection |
| Grafana | - | Dashboards |
| Jaeger | - | Distributed tracing |
| Loki | - | Log aggregation |

### DevOps

| Technology | Purpose |
|------------|---------|
| Docker | Containerization |
| Docker Compose | Local orchestration |
| GitHub Actions | CI/CD |
| Nginx | Reverse proxy |

---

## 📊 Screenshots

### Login Page
![Login](images/image.png)

### Dashboard
![Dashboard](images/image-1.png)

### AI Chat
![Chat](images/image-2.png)
![Chat](images/image-3.png)

### Health History
![History](images/image-4.png)

### MLflow UI
![MLflow](images/image-5.png)


---

## 🧪 Testing

```bash
# Backend tests
cd backend
python manage.py test

# Frontend tests
cd frontend
npm test

# Integration tests
pytest backend/api/tests/ -v
```

---

## 📈 Monitoring

### Prometheus Metrics

| Metric | Description |
|--------|-------------|
| `inference_requests_total` | Total inference requests |
| `inference_latency_seconds` | Inference latency histogram |
| `inference_cache_hits_total` | Cache hit counter |
| `agent_requests_total` | Agent request counter |
| `triage_sessions_total` | Triage sessions created |

### Grafana Dashboards

1. **System Overview** - RED method (Rate, Errors, Duration)
2. **ML Performance** - Accuracy, latency, cache hit rate
3. **Agent Performance** - Tool usage, conversation metrics
4. **Resource Utilization** - CPU, memory per service

### Access Dashboards

```bash
# Grafana
http://localhost:3000  # admin/admin

# Prometheus
http://localhost:9090

# Jaeger (Tracing)
http://localhost:16686
```

---

## 🔒 Security

- **JWT Authentication** - Secure token-based auth
- **HTTPS/TLS** - Encrypted communication
- **Rate Limiting** - DDoS protection (Nginx)
- **CORS** - Cross-origin request control
- **Input Validation** - Pydantic schemas
- **Audit Logging** - All actions logged for compliance

---

## 🚀 Deployment

### Local Development

```bash
cd docker
docker-compose up -d
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Django secret key | (required) |
| `DB_NAME` | PostgreSQL database | `medical_triage` |
| `DB_USER` | PostgreSQL user | `postgres` |
| `DB_PASSWORD` | PostgreSQL password | `postgres` |
| `DB_HOST` | PostgreSQL host | `localhost` |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379/0` |
| `GOOGLE_API_KEY` | Gemini API key | (required) |
| `MLFLOW_TRACKING_URI` | MLflow server URL | `http://localhost:5000` |

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Workflow

```bash
# Create branch
git checkout -b feature/your-feature

# Make changes, run tests
python manage.py test
npm test

# Commit with conventional commits
git commit -m "feat: add amazing feature"

# Push and create PR
git push origin feature/your-feature
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👥 Authors

- **Siddharth Solanki** - *Initial work* - [yourhandle](https://github.com/sidddha2004)

---

## 🙏 Acknowledgments

- Dataset: DiseaseAndSymptoms.csv
- Gemini API by Google
- XGBoost library
- Django and React communities



<div align="center">



</div>
