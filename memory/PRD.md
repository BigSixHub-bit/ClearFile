# NairaTrack - Nigerian Tax & Expense Management App

## Original Problem Statement
Build a Nigerian Tax, Expense Management and Bank Tracking App called "NairaTrack" to help Nigerian individuals, freelancers, SMEs, and registered businesses automatically track their spending by linking bank accounts (read-only), auto-categorize transactions, calculate taxes based on Nigerian tax law (FIRS, PITA, CITA, VAT at 7.5%, WHT), and guide them through filing.

## Architecture
- **Backend**: FastAPI with MongoDB (async with Motor)
- **Frontend**: React with Shadcn UI components, Tailwind CSS
- **AI Integration**: Claude Sonnet 4.5 via emergentintegrations library
- **Storage**: Emergent Object Storage for receipt uploads
- **Auth**: JWT with httpOnly cookies, bcrypt password hashing
- **Payments**: Paystack integration for subscription billing
- **Banking**: Mono Connect API for bank account linking (with mock fallback)

## User Personas
1. **Freelancer/Self-Employed**: Uses PITA tax calculation, manual expense tracking on Starter plan
2. **SME Owner**: Uses PITA/VAT, bank linking on Growth plan, needs VAT filing reminders
3. **Registered Company**: Uses CITA/VAT/WHT, full features on Business plan, multi-user access

## Core Requirements (Static)
- User onboarding with business type selection (Freelancer, SME, Company)
- Bank account linking (Mono API + mock fallback)
- AI transaction categorization
- Nigerian tax calculations (PITA progressive rates 7-24%, CITA 20-30%, VAT 7.5%)
- Receipt scanner with OCR
- Tax filing guidance with FIRS TaxPro-Max integration
- AI chat assistant for tax questions
- Subscription plans with Paystack payments (Starter ₦2k, Growth ₦4k, Business ₦6k)
- Security badges and trust indicators
- Pidgin English language toggle

## What's Been Implemented

### Phase 1 (2026-04-01)
- [x] Landing page with feature showcase and pricing
- [x] User registration and login with JWT auth
- [x] User onboarding flow with business type selection
- [x] Dashboard with Tax Health Score gauge
- [x] Bank account linking (mock Nigerian Open Banking)
- [x] Transaction management (add, view, delete)
- [x] Tax Calculator with PITA/CITA/VAT calculations
- [x] Tax Filing Guide with steps and checklist
- [x] Tax Education articles
- [x] AI Chat Assistant (Claude Sonnet 4.5)
- [x] Receipt upload functionality
- [x] Settings page with subscription management
- [x] Pidgin/English language toggle
- [x] Dark mode support
- [x] Mobile-responsive design

### Phase 2 (2026-04-17)
- [x] AI Chat markdown rendering with tables
- [x] Dashboard data sync fix (all-time totals)
- [x] Paystack payment integration for subscriptions
- [x] Mono Connect API integration for real bank linking
- [x] Mock bank linking fallback when Mono not configured
- [x] Payment verification flow
- [x] Webhook handlers for Paystack and Mono

## API Keys Required for Production
1. **Paystack**: PAYSTACK_SECRET_KEY, PAYSTACK_PUBLIC_KEY
2. **Mono**: MONO_SECRET_KEY, MONO_PUBLIC_KEY, MONO_WEBHOOK_SECRET
3. **AI**: EMERGENT_LLM_KEY (already configured)

## Prioritized Backlog

### P0 - Critical (For Production)
- [x] Paystack payment integration ✅
- [x] Mono bank linking integration ✅
- [ ] Add actual Paystack API keys
- [ ] Add actual Mono API keys
- [ ] Email verification on registration
- [ ] Password reset flow

### P1 - High Priority
- [ ] Receipt OCR with AI extraction
- [ ] PDF/Excel export for reports
- [ ] Push notifications for deadlines
- [ ] Multi-user access for Business plan

### P2 - Nice to Have
- [ ] Biometric login (fingerprint/face ID)
- [ ] Offline mode with sync
- [ ] Recurring expense detection
- [ ] Smart spending insights

## Test Credentials
- **Admin**: admin@nairatrack.ng / NairaTrack2024!
- **Business Type**: Company
- **Plan**: Business

## Deployment Status
- Backend: Running on port 8001
- Frontend: Running on port 3000
- Database: MongoDB connected
- Ready for deployment: YES
