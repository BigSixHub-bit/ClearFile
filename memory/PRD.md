# ClearFile NG - Nigerian Tax & Expense Management App
(Renamed from NairaTrack)

## Original Problem Statement
Build a Nigerian Tax, Expense Management and Bank Tracking App to help Nigerian individuals, freelancers, SMEs, salary earners, and registered businesses track spending, auto-categorize transactions, calculate taxes (PITA, CITA, VAT, WHT), route obligations to correct authorities, and guide filing.

## Architecture (v3.0 — Full Feature)
- **Backend**: FastAPI with MongoDB (modular: 13 route files)
  - `server.py` — Orchestrator
  - `routes/` — auth, transactions, dashboard, receipts, exports, chat, education, payments, banking, team, notifications, insights, **tax_engine** (NEW)
- **Frontend**: React + Shadcn UI + Tailwind + Recharts
- **AI**: Claude Sonnet 4.5 via emergentintegrations
- **Theme**: Deep green (#006400), white, gold (#FFD700). Mobile-first.

## What's Implemented

### Core
- [x] User auth (JWT cookies, bcrypt, brute-force protection)
- [x] Onboarding: 4 user types (Freelancer, SME, Company, Salary Earner) + state selection
- [x] Dashboard with Tax Health Score, Smart Insights, Recurring Expenses, TCC mini card
- [x] Transaction CRUD with AI categorization + "Tax Deductible" green badges
- [x] Receipt OCR (Claude Vision)
- [x] Tax Calculator (PITA/CITA/VAT)
- [x] CSV/JSON/PDF export, Team Access, Notifications
- [x] Pidgin/English toggle (100+ keys)

### New Features (v3.0)
- [x] **AI Smart Expense Categorizer** — Auto-categorize personal vs business, flag deductible expenses
- [x] **State vs Federal Tax Routing** — Route VAT/CIT to FIRS, PAYE to state revenue (11 states)
- [x] **TCC Tracker** — 0-100% progress bar, 6-item checklist, PDF TCC Request Letter generation
- [x] **Tax Planner (What-If Simulator)** — Interactive inputs, pie chart, Set Aside tax reserve
- [x] **Trust & Security Signals** — 256-bit SSL, NDPR badges, Mono/Okra/Stitch logos throughout
- [x] **Salary Earner support** — Added as 4th user type in registration and calculations

### Testing
- Iteration 4: 100% (19/19 backend, 100% frontend) — all new features verified

## Test Credentials
- **Admin**: admin@nairatrack.ng / NairaTrack2024!
- **Plan**: Business

## Remaining Backlog
- [ ] Real Paystack/Mono/Resend integration (needs API keys)
- [ ] WhatsApp/SMS deadline reminders
- [ ] Budget Planner feature
- [ ] Multi-currency support
