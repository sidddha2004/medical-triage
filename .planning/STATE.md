# STATE.md - Health Triage Assistant

**Current Phase:** Phase 3: ML Model Pipeline

**Phase Goal:** Train XGBoost classifier on provided dataset, serialize with joblib, serve via API.

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

## Active Phase

**Phase 3: ML Model Pipeline**

### Requirements
- None (infrastructure phase)

### Success Criteria
1. Dataset loaded and preprocessed
2. XGBoost model trained with F1-score > 0.8
3. Model serialized to `models/classifier.joblib`
4. Prediction API endpoint returns disease + confidence

### Tasks
- [ ] Load Disease_symptom_and_patient_profile_dataset.csv
- [ ] Clean data (missing values, encoding)
- [ ] Feature engineering (symptoms + patient profile)
- [ ] Train/test split
- [ ] Train XGBoost classifier
- [ ] Evaluate (F1-score, classification report)
- [ ] Serialize model + encoders with joblib
- [ ] Create prediction API endpoint

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-28)

**Core value:** Accurate, low-latency symptom assessment that guides patients to the right level of care — combining ML predictions with conversational AI for trusted health guidance.

**Current focus:** Phase 3: ML Model Pipeline

---
*Last updated: 2026-03-28 after Phase 2 completion*
