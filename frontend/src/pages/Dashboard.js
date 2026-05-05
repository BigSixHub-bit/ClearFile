import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import Layout from '../components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { toast } from 'sonner';
import { 
  TrendingUp, TrendingDown, Calculator, Wallet, PlusCircle, 
  Camera, FileText, Link2, AlertTriangle, Calendar, ArrowRight,
  Lightbulb, RefreshCw, Sparkles, Repeat, Info, CheckCircle, AlertCircle,
  Award, Landmark, TrendingUp as Planner, Shield, Lock, MessageSquare
} from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';

const API = process.env.REACT_APP_BACKEND_URL;

const InsightIcon = ({ type }) => {
  switch (type) {
    case 'warning': return <AlertCircle className="w-5 h-5 text-amber-500" />;
    case 'success': return <CheckCircle className="w-5 h-5 text-[#006400]" />;
    case 'ai': return <Sparkles className="w-5 h-5 text-purple-500" />;
    default: return <Info className="w-5 h-5 text-blue-500" />;
  }
};

const insightBg = {
  warning: 'bg-amber-50 border-amber-200',
  success: 'bg-[#E8F5E9] border-[#A5D6A7]',
  ai: 'bg-purple-50 border-purple-200',
  info: 'bg-blue-50 border-blue-200',
};

export default function Dashboard() {
  const { user } = useAuth();
  const { t } = useLanguage();
  const [dashboard, setDashboard] = useState(null);
  const [insights, setInsights] = useState([]);
  const [recurring, setRecurring] = useState([]);
  const [loading, setLoading] = useState(true);
  const [tccProgress, setTccProgress] = useState(null);

  useEffect(() => {
    fetchDashboard();
    fetchInsights();
    fetchRecurring();
    fetchTCCProgress();
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

  const fetchInsights = async () => {
    try {
      const { data } = await axios.get(`${API}/api/insights/spending`, { withCredentials: true });
      setInsights(data.insights || []);
    } catch (error) {
      console.error('Failed to load insights');
    }
  };

  const fetchRecurring = async () => {
    try {
      const { data } = await axios.get(`${API}/api/insights/recurring`, { withCredentials: true });
      setRecurring(data.recurring || []);
    } catch (error) {
      console.error('Failed to load recurring');
    }
  };

  const fetchTCCProgress = async () => {
    try {
      const { data } = await axios.get(`${API}/api/tcc/progress`, { withCredentials: true });
      setTccProgress(data);
    } catch (error) {
      console.error('Failed to load TCC');
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
            <p className="text-slate-500">{t('welcomeBack')}, {user?.name?.split(' ')[0]}!</p>
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
              <p className="text-xs text-slate-400 mt-1">{t('allTime')}</p>
            </CardContent>
          </Card>

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
              <p className="text-xs text-slate-400 mt-1">{t('allTime')}</p>
            </CardContent>
          </Card>

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
              <p className="text-xs text-slate-400 mt-1">{t('incomeTaxVat')}: {formatCurrency(dashboard?.vat_owed || 0)}</p>
            </CardContent>
          </Card>

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
              <p className="text-xs text-slate-400 mt-1">{dashboard?.bank_accounts_count || 0} {t('accountsLinked')}</p>
            </CardContent>
          </Card>
        </div>

        {/* Smart Insights */}
        {insights.length > 0 && (
          <Card className="rounded-2xl border-slate-200" data-testid="smart-insights-card">
            <CardHeader className="pb-3">
              <CardTitle className="text-lg flex items-center gap-2" style={{ fontFamily: 'Outfit' }}>
                <Lightbulb className="w-5 h-5 text-[#FFD700]" />
                {t('smartInsights')}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {insights.slice(0, 4).map((insight, idx) => (
                  <div
                    key={idx}
                    className={`p-4 rounded-xl border ${insightBg[insight.type] || insightBg.info}`}
                    data-testid={`insight-${idx}`}
                  >
                    <div className="flex items-start gap-3">
                      <InsightIcon type={insight.type} />
                      <div className="flex-1 min-w-0">
                        <p className="font-semibold text-sm text-[#022c22]">{insight.title}</p>
                        <p className="text-xs text-slate-600 mt-1 leading-relaxed">{insight.message}</p>
                        {insight.action && (
                          <Link to={
                            insight.action === 'View Transactions' ? '/transactions' :
                            insight.action === 'View Tax Calculator' ? '/tax-calculator' :
                            insight.action === 'Chat with Assistant' ? '/chat' :
                            '/transactions'
                          }>
                            <Button variant="link" className="h-auto p-0 mt-2 text-xs text-[#006400] font-medium">
                              {insight.action} <ArrowRight className="w-3 h-3 ml-1" />
                            </Button>
                          </Link>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Tax Health Score & Spending Breakdown */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <Card className="rounded-2xl border-slate-200" data-testid="tax-health-score-card">
            <CardHeader>
              <CardTitle className="text-lg" style={{ fontFamily: 'Outfit' }}>{t('taxHealthScore')}</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col items-center pb-6">
              <div className="relative w-40 h-40 mb-4">
                <svg className="w-full h-full transform -rotate-90">
                  <circle cx="80" cy="80" r="70" fill="none" stroke="#e2e8f0" strokeWidth="12" />
                  <circle
                    cx="80" cy="80" r="70" fill="none"
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
                  ? t('healthExcellent')
                  : dashboard?.tax_health_score >= 50
                  ? t('healthGood')
                  : t('healthLow')}
              </p>
            </CardContent>
          </Card>

          <Card className="rounded-2xl border-slate-200 lg:col-span-2" data-testid="spending-breakdown-card">
            <CardHeader>
              <CardTitle className="text-lg" style={{ fontFamily: 'Outfit' }}>{t('spendingBreakdown')}</CardTitle>
            </CardHeader>
            <CardContent>
              {spendingData.length > 0 ? (
                <div className="flex flex-col lg:flex-row items-center gap-6">
                  <div className="w-full lg:w-1/2 h-64">
                    <ResponsiveContainer width="100%" height="100%">
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
                  <p>{t('noExpenses')}</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Recurring Expenses */}
        {recurring.length > 0 && (
          <Card className="rounded-2xl border-slate-200" data-testid="recurring-expenses-card">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg flex items-center gap-2" style={{ fontFamily: 'Outfit' }}>
                  <Repeat className="w-5 h-5 text-[#006400]" />
                  {t('recurringExpenses')}
                </CardTitle>
                <Badge variant="outline" className="text-[#006400] border-[#006400]">
                  {formatCurrency(recurring.reduce((a, r) => a + r.estimated_monthly, 0))}{t('perMonth')}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {recurring.slice(0, 5).map((item, idx) => (
                  <div key={idx} className="flex items-center justify-between p-3 bg-slate-50 rounded-xl" data-testid={`recurring-${idx}`}>
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-[#E8F5E9] rounded-lg flex items-center justify-center">
                        <RefreshCw className="w-4 h-4 text-[#006400]" />
                      </div>
                      <div>
                        <p className="font-medium text-sm text-[#022c22]">{item.descriptions?.[0] || item.category}</p>
                        <p className="text-xs text-slate-500">{item.frequency} &middot; {item.occurrences} {t('occurrences')}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="font-semibold text-sm text-[#022c22]">{formatCurrency(item.amount)}</p>
                      <p className="text-xs text-slate-400">{item.frequency === 'Monthly' ? 'per month' : item.frequency.toLowerCase()}</p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Quick Actions & Alerts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* TCC Progress + Quick Actions */}
          <div className="space-y-6">
            {/* TCC Progress Mini Card */}
            {tccProgress && (
              <Link to="/tcc">
                <Card className="rounded-2xl border-[#FFD700] bg-gradient-to-r from-[#FFF8E1] to-white hover:shadow-md transition-shadow cursor-pointer" data-testid="tcc-mini-card">
                  <CardContent className="p-5">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="w-12 h-12 bg-[#FFD700] rounded-xl flex items-center justify-center">
                          <Award className="w-6 h-6 text-[#422006]" />
                        </div>
                        <div>
                          <p className="font-bold text-[#422006]">TCC Readiness</p>
                          <p className="text-sm text-slate-500">{tccProgress.completed_count}/{tccProgress.total_count} requirements met</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="text-2xl font-bold text-[#006400]" data-testid="tcc-dashboard-progress">{tccProgress.progress}%</span>
                        <ArrowRight className="w-5 h-5 text-slate-400" />
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </Link>
            )}

            {/* Quick Actions */}
            <Card className="rounded-2xl border-slate-200">
              <CardHeader>
                <CardTitle className="text-lg" style={{ fontFamily: 'Outfit' }}>{t('quickActions')}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <Link to="/transactions" className="block">
                  <Button variant="outline" className="w-full justify-start rounded-xl border-slate-200 hover:bg-[#E8F5E9]" data-testid="action-scan-receipt">
                    <Camera className="w-5 h-5 mr-3 text-[#006400]" />
                    {t('scanReceipt')}
                  </Button>
                </Link>
                <Link to="/tax-planner" className="block">
                  <Button variant="outline" className="w-full justify-start rounded-xl border-slate-200 hover:bg-[#E8F5E9]" data-testid="action-tax-planner">
                    <Calculator className="w-5 h-5 mr-3 text-[#006400]" />
                    Tax Planner
                  </Button>
                </Link>
                <Link to="/tax-obligations" className="block">
                  <Button variant="outline" className="w-full justify-start rounded-xl border-slate-200 hover:bg-[#E8F5E9]" data-testid="action-tax-routing">
                    <Landmark className="w-5 h-5 mr-3 text-[#006400]" />
                    State vs Federal Tax
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
          </div>

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

        {/* WhatsApp Expense Logging */}
        <Card className="rounded-2xl border-[#25D366] bg-gradient-to-r from-[#25D366]/5 to-white overflow-hidden" data-testid="whatsapp-card">
          <CardContent className="p-6">
            <div className="flex flex-col sm:flex-row items-center gap-6">
              <div className="w-16 h-16 bg-[#25D366] rounded-2xl flex items-center justify-center flex-shrink-0">
                <MessageSquare className="w-8 h-8 text-white" />
              </div>
              <div className="flex-1 text-center sm:text-left">
                <h3 className="text-lg font-bold text-[#022c22]" style={{ fontFamily: 'Outfit' }}>Log Expenses via WhatsApp</h3>
                <p className="text-sm text-slate-500 mt-1">Don't want to open the app? Just text your expenses to our AI bot.</p>
              </div>
              <Link to="/settings#whatsapp">
                <Button className="bg-[#25D366] hover:bg-[#1DA851] text-white rounded-xl px-6 py-5 flex items-center gap-2" data-testid="connect-whatsapp-btn">
                  <svg viewBox="0 0 24 24" className="w-5 h-5 fill-current"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>
                  Connect WhatsApp Bot
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>

        {/* Trust & Security Signals */}
        <Card className="rounded-2xl border-[#A5D6A7] bg-gradient-to-r from-[#E8F5E9] to-white" data-testid="trust-signals-card">
          <CardContent className="p-6">
            <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
              <div className="flex items-center gap-6 flex-wrap justify-center">
                <div className="flex items-center gap-2">
                  <Lock className="w-5 h-5 text-[#006400]" />
                  <span className="text-sm font-medium text-[#006400]">256-bit SSL</span>
                </div>
                <div className="flex items-center gap-2">
                  <Shield className="w-5 h-5 text-[#006400]" />
                  <span className="text-sm font-medium text-[#006400]">NDPR Compliant</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-5 h-5 text-[#006400]" />
                  <span className="text-sm font-medium text-[#006400]">Read-Only Access</span>
                </div>
              </div>
              <div className="flex items-center gap-3 text-xs text-slate-400">
                <span className="font-medium">Secured by:</span>
                <span>Mono</span>
                <span>Okra</span>
                <span>Stitch</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </Layout>
  );
}
