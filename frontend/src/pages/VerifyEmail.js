import React, { useEffect, useState } from 'react';
import { useSearchParams, Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { CheckCircle, XCircle, Loader2 } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

export default function VerifyEmail() {
  const [searchParams] = useSearchParams();
  const [status, setStatus] = useState('verifying'); // verifying, success, error
  const [message, setMessage] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    const token = searchParams.get('token');
    if (!token) {
      setStatus('error');
      setMessage('Invalid verification link');
      return;
    }

    verifyEmail(token);
  }, [searchParams]);

  const verifyEmail = async (token) => {
    try {
      const { data } = await axios.post(`${API}/api/auth/verify-email`, { token });
      setStatus('success');
      setMessage(data.message);
    } catch (error) {
      setStatus('error');
      setMessage(error.response?.data?.detail || 'Verification failed');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#E8F5E9] via-[#FAFAFA] to-[#FFF8E1] flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <Link to="/" className="inline-flex items-center gap-2">
            <div className="w-12 h-12 bg-[#006400] rounded-xl flex items-center justify-center">
              <span className="text-white font-bold text-xl">₦</span>
            </div>
            <span className="text-2xl font-bold text-[#022c22]" style={{ fontFamily: 'Outfit' }}>NairaTrack</span>
          </Link>
        </div>

        <Card className="border-slate-200 shadow-xl rounded-2xl">
          <CardHeader className="text-center pb-4">
            <CardTitle className="text-2xl font-bold text-[#022c22]" style={{ fontFamily: 'Outfit' }}>
              Email Verification
            </CardTitle>
          </CardHeader>
          <CardContent className="text-center">
            {status === 'verifying' && (
              <div className="py-8">
                <Loader2 className="w-12 h-12 text-[#006400] animate-spin mx-auto mb-4" />
                <p className="text-slate-600">Verifying your email...</p>
              </div>
            )}

            {status === 'success' && (
              <div className="py-8">
                <div className="w-16 h-16 bg-[#E8F5E9] rounded-full flex items-center justify-center mx-auto mb-4">
                  <CheckCircle className="w-10 h-10 text-[#006400]" />
                </div>
                <h3 className="text-lg font-semibold text-[#006400] mb-2">Email Verified!</h3>
                <p className="text-slate-600 mb-6">{message}</p>
                <Button
                  onClick={() => navigate('/dashboard')}
                  className="bg-[#006400] hover:bg-[#004d00] text-white rounded-xl"
                >
                  Go to Dashboard
                </Button>
              </div>
            )}

            {status === 'error' && (
              <div className="py-8">
                <div className="w-16 h-16 bg-red-50 rounded-full flex items-center justify-center mx-auto mb-4">
                  <XCircle className="w-10 h-10 text-red-500" />
                </div>
                <h3 className="text-lg font-semibold text-red-600 mb-2">Verification Failed</h3>
                <p className="text-slate-600 mb-6">{message}</p>
                <Link to="/login">
                  <Button className="bg-[#006400] hover:bg-[#004d00] text-white rounded-xl">
                    Go to Login
                  </Button>
                </Link>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
