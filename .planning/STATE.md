# STATE.md - Health Triage Assistant

**Current Phase:** Phase 1: Project Setup

**Phase Goal:** Monorepo structure with Django backend + React frontend, PostgreSQL + Redis configured, environment variables, Git initialized.

## Active Phase

**Phase 1: Project Setup**

### Requirements
- None (infrastructure phase)

### Success Criteria
1. `git status` shows clean repository
2. `docker-compose up` starts PostgreSQL + Redis
3. Django `python manage.py runserver` works
4. React `npm run dev` works
5. `.env` files configured for backend + frontend

### Tasks
- [ ] Create monorepo structure: `/backend`, `/frontend`, `/docker`
- [ ] Initialize Django 5 project with DRF, Channels
- [ ] Initialize React + TypeScript + Tailwind + React Query + Recharts
- [ ] Configure PostgreSQL (docker + local)
- [ ] Configure Redis (docker + local)
- [ ] Setup environment variables (.env backend + frontend)
- [ ] Initialize Git with proper .gitignore

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-28)

**Core value:** Accurate, low-latency symptom assessment that guides patients to the right level of care — combining ML predictions with conversational AI for trusted health guidance.

**Current focus:** Phase 1: Project Setup

---
*Last updated: 2026-03-28*
