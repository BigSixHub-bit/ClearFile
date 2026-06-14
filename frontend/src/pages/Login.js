import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { toast } from 'sonner';
import { ArrowRight, Lock } from 'lucide-react';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const user = await login(email, password);
      toast.success('Welcome back');
      navigate(user.onboarding_completed ? '/dashboard' : '/onboarding');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Invalid credentials');
    } finally { setLoading(false); }
  };

  return (
    <div className="min-h-screen bg-[#050505] flex items-center justify-center p-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8 animate-fade-in">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#00C896] to-[#3B82F6] flex items-center justify-center mx-auto mb-4">
            <span className="text-black font-bold">C</span>
          </div>
          <h1 className="text-2xl font-display font-semibold text-white">Welcome back</h1>
          <p className="text-sm text-[#A1A1AA] mt-1">Sign in to ClearFile NG</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4 animate-fade-in stagger-2" data-testid="login-form">
          <div>
            <label className="text-xs text-[#A1A1AA] font-medium uppercase tracking-wider mb-1.5 block">Email</label>
            <input
              type="email" value={email} onChange={e => setEmail(e.target.value)} required
              className="w-full bg-[#111111] border border-[#1E1E1E] rounded-xl px-4 py-3 text-white text-sm placeholder-[#333] focus:outline-none focus:border-[#00C896]/50 transition-colors"
              placeholder="you@company.com"
              data-testid="login-email"
            />
          </div>
          <div>
            <label className="text-xs text-[#A1A1AA] font-medium uppercase tracking-wider mb-1.5 block">Password</label>
            <input
              type="password" value={password} onChange={e => setPassword(e.target.value)} required
              className="w-full bg-[#111111] border border-[#1E1E1E] rounded-xl px-4 py-3 text-white text-sm placeholder-[#333] focus:outline-none focus:border-[#00C896]/50 transition-colors"
              placeholder="Enter password"
              data-testid="login-password"
            />
          </div>
          <button
            type="submit" disabled={loading}
            className="w-full btn-primary py-3 text-sm flex items-center justify-center gap-2"
            data-testid="login-submit"
          >
            {loading ? <span className="w-4 h-4 border-2 border-black/30 border-t-black rounded-full animate-spin"></span> : <>Sign In <ArrowRight className="w-4 h-4" /></>}
          </button>
        </form>

        <div className="mt-6 text-center space-y-2 animate-fade-in stagger-3">
          <Link to="/forgot-password" className="text-xs text-[#A1A1AA] hover:text-[#00C896] transition-colors">Forgot password?</Link>
          <p className="text-sm text-[#A1A1AA]">
            No account? <Link to="/register" className="text-[#00C896] hover:underline font-medium">Create one</Link>
          </p>
        </div>

        <div className="flex items-center justify-center gap-1.5 mt-8 text-[10px] text-[#333]">
          <Lock className="w-3 h-3" /> 256-bit encrypted
        </div>
      </div>
    </div>
  );
}
