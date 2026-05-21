# ClearFile NG - Nigerian Tax & Expense Management App

## Architecture (v4.0)
- **Backend**: FastAPI + MongoDB (16 route modules)
- **Frontend**: React + Shadcn UI + Tailwind + Recharts
- **AI**: Claude Sonnet 4.5 via emergentintegrations
- **WhatsApp**: Meta Business API (webhook + NLP)
- **Email**: Resend (live)

## What's Implemented

### Core
- [x] Auth (JWT cookies), 4 user types (Freelancer/SME/Company/Salary Earner)
- [x] Dashboard with Tax Health Score, Smart Insights, Recurring Expenses, TCC mini card
- [x] Transactions with "Tax Deductible" badges, AI categorization
- [x] Tax Calculator with filing CTA modal (3 options)
- [x] State vs Federal Tax Routing (11 Nigerian states)
- [x] TCC Tracker with progress bar, Fix Now buttons, PDF letter generation
- [x] Tax Planner (What-If Simulator) with pie chart + Set Aside
- [x] AI Chat Assistant, Receipt OCR, CSV/JSON/PDF export
- [x] WhatsApp Bot (NLP, subscription gate, transaction memory, proactive tagging)
- [x] Pidgin/English toggle, browser notifications, team access
- [x] Subscription: Starter (N2K) and Pro (N4K) plans

### New (v4.0)
- [x] **AI Tax Guide** — 6-step FIRS filing walkthrough with user's real data + AI advice per step
- [x] **Expert Matching** — Form to hire verified Pan-African tax professional (service type, urgency, budget)
- [x] Filing modal flow: Tax Calculator → AI Guide / Hire Expert / Send to Accountant

## Testing: iteration_5 — 100% (11/11 backend, 100% frontend)

## Credentials
- Admin: admin@clearfileng.com / ClearFileNG2024!
