# ClearFile NG — Security & Production Readiness Notes
Last updated: June 2026 (Security Hardening Update)

## Stack reality
ClearFile NG is React (CRA) + FastAPI + MongoDB (Motor). There is no Next.js or Prisma;
the owner's checklist was mapped onto the actual stack.

## Implemented security decisions
- Passwords: bcrypt hashing (utils/auth.py). Min length 8 on register & reset.
- Sessions: JWT (HS256) in httpOnly cookies; Secure flag auto-enabled when FRONTEND_URL is https; SameSite=Lax.
- Session revocation: `token_version` claim ("tv") in access + refresh tokens, checked against the user document on every request. Password reset increments token_version → all existing sessions are invalidated.
- CORS: wildcard removed; restricted to FRONTEND_URL (+ CORS_ORIGINS env, "*" ignored).
- Security headers middleware: X-Content-Type-Options, X-Frame-Options=DENY, Referrer-Policy, Permissions-Policy, HSTS (https only).
- Global exception handler: unhandled errors return a generic message; details only in server logs.
- Rate limiting (Mongo-backed, TTL-cleaned `rate_limits` collection):
  - register: 5/hour/IP
  - forgot-password: 3/15min/IP
  - reset-password: 5/15min/IP
  - resend-verification: 3/15min/user
  - AI chat: 20/5min/user (+4000 char message cap)
  - login: existing 5-failures/15min lockout (now keyed by X-Forwarded-For IP)
- Suspicious-session signal: `login_history` collection records IP+UA per login; a login from a new IP triggers an in-app "New login detected" notification. No geo-profiling, no automatic lockout.
- Privilege escalation closed: PUT /api/user/subscription now only allows downgrade to "starter"; upgrades must go through /api/subscription/initialize (payment flow). Role can never be set via any user-facing endpoint (settings whitelist excludes role/subscription).
- Admin: all /api/admin/* endpoints require role=admin server-side (require_admin dependency).
- IDOR: all financial resources (transactions, invoices, receipts, notifications, team, exports, memory) are query-scoped to the authenticated user id. Verified in audit June 2026.
- Uploads: receipts restricted to JPEG/PNG/WebP/PDF, 10MB max, extension derived from validated content-type (not filename), stored per-user in private object storage, download requires auth + ownership.
- Webhooks:
  - Mono: HMAC-SHA256 signature REQUIRED when MONO_WEBHOOK_SECRET is set (missing signature now rejected).
  - Flutterwave: verif-hash compared with constant-time compare.
  - WhatsApp: GET verify token; POST validates X-Hub-Signature-256 when WHATSAPP_APP_SECRET env is set (optional — Meta App Secret not yet provided).
- Logging: no passwords, tokens, OTPs or cookies are logged. Rate-limit/authz failures logged with truncated keys.
- AI: per-user sessions; system prompts never include other users' data; receipt OCR runs on the user's own upload only.

## Environment variables (new / optional)
- WHATSAPP_APP_SECRET (optional) — enables Meta webhook signature validation.
- CORS_ORIGINS (optional, comma-separated) — extra allowed origins; "*" is ignored.

## Deployment / legal-review TODOs (intentionally not faked in code)
1. BACKUPS: MongoDB automated backups + restore drill must be configured at the hosting layer
   (recommend daily snapshot, 30-day retention). Code cannot provide backups.
2. LEGAL REVIEW: /privacy and /terms are accurate to actual behavior but must be reviewed by
   licensed Nigerian counsel (NDPA 2023 registration/DPIA positions marked in the Privacy page).
3. CSP: a strict Content-Security-Policy for the frontend should be added at the hosting/CDN layer
   after deployment (CRA dev server requires eval, so a meta-tag CSP would break the preview).
4. Custom domain: robots.txt + sitemap.xml currently reference the preview URL — update on custom domain.
5. Step-up auth (OTP) for sensitive actions: no OTP system exists yet in this codebase; when the
   separate OTP feature lands, wire it to: password change, bank disconnect, account deletion, data export.
6. Analytics: none installed (by design). If added later, must respect consent and never send
   transaction amounts, tax data, or bank info.

## Cookie/consent position
Only strictly necessary auth cookies are used. No optional analytics/marketing cookies →
no consent banner required. Re-evaluate if analytics are ever added.
