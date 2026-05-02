import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Layout from '../components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { useAuth } from '../context/AuthContext';
import { toast } from 'sonner';
import { 
  Calculator, PiggyBank, TrendingUp, ArrowRight, Wallet
} from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';

const API = process.env.REACT_APP_BACKEND_URL;

export default function TaxPlanner() {
  const { user } = useAuth();
  const [income, setIncome] = useState('5000000');
  const [expenses, setExpenses] = useState('1500000');
  const [deductPct, setDeductPct] = useState('70');
  const [bizType, setBizType] = useState(user?.business_type || 'freelancer');
  const [result, setResult] = useState(null);
  const [reserve, setReserve] = useState(0);
  const [setAsideAmount, setSetAsideAmount] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchReserve();
    if (income && expenses) simulate();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const fetchReserve = async () => {
    try {
      const { data } = await axios.get(`${API}/api/tax-planner/reserve`, { withCredentials: true });
      setReserve(data.amount || 0);
    } catch (e) { /* ignore */ }
  };

  const simulate = async () => {
    setLoading(true);
    try {
      const { data } = await axios.post(`${API}/api/tax-planner/simulate`, {
        annual_income: parseFloat(income) || 0,
        annual_expenses: parseFloat(expenses) || 0,
        deductible_percentage: parseFloat(deductPct) || 70,
        business_type: bizType
      }, { withCredentials: true });
      setResult(data);
    } catch (error) {
      toast.error('Simulation failed');
    } finally {
      setLoading(false);
    }
  };

  const handleSetAside = async () => {
    if (!setAsideAmount || parseFloat(setAsideAmount) <= 0) return;
    try {
      const { data } = await axios.post(`${API}/api/tax-planner/set-aside`, {
        amount: parseFloat(setAsideAmount)
      }, { withCredentials: true });
      setReserve(data.total_reserve);
      setSetAsideAmount('');
      toast.success(`Set aside N${parseFloat(setAsideAmount).toLocaleString()} for tax reserve`);
    } catch (error) {
      toast.error('Failed to set aside');
    }
  };

  const formatCurrency = (v) => new Intl.NumberFormat('en-NG', { style: 'currency', currency: 'NGN', minimumFractionDigits: 0 }).format(v).replace('NGN', 'N');

  const COLORS = ['#006400', '#ef4444', '#FFD700', '#3b82f6'];

  const pieData = result ? [
    { name: 'Take Home', value: Math.max(0, result.breakdown.take_home) },
    { name: 'Tax', value: result.total_tax },
    { name: 'Expenses', value: result.annual_expenses },
  ].filter(d => d.value > 0) : [];

  return (
    <Layout>
      <div className="space-y-6 pb-20 lg:pb-0">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-[#022c22]" style={{ fontFamily: 'Outfit' }}>
            Tax Planner
          </h1>
          <p className="text-slate-500">What-if tax scenario simulator</p>
        </div>

        {/* Input Card */}
        <Card className="rounded-2xl border-slate-200" data-testid="tax-planner-inputs">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2" style={{ fontFamily: 'Outfit' }}>
              <Calculator className="w-5 h-5 text-[#006400]" />
              Simulate Your Tax Scenario
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Annual Income (N)</Label>
                <Input type="number" value={income} onChange={e => setIncome(e.target.value)} className="rounded-xl" data-testid="planner-income-input" />
              </div>
              <div className="space-y-2">
                <Label>Annual Expenses (N)</Label>
                <Input type="number" value={expenses} onChange={e => setExpenses(e.target.value)} className="rounded-xl" data-testid="planner-expenses-input" />
              </div>
              <div className="space-y-2">
                <Label>Deductible % of Expenses</Label>
                <Input type="number" min="0" max="100" value={deductPct} onChange={e => setDeductPct(e.target.value)} className="rounded-xl" data-testid="planner-deduct-input" />
              </div>
              <div className="space-y-2">
                <Label>Business Type</Label>
                <Select value={bizType} onValueChange={setBizType}>
                  <SelectTrigger className="rounded-xl" data-testid="planner-biz-type">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="freelancer">Freelancer</SelectItem>
                    <SelectItem value="sme">Small Business (SME)</SelectItem>
                    <SelectItem value="company">Company</SelectItem>
                    <SelectItem value="salary_earner">Salary Earner</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <Button onClick={simulate} disabled={loading} className="w-full bg-[#006400] hover:bg-[#004d00] text-white rounded-xl" data-testid="simulate-btn">
              {loading ? 'Calculating...' : 'Calculate Tax Estimate'}
            </Button>
          </CardContent>
        </Card>

        {/* Results */}
        {result && (
          <>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Pie Chart */}
              <Card className="rounded-2xl border-slate-200" data-testid="tax-planner-chart">
                <CardHeader>
                  <CardTitle className="text-lg" style={{ fontFamily: 'Outfit' }}>Income Breakdown</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={90} label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}>
                          {pieData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                        </Pie>
                        <Tooltip formatter={v => formatCurrency(v)} />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                  <div className="space-y-2 mt-4">
                    {pieData.map((item, i) => (
                      <div key={i} className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <div className="w-3 h-3 rounded-full" style={{ backgroundColor: COLORS[i] }}></div>
                          <span className="text-sm text-slate-600">{item.name}</span>
                        </div>
                        <span className="text-sm font-medium">{formatCurrency(item.value)}</span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* Numbers */}
              <Card className="rounded-2xl border-slate-200" data-testid="tax-planner-results">
                <CardHeader>
                  <CardTitle className="text-lg" style={{ fontFamily: 'Outfit' }}>Tax Estimate</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex justify-between p-3 bg-[#E8F5E9] rounded-xl">
                    <span className="text-slate-600">Income Tax ({result.tax_type})</span>
                    <span className="font-bold text-[#006400]" data-testid="result-income-tax">{formatCurrency(result.income_tax)}</span>
                  </div>
                  {result.vat > 0 && (
                    <div className="flex justify-between p-3 bg-blue-50 rounded-xl">
                      <span className="text-slate-600">VAT (7.5%)</span>
                      <span className="font-bold text-blue-600" data-testid="result-vat">{formatCurrency(result.vat)}</span>
                    </div>
                  )}
                  <div className="flex justify-between p-4 bg-[#006400] rounded-xl text-white">
                    <span className="font-bold">Total Tax</span>
                    <span className="font-bold text-xl" data-testid="result-total-tax">{formatCurrency(result.total_tax)}</span>
                  </div>
                  <div className="flex justify-between p-3 bg-[#FFF8E1] rounded-xl">
                    <span className="text-slate-600">Effective Tax Rate</span>
                    <span className="font-bold text-[#422006]">{result.effective_tax_rate}%</span>
                  </div>
                  <div className="flex justify-between p-3 bg-slate-50 rounded-xl">
                    <span className="text-slate-600">After-Tax Income</span>
                    <span className="font-bold text-[#006400]">{formatCurrency(result.after_tax_income)}</span>
                  </div>
                  <div className="flex justify-between p-3 bg-amber-50 rounded-xl border border-amber-200">
                    <span className="text-slate-600">Monthly Savings Needed</span>
                    <span className="font-bold text-amber-700">{formatCurrency(result.monthly_tax_savings)}</span>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Set Aside */}
            <Card className="rounded-2xl border-[#FFD700] bg-[#FFF8E1]" data-testid="set-aside-card">
              <CardContent className="p-6">
                <div className="flex items-start gap-4">
                  <div className="w-12 h-12 bg-[#FFD700] rounded-xl flex items-center justify-center flex-shrink-0">
                    <PiggyBank className="w-6 h-6 text-[#422006]" />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-bold text-[#422006] text-lg mb-1">Tax Reserve</h3>
                    <p className="text-slate-600 text-sm mb-3">
                      Current reserve: <span className="font-bold text-[#006400]">{formatCurrency(reserve)}</span>
                      {result && <> | Recommended monthly: <span className="font-bold">{formatCurrency(result.monthly_tax_savings)}</span></>}
                    </p>
                    <div className="flex gap-2">
                      <Input type="number" placeholder="Amount to set aside" value={setAsideAmount} onChange={e => setSetAsideAmount(e.target.value)} className="rounded-xl flex-1 bg-white" data-testid="set-aside-input" />
                      <Button onClick={handleSetAside} className="bg-[#006400] hover:bg-[#004d00] text-white rounded-xl" data-testid="set-aside-btn">
                        <Wallet className="w-4 h-4 mr-2" />
                        Set Aside
                      </Button>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </>
        )}
      </div>
    </Layout>
  );
}
