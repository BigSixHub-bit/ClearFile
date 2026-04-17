import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Layout from '../components/Layout';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Switch } from '../components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { Badge } from '../components/ui/badge';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { toast } from 'sonner';
import { 
  User, Bell, Moon, Languages, Shield, CreditCard, 
  Link2, Unlink, Building, Check, Crown, FileDown
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

export default function Settings() {
  const { user, updateSettings, logout } = useAuth();
  const { language, toggleLanguage, t } = useLanguage();
  const [bankAccounts, setBankAccounts] = useState([]);
  const [supportedBanks, setSupportedBanks] = useState([]);
  const [isLinkDialogOpen, setIsLinkDialogOpen] = useState(false);
  const [newBankAccount, setNewBankAccount] = useState({
    bank_name: '',
    account_number: '',
    account_name: ''
  });
  const [darkMode, setDarkMode] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchBankAccounts();
    fetchSupportedBanks();
  }, []);

  const fetchBankAccounts = async () => {
    try {
      const { data } = await axios.get(`${API}/api/bank-accounts`, { withCredentials: true });
      setBankAccounts(data);
    } catch (error) {
      console.error('Failed to load bank accounts');
    }
  };

  const fetchSupportedBanks = async () => {
    try {
      const { data } = await axios.get(`${API}/api/banks`, { withCredentials: true });
      setSupportedBanks(data.banks);
    } catch (error) {
      console.error('Failed to load banks');
    }
  };

  const handleLinkBank = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      // First, try Mono real bank linking
      const { data: monoData } = await axios.post(`${API}/api/mono/initiate-linking`, {}, { withCredentials: true });
      
      if (monoData.mode === 'live' && monoData.mono_url) {
        // Redirect to Mono Connect widget
        window.location.href = monoData.mono_url;
        return;
      }
      
      // Fallback to mock bank linking
      await axios.post(`${API}/api/bank-accounts`, newBankAccount, { withCredentials: true });
      toast.success('Bank account linked successfully! (Demo Mode)');
      setIsLinkDialogOpen(false);
      setNewBankAccount({ bank_name: '', account_number: '', account_name: '' });
      fetchBankAccounts();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to link bank account');
    } finally {
      setLoading(false);
    }
  };

  const handleMonoLinking = async () => {
    setLoading(true);
    try {
      const { data } = await axios.post(`${API}/api/mono/initiate-linking`, {}, { withCredentials: true });
      
      if (data.mode === 'live' && data.mono_url) {
        window.location.href = data.mono_url;
      } else {
        // Show mock dialog
        setIsLinkDialogOpen(true);
        toast.info('Mono not configured. Using simulated bank linking.');
      }
    } catch (error) {
      setIsLinkDialogOpen(true);
      toast.info('Using simulated bank linking mode.');
    } finally {
      setLoading(false);
    }
  };

  const handleUnlinkBank = async (accountId) => {
    if (!window.confirm('Are you sure you want to unlink this bank account?')) return;
    try {
      await axios.delete(`${API}/api/bank-accounts/${accountId}`, { withCredentials: true });
      toast.success('Bank account unlinked');
      fetchBankAccounts();
    } catch (error) {
      toast.error('Failed to unlink bank account');
    }
  };

  const handleToggleDarkMode = () => {
    const newMode = !darkMode;
    setDarkMode(newMode);
    document.documentElement.classList.toggle('dark', newMode);
  };

  const handleUpgradePlan = async (plan) => {
    if (user?.subscription_plan === plan) {
      toast.info('You are already on this plan');
      return;
    }
    
    setLoading(true);
    try {
      // Initialize Paystack payment
      const callbackUrl = `${window.location.origin}/settings?payment=success&plan=${plan}`;
      const { data } = await axios.post(`${API}/api/subscription/initialize`, {
        plan,
        callback_url: callbackUrl
      }, { withCredentials: true });
      
      if (data.authorization_url) {
        // Redirect to Paystack
        window.location.href = data.authorization_url;
      } else {
        // Fallback: direct upgrade (for demo/test mode)
        await axios.put(`${API}/api/user/subscription`, { plan }, { withCredentials: true });
        toast.success(`Upgraded to ${plan} plan!`);
        window.location.reload();
      }
    } catch (error) {
      // If Paystack not configured, do direct upgrade
      if (error.response?.status === 500) {
        try {
          await axios.put(`${API}/api/user/subscription`, { plan }, { withCredentials: true });
          toast.success(`Upgraded to ${plan} plan!`);
          window.location.reload();
        } catch (e) {
          toast.error('Failed to upgrade plan');
        }
      } else {
        toast.error(error.response?.data?.detail || 'Failed to initiate payment');
      }
    } finally {
      setLoading(false);
    }
  };

  // Handle payment callback
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const payment = params.get('payment');
    const reference = params.get('reference') || params.get('trxref');
    const plan = params.get('plan');
    
    if (payment === 'success' && reference) {
      // Verify payment
      axios.get(`${API}/api/subscription/verify/${reference}`, { withCredentials: true })
        .then(({ data }) => {
          if (data.status === 'success') {
            toast.success(`Successfully upgraded to ${data.plan} plan!`);
            window.history.replaceState({}, '', '/settings');
            window.location.reload();
          }
        })
        .catch(() => {
          toast.error('Payment verification failed');
        });
    } else if (params.get('bank_linked') === 'true') {
      toast.success('Bank account linked successfully!');
      window.history.replaceState({}, '', '/settings');
      fetchBankAccounts();
    }
  }, []);

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-NG', {
      style: 'currency',
      currency: 'NGN',
      minimumFractionDigits: 0
    }).format(amount).replace('NGN', '₦');
  };

  const plans = [
    { id: 'starter', name: 'Starter', price: 2000, features: ['Manual tracking', '50 transactions/month', 'Basic tax estimate'] },
    { id: 'growth', name: 'Growth', price: 4000, features: ['Bank linking (2 accounts)', '300 transactions/month', 'AI categorization', 'VAT tracking'] },
    { id: 'business', name: 'Business', price: 6000, features: ['Unlimited accounts', 'Unlimited transactions', 'PDF/Excel export', 'Multi-user access'] }
  ];

  return (
    <Layout>
      <div className="space-y-6 pb-20 lg:pb-0">
        {/* Header */}
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-[#022c22]" style={{ fontFamily: 'Outfit' }}>
            {t('settings')}
          </h1>
          <p className="text-slate-500">Manage your account and preferences</p>
        </div>

        {/* Profile */}
        <Card className="rounded-2xl border-slate-200">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2" style={{ fontFamily: 'Outfit' }}>
              <User className="w-5 h-5 text-[#006400]" />
              {t('profile')}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 bg-[#006400] rounded-2xl flex items-center justify-center text-white text-2xl font-bold">
                {user?.name?.charAt(0) || 'U'}
              </div>
              <div>
                <p className="font-bold text-[#022c22]" data-testid="user-name">{user?.name}</p>
                <p className="text-slate-500" data-testid="user-email">{user?.email}</p>
                <Badge className="mt-1 bg-[#E8F5E9] text-[#006400] capitalize" data-testid="user-business-type">
                  {user?.business_type}
                </Badge>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Subscription */}
        <Card className="rounded-2xl border-slate-200">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2" style={{ fontFamily: 'Outfit' }}>
              <Crown className="w-5 h-5 text-[#FFD700]" />
              Subscription Plan
            </CardTitle>
            <CardDescription>
              Current plan: <span className="font-bold text-[#006400] capitalize">{user?.subscription_plan}</span>
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {plans.map(plan => (
                <div
                  key={plan.id}
                  className={`p-4 rounded-xl border-2 ${
                    user?.subscription_plan === plan.id
                      ? 'border-[#006400] bg-[#E8F5E9]'
                      : 'border-slate-200'
                  }`}
                  data-testid={`plan-option-${plan.id}`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-bold text-[#022c22]">{plan.name}</h4>
                    {user?.subscription_plan === plan.id && (
                      <Badge className="bg-[#006400] text-white">Current</Badge>
                    )}
                  </div>
                  <p className="text-2xl font-bold text-[#006400] mb-3">
                    {formatCurrency(plan.price)}<span className="text-sm font-normal text-slate-500">/mo</span>
                  </p>
                  <ul className="space-y-1 mb-4">
                    {plan.features.map((f, i) => (
                      <li key={i} className="text-sm text-slate-600 flex items-center gap-2">
                        <Check className="w-4 h-4 text-[#006400]" />
                        {f}
                      </li>
                    ))}
                  </ul>
                  {user?.subscription_plan !== plan.id && (
                    <Button
                      onClick={() => handleUpgradePlan(plan.id)}
                      disabled={loading}
                      variant={plan.id === 'growth' ? 'default' : 'outline'}
                      className={`w-full rounded-xl ${
                        plan.id === 'growth' ? 'bg-[#006400] hover:bg-[#004d00] text-white' : ''
                      }`}
                      data-testid={`upgrade-to-${plan.id}`}
                    >
                      {loading ? 'Processing...' : (
                        plans.findIndex(p => p.id === user?.subscription_plan) < plans.findIndex(p => p.id === plan.id)
                          ? 'Upgrade with Paystack'
                          : 'Switch Plan'
                      )}
                    </Button>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Bank Accounts */}
        <Card className="rounded-2xl border-slate-200">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg flex items-center gap-2" style={{ fontFamily: 'Outfit' }}>
                <Building className="w-5 h-5 text-[#006400]" />
                Bank Accounts
              </CardTitle>
              {user?.subscription_plan !== 'starter' && (
                <div className="flex gap-2">
                  <Button 
                    onClick={handleMonoLinking}
                    disabled={loading}
                    className="bg-[#006400] hover:bg-[#004d00] text-white rounded-xl" 
                    data-testid="link-bank-btn"
                  >
                    <Link2 className="w-4 h-4 mr-2" />
                    {loading ? 'Connecting...' : 'Link Bank'}
                  </Button>
                </div>
              )}
            </div>
          </CardHeader>

          {/* Mock Bank Dialog (fallback when Mono not configured) */}
          <Dialog open={isLinkDialogOpen} onOpenChange={setIsLinkDialogOpen}>
            <DialogContent className="sm:max-w-md">
              <DialogHeader>
                <DialogTitle>Link Bank Account (Demo Mode)</DialogTitle>
              </DialogHeader>
              <form onSubmit={handleLinkBank} className="space-y-4">
                <div className="bg-[#FFF8E1] p-3 rounded-xl border border-[#FFE082]">
                  <p className="text-xs text-[#6D4C41]">
                    <strong>Note:</strong> This is a simulated bank linking for demo purposes. 
                    Real Mono/Okra integration requires API keys.
                  </p>
                </div>
                <div className="space-y-2">
                  <Label>Bank</Label>
                  <Select
                    value={newBankAccount.bank_name}
                    onValueChange={(v) => setNewBankAccount({ ...newBankAccount, bank_name: v })}
                  >
                    <SelectTrigger className="rounded-xl" data-testid="bank-select">
                      <SelectValue placeholder="Select your bank" />
                    </SelectTrigger>
                    <SelectContent>
                      {supportedBanks.map(bank => (
                        <SelectItem key={bank} value={bank}>{bank}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label>Account Number</Label>
                  <Input
                    value={newBankAccount.account_number}
                    onChange={(e) => setNewBankAccount({ ...newBankAccount, account_number: e.target.value })}
                    placeholder="0123456789"
                    maxLength={10}
                    className="rounded-xl"
                    required
                    data-testid="account-number-input"
                  />
                </div>

                <div className="space-y-2">
                  <Label>Account Name</Label>
                  <Input
                    value={newBankAccount.account_name}
                    onChange={(e) => setNewBankAccount({ ...newBankAccount, account_name: e.target.value })}
                    placeholder="John Doe"
                    className="rounded-xl"
                    required
                    data-testid="account-name-input"
                  />
                </div>

                <Button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-[#006400] hover:bg-[#004d00] text-white rounded-xl"
                  data-testid="submit-link-bank"
                >
                  {loading ? 'Linking...' : 'Link Bank Account (Demo)'}
                </Button>
              </form>
            </DialogContent>
          </Dialog>

          <CardContent>
            {user?.subscription_plan === 'starter' ? (
              <div className="text-center py-8 bg-slate-50 rounded-xl">
                <Shield className="w-12 h-12 text-slate-300 mx-auto mb-3" />
                <p className="text-slate-600 mb-2">Bank linking requires Growth or Business plan</p>
                <Button
                  onClick={() => handleUpgradePlan('growth')}
                  className="bg-[#006400] hover:bg-[#004d00] text-white rounded-xl"
                  data-testid="upgrade-for-bank"
                >
                  Upgrade to Growth
                </Button>
              </div>
            ) : bankAccounts.length === 0 ? (
              <div className="text-center py-8 text-slate-400">
                <Building className="w-12 h-12 mx-auto mb-3 opacity-50" />
                <p>No bank accounts linked yet</p>
              </div>
            ) : (
              <div className="space-y-3">
                {bankAccounts.map((account, idx) => (
                  <div
                    key={account.id || idx}
                    className="flex items-center justify-between p-4 bg-slate-50 rounded-xl"
                    data-testid={`bank-account-${idx}`}
                  >
                    <div>
                      <p className="font-medium text-[#022c22]">{account.bank_name}</p>
                      <p className="text-sm text-slate-500">{account.account_number} • {account.account_name}</p>
                      <p className="text-sm font-medium text-[#006400]">{formatCurrency(account.balance)}</p>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleUnlinkBank(account.id)}
                      className="text-red-500 hover:text-red-700 hover:bg-red-50"
                      data-testid={`unlink-bank-${idx}`}
                    >
                      <Unlink className="w-4 h-4 mr-1" />
                      Unlink
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Preferences */}
        <Card className="rounded-2xl border-slate-200">
          <CardHeader>
            <CardTitle className="text-lg" style={{ fontFamily: 'Outfit' }}>Preferences</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between p-4 bg-slate-50 rounded-xl">
              <div className="flex items-center gap-3">
                <Moon className="w-5 h-5 text-slate-600" />
                <div>
                  <p className="font-medium text-[#022c22]">{t('darkMode')}</p>
                  <p className="text-sm text-slate-500">Switch to dark theme</p>
                </div>
              </div>
              <Switch
                checked={darkMode}
                onCheckedChange={handleToggleDarkMode}
                data-testid="dark-mode-toggle"
              />
            </div>

            <div className="flex items-center justify-between p-4 bg-slate-50 rounded-xl">
              <div className="flex items-center gap-3">
                <Languages className="w-5 h-5 text-slate-600" />
                <div>
                  <p className="font-medium text-[#022c22]">{t('pidginMode')}</p>
                  <p className="text-sm text-slate-500">Switch to Pidgin English</p>
                </div>
              </div>
              <Switch
                checked={language === 'pidgin'}
                onCheckedChange={toggleLanguage}
                data-testid="pidgin-mode-toggle"
              />
            </div>
          </CardContent>
        </Card>

        {/* Export Data */}
        {user?.subscription_plan !== 'starter' && (
          <Card className="rounded-2xl border-slate-200">
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2" style={{ fontFamily: 'Outfit' }}>
                <FileDown className="w-5 h-5 text-[#006400]" />
                Export Data
              </CardTitle>
              <CardDescription>Download your financial data as CSV or JSON</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Button
                  variant="outline"
                  className="rounded-xl border-slate-200 hover:bg-[#E8F5E9]"
                  onClick={() => window.open(`${API}/api/export/transactions?format=csv&period=all`, '_blank')}
                  data-testid="export-transactions-csv"
                >
                  <FileDown className="w-4 h-4 mr-2" />
                  Export Transactions (CSV)
                </Button>
                <Button
                  variant="outline"
                  className="rounded-xl border-slate-200 hover:bg-[#E8F5E9]"
                  onClick={() => window.open(`${API}/api/export/tax-report?format=csv`, '_blank')}
                  data-testid="export-tax-report-csv"
                >
                  <FileDown className="w-4 h-4 mr-2" />
                  Export Tax Report (CSV)
                </Button>
              </div>
              <p className="text-xs text-slate-500">
                Note: You'll need to be logged in for exports to work. If download fails, try refreshing the page first.
              </p>
            </CardContent>
          </Card>
        )}

        {/* Security */}
        <Card className="rounded-2xl border-slate-200 bg-[#E8F5E9]">
          <CardContent className="p-6">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-[#006400] rounded-xl flex items-center justify-center">
                <Shield className="w-6 h-6 text-white" />
              </div>
              <div>
                <h3 className="font-bold text-[#006400]">Bank-Level Security</h3>
                <p className="text-sm text-slate-600">
                  Your data is protected with 256-bit encryption. We only have read-only access to your bank accounts.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </Layout>
  );
}
