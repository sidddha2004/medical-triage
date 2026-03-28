# Roadmap: Health Triage Assistant

**Created:** 2026-03-28
**Core Value:** Accurate, low-latency symptom assessment that guides patients to the right level of care — combining ML predictions with conversational AI for trusted health guidance.

---

## Phase Overview

| # | Phase | Goal | Requirements | Success Criteria |
|---|-------|------|--------------|------------------|
| 1 | Project Setup | Monorepo structure, Django + React skeleton, PostgreSQL + Redis configured | — | Repositories initialized, dev servers run |
| 2 | Database + Models | Patient, TriageSession, Prediction, AgentMessage models | — | Models defined, migrations run, admin configured |
| 3 | ML Model Pipeline | XGBoost classifier trained on dataset, served via API | — | Model trained (F1 > 0.8), predictions via API |
| 4 | REST API | JWT auth, Patient CRUD, Symptom submission, Prediction endpoint | AUTH-01, AUTH-02, AUTH-03, PAT-01, PAT-02, PAT-03, SYM-02 | API endpoints functional, authenticated |
| 5 | Agentic AI | LangChain agent with Gemini 2.5 Flash, tools, WebSocket streaming | AGT-01, AGT-02, AGT-03, AGT-04, AGT-05, AGT-06 | Agent handles conversation, calls tools, streams |
| 6 | Frontend Dashboard | Login, Dashboard, Chat UI, Results + History | DSH-01, DSH-02, DSH-03, SYM-01, SYM-03 | User can login, chat, view results |
| 7 | Async Tasks | Celery + Redis, email alerts, PDF generation, cleanup | TSK-01, TSK-02, TSK-03 | Tasks queued + executed, emails sent |
| 8 | Testing + Polish | Full flow testing, error handling, logging | All | End-to-end flow works |

---

## Phase Details

### Phase 1: Project Setup

**Goal:** Monorepo structure with Django backend + React frontend, PostgreSQL + Redis configured, environment variables, Git initialized.

**Requirements:** —

**Success Criteria:**
1. `git status` shows clean repository
2. `docker-compose up` starts PostgreSQL + Redis
3. Django `python manage.py runserver` works
4. React `npm run dev` works
5. `.env` files configured for backend + frontend

**Tasks:**
- [ ] Create monorepo structure: `/backend`, `/frontend`, `/docker`
- [ ] Initialize Django 5 project with DRF, Channels
- [ ] Initialize React + TypeScript + Tailwind + React Query + Recharts
- [ ] Configure PostgreSQL (docker + local)
- [ ] Configure Redis (docker + local)
- [ ] Setup environment variables (.env backend + frontend)
- [ ] Initialize Git with proper .gitignore

---

### Phase 2: Database + Models

**Goal:** Define and migrate Patient, TriageSession, Prediction, AgentMessage models.

**Requirements:** —

**Success Criteria:**
1. All models defined in `backend/models/`
2. Migrations run successfully
3. Django Admin configured for all models
4. Model relationships correct (Patient → TriageSession → Prediction)

**Tasks:**
- [ ] Define Patient model (user, name, DOB, gender, created_at)
- [ ] Define TriageSession model (patient, started_at, ended_at, status)
- [ ] Define Prediction model (session, symptoms, disease, confidence, triage_level)
- [ ] Define AgentMessage model (session, role, content, tool_calls, timestamp)
- [ ] Run migrations
- [ ] Configure Django Admin for all models

---

### Phase 3: ML Model Pipeline

**Goal:** Train XGBoost classifier on provided dataset, serialize with joblib, serve via API.

**Requirements:** —

**Success Criteria:**
1. Dataset loaded and preprocessed
2. XGBoost model trained with F1-score > 0.8
3. Model serialized to `models/classifier.joblib`
4. Prediction API endpoint returns disease + confidence

**Tasks:**
- [ ] Load Disease_symptom_and_patient_profile_dataset.csv
- [ ] Clean data (missing values, encoding)
- [ ] Feature engineering (symptoms + patient profile)
- [ ] Train/test split
- [ ] Train XGBoost classifier
- [ ] Evaluate (F1-score, classification report)
- [ ] Serialize model + encoders with joblib
- [ ] Create prediction API endpoint

---

### Phase 4: REST API

**Goal:** JWT authentication, Patient CRUD, Symptom submission, Prediction endpoint.

**Requirements:** AUTH-01, AUTH-02, AUTH-03, PAT-01, PAT-02, PAT-03, SYM-02

**Success Criteria:**
1. User can register/login via API
2. JWT token returned and validated
3. Patient CRUD endpoints work
4. Symptom submission returns ML prediction

**Tasks:**
- [ ] Setup JWT authentication (djangorestframework-simplejwt)
- [ ] Create User registration endpoint
- [ ] Create Login endpoint
- [ ] Create Patient CRUD endpoints (list, retrieve, update)
- [ ] Create Symptom submission endpoint
- [ ] Create Prediction endpoint (loads ML model, returns disease + confidence)
- [ ] Add permission classes
- [ ] Add request/response serializers

---

### Phase 5: Agentic AI

**Goal:** LangChain agent with Gemini 2.5 Flash, custom tools, WebSocket streaming via Django Channels.

**Requirements:** AGT-01, AGT-02, AGT-03, AGT-04, AGT-05, AGT-06

**Success Criteria:**
1. Agent handles natural conversation about symptoms
2. Agent selects and calls tools (ML classifier, history retriever, predictor, report generator, escalation alert)
3. Agent responses stream in real-time via WebSocket
4. Agent maintains conversation memory across session
5. Agent generates structured triage reports
6. Agent triggers escalation alerts for high-priority cases

**Tasks:**
- [ ] Setup LangChain with Google Generative AI (Gemini 2.5 Flash)
- [ ] Configure Gemini API key, enable streaming
- [ ] Define Tool 1: Symptom classifier (calls ML model)
- [ ] Define Tool 2: History retriever (queries DB)
- [ ] Define Tool 3: Predictor (disease + triage level)
- [ ] Define Tool 4: Report generator (structured output)
- [ ] Define Tool 5: Escalation alert (high-priority trigger)
- [ ] Implement agent tool selection loop
- [ ] Implement conversation memory (chat history)
- [ ] Setup Django Channels for WebSocket
- [ ] Create WebSocket consumer for chat
- [ ] Enable streaming responses to frontend
- [ ] Add structured output parsing

---

### Phase 6: Frontend Dashboard

**Goal:** Login, Dashboard, Chat UI with streaming, Results + History + Reports visualizations.

**Requirements:** DSH-01, DSH-02, DSH-03, SYM-01, SYM-03

**Success Criteria:**
1. User can login with JWT
2. Dashboard shows triage history
3. Chat UI streams agent responses in real-time
4. Results page shows past predictions + reports
5. Recharts visualizations show health trends

**Tasks:**
- [ ] Create Login page (email/password)
- [ ] Setup React Query for API calls
- [ ] Create Dashboard layout
- [ ] Create Chat UI component (WebSocket connection)
- [ ] Enable streaming response rendering
- [ ] Create Results page (list of past sessions)
- [ ] Create Report view (detailed triage report)
- [ ] Create History page with Recharts visualizations
- [ ] Add Tailwind styling

---

### Phase 7: Async Tasks

**Goal:** Celery + Redis for background tasks — email alerts, PDF generation, cleanup jobs.

**Requirements:** TSK-01, TSK-02, TSK-03

**Success Criteria:**
1. Celery worker processes tasks
2. Email alerts sent for high-priority triage
3. PDF reports generated and stored
4. Cleanup jobs run on schedule

**Tasks:**
- [ ] Setup Celery with Django
- [ ] Configure Redis as broker
- [ ] Create email alert task (high-priority triage)
- [ ] Create PDF report generation task
- [ ] Create cleanup task (old sessions)
- [ ] Setup Celery Beat for scheduled tasks
- [ ] Add task logging + error handling

---

### Phase 8: Testing + Polish

**Goal:** Full flow testing, error handling, logging, production readiness.

**Requirements:** All active requirements

**Success Criteria:**
1. Full flow works: symptom → agent → ML → response → report
2. All error cases handled gracefully
3. Logging configured for all components
4. API documented (Swagger/Redoc)
5. No console errors in frontend

**Tasks:**
- [ ] Write integration tests for full flow
- [ ] Add error handling to all endpoints
- [ ] Add logging to backend (structlog)
- [ ] Add error boundaries to frontend
- [ ] Setup API documentation (drf-spectacular)
- [ ] Test all user journeys
- [ ] Fix any bugs found

---

## v2 Requirements (Deferred to Phase 2 - Deployment)

### Deployment
- **DEP-01**: Backend dockerized, deployed to Railway/Render
- **DEP-02**: Frontend deployed to Vercel
- **DEP-03**: Managed PostgreSQL + Redis configured
- **DEP-04**: HTTPS enabled, CORS configured
- **DEP-05**: Rate limiting enabled
- **DEP-06**: Audit logs configured
- **DEP-07**: GitHub Actions CI/CD pipeline
- **DEP-08**: Sentry error monitoring
- **DEP-09**: Uptime monitoring configured

---

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| AUTH-01 | Phase 4 | Pending |
| AUTH-02 | Phase 4 | Pending |
| AUTH-03 | Phase 4 | Pending |
| PAT-01 | Phase 4 | Pending |
| PAT-02 | Phase 4 | Pending |
| PAT-03 | Phase 4 | Pending |
| SYM-01 | Phase 6 | Pending |
| SYM-02 | Phase 4 | Pending |
| SYM-03 | Phase 6 | Pending |
| AGT-01 | Phase 5 | Pending |
| AGT-02 | Phase 5 | Pending |
| AGT-03 | Phase 5 | Pending |
| AGT-04 | Phase 5 | Pending |
| AGT-05 | Phase 5 | Pending |
| AGT-06 | Phase 5 | Pending |
| DSH-01 | Phase 6 | Pending |
| DSH-02 | Phase 6 | Pending |
| DSH-03 | Phase 6 | Pending |
| TSK-01 | Phase 7 | Pending |
| TSK-02 | Phase 7 | Pending |
| TSK-03 | Phase 7 | Pending |

**Coverage:**
- v1 requirements: 21 total
- Mapped to phases: 21
- Unmapped: 0 ✓

---
*Last updated: 2026-03-28 after roadmap creation*
