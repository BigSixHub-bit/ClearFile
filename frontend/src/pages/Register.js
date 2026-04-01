import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { toast } from 'sonner';
import { User, Lock, Mail, Eye, EyeOff, Briefcase } from 'lucide-react';

function formatApiErrorDetail(detail) {
  if (detail == null) return "Something went wrong. Please try again.";
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail))
    return detail.map((e) => (e && typeof e.msg === "string" ? e.msg : JSON.stringify(e))).filter(Boolean).join(" ");
  if (detail && typeof detail.msg === "string") return detail.msg;
  return String(detail);
}

export default function Register() {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    business_type: 'freelancer',
    monthly_income_range: '0-100000'
  });
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();
  const { t } = useLanguage();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (formData.password.length < 6) {
      toast.error('Password must be at least 6 characters');
      return;
    }
    setLoading(true);
    try {
      await register(formData);
      toast.success('Account created successfully!');
      navigate('/onboarding');
    } catch (error) {
      toast.error(formatApiErrorDetail(error.response?.data?.detail) || error.message);
    } finally {
      setLoading(false);
    }
  };

  const incomeRanges = [
    { value: '0-100000', label: '₦0 - ₦100,000' },
    { value: '100000-500000', label: '₦100,000 - ₦500,000' },
    { value: '500000-1000000', label: '₦500,000 - ₦1,000,000' },
    { value: '1000000-5000000', label: '₦1,000,000 - ₦5,000,000' },
    { value: '5000000+', label: '₦5,000,000+' }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#E8F5E9] via-[#FAFAFA] to-[#FFF8E1] flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo */}
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
            <CardTitle className="text-2xl font-bold text-[#022c22]" style={{ fontFamily: 'Outfit' }}>Create Account</CardTitle>
            <CardDescription className="text-slate-600">Start your 7-day free trial today</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="name" className="text-slate-700">{t('name')}</Label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                  <Input
                    id="name"
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="John Doe"
                    className="pl-10 rounded-xl border-slate-200 focus:ring-[#006400]"
                    required
                    data-testid="register-name-input"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="email" className="text-slate-700">{t('email')}</Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                  <Input
                    id="email"
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    placeholder="you@example.com"
                    className="pl-10 rounded-xl border-slate-200 focus:ring-[#006400]"
                    required
                    data-testid="register-email-input"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="password" className="text-slate-700">{t('password')}</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                  <Input
                    id="password"
                    type={showPassword ? 'text' : 'password'}
                    value={formData.password}
                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                    placeholder="••••••••"
                    className="pl-10 pr-10 rounded-xl border-slate-200 focus:ring-[#006400]"
                    required
                    minLength={6}
                    data-testid="register-password-input"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                  >
                    {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                  </button>
                </div>
              </div>

              <div className="space-y-2">
                <Label className="text-slate-700">{t('businessType')}</Label>
                <Select 
                  value={formData.business_type} 
                  onValueChange={(value) => setFormData({ ...formData, business_type: value })}
                >
                  <SelectTrigger className="rounded-xl border-slate-200" data-testid="register-business-type-select">
                    <Briefcase className="w-5 h-5 text-slate-400 mr-2" />
                    <SelectValue placeholder="Select business type" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="freelancer">{t('freelancer')}</SelectItem>
                    <SelectItem value="sme">{t('sme')}</SelectItem>
                    <SelectItem value="company">{t('company')}</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label className="text-slate-700">{t('monthlyIncome')}</Label>
                <Select 
                  value={formData.monthly_income_range} 
                  onValueChange={(value) => setFormData({ ...formData, monthly_income_range: value })}
                >
                  <SelectTrigger className="rounded-xl border-slate-200" data-testid="register-income-select">
                    <SelectValue placeholder="Select income range" />
                  </SelectTrigger>
                  <SelectContent>
                    {incomeRanges.map(range => (
                      <SelectItem key={range.value} value={range.value}>{range.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <Button
                type="submit"
                disabled={loading}
                className="w-full bg-[#006400] hover:bg-[#004d00] text-white rounded-xl py-6"
                data-testid="register-submit-btn"
              >
                {loading ? 'Creating account...' : t('startTrial')}
              </Button>
            </form>

            <div className="mt-6 text-center">
              <p className="text-slate-600">
                {t('haveAccount')}{' '}
                <Link to="/login" className="text-[#006400] font-medium hover:underline" data-testid="goto-login-link">
                  {t('login')}
                </Link>
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
