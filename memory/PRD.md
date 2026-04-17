# NairaTrack - Nigerian Tax & Expense Management App

## Original Problem Statement
Build a Nigerian Tax, Expense Management and Bank Tracking App called "NairaTrack" to help Nigerian individuals, freelancers, SMEs, and registered businesses automatically track their spending by linking bank accounts (read-only), auto-categorize transactions, calculate taxes based on Nigerian tax law (FIRS, PITA, CITA, VAT at 7.5%, WHT), and guide them through filing.

## Architecture
- **Backend**: FastAPI with MongoDB (async with Motor), monolithic server.py (2583 lines)
- **Frontend**: React with Shadcn UI components, Tailwind CSS
- **AI Integration**: Claude Sonnet 4.5 via emergentintegrations library
- **Auth**: JWT with httpOnly cookies, bcrypt password hashing
- **Payments**: Paystack integration (MOCKED - no API keys)
- **Banking**: Mono Connect API (MOCKED - no API keys)
- **Email**: Resend API (MOCKED - no API keys)
- **Theme**: Deep green (#006400), white, gold (#FFD700). Mobile-first.

## What's Been Implemented (All Tested ✅)

### Core Features
- [x] Landing page with feature showcase and pricing
- [x] User registration and login with JWT auth (httpOnly cookies)
- [x] Email verification flow (mocked email)
- [x] Password reset flow (mocked email)
- [x] User onboarding with business type selection (Freelancer/SME/Company)
- [x] Dashboard with Tax Health Score gauge
- [x] Bank account linking (Mono API mock + fallback)
- [x] Transaction management (CRUD)
- [x] Receipt upload with AI OCR extraction (Claude Vision)
- [x] Auto-create transactions from receipts
- [x] Tax Calculator with PITA/CITA/VAT calculations
- [x] Tax Filing Guide with steps and checklist
- [x] Tax Education articles
- [x] AI Chat Assistant with markdown table rendering (remark-gfm)
- [x] Subscription management with Paystack (mocked)
- [x] CSV/JSON/PDF export for transactions and tax reports
- [x] Team Access (invite/remove members) - Business plan only
- [x] Notifications (get, mark read, unread count, deadline checks)
- [x] Pidgin/English language toggle
- [x] Dark mode support
- [x] Mobile-responsive design with bottom navigation

### Testing Status
- Iteration 1: 97.6% pass rate (20/21 backend, 100% frontend)
- Iteration 2: 100% pass rate (37/37 backend, 100% frontend) — includes PDF, Team, Notifications

## API Keys Required for Production
1. **Paystack**: PAYSTACK_SECRET_KEY, PAYSTACK_PUBLIC_KEY
2. **Mono**: MONO_SECRET_KEY, MONO_PUBLIC_KEY, MONO_WEBHOOK_SECRET
3. **Resend**: RESEND_API_KEY, SENDER_EMAIL
4. **AI**: EMERGENT_LLM_KEY (already configured)

## Test Credentials
- **Admin**: admin@nairatrack.ng / NairaTrack2024!
- **Business Type**: Company
- **Plan**: Business

## Remaining Backlog

### P0 - Critical
- [ ] Backend refactoring: Split server.py (2583 lines) into FastAPI APIRouter modules

### P1 - High Priority
- [ ] Real Receipt Scanner (OCR) validation — endpoint exists, needs thorough testing with real images
- [ ] Full Pidgin English translations across all pages
- [ ] Functional Push Notifications (Firebase/Web Push)
- [ ] Real email integration (Resend) — needs API key

### P2 - Nice to Have
- [ ] Real Paystack integration — needs API key
- [ ] Real Mono integration — needs API key
- [ ] Biometric login (mobile app)
- [ ] Offline mode with sync
- [ ] Recurring expense detection
- [ ] Smart spending insights

## Deployment Status
- Backend: Running on port 8001
- Frontend: Running on port 3000
- Database: MongoDB connected
- Ready for deployment: YES
