import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import Layout from '../components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Badge } from '../components/ui/badge';
import { useLanguage } from '../context/LanguageContext';
import { toast } from 'sonner';
import { 
  Plus, Search, Filter, TrendingUp, TrendingDown, 
  AlertTriangle, Upload, Trash2, Edit2, Camera
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

export default function Transactions() {
  const { t } = useLanguage();
  const [transactions, setTransactions] = useState([]);
  const [categories, setCategories] = useState({ income: [], expense: [] });
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState({ type: '', category: '', flagged: null });
  const [searchQuery, setSearchQuery] = useState('');
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);
  const [isReceiptDialogOpen, setIsReceiptDialogOpen] = useState(false);
  const [newTransaction, setNewTransaction] = useState({
    amount: '',
    type: 'expense',
    category: '',
    description: '',
    date: new Date().toISOString().split('T')[0]
  });

  const fetchTransactions = useCallback(async () => {
    try {
      const params = new URLSearchParams();
      if (filter.type) params.append('type', filter.type);
      if (filter.category) params.append('category', filter.category);
      if (filter.flagged !== null) params.append('flagged', filter.flagged);

      const { data } = await axios.get(`${API}/api/transactions?${params}`, { withCredentials: true });
      setTransactions(data);
    } catch (error) {
      toast.error('Failed to load transactions');
    } finally {
      setLoading(false);
    }
  }, [filter]);

  const fetchCategories = async () => {
    try {
      const { data } = await axios.get(`${API}/api/categories`, { withCredentials: true });
      setCategories(data);
    } catch (error) {
      console.error('Failed to load categories');
    }
  };

  useEffect(() => {
    fetchTransactions();
    fetchCategories();
  }, [fetchTransactions]);

  const handleAddTransaction = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/api/transactions`, {
        ...newTransaction,
        amount: parseFloat(newTransaction.amount)
      }, { withCredentials: true });
      toast.success('Transaction added!');
      setIsAddDialogOpen(false);
      setNewTransaction({
        amount: '',
        type: 'expense',
        category: '',
        description: '',
        date: new Date().toISOString().split('T')[0]
      });
      fetchTransactions();
    } catch (error) {
      toast.error('Failed to add transaction');
    }
  };

  const handleDeleteTransaction = async (txId) => {
    if (!window.confirm('Are you sure you want to delete this transaction?')) return;
    try {
      await axios.delete(`${API}/api/transactions/${txId}`, { withCredentials: true });
      toast.success('Transaction deleted');
      fetchTransactions();
    } catch (error) {
      toast.error('Failed to delete transaction');
    }
  };

  const handleUploadReceipt = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      await axios.post(`${API}/api/receipts/upload`, formData, {
        withCredentials: true,
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      toast.success('Receipt uploaded! AI will analyze it.');
      setIsReceiptDialogOpen(false);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to upload receipt');
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-NG', {
      style: 'currency',
      currency: 'NGN',
      minimumFractionDigits: 0
    }).format(amount).replace('NGN', '₦');
  };

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleDateString('en-NG', {
      day: 'numeric',
      month: 'short',
      year: 'numeric'
    });
  };

  const filteredTransactions = transactions.filter(tx =>
    tx.description?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    tx.category?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const totalIncome = filteredTransactions.filter(t => t.type === 'income').reduce((sum, t) => sum + t.amount, 0);
  const totalExpenses = filteredTransactions.filter(t => t.type === 'expense').reduce((sum, t) => sum + t.amount, 0);

  return (
    <Layout>
      <div className="space-y-6 pb-20 lg:pb-0">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold text-[#022c22]" style={{ fontFamily: 'Outfit' }}>
              {t('transactions')}
            </h1>
            <p className="text-slate-500">Track your income and expenses</p>
          </div>
          <div className="flex gap-2">
            <Dialog open={isReceiptDialogOpen} onOpenChange={setIsReceiptDialogOpen}>
              <DialogTrigger asChild>
                <Button variant="outline" className="rounded-xl border-slate-200" data-testid="upload-receipt-btn">
                  <Camera className="w-4 h-4 mr-2" />
                  {t('scanReceipt')}
                </Button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-md">
                <DialogHeader>
                  <DialogTitle>{t('scanReceipt')}</DialogTitle>
                </DialogHeader>
                <div className="space-y-4">
                  <div className="border-2 border-dashed border-slate-200 rounded-xl p-8 text-center">
                    <Upload className="w-12 h-12 text-slate-400 mx-auto mb-4" />
                    <p className="text-slate-600 mb-2">Upload a receipt image</p>
                    <p className="text-sm text-slate-400">JPEG, PNG, WebP, or PDF</p>
                    <Input
                      type="file"
                      accept="image/*,.pdf"
                      onChange={handleUploadReceipt}
                      className="mt-4"
                      data-testid="receipt-file-input"
                    />
                  </div>
                </div>
              </DialogContent>
            </Dialog>

            <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
              <DialogTrigger asChild>
                <Button className="bg-[#006400] hover:bg-[#004d00] text-white rounded-xl" data-testid="add-transaction-btn">
                  <Plus className="w-4 h-4 mr-2" />
                  Add Transaction
                </Button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-md">
                <DialogHeader>
                  <DialogTitle>Add Transaction</DialogTitle>
                </DialogHeader>
                <form onSubmit={handleAddTransaction} className="space-y-4">
                  <Tabs value={newTransaction.type} onValueChange={(v) => setNewTransaction({ ...newTransaction, type: v, category: '' })}>
                    <TabsList className="grid w-full grid-cols-2">
                      <TabsTrigger value="income" data-testid="type-income-tab">
                        <TrendingUp className="w-4 h-4 mr-2 text-[#006400]" />
                        {t('income')}
                      </TabsTrigger>
                      <TabsTrigger value="expense" data-testid="type-expense-tab">
                        <TrendingDown className="w-4 h-4 mr-2 text-red-500" />
                        {t('expense')}
                      </TabsTrigger>
                    </TabsList>
                  </Tabs>

                  <div className="space-y-2">
                    <Label>{t('amount')}</Label>
                    <div className="relative">
                      <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500">₦</span>
                      <Input
                        type="number"
                        value={newTransaction.amount}
                        onChange={(e) => setNewTransaction({ ...newTransaction, amount: e.target.value })}
                        placeholder="0.00"
                        className="pl-8 rounded-xl"
                        required
                        data-testid="transaction-amount-input"
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label>{t('category')}</Label>
                    <Select
                      value={newTransaction.category}
                      onValueChange={(v) => setNewTransaction({ ...newTransaction, category: v })}
                    >
                      <SelectTrigger className="rounded-xl" data-testid="transaction-category-select">
                        <SelectValue placeholder="Select category" />
                      </SelectTrigger>
                      <SelectContent>
                        {(newTransaction.type === 'income' ? categories.income : categories.expense).map(cat => (
                          <SelectItem key={cat} value={cat}>{cat}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label>{t('description')}</Label>
                    <Input
                      value={newTransaction.description}
                      onChange={(e) => setNewTransaction({ ...newTransaction, description: e.target.value })}
                      placeholder="What was this for?"
                      className="rounded-xl"
                      required
                      data-testid="transaction-description-input"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label>{t('date')}</Label>
                    <Input
                      type="date"
                      value={newTransaction.date}
                      onChange={(e) => setNewTransaction({ ...newTransaction, date: e.target.value })}
                      className="rounded-xl"
                      data-testid="transaction-date-input"
                    />
                  </div>

                  <Button type="submit" className="w-full bg-[#006400] hover:bg-[#004d00] text-white rounded-xl" data-testid="submit-transaction-btn">
                    Add Transaction
                  </Button>
                </form>
              </DialogContent>
            </Dialog>
          </div>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Card className="rounded-2xl border-slate-200 bg-[#E8F5E9]">
            <CardContent className="p-6 flex items-center justify-between">
              <div>
                <p className="text-sm text-[#004d00]">Total Income</p>
                <p className="text-2xl font-bold text-[#006400]" data-testid="summary-income">{formatCurrency(totalIncome)}</p>
              </div>
              <TrendingUp className="w-10 h-10 text-[#006400]" />
            </CardContent>
          </Card>
          <Card className="rounded-2xl border-slate-200 bg-red-50">
            <CardContent className="p-6 flex items-center justify-between">
              <div>
                <p className="text-sm text-red-700">Total Expenses</p>
                <p className="text-2xl font-bold text-red-600" data-testid="summary-expenses">{formatCurrency(totalExpenses)}</p>
              </div>
              <TrendingDown className="w-10 h-10 text-red-500" />
            </CardContent>
          </Card>
        </div>

        {/* Filters */}
        <Card className="rounded-2xl border-slate-200">
          <CardContent className="p-4">
            <div className="flex flex-col sm:flex-row gap-4">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                <Input
                  placeholder="Search transactions..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10 rounded-xl"
                  data-testid="search-transactions-input"
                />
              </div>
              <Select value={filter.type || 'all'} onValueChange={(v) => setFilter({ ...filter, type: v === 'all' ? '' : v })}>
                <SelectTrigger className="w-full sm:w-40 rounded-xl" data-testid="filter-type-select">
                  <Filter className="w-4 h-4 mr-2" />
                  <SelectValue placeholder="Type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">{t('all')}</SelectItem>
                  <SelectItem value="income">{t('income')}</SelectItem>
                  <SelectItem value="expense">{t('expense')}</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        {/* Transactions List */}
        <Card className="rounded-2xl border-slate-200">
          <CardHeader>
            <CardTitle className="text-lg" style={{ fontFamily: 'Outfit' }}>
              Recent Transactions ({filteredTransactions.length})
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            {loading ? (
              <div className="flex items-center justify-center h-40">
                <div className="w-8 h-8 border-4 border-[#006400] border-t-transparent rounded-full animate-spin"></div>
              </div>
            ) : filteredTransactions.length === 0 ? (
              <div className="text-center py-12 text-slate-400">
                <p>No transactions found</p>
                <p className="text-sm mt-1">Add your first transaction to get started</p>
              </div>
            ) : (
              <div className="divide-y divide-slate-100">
                {filteredTransactions.map((tx, idx) => (
                  <div
                    key={tx.id || idx}
                    className="flex items-center justify-between p-4 hover:bg-slate-50 transition-colors"
                    data-testid={`transaction-item-${idx}`}
                  >
                    <div className="flex items-center gap-4">
                      <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                        tx.type === 'income' ? 'bg-[#E8F5E9]' : 'bg-red-50'
                      }`}>
                        {tx.type === 'income' ? (
                          <TrendingUp className="w-5 h-5 text-[#006400]" />
                        ) : (
                          <TrendingDown className="w-5 h-5 text-red-500" />
                        )}
                      </div>
                      <div>
                        <p className="font-medium text-[#022c22]">{tx.description}</p>
                        <div className="flex items-center gap-2 mt-1">
                          <Badge variant="outline" className="text-xs">{tx.category}</Badge>
                          <span className="text-xs text-slate-400">{formatDate(tx.date)}</span>
                          {tx.flagged && (
                            <Badge variant="destructive" className="text-xs">
                              <AlertTriangle className="w-3 h-3 mr-1" />
                              Review
                            </Badge>
                          )}
                          {tx.ai_categorized && (
                            <Badge variant="secondary" className="text-xs bg-[#E8F5E9] text-[#006400]">AI</Badge>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <span className={`font-bold ${tx.type === 'income' ? 'text-[#006400]' : 'text-red-500'}`}>
                        {tx.type === 'income' ? '+' : '-'}{formatCurrency(tx.amount)}
                      </span>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => handleDeleteTransaction(tx.id)}
                        className="text-slate-400 hover:text-red-500"
                        data-testid={`delete-transaction-${idx}`}
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </Layout>
  );
}
