# Health Triage Assistant

A production-ready AI-powered health triage system that combines machine learning with conversational AI to provide accurate symptom assessments and triage recommendations.

## Features

- **AI-Powered Chat**: Real-time symptom assessment via WebSocket chat
- **ML predictions**: XGBoost classifier trained on medical dataset
- **Triage recommendations**: Self-care, GP visit, Urgent care, or Emergency
- **Health history**: Track assessments over time with visualizations
- **PDF reports**: Generated triage reports for records

## Tech Stack

### Backend
- Django 5 + Django REST Framework
- Django Channels (WebSocket)
- Celery + Redis (async tasks)
- PostgreSQL (database)
- LangChain + Gemini 2.5 Flash (AI agent)
- XGBoost + scikit-learn (ML)

### Frontend
- React 18 + TypeScript
- Tailwind CSS
- React Query
- Recharts
- Zustand (state management)

### Infrastructure
- Docker + Docker Compose
- Nginx (production)
- GitHub Actions (CI/CD)

## Quick Start

### Prerequisites
- Python 3.12+
- Node.js 20+
- Docker + Docker Compose

### Using Docker (Recommended)

```bash
# Start all services
cd docker
docker-compose up -d

# Backend available at http://localhost:8000
# Frontend available at http://localhost:80
# API docs at http://localhost:8000/api/docs/
```

### Local Development

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your settings
python manage.py migrate
python manage.py runserver
```

**Frontend:**
```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

**Infrastructure:**
```bash
cd docker
docker-compose up -d postgres redis
```

## Project Structure

```
medical-triage/
├── backend/           # Django backend
│   ├── api/          # REST API endpoints
│   ├── agent/        # AI agent + WebSocket handlers
│   ├── ml_pipeline/  # ML model training + prediction
│   ├── core/         # Shared utilities
│   └── backend/      # Django settings
├── frontend/          # React frontend
│   └── src/
│       ├── pages/    # Page components
│       ├── store/    # State management
│       └── lib/      # Utilities
├── docker/            # Docker configuration
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   ├── docker-compose.yml
│   └── nginx.conf
└── .planning/         # Project planning docs
```

## Environment Variables

**Backend (.env):**
```
SECRET_KEY=your-secret-key
DB_NAME=medical_triage
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432
REDIS_URL=redis://localhost:6379/0
GOOGLE_API_KEY=your-gemini-api-key
```

**Frontend (.env):**
```
VITE_API_URL=http://localhost:8000/api
```

## API Endpoints

- `POST /api/auth/register/` - User registration
- `POST /api/auth/login/` - User login
- `GET /api/patients/` - List patients
- `POST /api/symptoms/` - Submit symptoms
- `POST /api/predictions/` - Get ML prediction
- `WS /ws/triage/` - WebSocket chat endpoint
- `GET /api/docs/` - Swagger API documentation

## Development

```bash
# Run tests
cd backend && python manage.py test
cd frontend && npm test

# Lint
cd backend && flake8
cd frontend && npm run lint
```

## License

MIT
