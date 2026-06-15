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
  Link2, Unlink, Building, Check, Crown, FileDown, Users,
  Brain, Trash2, Edit2, Lock, MessageSquare
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

export default function Settings() {
  const { user, updateSettings, logout } = useAuth();
  const { language, toggleLanguage, t } = useLanguage();
  const [bankAccounts, setBankAccounts] = useState([]);
  const [supportedBanks, setSupportedBanks] = useState([]);
  const [memories, setMemories] = useState([]);
  const [waSettings, setWaSettings] = useState({ transaction_notifications: true, weekly_summary: true, tax_reminders: true, phone: null });
  const [isLinkDialogOpen, setIsLinkDialogOpen] = useState(false);
  const [newBankAccount, setNewBankAccount] = useState({
    bank_name: '',
    account_number: '',
    account_name: ''
  });
  const [darkMode, setDarkMode] = useState(false);
  const [loading, setLoading] = useState(false);
  const [teamMembers, setTeamMembers] = useState([]);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState('viewer');

  useEffect(() => {
    fetchBankAccounts();
    fetchSupportedBanks();
    fetchMemories();
    fetchWaSettings();
    if (user?.subscription_plan === 'business') {
      fetchTeamMembers();
    }
  }, [user]);

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

  const fetchMemories = async () => {
    try {
      const { data } = await axios.get(`${API}/api/transaction-memory`, { withCredentials: true });
      setMemories(data);
    } catch (e) {}
  };

  const fetchWaSettings = async () => {
    try {
      const { data } = await axios.get(`${API}/api/whatsapp/settings`, { withCredentials: true });
      setWaSettings(data);
    } catch (e) {}
  };

  const handleDeleteMemory = async (memId) => {
    try {
      await axios.delete(`${API}/api/transaction-memory/${memId}`, { withCredentials: true });
      toast.success('Memory cleared');
      fetchMemories();
    } catch (e) { toast.error('Failed to delete'); }
  };

  const handleToggleWaSetting = async (key) => {
    const updated = { ...waSettings, [key]: !waSettings[key] };
    setWaSettings(updated);
    try {
      await axios.put(`${API}/api/whatsapp/settings`, { [key]: updated[key] }, { withCredentials: true });
    } catch (e) { toast.error('Failed to update setting'); }
  };

  const fetchTeamMembers = async () => {
    try {
      const { data } = await axios.get(`${API}/api/team/members`, { withCredentials: true });
      setTeamMembers(data);
    } catch (error) {
      console.error('Failed to load team members');
    }
  };

  const handleInviteTeamMember = async () => {
    if (!inviteEmail) return;
    setLoading(true);
    try {
      await axios.post(`${API}/api/team/invite`, {
        email: inviteEmail,
        role: inviteRole
      }, { withCredentials: true });
      toast.success('Invitation sent!');
      setInviteEmail('');
      fetchTeamMembers();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to send invitation');
    } finally {
      setLoading(false);
    }
  };

  const handleRemoveTeamMember = async (memberId) => {
    if (!window.confirm('Remove this team member?')) return;
    try {
      await axios.delete(`${API}/api/team/members/${memberId}`, { withCredentials: true });
      toast.success('Team member removed');
      fetchTeamMembers();
    } catch (error) {
      toast.error('Failed to remove team member');
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
      const callbackUrl = `${window.location.origin}/payment-success`;
      const { data } = await axios.post(`${API}/api/subscription/initialize`, {
        plan,
        callback_url: callbackUrl
      }, { withCredentials: true });
      
      if (data.payment_link) {
        window.location.href = data.payment_link;
      } else if (data.mock || data.upgraded) {
        toast.success(`Upgraded to ${plan} plan!`);
        window.location.reload();
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to initiate payment');
    } finally {
      setLoading(false);
    }
  };

  // Handle bank link callback
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get('bank_linked') === 'true') {
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
    { id: 'starter', name: 'Starter', price: 2000, target: 'Freelancers / Simple Income', features: ['Manual income & expense tracking', 'Basic tax estimate & filing reminders', 'Receipt scanner (Up to 20/month)', 'Up to 100 transactions/month'] },
    { id: 'pro', name: 'Pro', price: 4000, popular: true, target: 'Power Users & Small Businesses', features: ['Everything in Starter', 'Unlimited bank account linking', 'Unlimited transactions & AI Auto-categorization', 'VAT & WHT tracking', 'Full AI Tax Assistant', '1-Click PDF/Excel tax report exports'] }
  ];

  return (
    <Layout>
      <div className="space-y-6 pb-20 lg:pb-0">
        {/* Header */}
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white" style={{ fontFamily: 'Clash Display, Satoshi, sans-serif' }}>
            {t('settings')}
          </h1>
          <p className="text-[#A1A1AA]">{t('manageAccount')}</p>
        </div>

        {/* Profile */}
        <Card className="card-dark">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2" style={{ fontFamily: 'Clash Display, Satoshi, sans-serif' }}>
              <User className="w-5 h-5 text-[#00C896]" />
              {t('profile')}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 bg-[#00C896] rounded-2xl flex items-center justify-center text-white text-2xl font-bold">
                {user?.name?.charAt(0) || 'U'}
              </div>
              <div>
                <p className="font-bold text-white" data-testid="user-name">{user?.name}</p>
                <p className="text-[#A1A1AA]" data-testid="user-email">{user?.email}</p>
                <Badge className="mt-1 bg-[#00C896]/10 text-[#00C896] capitalize" data-testid="user-business-type">
                  {user?.business_type}
                </Badge>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Subscription */}
        <Card className="card-dark">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2" style={{ fontFamily: 'Clash Display, Satoshi, sans-serif' }}>
              <Crown className="w-5 h-5 text-[#F59E0B]" />
              Subscription Plan
            </CardTitle>
            <CardDescription>
              Current plan: <span className="font-bold text-[#00C896] capitalize">{user?.subscription_plan}</span>
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-3xl mx-auto">
              {plans.map(plan => (
                <div
                  key={plan.id}
                  className={`p-6 rounded-2xl border-2 transition-all ${
                    user?.subscription_plan === plan.id || (user?.subscription_plan === 'growth' && plan.id === 'pro')
                      ? 'border-[#006400] bg-[#00C896]/10'
                      : plan.popular
                      ? 'border-[#006400]  shadow-[#006400]/10'
                      : 'border-[#1E1E1E]'
                  }`}
                  data-testid={`plan-option-${plan.id}`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <h4 className="font-bold text-lg text-white">{plan.name}</h4>
                    <div className="flex gap-2">
                      {plan.popular && (
                        <Badge className="bg-[#F59E0B] text-white font-bold">Most Popular</Badge>
                      )}
                      {(user?.subscription_plan === plan.id || (user?.subscription_plan === 'growth' && plan.id === 'pro')) && (
                        <Badge className="bg-[#00C896] text-white">Current</Badge>
                      )}
                    </div>
                  </div>
                  <p className="text-xs text-[#A1A1AA] mb-3">{plan.target}</p>
                  <p className="text-3xl font-bold text-[#00C896] mb-4">
                    {formatCurrency(plan.price)}<span className="text-sm font-normal text-[#A1A1AA]">/mo</span>
                  </p>
                  <ul className="space-y-2 mb-6">
                    {plan.features.map((f, i) => (
                      <li key={i} className="text-sm text-[#A1A1AA] flex items-start gap-2">
                        <Check className="w-4 h-4 text-[#00C896] flex-shrink-0 mt-0.5" />
                        {f}
                      </li>
                    ))}
                  </ul>
                  {!(user?.subscription_plan === plan.id || (user?.subscription_plan === 'growth' && plan.id === 'pro')) && (
                    <Button
                      onClick={() => handleUpgradePlan(plan.id === 'pro' ? 'growth' : plan.id)}
                      disabled={loading}
                      className={`w-full rounded-xl py-5 ${
                        plan.popular
                          ? 'bg-[#00C896] hover:bg-[#00dba6] text-white'
                          : 'bg-[#00C896]/10 hover:bg-[#00C896]/15 text-[#00C896]'
                      }`}
                      data-testid={`upgrade-to-${plan.id}`}
                    >
                      {loading ? 'Processing...' : 'Get Started'}
                    </Button>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Bank Accounts */}
        <Card className="card-dark">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg flex items-center gap-2" style={{ fontFamily: 'Clash Display, Satoshi, sans-serif' }}>
                <Building className="w-5 h-5 text-[#00C896]" />
                Bank Accounts
              </CardTitle>
              {user?.subscription_plan !== 'starter' && (
                <div className="flex gap-2">
                  <Button 
                    onClick={handleMonoLinking}
                    disabled={loading}
                    className="bg-[#00C896] hover:bg-[#00dba6] text-white rounded-xl" 
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
                <div className="bg-[#F59E0B]/10 p-3 rounded-xl border border-[#F59E0B]/20">
                  <p className="text-xs text-[#A1A1AA]">
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
                  className="w-full bg-[#00C896] hover:bg-[#00dba6] text-white rounded-xl"
                  data-testid="submit-link-bank"
                >
                  {loading ? 'Linking...' : 'Link Bank Account (Demo)'}
                </Button>
              </form>
            </DialogContent>
          </Dialog>

          <CardContent>
            {user?.subscription_plan === 'starter' ? (
              <div className="text-center py-8 bg-[#0A0A0A] rounded-xl">
                <Shield className="w-12 h-12 text-slate-300 mx-auto mb-3" />
                <p className="text-[#A1A1AA] mb-2">Bank linking requires Growth or Business plan</p>
                <Button
                  onClick={() => handleUpgradePlan('growth')}
                  className="bg-[#00C896] hover:bg-[#00dba6] text-white rounded-xl"
                  data-testid="upgrade-for-bank"
                >
                  Upgrade to Growth
                </Button>
              </div>
            ) : (
              <>
                {/* Trust Signal for Bank Linking */}
                <div className="mb-4 p-4 bg-[#00C896]/10 border border-[#00C896]/20 rounded-xl">
                  <div className="flex items-center gap-2 mb-2">
                    <Shield className="w-5 h-5 text-[#00C896]" />
                    <span className="font-medium text-[#00C896] text-sm">Your bank data is secure</span>
                  </div>
                  <p className="text-xs text-[#A1A1AA]">We never store your bank password. Read-only access only. Secured by 256-bit encryption.</p>
                  <div className="flex items-center gap-3 mt-2 text-xs text-[#555]">
                    <span>Mono</span><span>Okra</span><span>Stitch</span>
                  </div>
                </div>
                {bankAccounts.length === 0 ? (
                  <div className="text-center py-8 text-[#555]">
                    <Building className="w-12 h-12 mx-auto mb-3 opacity-50" />
                    <p>No bank accounts linked yet</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {bankAccounts.map((account, idx) => (
                      <div
                        key={account.id || idx}
                        className="flex items-center justify-between p-4 bg-[#0A0A0A] rounded-xl"
                        data-testid={`bank-account-${idx}`}
                      >
                        <div>
                          <p className="font-medium text-white">{account.bank_name}</p>
                          <p className="text-sm text-[#A1A1AA]">{account.account_number} • {account.account_name}</p>
                          <p className="text-sm font-medium text-[#00C896]">{formatCurrency(account.balance)}</p>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleUnlinkBank(account.id)}
                          className="text-red-500 hover:text-red-400 hover:bg-red-500/10"
                          data-testid={`unlink-bank-${idx}`}
                        >
                          <Unlink className="w-4 h-4 mr-1" />
                          Unlink
                        </Button>
                      </div>
                    ))}
                  </div>
                )}
              </>
            )}
          </CardContent>
        </Card>

        {/* Smart Memory */}
        <Card className="card-dark" data-testid="smart-memory-section">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2" style={{ fontFamily: 'Clash Display, Satoshi, sans-serif' }}>
              <Brain className="w-5 h-5 text-[#8B5CF6]" />
              Smart Memory
            </CardTitle>
            <CardDescription>Auto-categorization rules learned from your transactions</CardDescription>
          </CardHeader>
          <CardContent>
            {memories.length === 0 ? (
              <div className="text-center py-6 text-[#555]">
                <Brain className="w-8 h-8 mx-auto mb-2 opacity-30" />
                <p className="text-sm">No learned patterns yet. Add transactions to build memory.</p>
              </div>
            ) : (
              <div className="space-y-3">
                {memories.map((mem, idx) => (
                  <div key={mem.id || idx} className="flex items-center justify-between p-4 bg-[#0A0A0A] rounded-xl" data-testid={`memory-item-${idx}`}>
                    <div className="flex-1">
                      <p className="font-medium text-white">{mem.counterparty_name || mem.counterparty_account}</p>
                      <div className="flex items-center gap-2 mt-1">
                        <Badge variant="outline" className="text-xs">{mem.category}</Badge>
                        <Badge className={`text-xs ${mem.lock_status === 'hard' ? 'bg-[#00C896] text-white' : 'bg-[#F59E0B]/20 text-[#F59E0B]'}`}>
                          {mem.lock_status === 'hard' ? 'Hard Lock' : 'Soft Lock'}
                        </Badge>
                        <span className="text-xs text-[#555]">{mem.occurrence_count} transactions</span>
                      </div>
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => handleDeleteMemory(mem.id)}
                      className="text-[#555] hover:text-red-500"
                      data-testid={`delete-memory-${idx}`}
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* WhatsApp AI */}
        <Card className="card-dark" data-testid="whatsapp-settings-section">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2" style={{ fontFamily: 'Clash Display, Satoshi, sans-serif' }}>
              <MessageSquare className="w-5 h-5 text-[#25D366]" />
              WhatsApp AI
            </CardTitle>
            <CardDescription>Manage your WhatsApp bookkeeping assistant</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between p-4 bg-[#0A0A0A] rounded-xl">
              <div>
                <p className="font-medium text-white">Connected Number</p>
                <p className="text-sm text-[#A1A1AA]">{waSettings.phone || 'Not connected'}</p>
              </div>
              {!waSettings.phone && (
                <Badge className="bg-[#25D366]/10 text-[#25D366] text-xs">Message the ClearFile bot to activate</Badge>
              )}
            </div>
            <div className="flex items-center justify-between p-4 bg-[#0A0A0A] rounded-xl">
              <div className="flex items-center gap-3">
                <Bell className="w-5 h-5 text-[#A1A1AA]" />
                <div>
                  <p className="font-medium text-white">Transaction Notifications</p>
                  <p className="text-sm text-[#A1A1AA]">Get a WhatsApp ping for every transaction</p>
                </div>
              </div>
              <Switch checked={waSettings.transaction_notifications} onCheckedChange={() => handleToggleWaSetting('transaction_notifications')} data-testid="wa-tx-notifications-toggle" />
            </div>
            <div className="flex items-center justify-between p-4 bg-[#0A0A0A] rounded-xl">
              <div className="flex items-center gap-3">
                <FileDown className="w-5 h-5 text-[#A1A1AA]" />
                <div>
                  <p className="font-medium text-white">Weekly Summary</p>
                  <p className="text-sm text-[#A1A1AA]">Sunday digest of your finances</p>
                </div>
              </div>
              <Switch checked={waSettings.weekly_summary} onCheckedChange={() => handleToggleWaSetting('weekly_summary')} data-testid="wa-weekly-summary-toggle" />
            </div>
            <div className="flex items-center justify-between p-4 bg-[#0A0A0A] rounded-xl">
              <div className="flex items-center gap-3">
                <Shield className="w-5 h-5 text-[#A1A1AA]" />
                <div>
                  <p className="font-medium text-white">Tax Deadline Reminders</p>
                  <p className="text-sm text-[#A1A1AA]">Reminders 7 days before filing dates</p>
                </div>
              </div>
              <Switch checked={waSettings.tax_reminders} onCheckedChange={() => handleToggleWaSetting('tax_reminders')} data-testid="wa-tax-reminders-toggle" />
            </div>
          </CardContent>
        </Card>

        {/* Preferences */}
        <Card className="card-dark">
          <CardHeader>
            <CardTitle className="text-lg" style={{ fontFamily: 'Clash Display, Satoshi, sans-serif' }}>{t('preferences')}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between p-4 bg-[#0A0A0A] rounded-xl">
              <div className="flex items-center gap-3">
                <Moon className="w-5 h-5 text-[#A1A1AA]" />
                <div>
                  <p className="font-medium text-white">{t('darkMode')}</p>
                  <p className="text-sm text-[#A1A1AA]">{t('darkModeDesc')}</p>
                </div>
              </div>
              <Switch
                checked={darkMode}
                onCheckedChange={handleToggleDarkMode}
                data-testid="dark-mode-toggle"
              />
            </div>

            <div className="flex items-center justify-between p-4 bg-[#0A0A0A] rounded-xl">
              <div className="flex items-center gap-3">
                <Languages className="w-5 h-5 text-[#A1A1AA]" />
                <div>
                  <p className="font-medium text-white">{t('pidginMode')}</p>
                  <p className="text-sm text-[#A1A1AA]">{t('pidginModeDesc')}</p>
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
          <Card className="card-dark">
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2" style={{ fontFamily: 'Clash Display, Satoshi, sans-serif' }}>
                <FileDown className="w-5 h-5 text-[#00C896]" />
                Export Data
              </CardTitle>
              <CardDescription>{t('exportDesc')}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <Button
                  variant="outline"
                  className="rounded-xl border-[#1E1E1E] hover:bg-[#00C896]/10"
                  onClick={() => window.open(`${API}/api/export/transactions?format=csv&period=all`, '_blank')}
                  data-testid="export-transactions-csv"
                >
                  <FileDown className="w-4 h-4 mr-2" />
                  Transactions (CSV)
                </Button>
                <Button
                  variant="outline"
                  className="rounded-xl border-[#1E1E1E] hover:bg-[#00C896]/10"
                  onClick={() => window.open(`${API}/api/export/tax-report?format=csv`, '_blank')}
                  data-testid="export-tax-report-csv"
                >
                  <FileDown className="w-4 h-4 mr-2" />
                  Tax Report (CSV)
                </Button>
                <Button
                  className="rounded-xl bg-[#00C896] hover:bg-[#00dba6] text-white"
                  onClick={() => window.open(`${API}/api/export/tax-report?format=pdf`, '_blank')}
                  data-testid="export-tax-report-pdf"
                >
                  <FileDown className="w-4 h-4 mr-2" />
                  Tax Report (PDF)
                </Button>
              </div>
              <p className="text-xs text-[#A1A1AA]">
                Note: You'll need to be logged in for exports to work. If download fails, try refreshing the page first.
              </p>
            </CardContent>
          </Card>
        )}

        {/* Team Management (Business Plan) */}
        {user?.subscription_plan === 'business' && (
          <Card className="card-dark">
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2" style={{ fontFamily: 'Clash Display, Satoshi, sans-serif' }}>
                <Users className="w-5 h-5 text-[#00C896]" />
                Team Access
              </CardTitle>
              <CardDescription>{t('teamDesc')}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-2">
                <Input
                  type="email"
                  placeholder="Email address"
                  value={inviteEmail}
                  onChange={(e) => setInviteEmail(e.target.value)}
                  className="rounded-xl flex-1"
                  data-testid="invite-email-input"
                />
                <Select value={inviteRole} onValueChange={setInviteRole}>
                  <SelectTrigger className="w-32 rounded-xl">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="viewer">Viewer</SelectItem>
                    <SelectItem value="accountant">Accountant</SelectItem>
                  </SelectContent>
                </Select>
                <Button 
                  onClick={handleInviteTeamMember}
                  disabled={!inviteEmail || loading}
                  className="bg-[#00C896] hover:bg-[#00dba6] text-white rounded-xl"
                  data-testid="invite-btn"
                >
                  Invite
                </Button>
              </div>
              
              {teamMembers.length > 0 && (
                <div className="space-y-2">
                  {teamMembers.map((member, idx) => (
                    <div key={member.id || idx} className="flex items-center justify-between p-3 bg-[#0A0A0A] rounded-xl">
                      <div>
                        <p className="font-medium text-white">{member.email}</p>
                        <p className="text-xs text-[#A1A1AA] capitalize">{member.role} • {member.status}</p>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleRemoveTeamMember(member.id)}
                        className="text-red-500 hover:text-red-400"
                        data-testid={`remove-member-${idx}`}
                      >
                        Remove
                      </Button>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Security */}
        <Card className="card-dark bg-[#00C896]/10">
          <CardContent className="p-6">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-[#00C896] rounded-xl flex items-center justify-center">
                <Shield className="w-6 h-6 text-white" />
              </div>
              <div>
                <h3 className="font-bold text-[#00C896]">{t('bankSecurity')}</h3>
                <p className="text-sm text-[#A1A1AA]">
                  {t('bankSecurityDesc')}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </Layout>
  );
}
