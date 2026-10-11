import React from 'react';
import { Link } from 'react-router-dom';
import { useLanguage } from '../context/LanguageContext';
import { Shield, TrendingUp, Calculator, Wallet, Bot, Check, Lock, Award, Landmark, ArrowRight, Zap, Activity } from 'lucide-react';

export default function Landing() {
  const { t } = useLanguage();

  const features = [
    { icon: Wallet, title: 'Open Banking', desc: 'Connect Nigerian bank accounts securely. Read-only access — we never touch your money.', color: '#3B82F6' },
    { icon: Zap, title: 'AI Categorizer', desc: 'AI separates business from personal spending. Tax-deductible expenses flagged automatically.', color: '#00C896' },
    { icon: Calculator, title: 'Tax Engine', desc: 'Accurate NTA 2025, VAT at 7.5%, and WHT calculations powered by Nigerian tax law.', color: '#F59E0B' },
    { icon: Landmark, title: 'State vs Federal', desc: 'Auto-route obligations to NRS or your state revenue service. Never mix them again.', color: '#8B5CF6' },
    { icon: Award, title: 'TCC Tracker', desc: 'Track Tax Clearance Certificate readiness. Generate your application pack with one click.', color: '#EC4899' },
    { icon: Bot, title: 'AI Assistant', desc: 'Ask anything about Nigerian taxes. Get instant, clear, actionable answers.', color: '#00C896' },
  ];

  const plans = [
    {
      name: 'Starter', price: '₦2,000', target: 'Freelancers / Simple Income',
      features: ['Manual income & expense tracking', 'Basic tax estimate & filing reminders', 'Receipt scanner (Up to 20/month)', 'Up to 100 transactions/month'],
      highlight: false
    },
    {
      name: 'Pro', price: '₦4,000', target: 'Power Users & Small Businesses',
      features: ['Everything in Starter', 'Unlimited bank linking & AI categorization', 'VAT & WHT tracking', 'Full AI Tax Assistant', '1-Click PDF/Excel exports'],
      highlight: true
    }
  ];

  return (
    <div className="min-h-screen bg-[#050505]">
      {/* Nav */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-[#050505]/80 backdrop-blur-xl border-b border-[#1E1E1E]">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#00C896] to-[#3B82F6] flex items-center justify-center">
              <span className="text-black font-bold text-sm">C</span>
            </div>
            <span className="font-display font-semibold text-white">ClearFile NG</span>
          </div>
          <div className="flex items-center gap-3">
            <Link to="/login"><button className="text-sm text-[#A1A1AA] hover:text-white transition-colors px-3 py-2" data-testid="nav-login">Sign In</button></Link>
            <Link to="/register"><button className="btn-primary text-sm px-4 py-2" data-testid="nav-register">Get Started</button></Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="pt-32 pb-20 px-4 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-[#00C896]/5 via-transparent to-transparent"></div>
        <div className="max-w-4xl mx-auto text-center relative z-10">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-[#1E1E1E] bg-[#111111] text-xs text-[#A1A1AA] mb-6 animate-fade-in">
            <Activity className="w-3 h-3 text-[#00C896]" />
            AI-Powered Financial Infrastructure for Africa
          </div>
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-display font-semibold text-white leading-[1.1] tracking-tight mb-6 animate-fade-in stagger-1">
            The financial OS<br />
            <span className="gradient-text">for Nigerian businesses</span>
          </h1>
          <p className="text-base sm:text-lg text-[#A1A1AA] max-w-xl mx-auto mb-8 leading-relaxed animate-fade-in stagger-2">
            Auto-categorize transactions, calculate taxes, route obligations to the right authority, and file with confidence.
          </p>
          <div className="flex items-center justify-center gap-3 animate-fade-in stagger-3">
            <Link to="/register">
              <button className="btn-primary px-6 py-3 text-sm flex items-center gap-2" data-testid="hero-cta">
                Start Free <ArrowRight className="w-4 h-4" />
              </button>
            </Link>
            <Link to="/login">
              <button className="btn-ghost px-6 py-3 text-sm">Sign In</button>
            </Link>
          </div>
        </div>
      </section>

      {/* Trust Strip */}
      <div className="border-y border-[#1E1E1E] py-4">
        <div className="max-w-6xl mx-auto px-4 flex items-center justify-center gap-8 text-xs text-[#333]">
          <div className="flex items-center gap-1.5"><Lock className="w-3 h-3" /> 256-bit SSL</div>
          <div className="flex items-center gap-1.5"><Shield className="w-3 h-3" /> NDPR Compliant</div>
          <div className="flex items-center gap-1.5"><Check className="w-3 h-3" /> Read-Only Access</div>
          <div className="hidden sm:flex items-center gap-1.5 text-[#A1A1AA]">Mono &middot; Okra &middot; Stitch</div>
        </div>
      </div>

      {/* Features */}
      <section className="py-20 px-4">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-14">
            <h2 className="text-2xl sm:text-3xl font-display font-semibold text-white mb-3">Built for African businesses</h2>
            <p className="text-[#A1A1AA] text-sm max-w-md mx-auto">Everything you need to manage finances, stay compliant, and grow — in one platform.</p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {features.map((f, i) => (
              <div key={i} className="card-dark p-6 hover-lift animate-fade-in" style={{ animationDelay: `${i * 0.05}s` }} data-testid={`feature-${i}`}>
                <div className="w-10 h-10 rounded-xl flex items-center justify-center mb-4" style={{ backgroundColor: `${f.color}15` }}>
                  <f.icon className="w-5 h-5" style={{ color: f.color }} />
                </div>
                <h3 className="font-display font-semibold text-white mb-2">{f.title}</h3>
                <p className="text-sm text-[#A1A1AA] leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section className="py-20 px-4 border-t border-[#1E1E1E]">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-14">
            <h2 className="text-2xl sm:text-3xl font-display font-semibold text-white mb-3">Simple pricing</h2>
            <p className="text-[#A1A1AA] text-sm">No hidden fees. Cancel anytime.</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {plans.map((plan, i) => (
              <div key={i} className={`card-dark p-7 ${plan.highlight ? 'border-[#00C896]/30 glow-accent' : ''}`} data-testid={`plan-${plan.name.toLowerCase()}`}>
                {plan.highlight && (
                  <span className="inline-block text-[10px] font-bold uppercase tracking-wider text-black bg-[#00C896] px-2.5 py-1 rounded-md mb-4">Most Popular</span>
                )}
                <h3 className="font-display font-semibold text-white text-lg">{plan.name}</h3>
                <p className="text-xs text-[#A1A1AA] mt-0.5 mb-4">{plan.target}</p>
                <div className="flex items-baseline gap-1 mb-6">
                  <span className="text-3xl font-display font-semibold text-white tabular-nums">{plan.price}</span>
                  <span className="text-sm text-[#A1A1AA]">/month</span>
                </div>
                <ul className="space-y-2.5 mb-6">
                  {plan.features.map((f, j) => (
                    <li key={j} className="flex items-start gap-2.5 text-sm text-[#A1A1AA]">
                      <Check className="w-4 h-4 text-[#00C896] flex-shrink-0 mt-0.5" />
                      {f}
                    </li>
                  ))}
                </ul>
                <Link to="/register">
                  <button className={`w-full py-3 rounded-xl text-sm font-medium transition-all ${
                    plan.highlight ? 'btn-primary' : 'btn-ghost'
                  }`} data-testid={`select-${plan.name.toLowerCase()}`}>
                    Get Started
                  </button>
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-[#1E1E1E] py-8 px-4">
        <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-md bg-gradient-to-br from-[#00C896] to-[#3B82F6] flex items-center justify-center">
              <span className="text-black font-bold text-[10px]">C</span>
            </div>
            <span className="text-sm text-[#A1A1AA]">ClearFile NG</span>
          </div>
          <div className="flex items-center gap-4">
            <Link to="/privacy" data-testid="footer-privacy-link" className="text-xs text-[#A1A1AA] hover:text-[#00C896] transition-colors">Privacy Policy</Link>
            <Link to="/terms" data-testid="footer-terms-link" className="text-xs text-[#A1A1AA] hover:text-[#00C896] transition-colors">Terms of Service</Link>
          </div>
          <p className="text-xs text-[#333]">&copy; {new Date().getFullYear()} ClearFile NG. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}
