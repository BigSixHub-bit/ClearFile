# NairaTrack - Nigerian Tax & Expense Management App

## Original Problem Statement
Build a Nigerian Tax, Expense Management and Bank Tracking App called "NairaTrack" to help Nigerian individuals, freelancers, SMEs, and registered businesses automatically track their spending by linking bank accounts (read-only), auto-categorize transactions, calculate taxes based on Nigerian tax law (FIRS, PITA, CITA, VAT at 7.5%, WHT), and guide them through filing.

## Architecture (v2.0 — Modular)
- **Backend**: FastAPI with MongoDB (async with Motor)
  - `server.py` — Slim orchestrator (~130 lines)
  - `database.py`, `config.py`, `models.py` — Shared modules
  - `utils/auth.py`, `utils/storage.py`, `utils/tax.py` — Utilities
  - `routes/` — 12 modular route files (auth, transactions, dashboard, receipts, exports, chat, education, payments, banking, team, notifications, insights)
- **Frontend**: React with Shadcn UI, Tailwind CSS
- **AI Integration**: Claude Sonnet 4.5 via emergentintegrations
- **Auth**: JWT with httpOnly cookies, bcrypt password hashing
- **Payments**: Paystack integration (MOCKED)
- **Banking**: Mono Connect API (MOCKED)
- **Email**: Resend API (MOCKED)
- **Theme**: Deep green (#006400), white, gold (#FFD700). Mobile-first.

## What's Been Implemented (All Tested)

### Core Features
- [x] Landing page with feature showcase and pricing
- [x] User registration and login with JWT auth
- [x] Email verification and Password reset flows (mocked email)
- [x] User onboarding with business type selection
- [x] Dashboard with Tax Health Score gauge
- [x] Bank account linking (Mono mock + fallback)
- [x] Transaction management (CRUD)
- [x] Receipt upload with AI OCR extraction
- [x] Tax Calculator with PITA/CITA/VAT
- [x] Tax Filing Guide with steps and checklist
- [x] Tax Education articles
- [x] AI Chat Assistant with markdown tables
- [x] Subscription management with Paystack (mocked)
- [x] CSV/JSON/PDF export
- [x] Team Access (Business plan)
- [x] Notifications with deadline checks
- [x] Dark mode support
- [x] Mobile-responsive with bottom navigation

### New Features (v2.0)
- [x] Backend modular refactoring (2583 lines -> 12 route modules)
- [x] Recurring Expense Detection (auto-detect patterns)
- [x] Smart Spending Insights (rule-based + AI-powered)
- [x] Full Pidgin English translations (100+ keys)
- [x] Browser Push Notifications (Notification API)

### Testing Status
- Iteration 1: 97.6% (initial MVP)
- Iteration 2: 100% (37/37 backend, 100% frontend)
- Iteration 3: 100% (40/40 backend, 100% frontend) — after refactoring + 5 new features

## API Keys Required for Production
1. **Paystack**: PAYSTACK_SECRET_KEY, PAYSTACK_PUBLIC_KEY
2. **Mono**: MONO_SECRET_KEY, MONO_PUBLIC_KEY, MONO_WEBHOOK_SECRET
3. **Resend**: RESEND_API_KEY, SENDER_EMAIL
4. **AI**: EMERGENT_LLM_KEY (configured)

## Test Credentials
- **Admin**: admin@nairatrack.ng / NairaTrack2024!
- **Business Type**: Company
- **Plan**: Business

## Remaining Backlog

### P1 - High Priority
- [ ] Real Paystack/Mono/Resend integration (needs API keys)
- [ ] Service worker for offline support

### P2 - Nice to Have
- [ ] Biometric login (mobile app)
- [ ] WhatsApp/SMS deadline reminders
- [ ] Recurring expense auto-budgeting
- [ ] Multi-currency support

## Deployment Status
- Backend: Running on port 8001 (modular architecture)
- Frontend: Running on port 3000
- Database: MongoDB connected
- Ready for deployment: YES
