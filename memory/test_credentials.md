# ClearFile NG Test Credentials

## Admin Account
- Email: admin@clearfileng.com
- Password: ClearFileNG2024!
- Role: admin
- Plan: Business

## Test User (create via registration)
- Register with any email/password
- Default plan: Starter

## Flutterwave Payment Keys
- FLW_CLIENT_ID: 38c5f926-5c96-4d38-986d-148b95d36acf
- FLW_CLIENT_SECRET: C7icsbjbDPuspJRY4osOH4vE0GYzC1Dl
- FLW_ENV: production
- Note: Credentials currently return 401 from Flutterwave token endpoint. User needs to verify in Flutterwave dashboard.

## API Endpoints
- POST /api/auth/register
- POST /api/auth/login
- POST /api/auth/logout
- GET /api/auth/me
- GET /api/dashboard
- GET /api/transactions
- POST /api/transactions
- GET /api/bank-accounts
- POST /api/bank-accounts
- GET /api/tax-calculation
- POST /api/chat
- POST /api/receipts/upload
- GET /api/insights/recurring
- GET /api/insights/spending
- POST /api/payments/ai-guide/initialize
- GET /api/payments/ai-guide/verify
- GET /api/payments/ai-guide/status
- POST /api/subscription/initialize
- GET /api/subscription/verify
- POST /api/subscription/webhook
- GET /api/subscription/plans
