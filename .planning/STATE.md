# STATE.md - Health Triage Assistant

**Current Phase:** Phase 4: REST API

**Phase Goal:** JWT authentication, Patient CRUD, Symptom submission, Prediction endpoint.

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

## Active Phase

**Phase 4: REST API**

### Requirements
- AUTH-01: User can register with email and password
- AUTH-02: User can login with JWT token
- AUTH-03: User session persists across page refresh
- PAT-01: User can create patient profile
- PAT-02: User can view and edit patient profile
- PAT-03: User can view patient history
- SYM-02: System returns ML-based symptom classification

### Success Criteria
1. User can register/login via API
2. JWT token returned and validated
3. Patient CRUD endpoints work
4. Symptom submission returns ML prediction

### Tasks
- [ ] Setup JWT authentication (djangorestframework-simplejwt)
- [ ] Create User registration endpoint
- [ ] Create Login endpoint
- [ ] Create Patient CRUD endpoints (list, retrieve, update)
- [ ] Create Symptom submission endpoint
- [ ] Create Prediction endpoint (loads ML model, returns disease + confidence)
- [ ] Add permission classes
- [ ] Add request/response serializers

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-28)

**Core value:** Accurate, low-latency symptom assessment that guides patients to the right level of care — combining ML predictions with conversational AI for trusted health guidance.

**Current focus:** Phase 4: REST API

---
*Last updated: 2026-03-28 after Phase 3 completion*