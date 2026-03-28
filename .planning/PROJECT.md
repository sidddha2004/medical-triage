# Health Triage Assistant

## What This Is

A production-ready Health Triage Assistant that helps patients assess symptoms and get personalized health guidance. Users submit symptoms through a chat interface, receive AI-powered triage assessments backed by ML predictions, and can escalate to medical professionals when needed.

## Core Value

Accurate, low-latency symptom assessment that guides patients to the right level of care — combining ML predictions with conversational AI for trusted health guidance.

## Requirements

### Validated

(None yet — ship to validate)

### Active

#### Authentication
- [ ] **AUTH-01**: User can register with email and password
- [ ] **AUTH-02**: User can login with JWT token
- [ ] **AUTH-03**: User session persists across page refresh

#### Patient Management
- [ ] **PAT-01**: User can create patient profile
- [ ] **PAT-02**: User can view and edit patient profile
- [ ] **PAT-03**: User can view patient history

#### Symptom Assessment
- [ ] **SYM-01**: User can submit symptoms via chat interface
- [ ] **SYM-02**: System returns ML-based symptom classification
- [ ] **SYM-03**: System provides triage recommendation (self-care / GP / urgent / emergency)

#### AI Agent
- [ ] **AGT-01**: Agent handles natural conversation about symptoms
- [ ] **AGT-02**: Agent selects and calls tools (ML classifier, history, predictor)
- [ ] **AGT-03**: Agent responses stream in real-time via WebSocket
- [ ] **AGT-04**: Agent maintains conversation memory across session
- [ ] **AGT-05**: Agent generates structured triage reports
- [ ] **AGT-06**: Agent triggers escalation alerts when needed

#### Dashboard & History
- [ ] **DSH-01**: User can view triage history
- [ ] **DSH-02**: User can view past reports
- [ ] **DSH-03**: User can view health trends (Recharts visualizations)

#### Async Tasks
- [ ] **TSK-01**: System sends email alerts for high-priority triage
- [ ] **TSK-02**: System generates PDF reports asynchronously
- [ ] **TSK-03**: System runs cleanup jobs on schedule

### Out of Scope

- Direct integration with healthcare providers — legal/compliance complexity
- Prescription recommendations — regulatory requirements
- Mobile native apps — web-first approach

## Context

**Technical Environment:**
- Monorepo: frontend (React) + backend (Django)
- Real-time communication via Django Channels + WebSocket
- ML model trained on provided dataset (Disease_symptom_and_patient_profile_dataset.csv)
- LLM: Gemini 2.5 Flash via Google Generative AI API

**Dataset:**
- File: Disease_symptom_and_patient_profile_dataset.csv (20.51 kB)
- Contains symptoms + patient profiles mapped to diseases
- Used for XGBoost classifier training

**AI Agent Architecture:**
- LangChain agent with Gemini 2.5 Flash
- Custom tool loop for ML prediction, history retrieval, report generation
- Streaming responses for chat UX

## Constraints

- **Tech Stack**: React + TypeScript + Tailwind + React Query + Recharts (frontend), Django 5 + DRF + Channels + Celery + Redis (backend), PostgreSQL + Redis (data), XGBoost + spaCy + scikit-learn (ML), LangChain + Gemini 2.5 Flash (agent)
- **LLM**: Gemini 2.5 Flash mandatory — low latency, streaming, function calling
- **Dataset**: Must use provided CSV for ML training
- **Deployment**: Docker + Railway/Render (backend), Vercel (frontend)
- **Security**: HTTPS, CORS, rate limiting, audit logs, Sentry monitoring

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Gemini 2.5 Flash for agent | Low latency, cost-effective, supports streaming + tool calling | — Pending |
| XGBoost for ML classifier | High performance on tabular symptom data, interpretable | — Pending |
| Django Channels for WebSocket | Native Django integration, handles real-time chat | — Pending |
| Monorepo structure | Co-located frontend/backend for easier local dev | — Pending |
| PostgreSQL for patient data | Relational integrity for medical records | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd:transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-03-28 after initialization*
