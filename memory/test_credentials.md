# ClearFile NG Test Credentials

## Admin Account
- Email: admin@clearfileng.com
- Password: ClearFileNG2024!
- Role: admin
- Plan: Business

## WhatsApp Bot Commands
- "help" — Show all commands
- "summary" / "tax" / "vat" — Tax & VAT micro-dashboard
- "balance" — Quick expense totals
- "invoice 500k for Client Name" — Create invoice with auto VAT
- "inject 200k" → "I funded business" / "Business paid me back"
- "memory" — View saved account categories
- Standard: "Paid 5k for MTN data", "Sent 50k to 0123456789 for rent"

## API Endpoints (New)
- POST /api/payments/ai-guide/initialize (₦70,000 Paystack payment)
- GET /api/payments/ai-guide/status
- POST /api/invoices, GET /api/invoices
- GET /api/vat/summary
- POST /api/journal-entries, GET /api/journal-entries
- POST /api/whatsapp/mono-sync (Mono guardrail trigger)
