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
- **Email**: Resend API for transactional emails

## What's Been Implemented

### Core Features ✅
- [x] Landing page with feature showcase and pricing
- [x] User registration and login with JWT auth
- [x] Email verification flow
- [x] Password reset flow (forgot password)
- [x] User onboarding with business type selection
- [x] Dashboard with Tax Health Score gauge
- [x] Bank account linking (Mono API + mock fallback)
- [x] Transaction management (add, view, delete)
- [x] Receipt upload with AI OCR extraction
- [x] Auto-create transactions from receipts
- [x] Tax Calculator with PITA/CITA/VAT calculations
- [x] Tax Filing Guide with steps and checklist
- [x] Tax Education articles
- [x] AI Chat Assistant with markdown table rendering
- [x] Subscription management with Paystack
- [x] CSV/JSON export for transactions and tax reports
- [x] Pidgin/English language toggle
- [x] Dark mode support
- [x] Mobile-responsive design

### Integrations ✅
- [x] Paystack payment processing
- [x] Mono Connect bank linking
- [x] Resend email service
- [x] Claude Sonnet 4.5 AI assistant
- [x] Emergent Object Storage for receipts

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

### P1 - High Priority
- [ ] Push notifications for deadlines
- [ ] Multi-user access for Business plan
- [ ] Real PDF generation (currently CSV)

### P2 - Nice to Have
- [ ] Biometric login (mobile app)
- [ ] Offline mode with sync
- [ ] Recurring expense detection
- [ ] Smart spending insights

## Deployment Status
- Backend: Running on port 8001
- Frontend: Running on port 3000
- Database: MongoDB connected
- Ready for deployment: YES
