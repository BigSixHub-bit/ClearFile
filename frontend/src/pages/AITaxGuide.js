import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import Layout from '../components/Layout';
import { Card, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { useAuth } from '../context/AuthContext';
import { toast } from 'sonner';
import { 
  ArrowLeft, ArrowRight, ExternalLink, Bot, CheckCircle, 
  Lightbulb, ClipboardList, Sparkles, Loader2
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

export default function AITaxGuide() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [stepData, setStepData] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [completedSteps, setCompletedSteps] = useState(new Set());
  const [unlocked, setUnlocked] = useState(false);
  const [checkingAccess, setCheckingAccess] = useState(true);

  const totalSteps = 6;

  useEffect(() => {
    checkAccess();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (unlocked) fetchStep(step);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [step, unlocked]);

  const checkAccess = async () => {
    try {
      // Handle Flutterwave redirect callback
      const params = new URLSearchParams(window.location.search);
      const status = params.get('status');
      const transactionId = params.get('transaction_id');
      const txRef = params.get('tx_ref');

      if (status === 'successful' && transactionId) {
        try {
          const { data: verifyData } = await axios.get(
            `${API}/api/payments/ai-guide/verify?transaction_id=${transactionId}&tx_ref=${txRef}`,
            { withCredentials: true }
          );
          if (verifyData.status === 'success' || verifyData.unlocked) {
            setUnlocked(true);
            toast.success('AI Guide unlocked successfully!');
            window.history.replaceState({}, '', '/ai-tax-guide');
            setCheckingAccess(false);
            return;
          }
        } catch (err) {
          toast.error('Payment verification failed');
        }
        window.history.replaceState({}, '', '/ai-tax-guide');
      }

      const { data } = await axios.get(`${API}/api/payments/ai-guide/status`, { withCredentials: true });
      setUnlocked(data.unlocked);
    } catch (e) {
      // silent
    } finally {
      setCheckingAccess(false);
    }
  };

  const handleUnlock = async () => {
    try {
      const { data } = await axios.post(`${API}/api/payments/ai-guide/initialize`, {
        callback_url: `${window.location.origin}/payment-success`
      }, { withCredentials: true });

      if (data.already_unlocked || data.unlocked || data.mock) {
        setUnlocked(true);
        toast.success('AI Guide unlocked!');
        return;
      }
      if (data.payment_link) {
        window.location.href = data.payment_link;
      }
    } catch (e) {
      toast.error('Payment failed. Try again.');
    }
  };

  const fetchStep = async (s) => {
    setLoading(true);
    try {
      const { data } = await axios.post(`${API}/api/tax-guide/ai-walkthrough`, {
        step: s,
        session_id: sessionId
      }, { withCredentials: true });
      setStepData(data);
      if (!sessionId) setSessionId(data.session_id);
    } catch (error) {
      toast.error('Failed to load guide step');
    } finally {
      setLoading(false);
    }
  };

  const markComplete = () => {
    setCompletedSteps(prev => new Set([...prev, step]));
    if (step < totalSteps) {
      setStep(step + 1);
    } else {
      toast.success('All steps complete! You\'re ready to file.');
    }
  };

  const formatCurrency = (v) =>
    new Intl.NumberFormat('en-NG', { style: 'currency', currency: 'NGN', minimumFractionDigits: 0 })
      .format(v).replace('NGN', 'N');

  const stepIcons = ['1', '2', '3', '4', '5', '6'];

  return (
    <Layout>
      <div className="space-y-6 pb-20 lg:pb-0">
        {/* Header */}
        <div className="flex items-center gap-3">
          <button onClick={() => navigate('/tax-calculator')} className="btn-ghost p-2 rounded-xl" data-testid="guide-back-btn">
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-2xl font-display font-semibold text-white">AI Tax Filing Guide</h1>
            <p className="text-[#A1A1AA] text-sm">Step-by-step NRS walkthrough with your data</p>
          </div>
        </div>

        {/* Payment Gate */}
        {checkingAccess ? (
          <div className="flex items-center justify-center h-48"><Loader2 className="w-8 h-8 animate-spin text-[#00C896]" /></div>
        ) : !unlocked ? (
          <div className="card-dark p-8 text-center animate-fade-in">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-[#00C896] to-[#3B82F6] flex items-center justify-center mx-auto mb-4">
              <Bot className="w-8 h-8 text-black" />
            </div>
            <h2 className="text-xl font-display font-semibold text-white mb-2">Unlock AI Tax Guide</h2>
            <p className="text-[#A1A1AA] text-sm mb-1 max-w-sm mx-auto">
              Let ClearFile AI walk you step-by-step through the NRS portal using your exact financial data.
            </p>
            <p className="text-2xl font-display font-semibold text-white mb-6 mt-4">₦70,000</p>
            <button onClick={handleUnlock} className="btn-primary px-8 py-3 text-sm inline-flex items-center gap-2" data-testid="unlock-ai-guide-btn">
              <Sparkles className="w-4 h-4" /> Unlock AI Guide
            </button>
            <p className="text-xs text-[#555] mt-4">One-time payment. Includes personalized AI advice for each step.</p>
          </div>
        ) : (
          <>

        {/* Progress Stepper */}
        <div className="flex items-center justify-between gap-1 px-2">
          {[1, 2, 3, 4, 5, 6].map(s => (
            <button
              key={s}
              onClick={() => setStep(s)}
              className={`flex-1 flex flex-col items-center gap-1 transition-all ${step === s ? 'scale-105' : ''}`}
              data-testid={`step-indicator-${s}`}
            >
              <div className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold transition-all ${
                completedSteps.has(s)
                  ? 'bg-[#00C896] text-white'
                  : step === s
                  ? 'bg-gradient-to-br from-[#FFD700] to-[#D4A017] text-white  shadow-[#FFD700]/30'
                  : 'bg-slate-100 text-[#555]'
              }`}>
                {completedSteps.has(s) ? <CheckCircle className="w-5 h-5" /> : s}
              </div>
              <div className={`h-1 w-full rounded-full ${
                completedSteps.has(s) ? 'bg-[#00C896]' : step === s ? 'bg-[#F59E0B]' : 'bg-slate-200'
              }`} />
            </button>
          ))}
        </div>

        {/* Your Tax Summary Bar */}
        {stepData?.user_summary && (
          <div className="flex items-center gap-4 px-4 py-3 bg-[#00C896] text-white rounded-2xl text-sm overflow-x-auto">
            <span className="whitespace-nowrap">
              <span className="text-[#A5D6A7]">Income:</span> {formatCurrency(stepData.user_summary.gross_income)}
            </span>
            <span className="text-white/30">|</span>
            <span className="whitespace-nowrap">
              <span className="text-[#A5D6A7]">Tax:</span> {formatCurrency(stepData.user_summary.total_tax)}
            </span>
            <span className="text-white/30">|</span>
            <span className="whitespace-nowrap capitalize">
              <span className="text-[#A5D6A7]">Type:</span> {stepData.user_summary.tax_type}
            </span>
          </div>
        )}

        {/* Step Content */}
        {loading ? (
          <div className="flex flex-col items-center justify-center h-48 gap-3">
            <Loader2 className="w-8 h-8 animate-spin text-[#00C896]" />
            <p className="text-[#A1A1AA] text-sm">Loading step {step}...</p>
          </div>
        ) : stepData && (
          <>
            {/* Step Title */}
            <Card className="rounded-2xl border-[#F59E0B]/20 bg-gradient-to-r from-[#FFF8E1] to-white" data-testid="step-content">
              <CardContent className="p-6">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-12 h-12 bg-gradient-to-br from-[#FFD700] to-[#D4A017] rounded-xl flex items-center justify-center">
                    <span className="text-xl font-bold text-white">{step}</span>
                  </div>
                  <div>
                    <Badge className="bg-[#F59E0B]/10 text-[#D4A017] border border-[#F59E0B]/20 mb-1">
                      Step {step} of {totalSteps}
                    </Badge>
                    <h2 className="text-xl font-bold text-white" style={{ fontFamily: 'Clash Display, Satoshi, sans-serif' }}>
                      {stepData.title}
                    </h2>
                  </div>
                </div>

                {/* Portal Link */}
                {stepData.portal && (
                  <a href={stepData.portal} target="_blank" rel="noopener noreferrer"
                    className="flex items-center gap-2 p-3 bg-[#3B82F6]/10 border border-[#3B82F6]/20 rounded-xl text-[#3B82F6] hover:bg-blue-100 transition-colors mb-4"
                    data-testid="portal-link"
                  >
                    <ExternalLink className="w-4 h-4" />
                    <span className="text-sm font-medium">{stepData.portal}</span>
                  </a>
                )}

                {/* Instructions */}
                <div className="space-y-3">
                  {stepData.instructions?.map((instruction, idx) => (
                    <div key={idx} className="flex items-start gap-3">
                      <div className="w-6 h-6 bg-[#00C896]/10 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                        <ClipboardList className="w-3 h-3 text-[#00C896]" />
                      </div>
                      <p className="text-[#ccc] text-sm leading-relaxed">{instruction}</p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Your Data for This Step */}
            {stepData.your_data && Object.keys(stepData.your_data).length > 0 && (
              <Card className="rounded-2xl border-[#00C896]/20 bg-[#00C896]/10" data-testid="your-data-card">
                <CardContent className="p-5">
                  <h4 className="font-bold text-[#00C896] text-sm mb-3 flex items-center gap-2">
                    <ClipboardList className="w-4 h-4" />
                    Your ClearFile NG Data for This Step
                  </h4>
                  <div className="space-y-2">
                    {Object.entries(stepData.your_data).map(([key, value]) => {
                      if (typeof value === 'object') return null;
                      const label = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                      const display = typeof value === 'number' ? formatCurrency(value) : String(value);
                      return (
                        <div key={key} className="flex items-center justify-between py-1">
                          <span className="text-sm text-[#00C896]">{label}</span>
                          <span className="font-bold text-[#00C896] text-sm">{display}</span>
                        </div>
                      );
                    })}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Quick Tip */}
            {stepData.tip && (
              <div className="flex items-start gap-3 p-4 bg-[#F59E0B]/10 border border-[#F59E0B]/20 rounded-2xl">
                <Lightbulb className="w-5 h-5 text-[#D4A017] flex-shrink-0 mt-0.5" />
                <p className="text-sm text-[#A1A1AA]">{stepData.tip}</p>
              </div>
            )}

            {/* AI Personalized Advice */}
            {stepData.ai_advice && (
              <Card className="rounded-2xl border-[#8B5CF6]/20 bg-[#8B5CF6]/10" data-testid="ai-advice-card">
                <CardContent className="p-5">
                  <div className="flex items-start gap-3">
                    <div className="w-10 h-10 bg-purple-100 rounded-xl flex items-center justify-center flex-shrink-0">
                      <Sparkles className="w-5 h-5 text-[#8B5CF6]" />
                    </div>
                    <div>
                      <p className="font-bold text-[#8B5CF6] text-sm mb-1">AI Tip for You</p>
                      <p className="text-sm text-[#ccc] leading-relaxed">{stepData.ai_advice}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Navigation Buttons */}
            <div className="flex gap-3">
              {step > 1 && (
                <Button
                  variant="outline"
                  onClick={() => setStep(step - 1)}
                  className="flex-1 rounded-xl border-[#1E1E1E] py-5"
                  data-testid="prev-step-btn"
                >
                  <ArrowLeft className="w-4 h-4 mr-2" /> Previous
                </Button>
              )}
              <Button
                onClick={markComplete}
                className={`flex-1 rounded-xl py-5 ${
                  step === totalSteps
                    ? 'bg-[#00C896] hover:bg-[#00dba6] text-white'
                    : 'bg-gradient-to-r from-[#D4A017] to-[#FFD700] hover:from-[#B8860B] hover:to-[#D4A017] text-white'
                } font-bold`}
                data-testid="next-step-btn"
              >
                {completedSteps.has(step) && <CheckCircle className="w-4 h-4 mr-2" />}
                {step === totalSteps ? 'Complete Filing Guide' : 'Mark Complete & Next'}
                {step < totalSteps && <ArrowRight className="w-4 h-4 ml-2" />}
              </Button>
            </div>
          </>
        )}
        </>
        )}
      </div>
    </Layout>
  );
}
