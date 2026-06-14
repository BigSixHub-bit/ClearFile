import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { toast } from 'sonner';
import { Check, Shield, Wallet, ArrowRight, MapPin, Lock, ArrowLeft } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

export default function Onboarding() {
  const [step, setStep] = useState(1);
  const [selectedState, setSelectedState] = useState('lagos');
  const [states, setStates] = useState([]);
  const { user, updateSettings } = useAuth();
  const navigate = useNavigate();

  useEffect(() => { fetchStates(); }, []);
  const fetchStates = async () => { try { const { data } = await axios.get(`${API}/api/states`, { withCredentials: true }); setStates(data.states || []); } catch (e) {} };

  const completeOnboarding = async () => {
    try {
      await axios.put(`${API}/api/user/state`, { state_of_residence: selectedState }, { withCredentials: true });
      await updateSettings({ onboarding_completed: true });
      toast.success('Welcome to ClearFile NG!');
      navigate('/dashboard');
    } catch (error) { toast.error('Something went wrong'); }
  };

  const steps = [
    {
      title: 'Welcome to ClearFile NG',
      subtitle: `Let's set up your financial command center, ${user?.name?.split(' ')[0] || 'there'}.`,
      content: (
        <div className="space-y-3">
          {['Auto-categorize transactions with AI', 'Calculate taxes (PITA, CITA, VAT)', 'Route obligations to FIRS or state revenue', 'Track TCC readiness', 'AI assistant for tax questions'].map((item, i) => (
            <div key={i} className="flex items-start gap-3 p-3 rounded-xl bg-[#111111] border border-[#1E1E1E]">
              <div className="w-5 h-5 rounded-full bg-[#00C896] flex items-center justify-center flex-shrink-0 mt-0.5">
                <Check className="w-3 h-3 text-black" />
              </div>
              <span className="text-sm text-[#A1A1AA]">{item}</span>
            </div>
          ))}
        </div>
      )
    },
    {
      title: 'Select Your State',
      subtitle: 'We need this to route PAYE and state taxes correctly.',
      content: (
        <div className="space-y-4">
          <div className="p-4 rounded-xl bg-[#111111] border border-[#1E1E1E]">
            <div className="flex items-center gap-2 mb-3">
              <MapPin className="w-4 h-4 text-[#00C896]" />
              <span className="text-sm font-medium text-white">State of Residence</span>
            </div>
            <select value={selectedState} onChange={e => setSelectedState(e.target.value)}
              className="w-full bg-[#0A0A0A] border border-[#1E1E1E] rounded-xl px-4 py-3 text-white text-sm focus:outline-none focus:border-[#00C896]/50"
              data-testid="onboarding-state-select"
            >
              {states.map(s => <option key={s.id} value={s.id}>{s.name} ({s.service})</option>)}
            </select>
          </div>
        </div>
      )
    },
    {
      title: 'Your Data Is Secure',
      subtitle: 'Bank-grade encryption for your finances.',
      content: (
        <div className="space-y-4">
          <div className="p-5 rounded-xl bg-[#111111] border border-[#1E1E1E] text-center">
            <Shield className="w-10 h-10 text-[#00C896] mx-auto mb-3" />
            <p className="text-white font-medium mb-2">100% Read-Only Access</p>
            <p className="text-sm text-[#A1A1AA]">We never store your bank password. Secured by 256-bit encryption.</p>
            <div className="flex items-center justify-center gap-4 mt-4 text-xs text-[#555]">
              <span className="flex items-center gap-1"><Lock className="w-3 h-3" /> SSL</span>
              <span className="flex items-center gap-1"><Shield className="w-3 h-3" /> NDPR</span>
              <span className="flex items-center gap-1"><Check className="w-3 h-3" /> Read-Only</span>
            </div>
          </div>
        </div>
      )
    },
    {
      title: "You're All Set",
      subtitle: 'Start tracking your finances.',
      content: (
        <div className="space-y-3">
          {['Link your bank account (Pro plan)', 'Review and categorize transactions', 'Check your TCC progress and tax estimate'].map((item, i) => (
            <div key={i} className="flex items-start gap-3 p-3 rounded-xl bg-[#111111] border border-[#1E1E1E]">
              <span className="w-6 h-6 rounded-full bg-[#00C896] text-black flex items-center justify-center text-xs font-bold flex-shrink-0">{i + 1}</span>
              <span className="text-sm text-[#A1A1AA]">{item}</span>
            </div>
          ))}
        </div>
      )
    }
  ];

  const current = steps[step - 1];

  return (
    <div className="min-h-screen bg-[#050505] flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Progress */}
        <div className="flex items-center justify-center gap-2 mb-8">
          {steps.map((_, i) => (
            <div key={i} className={`h-1 rounded-full transition-all ${i + 1 <= step ? 'bg-[#00C896] w-10' : 'bg-[#1E1E1E] w-6'}`} />
          ))}
        </div>

        <div className="card-dark p-8 animate-fade-in">
          <div className="text-center mb-6">
            <h1 className="text-xl font-display font-semibold text-white mb-1">{current.title}</h1>
            <p className="text-sm text-[#A1A1AA]">{current.subtitle}</p>
          </div>
          {current.content}
          <div className="flex gap-3 mt-6">
            {step > 1 && (
              <button onClick={() => setStep(step - 1)} className="flex-1 btn-ghost py-3 text-sm flex items-center justify-center gap-2" data-testid="onboarding-back-btn">
                <ArrowLeft className="w-4 h-4" /> Back
              </button>
            )}
            <button
              onClick={() => step < steps.length ? setStep(step + 1) : completeOnboarding()}
              className="flex-1 btn-primary py-3 text-sm flex items-center justify-center gap-2"
              data-testid="onboarding-next-btn"
            >
              {step < steps.length ? <>Continue <ArrowRight className="w-4 h-4" /></> : 'Launch Dashboard'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
