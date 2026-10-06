import { Link } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';

const Section = ({ title, children }) => (
  <section className="mb-8">
    <h2 className="text-lg font-semibold text-white mb-3">{title}</h2>
    <div className="text-sm text-[#A1A1AA] leading-relaxed space-y-3">{children}</div>
  </section>
);

export default function Privacy() {
  return (
    <div className="min-h-screen bg-[#0A0A0A]" data-testid="privacy-page">
      <header className="border-b border-[#1E1E1E] px-4 py-4">
        <div className="max-w-3xl mx-auto flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2" data-testid="privacy-home-link">
            <div className="w-7 h-7 rounded-md bg-gradient-to-br from-[#00C896] to-[#3B82F6] flex items-center justify-center">
              <span className="text-black font-bold text-xs">C</span>
            </div>
            <span className="text-white font-semibold">ClearFile NG</span>
          </Link>
          <Link to="/" className="inline-flex items-center gap-1 text-sm text-[#A1A1AA] hover:text-white transition-colors">
            <ArrowLeft className="w-4 h-4" /> Back
          </Link>
        </div>
      </header>
      <main className="max-w-3xl mx-auto px-4 py-10">
        <h1 className="text-3xl sm:text-4xl font-bold text-white mb-2">Privacy Policy</h1>
        <p className="text-xs text-[#555] mb-10">Last updated: June 2026</p>

        <Section title="1. Who We Are">
          <p>
            ClearFile NG ("ClearFile", "we", "us") is a Nigerian bookkeeping, expense management and
            tax-compliance platform for freelancers, MSMEs and companies. This policy explains what
            personal data we collect, why we collect it, and how we protect it.
          </p>
        </Section>

        <Section title="2. Data We Collect">
          <p>We collect only what is needed to provide the service:</p>
          <ul className="list-disc pl-5 space-y-1">
            <li><span className="text-white">Account information</span> — name, email address, password (stored only as a secure bcrypt hash, never in plaintext), business type and income range.</li>
            <li><span className="text-white">Phone number</span> — if you use the WhatsApp experience, your WhatsApp number is used to link messages to your account.</li>
            <li><span className="text-white">Business &amp; financial records</span> — transactions, invoices, journal entries, VAT and tax calculations you create or that are generated from your inputs.</li>
            <li><span className="text-white">Uploaded receipts/documents</span> — stored in access-controlled object storage, readable only by your authenticated account.</li>
            <li><span className="text-white">Bank connection data</span> — if you link a bank account via Mono, we receive transaction and balance data you authorise. We never see or store your bank login credentials.</li>
            <li><span className="text-white">Payment information</span> — subscription payments are processed by Flutterwave. We store payment references and status, never your full card details.</li>
            <li><span className="text-white">Security data</span> — login timestamps, IP address and device information used solely to detect suspicious account activity.</li>
          </ul>
        </Section>

        <Section title="3. How We Use Your Data">
          <ul className="list-disc pl-5 space-y-1">
            <li>To operate your bookkeeping ledger, invoices and tax calculations.</li>
            <li>To categorise transactions, including AI-assisted categorisation.</li>
            <li>To send service emails (verification, password reset, expert-match updates) via Resend.</li>
            <li>To respond to your WhatsApp messages via the Meta WhatsApp Business API.</li>
            <li>To protect your account from unauthorised access.</li>
          </ul>
          <p>We do not sell your personal data. We do not use your financial data for advertising.</p>
        </Section>

        <Section title="4. AI Processing">
          <p>
            Some features (receipt OCR, chat assistant, WhatsApp assistant) send the relevant content
            you provide to AI model providers to generate a response. Only your own data is used in
            your requests — one user's financial information is never included in another user's AI request.
          </p>
        </Section>

        <Section title="5. Third-Party Processors">
          <ul className="list-disc pl-5 space-y-1">
            <li>Mono (bank account connections)</li>
            <li>Flutterwave (payment processing)</li>
            <li>Resend (transactional email)</li>
            <li>Meta WhatsApp Business API (WhatsApp messaging)</li>
            <li>AI model providers (Anthropic Claude, for assistant and OCR features)</li>
          </ul>
          <p>Each processor receives only the data necessary for its function.</p>
        </Section>

        <Section title="6. Cookies">
          <p>
            ClearFile uses strictly necessary cookies only: secure, httpOnly session cookies that keep
            you logged in. We do not use advertising or cross-site tracking cookies. Because we use
            only essential cookies, no consent banner is required.
          </p>
        </Section>

        <Section title="7. Security">
          <p>
            Passwords are hashed with bcrypt. Sessions use short-lived signed tokens in httpOnly,
            Secure cookies. All traffic is served over HTTPS. Financial records are scoped to your
            account — every read, update and delete is verified against your authenticated identity.
            Receipts are stored in private storage and are never publicly accessible.
          </p>
        </Section>

        <Section title="8. Retention & Deletion">
          <p>
            We retain your records while your account is active so your bookkeeping and tax history
            remains available to you. You may request deletion of your account and associated data by
            contacting us; we will delete your personal data except where retention is required for
            legal or accounting obligations.
          </p>
        </Section>

        <Section title="9. Your Rights (Nigeria Data Protection Act)">
          <p>
            Subject to the Nigeria Data Protection Act 2023, you have the right to access, correct,
            or delete your personal data, and to object to or restrict certain processing. To exercise
            these rights, contact us using the details below.
          </p>
          <p className="text-xs text-[#555]">
            Note: formal NDPA compliance positions (e.g. registration, DPIA requirements) should be
            confirmed with licensed Nigerian privacy counsel.
          </p>
        </Section>

        <Section title="10. Contact">
          <p>
            For privacy questions or data requests, email{' '}
            <span className="text-[#00C896]">support@clearfileng.com</span>.
          </p>
        </Section>
      </main>
      <footer className="border-t border-[#1E1E1E] py-6 text-center">
        <p className="text-xs text-[#555]">
          &copy; {new Date().getFullYear()} ClearFile NG · <Link to="/terms" className="hover:text-[#00C896]">Terms of Service</Link>
        </p>
      </footer>
    </div>
  );
}
