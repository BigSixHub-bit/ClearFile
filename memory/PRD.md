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

## Phase 1 Mega-Update (June 2026) — COMPLETE & TESTED (iteration_9, 100%)
- [x] Urgent: Duplicate transaction detection + one-time cleanup + UI warning banner/modal
- [x] Update 1: Transaction Memory (auto-categorization, soft/hard locks, Settings management)
- [x] Update 2: WhatsApp AI upgraded to Claude Opus 4.8 (emergentintegrations LlmChat)
- [x] Update 3: Invoice Management (CRUD backend + /invoices page, auto-reconciliation, overdue status persisted to DB)
- [x] Update 4: Bank balance calculation fixed (accurate inflow/outflow sums)
- [x] Update 5: WhatsApp Setup panel in Settings
- [x] Update 6: Renamed project to ClearFile NG
- [x] Post-test fixes: dropped stale `user_id_1_receiver_account_1` index (verified via startup migration), duplicate description overlap threshold raised to 0.7, overdue invoice status persisted

## Testing: iteration_8 — 100% (11/11 backend, 8/8 frontend); iteration_9 — 100% (Phase 1 features)
## Credentials: admin@clearfileng.com / ClearFileNG2024! (cookie-based auth)

## Upcoming Tasks
- P1: Live Mono Bank Linking Integration (user providing keys)
- P2: Vove ID Verification integration
- P2: Weekly Automated WhatsApp Tax Digest
- P2: Expert Self-Service Portal
- P2: Multi-currency Support
