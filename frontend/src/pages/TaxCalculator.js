import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import Layout from '../components/Layout';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { toast } from 'sonner';
import { 
  Calculator, TrendingUp, TrendingDown, 
  Lightbulb, Bot, Handshake, Send, X, ChevronDown
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

export default function TaxCalculator() {
  const { user } = useAuth();
  const { t } = useLanguage();
  const navigate = useNavigate();
  const [taxData, setTaxData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showFilingModal, setShowFilingModal] = useState(false);
  const [showEmailModal, setShowEmailModal] = useState(false);
  const [accountantEmail, setAccountantEmail] = useState('');
  const [sendingEmail, setSendingEmail] = useState(false);

  useEffect(() => { fetchTaxCalculation(); }, []);

  const fetchTaxCalculation = async () => {
    try {
      const { data } = await axios.get(`${API}/api/tax-calculation`, { withCredentials: true });
      setTaxData(data);
    } catch (error) {
      toast.error('Failed to calculate taxes');
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount) =>
    new Intl.NumberFormat('en-NG', { style: 'currency', currency: 'NGN', minimumFractionDigits: 0 })
      .format(amount).replace('NGN', '₦');

  const handleAIGuide = () => {
    setShowFilingModal(false);
    navigate('/ai-tax-guide');
  };

  const handleHireExpert = () => {
    setShowFilingModal(false);
    navigate('/hire-expert');
  };

  const handleSendToAccountant = () => {
    setShowFilingModal(false);
    setShowEmailModal(true);
  };

  const submitAccountantEmail = async () => {
    if (!accountantEmail || !accountantEmail.includes('@')) {
      toast.error('Please enter a valid email');
      return;
    }
    setSendingEmail(true);
    try {
      // Export tax report and notify
      const response = await axios.get(`${API}/api/export/tax-report?format=pdf`, {
        withCredentials: true,
        responseType: 'blob'
      });
      toast.success(`Tax report ready! Send it to ${accountantEmail}`);
      // Trigger download
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `clearfileng_tax_report_${new Date().getFullYear()}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      setShowEmailModal(false);
      setAccountantEmail('');
    } catch (error) {
      toast.error('Failed to generate report. Please try again.');
    } finally {
      setSendingEmail(false);
    }
  };

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-64">
          <div className="w-12 h-12 border-4 border-[#006400] border-t-transparent rounded-full animate-spin"></div>
        </div>
      </Layout>
    );
  }

  const taxBreakdown = [
    { label: t('grossIncome'), value: taxData?.gross_income || 0, icon: TrendingUp, color: 'text-[#00C896]', bg: 'bg-[#00C896]/10' },
    { label: t('deductibleExpenses'), value: taxData?.deductible_expenses || 0, icon: TrendingDown, color: 'text-orange-500', bg: 'bg-orange-500/10', subtract: true },
    { label: t('taxableIncome'), value: taxData?.taxable_income || 0, icon: Calculator, color: 'text-blue-500', bg: 'bg-[#3B82F6]/10' },
  ];

  return (
    <Layout>
      <div className="space-y-6 pb-28 lg:pb-24">
        {/* Header */}
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white" style={{ fontFamily: 'Clash Display, Satoshi, sans-serif' }}>
            {t('taxCalculator')}
          </h1>
          <p className="text-[#A1A1AA]">Estimated taxes based on Nigerian law</p>
        </div>

        {/* Tax Type Badge */}
        <Card className="card-dark bg-[#00C896] text-white">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-[#A5D6A7] text-sm">Tax Type</p>
                <p className="text-xl font-bold" data-testid="tax-type">{taxData?.tax_type}</p>
              </div>
              <div className="text-right">
                <p className="text-[#A5D6A7] text-sm">Business Type</p>
                <p className="text-lg font-medium capitalize" data-testid="business-type">{taxData?.business_type}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Income Breakdown */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {taxBreakdown.map((item, idx) => (
            <Card key={idx} className="card-dark" data-testid={`breakdown-${idx}`}>
              <CardContent className="p-6">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-[#A1A1AA]">{item.label}</span>
                  <div className={`w-10 h-10 ${item.bg} rounded-xl flex items-center justify-center`}>
                    <item.icon className={`w-5 h-5 ${item.color}`} />
                  </div>
                </div>
                <p className={`text-2xl font-bold ${item.color}`}>
                  {item.subtract && '-'}{formatCurrency(item.value)}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Tax Summary */}
        <Card className="card-dark">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2" style={{ fontFamily: 'Clash Display, Satoshi, sans-serif' }}>
              <Calculator className="w-5 h-5 text-[#00C896]" />
              Tax Summary
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex items-center justify-between p-4 bg-[#F59E0B]/10 rounded-xl">
              <div>
                <p className="font-medium text-white">{t('incomeTax')}</p>
                <p className="text-sm text-[#A1A1AA]">{taxData?.tax_type}</p>
              </div>
              <p className="text-2xl font-bold text-white" data-testid="income-tax-value">
                {formatCurrency(taxData?.income_tax || 0)}
              </p>
            </div>

            {taxData?.vat > 0 && (
              <div className="flex items-center justify-between p-4 bg-[#00C896]/10 rounded-xl">
                <div>
                  <p className="font-medium text-[#00C896]">{t('vat')}</p>
                  <p className="text-sm text-[#A1A1AA]">Value Added Tax</p>
                </div>
                <p className="text-2xl font-bold text-[#00C896]" data-testid="vat-value">
                  {formatCurrency(taxData?.vat || 0)}
                </p>
              </div>
            )}

            <div className="border-t-2 border-dashed border-[#1E1E1E] pt-4">
              <div className="flex items-center justify-between p-4 bg-[#00C896] rounded-xl text-white">
                <div>
                  <p className="font-bold text-lg">{t('totalTaxOwed')}</p>
                  <p className="text-sm text-[#A5D6A7]">Estimated annual tax</p>
                </div>
                <p className="text-3xl font-bold" data-testid="total-tax-value">
                  {formatCurrency(taxData?.total_tax_owed || 0)}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Potential Savings */}
        {taxData?.potential_savings > 0 && (
          <Card className="rounded-2xl border-[#FFD700] bg-[#F59E0B]/10">
            <CardContent className="p-6">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 bg-[#F59E0B] rounded-xl flex items-center justify-center flex-shrink-0">
                  <Lightbulb className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h3 className="font-bold text-white text-lg">{t('potentialSavings')}</h3>
                  <p className="text-[#A1A1AA] mb-2">
                    You could save up to <span className="font-bold text-[#00C896]">{formatCurrency(taxData.potential_savings)}</span> by properly 
                    categorizing all your business expenses as deductible.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* PITA Brackets */}
        {taxData?.tax_brackets && (
          <Card className="card-dark">
            <CardHeader>
              <CardTitle className="text-lg" style={{ fontFamily: 'Clash Display, Satoshi, sans-serif' }}>PITA Tax Brackets</CardTitle>
              <CardDescription>Progressive tax rates for personal income</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {[
                  { range: 'First ₦300,000', rate: '7%' },
                  { range: 'Next ₦300,000', rate: '11%' },
                  { range: 'Next ₦500,000', rate: '15%' },
                  { range: 'Next ₦500,000', rate: '19%' },
                  { range: 'Next ₦1,600,000', rate: '21%' },
                  { range: 'Above ₦3,200,000', rate: '24%' },
                ].map((bracket, idx) => (
                  <div key={idx} className="flex items-center justify-between p-3 bg-[#0A0A0A] rounded-xl">
                    <span className="text-[#A1A1AA]">{bracket.range}</span>
                    <span className="font-bold text-[#00C896]">{bracket.rate}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* ========== STICKY BOTTOM CTA BUTTON ========== */}
      <div className="fixed bottom-16 lg:bottom-0 left-0 lg:left-64 right-0 z-40 p-4 bg-gradient-to-t from-white via-white to-transparent">
        <Button
          onClick={() => setShowFilingModal(true)}
          className="w-full bg-gradient-to-r from-[#D4A017] to-[#FFD700] hover:from-[#B8860B] hover:to-[#D4A017] text-white font-bold text-base rounded-2xl py-6  shadow-[#FFD700]/30 transition-all active:scale-[0.98]"
          data-testid="filing-cta-btn"
        >
          Ready for final filing? Choose an option.
        </Button>
      </div>

      {/* ========== FILING OPTIONS BOTTOM SHEET MODAL ========== */}
      {showFilingModal && (
        <div className="fixed inset-0 z-50 flex items-end justify-center" onClick={() => setShowFilingModal(false)}>
          <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" />
          <div
            className="relative w-full max-w-lg bg-gradient-to-b from-[#FFF8E1] to-white rounded-t-3xl shadow-2xl animate-in slide-in-from-bottom duration-300"
            onClick={e => e.stopPropagation()}
          >
            {/* Handle / Close */}
            <div className="flex flex-col items-center pt-3 pb-2">
              <div className="w-10 h-1.5 bg-slate-300 rounded-full" />
            </div>
            <div className="flex items-center justify-between px-6 pb-4">
              <h3 className="text-lg font-bold text-white" style={{ fontFamily: 'Clash Display, Satoshi, sans-serif' }}>
                Filing Options
              </h3>
              <button
                onClick={() => setShowFilingModal(false)}
                className="w-8 h-8 rounded-full bg-slate-200 flex items-center justify-center hover:bg-slate-300 transition-colors"
                data-testid="close-filing-modal"
              >
                <X className="w-4 h-4 text-[#A1A1AA]" />
              </button>
            </div>

            {/* Options */}
            <div className="px-6 pb-8 space-y-3">
              {/* AI Tax Guide */}
              <button
                onClick={handleAIGuide}
                className="w-full flex items-start gap-4 p-4 rounded-2xl bg-[#111111] border border-[#F59E0B]/20 hover:bg-[#F59E0B]/10 transition-all text-left group"
                data-testid="filing-ai-guide"
              >
                <div className="w-12 h-12 bg-gradient-to-br from-[#FFD700] to-[#D4A017] rounded-xl flex items-center justify-center flex-shrink-0 group-hover:scale-105 transition-transform">
                  <Bot className="w-6 h-6 text-white" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-bold text-white">AI Tax Guide</p>
                  <p className="text-sm text-[#A1A1AA] mt-0.5 leading-relaxed">
                    Let ClearFile AI walk you step-by-step through the FIRS portal using this exact data.
                  </p>
                  <span className="inline-block mt-2 text-xs font-bold text-[#D4A017] bg-[#F59E0B]/10 px-2 py-1 rounded-lg border border-[#F59E0B]/20">
                    ₦70,000 unlock
                  </span>
                </div>
              </button>

              {/* Hire Expert */}
              <button
                onClick={handleHireExpert}
                className="w-full flex items-start gap-4 p-4 rounded-2xl bg-[#111111] border border-[#00C896]/20 hover:bg-[#00C896]/10 transition-all text-left group"
                data-testid="filing-hire-expert"
              >
                <div className="w-12 h-12 bg-gradient-to-br from-[#006400] to-[#228B22] rounded-xl flex items-center justify-center flex-shrink-0 group-hover:scale-105 transition-transform">
                  <Handshake className="w-6 h-6 text-white" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-bold text-white">Hire a Verified Expert</p>
                  <p className="text-sm text-[#A1A1AA] mt-0.5 leading-relaxed">
                    Securely send this data to a vetted Pan-African tax professional to file for you.
                  </p>
                </div>
              </button>

              {/* Send to Accountant */}
              <button
                onClick={handleSendToAccountant}
                className="w-full flex items-start gap-4 p-4 rounded-2xl bg-[#111111] border border-[#3B82F6]/20 hover:bg-[#3B82F6]/10 transition-all text-left group"
                data-testid="filing-send-accountant"
              >
                <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl flex items-center justify-center flex-shrink-0 group-hover:scale-105 transition-transform">
                  <Send className="w-6 h-6 text-white" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-bold text-white">Send to My Accountant</p>
                  <p className="text-sm text-[#A1A1AA] mt-0.5 leading-relaxed">
                    Export these ready-to-file records directly to your accountant's email.
                  </p>
                </div>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ========== EMAIL INPUT MODAL ========== */}
      {showEmailModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4" onClick={() => setShowEmailModal(false)}>
          <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" />
          <div
            className="relative w-full max-w-md bg-[#111111] rounded-2xl shadow-2xl p-6"
            onClick={e => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-white" style={{ fontFamily: 'Clash Display, Satoshi, sans-serif' }}>Send to Accountant</h3>
              <button
                onClick={() => setShowEmailModal(false)}
                className="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center hover:bg-slate-200"
                data-testid="close-email-modal"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <p className="text-sm text-[#A1A1AA] mb-4">
              We'll generate your tax report PDF and download it for you to send.
            </p>
            <div className="space-y-3">
              <div>
                <Label>Accountant's Email</Label>
                <Input
                  type="email"
                  placeholder="accountant@example.com"
                  value={accountantEmail}
                  onChange={e => setAccountantEmail(e.target.value)}
                  className="rounded-xl mt-1"
                  data-testid="accountant-email-input"
                />
              </div>
              <Button
                onClick={submitAccountantEmail}
                disabled={sendingEmail}
                className="w-full bg-[#00C896] hover:bg-[#00dba6] text-white rounded-xl py-5"
                data-testid="send-report-btn"
              >
                {sendingEmail ? 'Generating Report...' : 'Download & Send Report'}
              </Button>
            </div>
          </div>
        </div>
      )}
    </Layout>
  );
}
