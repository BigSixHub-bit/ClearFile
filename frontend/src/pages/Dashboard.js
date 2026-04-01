import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import Layout from '../components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Progress } from '../components/ui/progress';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { toast } from 'sonner';
import { 
  TrendingUp, TrendingDown, Calculator, Wallet, PlusCircle, 
  Camera, FileText, Link2, AlertTriangle, Calendar, ArrowRight
} from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip } from 'recharts';

const API = process.env.REACT_APP_BACKEND_URL;

export default function Dashboard() {
  const { user } = useAuth();
  const { t } = useLanguage();
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboard();
  }, []);

  const fetchDashboard = async () => {
    try {
      const { data } = await axios.get(`${API}/api/dashboard`, { withCredentials: true });
      setDashboard(data);
    } catch (error) {
      toast.error('Failed to load dashboard');
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

  const getHealthScoreColor = (score) => {
    if (score >= 80) return '#006400';
    if (score >= 50) return '#FFD700';
    return '#ef4444';
  };

  const COLORS = ['#006400', '#008000', '#228B22', '#32CD32', '#90EE90', '#FFD700', '#FFA500', '#FF6347'];

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-64">
          <div className="w-12 h-12 border-4 border-[#006400] border-t-transparent rounded-full animate-spin"></div>
        </div>
      </Layout>
    );
  }

  const spendingData = dashboard?.spending_breakdown 
    ? Object.entries(dashboard.spending_breakdown).map(([name, value]) => ({ name, value }))
    : [];

  return (
    <Layout>
      <div className="space-y-6 pb-20 lg:pb-0">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold text-[#022c22]" style={{ fontFamily: 'Outfit' }}>
              {t('dashboard')}
            </h1>
            <p className="text-slate-500">Welcome back, {user?.name?.split(' ')[0]}!</p>
          </div>
          <div className="flex gap-2 flex-wrap">
            <Link to="/transactions">
              <Button variant="outline" className="rounded-xl border-slate-200" data-testid="quick-add-income-btn">
                <PlusCircle className="w-4 h-4 mr-2 text-[#006400]" />
                {t('addIncome')}
              </Button>
            </Link>
            <Link to="/transactions">
              <Button variant="outline" className="rounded-xl border-slate-200" data-testid="quick-add-expense-btn">
                <PlusCircle className="w-4 h-4 mr-2 text-red-500" />
                {t('addExpense')}
              </Button>
            </Link>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Total Income */}
          <Card className="rounded-2xl border-slate-200 hover-lift" data-testid="total-income-card">
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-slate-500">{t('totalIncome')}</span>
                <div className="w-10 h-10 bg-[#E8F5E9] rounded-xl flex items-center justify-center">
                  <TrendingUp className="w-5 h-5 text-[#006400]" />
                </div>
              </div>
              <p className="text-2xl font-bold text-[#006400]" data-testid="total-income-value">
                {formatCurrency(dashboard?.total_income || 0)}
              </p>
              <p className="text-xs text-slate-400 mt-1">All time</p>
            </CardContent>
          </Card>

          {/* Total Expenses */}
          <Card className="rounded-2xl border-slate-200 hover-lift" data-testid="total-expenses-card">
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-slate-500">{t('totalExpenses')}</span>
                <div className="w-10 h-10 bg-red-50 rounded-xl flex items-center justify-center">
                  <TrendingDown className="w-5 h-5 text-red-500" />
                </div>
              </div>
              <p className="text-2xl font-bold text-red-500" data-testid="total-expenses-value">
                {formatCurrency(dashboard?.total_expenses || 0)}
              </p>
              <p className="text-xs text-slate-400 mt-1">All time</p>
            </CardContent>
          </Card>

          {/* Estimated Tax */}
          <Card className="rounded-2xl border-slate-200 hover-lift" data-testid="estimated-tax-card">
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-slate-500">{t('estimatedTax')}</span>
                <div className="w-10 h-10 bg-[#FFF8E1] rounded-xl flex items-center justify-center">
                  <Calculator className="w-5 h-5 text-[#FFD700]" />
                </div>
              </div>
              <p className="text-2xl font-bold text-[#422006]" data-testid="estimated-tax-value">
                {formatCurrency(dashboard?.estimated_tax || 0)}
              </p>
              <p className="text-xs text-slate-400 mt-1">Income Tax + VAT: {formatCurrency(dashboard?.vat_owed || 0)}</p>
            </CardContent>
          </Card>

          {/* Bank Balance */}
          <Card className="rounded-2xl border-slate-200 hover-lift" data-testid="bank-balance-card">
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-slate-500">{t('bankBalance')}</span>
                <div className="w-10 h-10 bg-blue-50 rounded-xl flex items-center justify-center">
                  <Wallet className="w-5 h-5 text-blue-500" />
                </div>
              </div>
              <p className="text-2xl font-bold text-blue-600" data-testid="bank-balance-value">
                {formatCurrency(dashboard?.total_bank_balance || 0)}
              </p>
              <p className="text-xs text-slate-400 mt-1">{dashboard?.bank_accounts_count || 0} accounts linked</p>
            </CardContent>
          </Card>
        </div>

        {/* Tax Health Score & Spending Breakdown */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Tax Health Score */}
          <Card className="rounded-2xl border-slate-200" data-testid="tax-health-score-card">
            <CardHeader>
              <CardTitle className="text-lg" style={{ fontFamily: 'Outfit' }}>{t('taxHealthScore')}</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col items-center pb-6">
              <div className="relative w-40 h-40 mb-4">
                <svg className="w-full h-full transform -rotate-90">
                  <circle
                    cx="80"
                    cy="80"
                    r="70"
                    fill="none"
                    stroke="#e2e8f0"
                    strokeWidth="12"
                  />
                  <circle
                    cx="80"
                    cy="80"
                    r="70"
                    fill="none"
                    stroke={getHealthScoreColor(dashboard?.tax_health_score || 0)}
                    strokeWidth="12"
                    strokeDasharray={440}
                    strokeDashoffset={440 - (440 * (dashboard?.tax_health_score || 0)) / 100}
                    className="health-score-ring"
                  />
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <span 
                    className="text-4xl font-bold" 
                    style={{ color: getHealthScoreColor(dashboard?.tax_health_score || 0) }}
                    data-testid="tax-health-score-value"
                  >
                    {dashboard?.tax_health_score || 0}
                  </span>
                  <span className="text-sm text-slate-500">/ 100</span>
                </div>
              </div>
              <p className="text-center text-slate-600 text-sm">
                {dashboard?.tax_health_score >= 80 
                  ? 'Excellent! Your finances are well organized.' 
                  : dashboard?.tax_health_score >= 50
                  ? 'Good progress! Keep tracking your expenses.'
                  : 'Link your bank and track more transactions to improve.'}
              </p>
            </CardContent>
          </Card>

          {/* Spending Breakdown */}
          <Card className="rounded-2xl border-slate-200 lg:col-span-2" data-testid="spending-breakdown-card">
            <CardHeader>
              <CardTitle className="text-lg" style={{ fontFamily: 'Outfit' }}>{t('spendingBreakdown')}</CardTitle>
            </CardHeader>
            <CardContent>
              {spendingData.length > 0 ? (
                <div className="flex flex-col lg:flex-row items-center gap-6">
                  <div className="w-full lg:w-1/2 h-64">
                    <ResponsiveContainer>
                      <PieChart>
                        <Pie
                          data={spendingData}
                          dataKey="value"
                          nameKey="name"
                          cx="50%"
                          cy="50%"
                          outerRadius={80}
                          label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                        >
                          {spendingData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                          ))}
                        </Pie>
                        <Tooltip formatter={(value) => formatCurrency(value)} />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                  <div className="w-full lg:w-1/2 space-y-2">
                    {spendingData.slice(0, 5).map((item, idx) => (
                      <div key={idx} className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <div className="w-3 h-3 rounded-full" style={{ backgroundColor: COLORS[idx % COLORS.length] }}></div>
                          <span className="text-sm text-slate-600">{item.name}</span>
                        </div>
                        <span className="text-sm font-medium">{formatCurrency(item.value)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="h-64 flex items-center justify-center text-slate-400">
                  <p>No expenses tracked yet</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Quick Actions & Alerts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Quick Actions */}
          <Card className="rounded-2xl border-slate-200">
            <CardHeader>
              <CardTitle className="text-lg" style={{ fontFamily: 'Outfit' }}>Quick Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <Link to="/transactions" className="block">
                <Button variant="outline" className="w-full justify-start rounded-xl border-slate-200 hover:bg-[#E8F5E9]" data-testid="action-scan-receipt">
                  <Camera className="w-5 h-5 mr-3 text-[#006400]" />
                  {t('scanReceipt')}
                </Button>
              </Link>
              <Link to="/tax-calculator" className="block">
                <Button variant="outline" className="w-full justify-start rounded-xl border-slate-200 hover:bg-[#E8F5E9]" data-testid="action-view-report">
                  <FileText className="w-5 h-5 mr-3 text-[#006400]" />
                  {t('viewReport')}
                </Button>
              </Link>
              {user?.subscription_plan !== 'starter' && (
                <Link to="/settings" className="block">
                  <Button variant="outline" className="w-full justify-start rounded-xl border-slate-200 hover:bg-[#E8F5E9]" data-testid="action-link-bank">
                    <Link2 className="w-5 h-5 mr-3 text-[#006400]" />
                    {t('linkBank')}
                  </Button>
                </Link>
              )}
            </CardContent>
          </Card>

          {/* Upcoming Deadlines & Flagged */}
          <Card className="rounded-2xl border-slate-200">
            <CardHeader>
              <CardTitle className="text-lg" style={{ fontFamily: 'Outfit' }}>{t('upcomingDeadlines')}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {dashboard?.upcoming_deadlines?.map((deadline, idx) => (
                <div key={idx} className="flex items-center justify-between p-3 bg-[#FFF8E1] rounded-xl" data-testid={`deadline-${idx}`}>
                  <div className="flex items-center gap-3">
                    <Calendar className="w-5 h-5 text-[#FFD700]" />
                    <span className="font-medium text-[#422006]">{deadline.name}</span>
                  </div>
                  <span className="text-sm text-slate-600">{deadline.date}</span>
                </div>
              ))}

              {dashboard?.flagged_transactions_count > 0 && (
                <Link to="/transactions?flagged=true" className="block">
                  <div className="flex items-center justify-between p-3 bg-red-50 rounded-xl hover:bg-red-100 transition-colors" data-testid="flagged-transactions-alert">
                    <div className="flex items-center gap-3">
                      <AlertTriangle className="w-5 h-5 text-red-500" />
                      <span className="font-medium text-red-700">{t('flaggedTransactions')}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="bg-red-500 text-white text-xs px-2 py-1 rounded-full">
                        {dashboard.flagged_transactions_count}
                      </span>
                      <ArrowRight className="w-4 h-4 text-red-500" />
                    </div>
                  </div>
                </Link>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </Layout>
  );
}
