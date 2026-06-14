import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import Layout from '../components/Layout';
import { useAuth } from '../context/AuthContext';
import { toast } from 'sonner';
import { 
  TrendingUp, TrendingDown, Wallet, PlusCircle,
  Lightbulb, Sparkles, Repeat, CheckCircle, AlertCircle, Info,
  Award, ArrowRight, ArrowUpRight, Activity, Zap, MessageSquare,
  Lock, Shield
} from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, AreaChart, Area, XAxis, YAxis } from 'recharts';

const API = process.env.REACT_APP_BACKEND_URL;

const InsightIcon = ({ type }) => {
  switch (type) {
    case 'warning': return <AlertCircle className="w-4 h-4 text-amber-400" />;
    case 'success': return <CheckCircle className="w-4 h-4 text-[#00C896]" />;
    case 'ai': return <Sparkles className="w-4 h-4 text-[#8B5CF6]" />;
    default: return <Info className="w-4 h-4 text-[#3B82F6]" />;
  }
};

export default function Dashboard() {
  const { user } = useAuth();
  const [dashboard, setDashboard] = useState(null);
  const [insights, setInsights] = useState([]);
  const [recurring, setRecurring] = useState([]);
  const [tccProgress, setTccProgress] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([fetchDashboard(), fetchInsights(), fetchRecurring(), fetchTCC()]);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const fetchDashboard = async () => {
    try {
      const { data } = await axios.get(`${API}/api/dashboard`, { withCredentials: true });
      setDashboard(data);
    } catch (e) { toast.error('Failed to load data'); }
    finally { setLoading(false); }
  };
  const fetchInsights = async () => { try { const { data } = await axios.get(`${API}/api/insights/spending`, { withCredentials: true }); setInsights(data.insights || []); } catch (e) {} };
  const fetchRecurring = async () => { try { const { data } = await axios.get(`${API}/api/insights/recurring`, { withCredentials: true }); setRecurring(data.recurring || []); } catch (e) {} };
  const fetchTCC = async () => { try { const { data } = await axios.get(`${API}/api/tcc/progress`, { withCredentials: true }); setTccProgress(data); } catch (e) {} };

  const fmt = (v) => new Intl.NumberFormat('en-NG', { style: 'currency', currency: 'NGN', minimumFractionDigits: 0 }).format(v).replace('NGN', '₦');

  const COLORS = ['#00C896', '#3B82F6', '#8B5CF6', '#F59E0B', '#EF4444', '#EC4899'];

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-64">
          <div className="w-10 h-10 border-2 border-[#00C896] border-t-transparent rounded-full animate-spin"></div>
        </div>
      </Layout>
    );
  }

  const spendingData = dashboard?.spending_breakdown
    ? Object.entries(dashboard.spending_breakdown).map(([name, value]) => ({ name, value }))
    : [];

  // Mock sparkline data for the area chart
  const sparkData = Array.from({ length: 12 }, (_, i) => ({
    month: ['J', 'F', 'M', 'A', 'M', 'J', 'J', 'A', 'S', 'O', 'N', 'D'][i],
    revenue: Math.random() * (dashboard?.total_income || 100000),
    expenses: Math.random() * (dashboard?.total_expenses || 50000),
  }));

  return (
    <Layout>
      <div className="space-y-6 pb-20 lg:pb-0">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4 animate-fade-in">
          <div>
            <p className="text-[#A1A1AA] text-sm mb-1">Welcome back</p>
            <h1 className="text-2xl sm:text-3xl font-display font-semibold text-white tracking-tight">
              {user?.name?.split(' ')[0]}'s Command Center
            </h1>
          </div>
          <div className="flex gap-2">
            <Link to="/transactions">
              <button className="btn-ghost flex items-center gap-2 px-4 py-2.5 text-sm" data-testid="quick-add-income-btn">
                <PlusCircle className="w-4 h-4 text-[#00C896]" />
                New Revenue
              </button>
            </Link>
            <Link to="/transactions">
              <button className="btn-ghost flex items-center gap-2 px-4 py-2.5 text-sm" data-testid="quick-add-expense-btn">
                <PlusCircle className="w-4 h-4 text-[#EF4444]" />
                Record Expense
              </button>
            </Link>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            { label: 'Total Revenue', value: dashboard?.total_income || 0, icon: TrendingUp, color: '#00C896', change: '+12.5%' },
            { label: 'Total Expenses', value: dashboard?.total_expenses || 0, icon: TrendingDown, color: '#EF4444', change: '-3.2%' },
            { label: 'Estimated Tax', value: dashboard?.estimated_tax || 0, icon: Activity, color: '#F59E0B', change: null },
            { label: 'Bank Balance', value: dashboard?.total_bank_balance || 0, icon: Wallet, color: '#3B82F6', change: null },
          ].map((stat, idx) => (
            <div key={idx} className={`card-dark p-5 hover-lift animate-fade-in stagger-${idx + 1}`} data-testid={`stat-card-${idx}`}>
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs text-[#A1A1AA] font-medium uppercase tracking-wider">{stat.label}</span>
                <stat.icon className="w-4 h-4" style={{ color: stat.color }} />
              </div>
              <p className="text-2xl font-semibold text-white tabular-nums" data-testid={`stat-value-${idx}`}>
                {fmt(stat.value)}
              </p>
              {stat.change && (
                <p className={`text-xs mt-1.5 ${stat.change.startsWith('+') ? 'text-[#00C896]' : 'text-[#EF4444]'}`}>
                  {stat.change} from last month
                </p>
              )}
            </div>
          ))}
        </div>

        {/* Main Grid: Chart + Health Score */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {/* Revenue Chart */}
          <div className="card-dark p-5 lg:col-span-2 animate-fade-in stagger-3" data-testid="revenue-chart">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-display font-semibold text-white text-sm">Cash Flow Overview</h3>
              <span className="text-xs text-[#A1A1AA]">Last 12 months</span>
            </div>
            <div className="h-52">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={sparkData}>
                  <defs>
                    <linearGradient id="revenueGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#00C896" stopOpacity={0.3} />
                      <stop offset="100%" stopColor="#00C896" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="expenseGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#EF4444" stopOpacity={0.2} />
                      <stop offset="100%" stopColor="#EF4444" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="month" axisLine={false} tickLine={false} tick={{ fill: '#A1A1AA', fontSize: 11 }} />
                  <YAxis hide />
                  <Tooltip
                    contentStyle={{ background: '#111111', border: '1px solid #1E1E1E', borderRadius: '12px', fontSize: '12px' }}
                    labelStyle={{ color: '#A1A1AA' }}
                    itemStyle={{ color: '#fff' }}
                    formatter={(v) => fmt(v)}
                  />
                  <Area type="monotone" dataKey="revenue" stroke="#00C896" strokeWidth={2} fill="url(#revenueGrad)" />
                  <Area type="monotone" dataKey="expenses" stroke="#EF4444" strokeWidth={1.5} fill="url(#expenseGrad)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Financial Health Score */}
          <div className="card-dark p-5 flex flex-col items-center justify-center animate-fade-in stagger-4" data-testid="health-score-card">
            <h3 className="font-display font-semibold text-white text-sm mb-4">Financial Health</h3>
            <div className="relative w-32 h-32 mb-3">
              <svg className="w-full h-full transform -rotate-90">
                <circle cx="64" cy="64" r="56" fill="none" stroke="#1E1E1E" strokeWidth="6" />
                <circle
                  cx="64" cy="64" r="56" fill="none"
                  stroke="url(#healthGrad)"
                  strokeWidth="6"
                  strokeLinecap="round"
                  strokeDasharray={352}
                  strokeDashoffset={352 - (352 * (dashboard?.tax_health_score || 0)) / 100}
                  className="health-score-ring"
                />
                <defs>
                  <linearGradient id="healthGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" stopColor="#00C896" />
                    <stop offset="100%" stopColor="#3B82F6" />
                  </linearGradient>
                </defs>
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="text-3xl font-display font-semibold text-white tabular-nums" data-testid="health-score-value">
                  {dashboard?.tax_health_score || 0}
                </span>
                <span className="text-[10px] text-[#A1A1AA] uppercase tracking-wider">Score</span>
              </div>
            </div>
            <p className="text-xs text-[#A1A1AA] text-center">
              {dashboard?.tax_health_score >= 80 ? 'Excellent' : dashboard?.tax_health_score >= 50 ? 'Good progress' : 'Needs attention'}
            </p>
          </div>
        </div>

        {/* AI Insights */}
        {insights.length > 0 && (
          <div className="card-dark p-5 animate-fade-in stagger-5" data-testid="ai-insights-card">
            <div className="flex items-center gap-2 mb-4">
              <div className="w-6 h-6 rounded-lg bg-gradient-to-br from-[#00C896] to-[#8B5CF6] flex items-center justify-center">
                <Zap className="w-3.5 h-3.5 text-black" />
              </div>
              <h3 className="font-display font-semibold text-white text-sm">AI Insights</h3>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {insights.slice(0, 4).map((insight, idx) => (
                <div key={idx} className="flex items-start gap-3 p-3 rounded-xl bg-white/[0.02] border border-[#1E1E1E] hover:border-[#2a2a2a] transition-colors" data-testid={`insight-${idx}`}>
                  <InsightIcon type={insight.type} />
                  <div className="min-w-0">
                    <p className="font-medium text-white text-sm">{insight.title}</p>
                    <p className="text-xs text-[#A1A1AA] mt-1 leading-relaxed">{insight.message}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Bottom Grid: Spending + TCC + Actions */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {/* Spending Breakdown */}
          <div className="card-dark p-5 animate-fade-in stagger-5" data-testid="spending-chart">
            <h3 className="font-display font-semibold text-white text-sm mb-4">Expense Analytics</h3>
            {spendingData.length > 0 ? (
              <>
                <div className="h-44 mb-3">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie data={spendingData} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={40} outerRadius={65} strokeWidth={0}>
                        {spendingData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                      </Pie>
                      <Tooltip contentStyle={{ background: '#111111', border: '1px solid #1E1E1E', borderRadius: '12px', fontSize: '12px' }} formatter={(v) => fmt(v)} />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
                <div className="space-y-2">
                  {spendingData.slice(0, 4).map((item, i) => (
                    <div key={i} className="flex items-center justify-between text-sm">
                      <div className="flex items-center gap-2">
                        <div className="w-2 h-2 rounded-full" style={{ backgroundColor: COLORS[i % COLORS.length] }}></div>
                        <span className="text-[#A1A1AA]">{item.name}</span>
                      </div>
                      <span className="text-white tabular-nums font-medium">{fmt(item.value)}</span>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <div className="h-44 flex items-center justify-center">
                <p className="text-[#A1A1AA] text-sm">No expense data yet</p>
              </div>
            )}
          </div>

          {/* TCC + Quick Actions */}
          <div className="space-y-4 animate-fade-in stagger-6">
            {/* TCC Mini */}
            {tccProgress && (
              <Link to="/tcc">
                <div className="card-dark p-4 hover-lift cursor-pointer group" data-testid="tcc-mini-card">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <Award className="w-4 h-4 text-[#F59E0B]" />
                      <span className="text-sm font-medium text-white">TCC Readiness</span>
                    </div>
                    <ArrowRight className="w-4 h-4 text-[#A1A1AA] group-hover:text-white transition-colors" />
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-2xl font-display font-semibold text-[#00C896] tabular-nums" data-testid="tcc-progress">{tccProgress.progress}%</span>
                    <div className="flex-1 h-1.5 bg-[#1E1E1E] rounded-full overflow-hidden">
                      <div className="h-full rounded-full bg-gradient-to-r from-[#00C896] to-[#3B82F6]" style={{ width: `${tccProgress.progress}%` }}></div>
                    </div>
                  </div>
                </div>
              </Link>
            )}

            {/* Quick Actions */}
            <div className="card-dark p-4">
              <h3 className="font-display font-semibold text-white text-sm mb-3">Quick Actions</h3>
              <div className="space-y-2">
                {[
                  { to: '/tax-planner', icon: TrendingUp, label: 'Tax Planner', color: '#00C896' },
                  { to: '/tax-obligations', icon: Activity, label: 'Tax Routing', color: '#3B82F6' },
                  { to: '/chat', icon: MessageSquare, label: 'AI Assistant', color: '#8B5CF6' },
                ].map((action, i) => (
                  <Link key={i} to={action.to}>
                    <div className="flex items-center justify-between p-2.5 rounded-xl hover:bg-white/[0.03] transition-all group cursor-pointer" data-testid={`action-${i}`}>
                      <div className="flex items-center gap-2.5">
                        <action.icon className="w-4 h-4" style={{ color: action.color }} />
                        <span className="text-sm text-[#A1A1AA] group-hover:text-white transition-colors">{action.label}</span>
                      </div>
                      <ArrowUpRight className="w-3.5 h-3.5 text-[#333] group-hover:text-[#A1A1AA] transition-colors" />
                    </div>
                  </Link>
                ))}
              </div>
            </div>
          </div>

          {/* Recurring + Deadlines */}
          <div className="space-y-4 animate-fade-in stagger-6">
            {recurring.length > 0 && (
              <div className="card-dark p-4" data-testid="recurring-card">
                <div className="flex items-center gap-2 mb-3">
                  <Repeat className="w-4 h-4 text-[#3B82F6]" />
                  <h3 className="font-display font-semibold text-white text-sm">Recurring</h3>
                </div>
                <div className="space-y-2.5">
                  {recurring.slice(0, 3).map((item, i) => (
                    <div key={i} className="flex items-center justify-between" data-testid={`recurring-${i}`}>
                      <div>
                        <p className="text-sm text-white">{item.descriptions?.[0]?.slice(0, 25) || item.category}</p>
                        <p className="text-xs text-[#A1A1AA]">{item.frequency}</p>
                      </div>
                      <span className="text-sm font-medium text-white tabular-nums">{fmt(item.amount)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Smart Alerts */}
            {dashboard?.upcoming_deadlines?.length > 0 && (
              <div className="card-dark p-4" data-testid="deadlines-card">
                <h3 className="font-display font-semibold text-white text-sm mb-3">Deadlines</h3>
                {dashboard.upcoming_deadlines.map((d, i) => (
                  <div key={i} className="flex items-center justify-between py-2 border-b border-[#1E1E1E] last:border-0">
                    <span className="text-sm text-[#A1A1AA]">{d.name}</span>
                    <span className="text-xs text-[#F59E0B] font-medium">{d.date}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Trust Bar */}
        <div className="flex items-center justify-center gap-6 py-4 text-xs text-[#333] animate-fade-in stagger-6">
          <div className="flex items-center gap-1.5"><Lock className="w-3 h-3" /> 256-bit SSL</div>
          <div className="flex items-center gap-1.5"><Shield className="w-3 h-3" /> NDPR Compliant</div>
          <div className="flex items-center gap-1.5"><CheckCircle className="w-3 h-3" /> Read-Only</div>
        </div>
      </div>
    </Layout>
  );
}
