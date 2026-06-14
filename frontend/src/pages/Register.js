import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { toast } from 'sonner';
import { ArrowRight, Lock } from 'lucide-react';

export default function Register() {
  const [form, setForm] = useState({ email: '', password: '', name: '', business_type: 'freelancer', monthly_income_range: '0-100000' });
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();
  const { t } = useLanguage();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (form.password.length < 6) { toast.error('Password must be at least 6 characters'); return; }
    setLoading(true);
    try {
      await register(form);
      toast.success('Account created!');
      navigate('/onboarding');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Registration failed');
    } finally { setLoading(false); }
  };

  const bizTypes = [
    { value: 'freelancer', label: 'Freelancer' },
    { value: 'sme', label: 'Small Business' },
    { value: 'company', label: 'Company (LLC)' },
    { value: 'salary_earner', label: 'Salary Earner' },
  ];

  return (
    <div className="min-h-screen bg-[#050505] flex items-center justify-center p-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8 animate-fade-in">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#00C896] to-[#3B82F6] flex items-center justify-center mx-auto mb-4">
            <span className="text-black font-bold">C</span>
          </div>
          <h1 className="text-2xl font-display font-semibold text-white">Create your account</h1>
          <p className="text-sm text-[#A1A1AA] mt-1">Start managing your finances</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-3.5 animate-fade-in stagger-2" data-testid="register-form">
          <div>
            <label className="text-xs text-[#A1A1AA] font-medium uppercase tracking-wider mb-1.5 block">Full Name</label>
            <input type="text" value={form.name} onChange={e => setForm({...form, name: e.target.value})} required
              className="w-full bg-[#111111] border border-[#1E1E1E] rounded-xl px-4 py-3 text-white text-sm placeholder-[#333] focus:outline-none focus:border-[#00C896]/50 transition-colors"
              placeholder="John Doe" data-testid="register-name" />
          </div>
          <div>
            <label className="text-xs text-[#A1A1AA] font-medium uppercase tracking-wider mb-1.5 block">Email</label>
            <input type="email" value={form.email} onChange={e => setForm({...form, email: e.target.value})} required
              className="w-full bg-[#111111] border border-[#1E1E1E] rounded-xl px-4 py-3 text-white text-sm placeholder-[#333] focus:outline-none focus:border-[#00C896]/50 transition-colors"
              placeholder="you@company.com" data-testid="register-email" />
          </div>
          <div>
            <label className="text-xs text-[#A1A1AA] font-medium uppercase tracking-wider mb-1.5 block">Password</label>
            <input type="password" value={form.password} onChange={e => setForm({...form, password: e.target.value})} required
              className="w-full bg-[#111111] border border-[#1E1E1E] rounded-xl px-4 py-3 text-white text-sm placeholder-[#333] focus:outline-none focus:border-[#00C896]/50 transition-colors"
              placeholder="Min 6 characters" data-testid="register-password" />
          </div>
          <div>
            <label className="text-xs text-[#A1A1AA] font-medium uppercase tracking-wider mb-1.5 block">Business Type</label>
            <div className="grid grid-cols-2 gap-2">
              {bizTypes.map(bt => (
                <button key={bt.value} type="button" onClick={() => setForm({...form, business_type: bt.value})}
                  className={`px-3 py-2.5 rounded-xl text-xs font-medium border transition-all ${
                    form.business_type === bt.value
                      ? 'border-[#00C896] bg-[#00C896]/10 text-[#00C896]'
                      : 'border-[#1E1E1E] bg-[#111111] text-[#A1A1AA] hover:border-[#333]'
                  }`} data-testid={`biz-type-${bt.value}`}
                >{bt.label}</button>
              ))}
            </div>
          </div>
          <button type="submit" disabled={loading}
            className="w-full btn-primary py-3 text-sm flex items-center justify-center gap-2 mt-2"
            data-testid="register-submit"
          >
            {loading ? <span className="w-4 h-4 border-2 border-black/30 border-t-black rounded-full animate-spin"></span> : <>Get Started <ArrowRight className="w-4 h-4" /></>}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-[#A1A1AA] animate-fade-in stagger-3">
          Already have an account? <Link to="/login" className="text-[#00C896] hover:underline font-medium">Sign in</Link>
        </p>
        <div className="flex items-center justify-center gap-1.5 mt-6 text-[10px] text-[#333]">
          <Lock className="w-3 h-3" /> 256-bit encrypted
        </div>
      </div>
    </div>
  );
}
