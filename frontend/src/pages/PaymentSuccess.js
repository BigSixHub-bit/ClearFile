import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { toast } from 'sonner';
import { CheckCircle, XCircle, Loader2, ArrowRight } from 'lucide-react';
import { Button } from '../components/ui/button';

const API = process.env.REACT_APP_BACKEND_URL;

export default function PaymentSuccess() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [verifying, setVerifying] = useState(true);
  const [result, setResult] = useState(null);

  const status = searchParams.get('status');
  const transactionId = searchParams.get('transaction_id');
  const txRef = searchParams.get('tx_ref');

  useEffect(() => {
    verifyPayment();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const verifyPayment = async () => {
    if (status === 'cancelled') {
      setResult({ success: false, message: 'Payment was cancelled.' });
      setVerifying(false);
      return;
    }

    if (!transactionId) {
      setResult({ success: false, message: 'No transaction information found.' });
      setVerifying(false);
      return;
    }

    try {
      const isAiGuide = txRef?.startsWith('cfng_aiguide_');
      const isSubscription = txRef?.startsWith('cfng_sub_');

      if (isAiGuide) {
        const { data } = await axios.get(
          `${API}/api/payments/ai-guide/verify?transaction_id=${transactionId}&tx_ref=${txRef}`,
          { withCredentials: true }
        );
        if (data.status === 'success' || data.unlocked) {
          setResult({ success: true, type: 'ai_guide', message: 'AI Tax Guide unlocked!' });
        } else {
          setResult({ success: false, message: data.message || 'Verification failed' });
        }
      } else if (isSubscription) {
        const { data } = await axios.get(
          `${API}/api/subscription/verify?transaction_id=${transactionId}&tx_ref=${txRef}`,
          { withCredentials: true }
        );
        if (data.status === 'success') {
          setResult({ success: true, type: 'subscription', plan: data.plan, message: `Upgraded to ${data.plan} plan!` });
        } else {
          setResult({ success: false, message: data.message || 'Verification failed' });
        }
      } else {
        setResult({ success: false, message: 'Unknown payment type.' });
      }
    } catch (err) {
      setResult({ success: false, message: 'Payment verification failed. Please contact support.' });
    } finally {
      setVerifying(false);
    }
  };

  const handleContinue = () => {
    if (result?.type === 'ai_guide') {
      navigate('/ai-tax-guide');
    } else if (result?.type === 'subscription') {
      navigate('/settings');
    } else {
      navigate('/dashboard');
    }
  };

  return (
    <div className="min-h-screen bg-[#050505] flex items-center justify-center p-4">
      <div className="max-w-md w-full">
        <div className="bg-[#111111] border border-[#1E1E1E] rounded-2xl p-8 text-center" data-testid="payment-result-card">
          {verifying ? (
            <div className="space-y-4" data-testid="payment-verifying">
              <Loader2 className="w-12 h-12 animate-spin text-[#00C896] mx-auto" />
              <h2 className="text-xl font-semibold text-white" style={{ fontFamily: 'Clash Display, Satoshi, sans-serif' }}>
                Verifying Payment...
              </h2>
              <p className="text-[#A1A1AA] text-sm">Please wait while we confirm your payment.</p>
            </div>
          ) : result?.success ? (
            <div className="space-y-5" data-testid="payment-success">
              <div className="w-16 h-16 rounded-full bg-[#00C896]/10 flex items-center justify-center mx-auto">
                <CheckCircle className="w-8 h-8 text-[#00C896]" />
              </div>
              <h2 className="text-xl font-semibold text-white" style={{ fontFamily: 'Clash Display, Satoshi, sans-serif' }}>
                Payment Successful
              </h2>
              <p className="text-[#A1A1AA] text-sm">{result.message}</p>
              <Button
                onClick={handleContinue}
                className="w-full bg-[#00C896] hover:bg-[#00dba6] text-white rounded-xl py-3 font-medium"
                data-testid="payment-continue-btn"
              >
                Continue <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </div>
          ) : (
            <div className="space-y-5" data-testid="payment-failed">
              <div className="w-16 h-16 rounded-full bg-red-500/10 flex items-center justify-center mx-auto">
                <XCircle className="w-8 h-8 text-red-500" />
              </div>
              <h2 className="text-xl font-semibold text-white" style={{ fontFamily: 'Clash Display, Satoshi, sans-serif' }}>
                Payment Failed
              </h2>
              <p className="text-[#A1A1AA] text-sm">{result?.message}</p>
              <div className="flex gap-3">
                <Button
                  variant="outline"
                  onClick={() => navigate('/dashboard')}
                  className="flex-1 border-[#1E1E1E] rounded-xl py-3"
                  data-testid="payment-back-btn"
                >
                  Dashboard
                </Button>
                <Button
                  onClick={() => navigate('/ai-tax-guide')}
                  className="flex-1 bg-[#00C896] hover:bg-[#00dba6] text-white rounded-xl py-3"
                  data-testid="payment-retry-btn"
                >
                  Try Again
                </Button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
