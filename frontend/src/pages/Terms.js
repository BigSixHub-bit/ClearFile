import { Link } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';

const Section = ({ title, children }) => (
  <section className="mb-8">
    <h2 className="text-lg font-semibold text-white mb-3">{title}</h2>
    <div className="text-sm text-[#A1A1AA] leading-relaxed space-y-3">{children}</div>
  </section>
);

export default function Terms() {
  return (
    <div className="min-h-screen bg-[#0A0A0A]" data-testid="terms-page">
      <header className="border-b border-[#1E1E1E] px-4 py-4">
        <div className="max-w-3xl mx-auto flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2" data-testid="terms-home-link">
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
        <h1 className="text-3xl sm:text-4xl font-bold text-white mb-2">Terms of Service</h1>
        <p className="text-xs text-[#555] mb-10">Last updated: June 2026</p>

        <Section title="1. The Service">
          <p>
            ClearFile NG provides bookkeeping, expense tracking, invoicing, bank-transaction syncing,
            tax estimation tools and related features for Nigerian freelancers, MSMEs and companies.
            By creating an account you agree to these terms.
          </p>
        </Section>

        <Section title="2. Important: Not Tax or Legal Advice">
          <p className="text-white">
            ClearFile is a software tool, not a licensed tax adviser, accountant or law firm.
          </p>
          <p>
            Tax calculations, estimates, guides and AI-generated responses are provided for general
            information only and may not reflect your exact circumstances or the latest regulations.
            You should verify figures and, where necessary, consult a certified tax professional
            before filing. Experts matched through our platform are independent professionals and
            contract with you directly.
          </p>
        </Section>

        <Section title="3. Your Account & Responsibilities">
          <ul className="list-disc pl-5 space-y-1">
            <li>You must provide accurate information and keep your password confidential.</li>
            <li>You are responsible for the accuracy of the financial data you enter or import.</li>
            <li>You are responsible for your own tax filings and payments to the relevant authorities.</li>
            <li>You must be at least 18 years old and legally able to enter this agreement.</li>
          </ul>
        </Section>

        <Section title="4. Acceptable Use">
          <p>You agree not to:</p>
          <ul className="list-disc pl-5 space-y-1">
            <li>access or attempt to access another user's data;</li>
            <li>abuse, overload or attempt to disrupt the service, including AI features;</li>
            <li>upload malicious files or unlawful content;</li>
            <li>use the service for fraud, money laundering or any illegal purpose.</li>
          </ul>
        </Section>

        <Section title="5. Subscriptions & Payments">
          <p>
            ClearFile offers paid plans (e.g. Starter ₦2,000/month, Pro ₦4,000/month) and one-time
            purchases (e.g. the AI Tax Filing Guide). Payments are processed by Flutterwave. Plan
            upgrades take effect on successful payment. You may cancel or downgrade at any time;
            access to paid features continues to the end of the paid period. Fees already paid are
            non-refundable except where required by law.
          </p>
        </Section>

        <Section title="6. Bank Connections">
          <p>
            Bank linking is provided through Mono. By connecting an account you authorise ClearFile
            to receive the transaction and balance data needed for bookkeeping. You can disconnect a
            linked account at any time from the app.
          </p>
        </Section>

        <Section title="7. Intellectual Property">
          <p>
            ClearFile NG, its logo, design and software remain our property. Your data remains yours —
            we only process it to provide the service as described in our{' '}
            <Link to="/privacy" className="text-[#00C896] hover:underline">Privacy Policy</Link>.
          </p>
        </Section>

        <Section title="8. Availability & Limitation of Liability">
          <p>
            We aim for high availability but the service is provided "as is" without warranty of
            uninterrupted operation. To the maximum extent permitted by Nigerian law, ClearFile is not
            liable for indirect or consequential losses, including penalties, interest or assessments
            arising from reliance on estimates produced by the software. Our total liability is
            limited to the fees you paid in the 12 months preceding the claim.
          </p>
        </Section>

        <Section title="9. Termination">
          <p>
            You may close your account at any time. We may suspend or terminate accounts that violate
            these terms or present a security risk, with notice where practicable.
          </p>
        </Section>

        <Section title="10. Changes & Contact">
          <p>
            We may update these terms; material changes will be communicated in-app or by email.
            Questions? Contact <span className="text-[#00C896]">support@clearfileng.com</span>.
          </p>
        </Section>
      </main>
      <footer className="border-t border-[#1E1E1E] py-6 text-center">
        <p className="text-xs text-[#555]">
          &copy; {new Date().getFullYear()} ClearFile NG · <Link to="/privacy" className="hover:text-[#00C896]">Privacy Policy</Link>
        </p>
      </footer>
    </div>
  );
}
