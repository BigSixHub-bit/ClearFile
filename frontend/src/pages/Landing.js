import React from 'react';
import { Link } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';
import { useLanguage } from '../context/LanguageContext';
import { Shield, TrendingUp, Calculator, FileText, Wallet, Bot, ChevronRight, Check, Lock, Award, Landmark } from 'lucide-react';

export default function Landing() {
  const { t } = useLanguage();

  const features = [
    { icon: Wallet, title: 'Bank Account Linking', desc: 'Connect your Nigerian bank accounts securely. Read-only access - we never touch your money.' },
    { icon: TrendingUp, title: 'AI Smart Categorizer', desc: 'AI automatically sorts your transactions into business vs personal, flagging tax-deductible expenses.' },
    { icon: Calculator, title: 'Nigerian Tax Calculator', desc: 'Accurate PITA, CITA, VAT at 7.5%, and WHT calculations based on Nigerian law.' },
    { icon: Landmark, title: 'State vs Federal Routing', desc: 'Auto-route your tax obligations to FIRS (federal) or your state revenue service.' },
    { icon: Award, title: 'TCC Tracker', desc: 'Track your Tax Clearance Certificate readiness and generate your TCC request letter.' },
    { icon: Bot, title: 'AI Tax Assistant', desc: 'Ask questions about Nigerian taxes and get instant, clear answers.' },
  ];

  const plans = [
    {
      name: 'Starter',
      price: '₦2,000',
      target: 'Freelancers / Simple Income',
      features: ['Manual income & expense tracking', 'Basic tax estimate & filing reminders', 'Receipt scanner (Up to 20/month)', 'Up to 100 transactions/month'],
      highlight: false
    },
    {
      name: 'Pro',
      price: '₦4,000',
      target: 'Power Users & Small Businesses',
      features: ['Everything in Starter', 'Unlimited bank account linking', 'Unlimited transactions & AI Auto-categorization', 'VAT & WHT tracking', 'Full AI Tax Assistant', '1-Click PDF/Excel tax report exports'],
      highlight: true
    }
  ];

  return (
    <div className="min-h-screen bg-[#FAFAFA]">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-white/80 backdrop-blur-xl border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-10 h-10 bg-[#006400] rounded-xl flex items-center justify-center">
              <span className="text-white font-bold text-lg">₦</span>
            </div>
            <span className="text-xl font-bold text-[#022c22]" style={{ fontFamily: 'Outfit' }}>ClearFile NG</span>
          </div>
          <div className="flex items-center gap-3">
            <Link to="/login">
              <Button variant="ghost" data-testid="login-btn" className="text-[#006400] hover:bg-[#E8F5E9]">
                {t('login')}
              </Button>
            </Link>
            <Link to="/register">
              <Button data-testid="register-btn" className="bg-[#006400] hover:bg-[#004d00] text-white rounded-xl">
                {t('getStarted')}
              </Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-[#E8F5E9] via-white to-[#FFF8E1] opacity-50"></div>
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 lg:py-32">
          <div className="text-center max-w-4xl mx-auto">
            <div className="inline-flex items-center gap-2 bg-[#E8F5E9] text-[#006400] px-4 py-2 rounded-full text-sm font-medium mb-6">
              <Lock className="w-4 h-4" />
              <span>Your money is always safe with us</span>
            </div>
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-[#022c22] tracking-tight mb-6" style={{ fontFamily: 'Outfit' }}>
              Nigerian Tax & Expense
              <span className="block text-[#006400]">Made Simple</span>
            </h1>
            <p className="text-lg sm:text-xl text-slate-600 mb-8 max-w-2xl mx-auto">
              Track spending, calculate taxes accurately using Nigerian law (PITA, CITA, VAT, WHT), and file with confidence. 
              Built for freelancers, SMEs, and registered businesses.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link to="/register">
                <Button data-testid="hero-cta-btn" size="lg" className="bg-[#006400] hover:bg-[#004d00] text-white rounded-xl px-8 py-6 text-lg w-full sm:w-auto">
                  {t('startTrial')}
                  <ChevronRight className="ml-2 w-5 h-5" />
                </Button>
              </Link>
            </div>
            <p className="text-sm text-slate-500 mt-4">No credit card required • 7-day free trial</p>
          </div>
        </div>
      </section>

      {/* Trust Badge */}
      <section className="py-8 bg-[#006400]">
        <div className="max-w-7xl mx-auto px-4 text-center">
          <div className="flex flex-wrap items-center justify-center gap-6 text-white">
            <div className="flex items-center gap-2">
              <Lock className="w-5 h-5 text-[#FFD700]" />
              <span>256-bit SSL Encryption</span>
            </div>
            <div className="h-4 w-px bg-white/30 hidden sm:block"></div>
            <div className="flex items-center gap-2">
              <Shield className="w-5 h-5 text-[#FFD700]" />
              <span>NDPR Compliant</span>
            </div>
            <div className="h-4 w-px bg-white/30 hidden sm:block"></div>
            <div className="flex items-center gap-2">
              <Check className="w-5 h-5 text-[#FFD700]" />
              <span>Read-Only Bank Access</span>
            </div>
            <div className="h-4 w-px bg-white/30 hidden sm:block"></div>
            <div className="flex items-center gap-2 text-white/70">
              <span className="text-xs">Secured by: Mono | Okra | Stitch</span>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold text-[#022c22] mb-4" style={{ fontFamily: 'Outfit' }}>
              Everything You Need to Manage Nigerian Taxes
            </h2>
            <p className="text-lg text-slate-600 max-w-2xl mx-auto">
              From automatic transaction tracking to accurate tax calculations — all in one place.
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((feature, idx) => (
              <Card key={idx} className="border border-slate-200 hover-lift rounded-2xl" data-testid={`feature-card-${idx}`}>
                <CardContent className="p-6">
                  <div className="w-12 h-12 bg-[#E8F5E9] rounded-xl flex items-center justify-center mb-4">
                    <feature.icon className="w-6 h-6 text-[#006400]" />
                  </div>
                  <h3 className="text-lg font-semibold text-[#022c22] mb-2" style={{ fontFamily: 'Outfit' }}>{feature.title}</h3>
                  <p className="text-slate-600">{feature.desc}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section className="py-20 bg-[#FAFAFA]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold text-[#022c22] mb-4" style={{ fontFamily: 'Outfit' }}>
              Simple, Transparent Pricing
            </h2>
            <p className="text-lg text-slate-600">Choose the plan that fits your business</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl mx-auto">
            {plans.map((plan, idx) => (
              <Card 
                key={idx} 
                className={`rounded-2xl ${plan.highlight ? 'border-2 border-[#006400] shadow-lg shadow-[#006400]/10' : 'border border-slate-200'}`}
                data-testid={`plan-card-${plan.name.toLowerCase()}`}
              >
                <CardContent className="p-8">
                  {plan.highlight && (
                    <div className="bg-[#FFD700] text-[#422006] text-xs font-bold px-3 py-1 rounded-full inline-block mb-4">
                      MOST POPULAR
                    </div>
                  )}
                  <h3 className="text-xl font-bold text-[#022c22] mb-1" style={{ fontFamily: 'Outfit' }}>{plan.name}</h3>
                  <p className="text-sm text-slate-500 mb-4">{plan.target}</p>
                  <div className="flex items-baseline gap-1 mb-6">
                    <span className="text-4xl font-bold text-[#006400]">{plan.price}</span>
                    <span className="text-slate-500">/month</span>
                  </div>
                  <ul className="space-y-3 mb-8">
                    {plan.features.map((f, i) => (
                      <li key={i} className="flex items-start gap-2">
                        <Check className="w-5 h-5 text-[#006400] flex-shrink-0 mt-0.5" />
                        <span className="text-slate-600 text-sm">{f}</span>
                      </li>
                    ))}
                  </ul>
                  <Link to="/register">
                    <Button 
                      className={`w-full rounded-xl py-5 ${plan.highlight ? 'bg-[#006400] hover:bg-[#004d00] text-white' : 'bg-[#E8F5E9] hover:bg-[#C8E6C9] text-[#006400]'}`}
                      data-testid={`select-plan-${plan.name.toLowerCase()}`}
                    >
                      Get Started
                    </Button>
                  </Link>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Banks Supported */}
      <section className="py-16 bg-white">
        <div className="max-w-7xl mx-auto px-4 text-center">
          <h3 className="text-lg font-medium text-slate-500 mb-8">Supports All Major Nigerian Banks</h3>
          <div className="flex flex-wrap justify-center gap-8 text-slate-400">
            {['GTBank', 'Access Bank', 'Zenith', 'First Bank', 'UBA', 'Kuda', 'Opay', 'Moniepoint'].map((bank, i) => (
              <span key={i} className="font-medium">{bank}</span>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 bg-[#022c22] text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row justify-between items-center gap-6">
            <div className="flex items-center gap-2">
              <div className="w-10 h-10 bg-[#006400] rounded-xl flex items-center justify-center">
                <span className="text-white font-bold text-lg">₦</span>
              </div>
              <span className="text-xl font-bold" style={{ fontFamily: 'Outfit' }}>ClearFile NG</span>
            </div>
            <p className="text-slate-400 text-sm">© 2024 ClearFile NG. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
