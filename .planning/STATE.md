# STATE.md - Health Triage Assistant

**Current Phase:** Phase 2: Database + Models

**Phase Goal:** Define and migrate Patient, TriageSession, Prediction, AgentMessage models.

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

## Active Phase

**Phase 2: Database + Models**

### Requirements
- None (infrastructure phase)

### Success Criteria
1. All models defined in `backend/models/`
2. Migrations run successfully
3. Django Admin configured for all models
4. Model relationships correct (Patient → TriageSession → Prediction)

### Tasks
- [ ] Define Patient model (user, name, DOB, gender, created_at)
- [ ] Define TriageSession model (patient, started_at, ended_at, status)
- [ ] Define Prediction model (session, symptoms, disease, confidence, triage_level)
- [ ] Define AgentMessage model (session, role, content, tool_calls, timestamp)
- [ ] Run migrations
- [ ] Configure Django Admin for all models

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-28)

**Core value:** Accurate, low-latency symptom assessment that guides patients to the right level of care — combining ML predictions with conversational AI for trusted health guidance.

**Current focus:** Phase 2: Database + Models

---
*Last updated: 2026-03-28 after Phase 1 completion*
