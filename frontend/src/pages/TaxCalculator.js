import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Layout from '../components/Layout';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Progress } from '../components/ui/progress';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { toast } from 'sonner';
import { 
  Calculator, TrendingUp, TrendingDown, Percent, 
  AlertCircle, Lightbulb, FileText
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

export default function TaxCalculator() {
  const { user } = useAuth();
  const { t } = useLanguage();
  const [taxData, setTaxData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTaxCalculation();
  }, []);

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

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-NG', {
      style: 'currency',
      currency: 'NGN',
      minimumFractionDigits: 0
    }).format(amount).replace('NGN', '₦');
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
    { label: t('grossIncome'), value: taxData?.gross_income || 0, icon: TrendingUp, color: 'text-[#006400]', bg: 'bg-[#E8F5E9]' },
    { label: t('deductibleExpenses'), value: taxData?.deductible_expenses || 0, icon: TrendingDown, color: 'text-orange-500', bg: 'bg-orange-50', subtract: true },
    { label: t('taxableIncome'), value: taxData?.taxable_income || 0, icon: Calculator, color: 'text-blue-500', bg: 'bg-blue-50' },
  ];

  return (
    <Layout>
      <div className="space-y-6 pb-20 lg:pb-0">
        {/* Header */}
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-[#022c22]" style={{ fontFamily: 'Outfit' }}>
            {t('taxCalculator')}
          </h1>
          <p className="text-slate-500">Estimated taxes based on Nigerian law</p>
        </div>

        {/* Tax Type Badge */}
        <Card className="rounded-2xl border-slate-200 bg-[#006400] text-white">
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
            <Card key={idx} className="rounded-2xl border-slate-200" data-testid={`breakdown-${idx}`}>
              <CardContent className="p-6">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-slate-500">{item.label}</span>
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
        <Card className="rounded-2xl border-slate-200">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2" style={{ fontFamily: 'Outfit' }}>
              <Calculator className="w-5 h-5 text-[#006400]" />
              Tax Summary
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Income Tax */}
            <div className="flex items-center justify-between p-4 bg-[#FFF8E1] rounded-xl">
              <div>
                <p className="font-medium text-[#422006]">{t('incomeTax')}</p>
                <p className="text-sm text-slate-500">{taxData?.tax_type}</p>
              </div>
              <p className="text-2xl font-bold text-[#422006]" data-testid="income-tax-value">
                {formatCurrency(taxData?.income_tax || 0)}
              </p>
            </div>

            {/* VAT */}
            {taxData?.vat > 0 && (
              <div className="flex items-center justify-between p-4 bg-[#E8F5E9] rounded-xl">
                <div>
                  <p className="font-medium text-[#006400]">{t('vat')}</p>
                  <p className="text-sm text-slate-500">Value Added Tax</p>
                </div>
                <p className="text-2xl font-bold text-[#006400]" data-testid="vat-value">
                  {formatCurrency(taxData?.vat || 0)}
                </p>
              </div>
            )}

            {/* Total */}
            <div className="border-t-2 border-dashed border-slate-200 pt-4">
              <div className="flex items-center justify-between p-4 bg-[#006400] rounded-xl text-white">
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
          <Card className="rounded-2xl border-[#FFD700] bg-[#FFF8E1]">
            <CardContent className="p-6">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 bg-[#FFD700] rounded-xl flex items-center justify-center flex-shrink-0">
                  <Lightbulb className="w-6 h-6 text-[#422006]" />
                </div>
                <div>
                  <h3 className="font-bold text-[#422006] text-lg">{t('potentialSavings')}</h3>
                  <p className="text-[#6D4C41] mb-2">
                    You could save up to <span className="font-bold text-[#006400]">{formatCurrency(taxData.potential_savings)}</span> by properly 
                    categorizing all your business expenses as deductible.
                  </p>
                  <p className="text-sm text-slate-500">
                    Tip: Make sure all business expenses are properly categorized in the Transactions page.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* PITA Brackets */}
        {taxData?.tax_brackets && (
          <Card className="rounded-2xl border-slate-200">
            <CardHeader>
              <CardTitle className="text-lg" style={{ fontFamily: 'Outfit' }}>
                PITA Tax Brackets
              </CardTitle>
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
                  <div key={idx} className="flex items-center justify-between p-3 bg-slate-50 rounded-xl">
                    <span className="text-slate-600">{bracket.range}</span>
                    <span className="font-bold text-[#006400]">{bracket.rate}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Disclaimer */}
        <Card className="rounded-2xl border-slate-200 bg-slate-50">
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-slate-400 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-slate-500">
                {t('disclaimer')}
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </Layout>
  );
}
