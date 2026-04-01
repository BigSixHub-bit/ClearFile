import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';
import { useAuth } from '../context/AuthContext';
import { toast } from 'sonner';
import { Check, Shield, Wallet, ArrowRight } from 'lucide-react';

export default function Onboarding() {
  const [step, setStep] = useState(1);
  const { user, updateSettings } = useAuth();
  const navigate = useNavigate();

  const completeOnboarding = async () => {
    try {
      await updateSettings({ onboarding_completed: true });
      toast.success('Welcome to NairaTrack!');
      navigate('/dashboard');
    } catch (error) {
      toast.error('Something went wrong');
    }
  };

  const steps = [
    {
      title: 'Welcome to NairaTrack!',
      subtitle: `Hi ${user?.name || 'there'}! We're excited to help you manage your taxes.`,
      content: (
        <div className="space-y-4">
          <div className="bg-[#E8F5E9] rounded-2xl p-6">
            <h3 className="font-semibold text-[#006400] mb-3 text-lg">What NairaTrack does:</h3>
            <ul className="space-y-3">
              {[
                'Track all your income and expenses automatically',
                'Calculate your taxes based on Nigerian law (PITA, CITA, VAT)',
                'Guide you through filing with FIRS',
                'Keep your financial records organized'
              ].map((item, i) => (
                <li key={i} className="flex items-start gap-3">
                  <div className="w-5 h-5 bg-[#006400] rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                    <Check className="w-3 h-3 text-white" />
                  </div>
                  <span className="text-slate-700">{item}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )
    },
    {
      title: 'Your Money Is Safe',
      subtitle: 'Understanding how bank linking works',
      content: (
        <div className="space-y-6">
          <div className="bg-gradient-to-br from-[#E8F5E9] to-[#C8E6C9] rounded-2xl p-6 border border-[#A5D6A7]">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-12 h-12 bg-[#006400] rounded-full flex items-center justify-center">
                <Shield className="w-6 h-6 text-white" />
              </div>
              <div>
                <h3 className="font-bold text-[#006400] text-lg">100% Read-Only Access</h3>
                <p className="text-sm text-[#004d00]">We can NEVER move your money</p>
              </div>
            </div>
            <p className="text-slate-700 mb-4">
              When you link your bank account, NairaTrack only reads your transaction history to help categorize expenses. 
              We use bank-level 256-bit encryption.
            </p>
            <div className="bg-white/60 rounded-xl p-4">
              <p className="text-sm text-slate-600 font-medium">
                You can unlink your bank at any time with one tap in Settings.
              </p>
            </div>
          </div>
        </div>
      )
    },
    {
      title: "You're All Set!",
      subtitle: 'Start tracking your finances',
      content: (
        <div className="space-y-6">
          <div className="bg-[#FFF8E1] rounded-2xl p-6 border border-[#FFE082]">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-12 h-12 bg-[#FFD700] rounded-full flex items-center justify-center">
                <Wallet className="w-6 h-6 text-[#422006]" />
              </div>
              <div>
                <h3 className="font-bold text-[#422006] text-lg">Quick Start Guide</h3>
                <p className="text-sm text-[#6D4C41]">Get started in 3 easy steps</p>
              </div>
            </div>
            <ol className="space-y-3">
              {[
                'Link your bank account (Growth/Business plans)',
                'Review and categorize your transactions',
                'Check your tax estimate on the dashboard'
              ].map((item, i) => (
                <li key={i} className="flex items-start gap-3">
                  <span className="w-6 h-6 bg-[#FFD700] text-[#422006] rounded-full flex items-center justify-center text-sm font-bold flex-shrink-0">
                    {i + 1}
                  </span>
                  <span className="text-slate-700">{item}</span>
                </li>
              ))}
            </ol>
          </div>
          <p className="text-center text-slate-500 text-sm">
            You're on the <span className="font-semibold text-[#006400] capitalize">{user?.subscription_plan || 'Starter'}</span> plan. 
            You can upgrade anytime in Settings.
          </p>
        </div>
      )
    }
  ];

  const currentStep = steps[step - 1];

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#E8F5E9] via-[#FAFAFA] to-[#FFF8E1] flex items-center justify-center p-4">
      <div className="w-full max-w-lg">
        {/* Progress */}
        <div className="flex items-center justify-center gap-2 mb-8">
          {steps.map((_, i) => (
            <div
              key={i}
              className={`h-2 rounded-full transition-all ${
                i + 1 <= step ? 'bg-[#006400] w-10' : 'bg-slate-200 w-6'
              }`}
            />
          ))}
        </div>

        <Card className="border-slate-200 shadow-xl rounded-2xl overflow-hidden">
          <CardContent className="p-8">
            <div className="text-center mb-6">
              <h1 className="text-2xl font-bold text-[#022c22] mb-2" style={{ fontFamily: 'Outfit' }}>
                {currentStep.title}
              </h1>
              <p className="text-slate-600">{currentStep.subtitle}</p>
            </div>

            {currentStep.content}

            <div className="flex gap-3 mt-8">
              {step > 1 && (
                <Button
                  variant="outline"
                  onClick={() => setStep(step - 1)}
                  className="flex-1 rounded-xl border-slate-200"
                  data-testid="onboarding-back-btn"
                >
                  Back
                </Button>
              )}
              <Button
                onClick={() => step < steps.length ? setStep(step + 1) : completeOnboarding()}
                className="flex-1 bg-[#006400] hover:bg-[#004d00] text-white rounded-xl"
                data-testid="onboarding-next-btn"
              >
                {step < steps.length ? (
                  <>Continue <ArrowRight className="w-4 h-4 ml-2" /></>
                ) : (
                  'Go to Dashboard'
                )}
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
