# STATE.md - Health Triage Assistant

**Current Phase:** Phase 5: Agentic AI

**Phase Goal:** LangChain agent with Gemini 2.5 Flash, custom tools, WebSocket streaming via Django Channels.

## Completed Phases

### Phase 1: Project Setup ✓

**Completed:** 2026-03-28

**Success Criteria:**
1. ✓ `git status` shows clean repository
2. ✓ `docker-compose up` starts PostgreSQL + Redis (ready)
3. ✓ Django `python manage.py runserver` works (ready)
4. ✓ React `npm run dev` works (ready)
5. ✓ `.env` files configured for backend + frontend

**Tasks:** All completed

### Phase 2: Database + Models ✓

**Completed:** 2026-03-28

**Success Criteria:**
1. ✓ All models defined in `backend/core/models.py`
2. ✓ Migrations run successfully
3. ✓ Django Admin configured for all models
4. ✓ Model relationships correct (Patient → TriageSession → Prediction)

**Tasks:** All completed

### Phase 3: ML Model Pipeline ✓

**Completed:** 2026-03-28

**Success Criteria:**
1. ✓ Dataset loaded and preprocessed
2. ✓ XGBoost model trained with F1-score > 0.8 (achieved 86.7%)
3. ✓ Model serialized to `models/classifier.json`
4. ✓ Prediction API endpoint returns disease + confidence

**Tasks:** All completed

### Phase 4: REST API ✓

**Completed:** 2026-03-28

**Success Criteria:**
1. ✓ User can register/login via API
2. ✓ JWT token returned and validated
3. ✓ Patient CRUD endpoints work
4. ✓ Symptom submission returns ML prediction

**Tasks:** All completed

## Active Phase

**Phase 5: Agentic AI**

### Requirements
- AGT-01: Agent handles natural conversation about symptoms
- AGT-02: Agent selects and calls tools (ML classifier, history retriever, predictor, report generator, escalation alert)
- AGT-03: Agent responses stream in real-time via WebSocket
- AGT-04: Agent maintains conversation memory across session
- AGT-05: Agent generates structured triage reports
- AGT-06: Agent triggers escalation alerts for high-priority cases

### Success Criteria
1. LangChain agent with Gemini 2.5 Flash configured
2. Custom tools defined (ML classifier, history retriever, predictor, report generator, escalation)
3. WebSocket consumer for real-time chat
4. Streaming responses to frontend
5. Conversation memory persisted

### Tasks
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

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-28)

**Core value:** Accurate, low-latency symptom assessment that guides patients to the right level of care — combining ML predictions with conversational AI for trusted health guidance.

**Current focus:** Phase 5: Agentic AI

---
*Last updated: 2026-03-28 after Phase 4 completion*