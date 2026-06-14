# ClearFile NG - AI Financial Infrastructure Platform

## Design System v5.0 (Premium Dark SaaS)
- **Background**: #050505 (primary), #0A0A0A (secondary), #111111 (cards)
- **Border**: #1E1E1E (1px always)
- **Accent**: #00C896 (primary), #3B82F6 (secondary), #8B5CF6 (tertiary)
- **Glow**: linear-gradient(90deg, #00C896, #3B82F6, #8B5CF6)
- **Typography**: Clash Display/Satoshi (headings), Inter (body)
- **Inspiration**: Resend, Stripe, Linear, Vercel

## Architecture
- Backend: FastAPI + MongoDB (17 route modules under /app/backend/routes/)
- Frontend: React + Shadcn UI + Tailwind + Recharts
- AI: Claude Sonnet 4.5 (Emergent LLM Key)
- WhatsApp: Meta Business API (LIVE)
- Email: Resend (domain verified: clearfileng.com, LIVE)
- Payments: Flutterwave V4 OAuth2 (Card, Bank Transfer, USSD)

## All Features (Tested)
- [x] Auth, 4 user types, State selection
- [x] Dashboard: AI Financial Command Center
- [x] Transactions with Tax Deductible badges
- [x] Tax Engine with filing modal (AI Guide / Expert / Accountant)
- [x] State vs Federal Tax Routing
- [x] TCC Tracker with Fix Now + PDF generation
- [x] Tax Planner with pie chart + Set Aside
- [x] AI Chat Assistant, Receipt OCR, PDF/CSV export
- [x] WhatsApp Bot (NLP, subscription gate, memory, proactive tagging)
- [x] Expert Matching + Admin Panel
- [x] Email notifications on expert match (Resend live)
- [x] AI Tax Guide (6-step FIRS walkthrough)
- [x] Pidgin/English toggle, Browser notifications
- [x] Premium Dark SaaS redesign (Stripe/Linear aesthetic)
- [x] Flutterwave V4 Payment Integration (AI Guide ₦70,000 + Subscriptions)
- [x] PaymentSuccess callback page (/payment-success)
- [x] Unified webhook handler for all Flutterwave events

## Payment Flows
- AI Tax Guide: POST /api/payments/ai-guide/initialize -> Flutterwave hosted checkout -> /payment-success callback -> GET /api/payments/ai-guide/verify
- Subscriptions: POST /api/subscription/initialize -> Flutterwave hosted checkout -> /payment-success callback -> GET /api/subscription/verify
- Webhook: POST /api/subscription/webhook (verif-hash validation)
- Mock mode: Active when Flutterwave credentials are not configured (is_flutterwave_configured() = false)

## Known Issues
- Flutterwave V4 OAuth2 credentials returning 401 from idp.flutterwave.com — user needs to verify FLW_CLIENT_ID/FLW_CLIENT_SECRET in Flutterwave dashboard
- Mono bank linking: MOCKED (waiting for user to provide Mono API keys)

## Testing: iteration_8 — 100% (11/11 backend, 8/8 frontend)
## Credentials: admin@clearfileng.com / ClearFileNG2024!

## Upcoming Tasks
- P1: Live Mono Bank Linking Integration (user providing keys)
- P2: Vove ID Verification integration
- P2: Weekly Automated WhatsApp Tax Digest
- P2: Expert Self-Service Portal
- P2: Multi-currency Support
