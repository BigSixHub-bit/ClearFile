import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Layout from '../components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Switch } from '../components/ui/switch';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { Badge } from '../components/ui/badge';
import { toast } from 'sonner';
import { Plus, FileText, Trash2, CheckCircle, Clock, AlertCircle, X } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

const statusColors = {
  paid: 'bg-[#00C896] text-white',
  unpaid: 'bg-[#F59E0B]/20 text-[#F59E0B]',
  partial: 'bg-[#3B82F6]/20 text-[#3B82F6]',
  overdue: 'bg-red-500/20 text-red-400'
};

const statusIcons = {
  paid: CheckCircle,
  unpaid: Clock,
  partial: Clock,
  overdue: AlertCircle
};

export default function Invoices() {
  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [selectedInvoice, setSelectedInvoice] = useState(null);
  const [form, setForm] = useState({
    customer_name: '',
    customer_phone: '',
    items: [{ description: '', quantity: 1, unit_price: '' }],
    due_date: '',
    vat_enabled: false
  });

  useEffect(() => { fetchInvoices(); }, []);

  const fetchInvoices = async () => {
    try {
      const { data } = await axios.get(`${API}/api/invoices`, { withCredentials: true });
      setInvoices(data);
    } catch (e) { toast.error('Failed to load invoices'); }
    finally { setLoading(false); }
  };

  const addItem = () => {
    setForm(f => ({ ...f, items: [...f.items, { description: '', quantity: 1, unit_price: '' }] }));
  };

  const removeItem = (idx) => {
    setForm(f => ({ ...f, items: f.items.filter((_, i) => i !== idx) }));
  };

  const updateItem = (idx, field, value) => {
    setForm(f => {
      const items = [...f.items];
      items[idx] = { ...items[idx], [field]: value };
      return { ...f, items };
    });
  };

  const subtotal = form.items.reduce((sum, item) => sum + (parseFloat(item.unit_price) || 0) * (parseFloat(item.quantity) || 0), 0);
  const vatAmount = form.vat_enabled ? Math.round(subtotal * 0.075 * 100) / 100 : 0;
  const total = subtotal + vatAmount;

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!form.customer_name || form.items.every(i => !i.unit_price)) {
      toast.error('Please fill in customer name and at least one item');
      return;
    }
    try {
      await axios.post(`${API}/api/invoices`, {
        customer_name: form.customer_name,
        customer_phone: form.customer_phone,
        items: form.items.filter(i => i.unit_price).map(i => ({
          description: i.description,
          quantity: parseFloat(i.quantity) || 1,
          unit_price: parseFloat(i.unit_price) || 0
        })),
        due_date: form.due_date || undefined,
        vat_enabled: form.vat_enabled
      }, { withCredentials: true });
      toast.success('Invoice created!');
      setIsCreateOpen(false);
      setForm({ customer_name: '', customer_phone: '', items: [{ description: '', quantity: 1, unit_price: '' }], due_date: '', vat_enabled: false });
      fetchInvoices();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create invoice');
    }
  };

  const handleMarkPaid = async (invId) => {
    try {
      await axios.put(`${API}/api/invoices/${invId}/status`, { status: 'paid' }, { withCredentials: true });
      toast.success('Invoice marked as paid');
      fetchInvoices();
      setSelectedInvoice(null);
    } catch (e) { toast.error('Failed to update'); }
  };

  const fmt = (v) => new Intl.NumberFormat('en-NG', { style: 'currency', currency: 'NGN', minimumFractionDigits: 0 }).format(v).replace('NGN', '₦');
  const fmtDate = (d) => d ? new Date(d).toLocaleDateString('en-NG', { day: 'numeric', month: 'short', year: 'numeric' }) : '—';

  return (
    <Layout>
      <div className="space-y-6 pb-20 lg:pb-0">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold text-white" style={{ fontFamily: 'Clash Display, Satoshi, sans-serif' }}>
              Invoices
            </h1>
            <p className="text-[#A1A1AA]">Create and manage customer invoices</p>
          </div>
          <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
            <DialogTrigger asChild>
              <Button className="bg-[#00C896] hover:bg-[#00dba6] text-white rounded-xl" data-testid="create-invoice-btn">
                <Plus className="w-4 h-4 mr-2" /> Create Invoice
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-lg max-h-[85vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>New Invoice</DialogTitle>
              </DialogHeader>
              <form onSubmit={handleCreate} className="space-y-4">
                <div className="space-y-2">
                  <Label>Customer Name *</Label>
                  <Input value={form.customer_name} onChange={e => setForm(f => ({ ...f, customer_name: e.target.value }))} placeholder="Enter customer name" className="rounded-xl" required data-testid="invoice-customer-name" />
                </div>
                <div className="space-y-2">
                  <Label>Customer Phone (optional)</Label>
                  <Input value={form.customer_phone} onChange={e => setForm(f => ({ ...f, customer_phone: e.target.value }))} placeholder="08012345678" className="rounded-xl" data-testid="invoice-customer-phone" />
                </div>

                {/* Line Items */}
                <div className="space-y-3">
                  <Label>Items</Label>
                  {form.items.map((item, idx) => (
                    <div key={idx} className="flex gap-2 items-end" data-testid={`invoice-item-${idx}`}>
                      <div className="flex-1">
                        <Input value={item.description} onChange={e => updateItem(idx, 'description', e.target.value)} placeholder="Description" className="rounded-xl text-sm" />
                      </div>
                      <div className="w-16">
                        <Input type="number" value={item.quantity} onChange={e => updateItem(idx, 'quantity', e.target.value)} placeholder="Qty" className="rounded-xl text-sm" min="1" />
                      </div>
                      <div className="w-28">
                        <Input type="number" value={item.unit_price} onChange={e => updateItem(idx, 'unit_price', e.target.value)} placeholder="Price (₦)" className="rounded-xl text-sm" />
                      </div>
                      {form.items.length > 1 && (
                        <Button type="button" variant="ghost" size="icon" onClick={() => removeItem(idx)} className="text-red-500">
                          <X className="w-4 h-4" />
                        </Button>
                      )}
                    </div>
                  ))}
                  <Button type="button" variant="outline" size="sm" onClick={addItem} className="rounded-xl border-[#1E1E1E] text-sm" data-testid="add-invoice-item">
                    <Plus className="w-3 h-3 mr-1" /> Add Item
                  </Button>
                </div>

                <div className="space-y-2">
                  <Label>Due Date</Label>
                  <Input type="date" value={form.due_date} onChange={e => setForm(f => ({ ...f, due_date: e.target.value }))} className="rounded-xl" data-testid="invoice-due-date" />
                </div>

                <div className="flex items-center justify-between p-3 bg-[#0A0A0A] rounded-xl">
                  <Label className="cursor-pointer">Add 7.5% VAT</Label>
                  <Switch checked={form.vat_enabled} onCheckedChange={v => setForm(f => ({ ...f, vat_enabled: v }))} data-testid="invoice-vat-toggle" />
                </div>

                {/* Preview */}
                <div className="border border-[#1E1E1E] rounded-xl p-4 space-y-2">
                  <div className="flex justify-between text-sm text-[#A1A1AA]">
                    <span>Subtotal</span><span>{fmt(subtotal)}</span>
                  </div>
                  {form.vat_enabled && (
                    <div className="flex justify-between text-sm text-[#A1A1AA]">
                      <span>VAT (7.5%)</span><span>{fmt(vatAmount)}</span>
                    </div>
                  )}
                  <div className="flex justify-between text-white font-bold border-t border-[#1E1E1E] pt-2">
                    <span>Total</span><span data-testid="invoice-preview-total">{fmt(total)}</span>
                  </div>
                </div>

                <Button type="submit" className="w-full bg-[#00C896] hover:bg-[#00dba6] text-white rounded-xl" data-testid="submit-invoice-btn">
                  Create Invoice
                </Button>
              </form>
            </DialogContent>
          </Dialog>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {[
            { label: 'Total', count: invoices.length, color: '#A1A1AA' },
            { label: 'Unpaid', count: invoices.filter(i => i.status === 'unpaid').length, color: '#F59E0B' },
            { label: 'Paid', count: invoices.filter(i => i.status === 'paid').length, color: '#00C896' },
            { label: 'Overdue', count: invoices.filter(i => i.status === 'overdue').length, color: '#EF4444' },
          ].map((s, idx) => (
            <div key={idx} className="card-dark p-4 text-center" data-testid={`invoice-stat-${s.label.toLowerCase()}`}>
              <p className="text-2xl font-bold" style={{ color: s.color }}>{s.count}</p>
              <p className="text-xs text-[#A1A1AA]">{s.label}</p>
            </div>
          ))}
        </div>

        {/* Invoice List */}
        <Card className="card-dark">
          <CardHeader>
            <CardTitle className="text-lg" style={{ fontFamily: 'Clash Display, Satoshi, sans-serif' }}>
              All Invoices
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            {loading ? (
              <div className="flex items-center justify-center h-40">
                <div className="w-8 h-8 border-4 border-[#006400] border-t-transparent rounded-full animate-spin"></div>
              </div>
            ) : invoices.length === 0 ? (
              <div className="text-center py-12 text-[#555]">
                <FileText className="w-10 h-10 mx-auto mb-3 opacity-30" />
                <p>No invoices yet</p>
                <p className="text-sm mt-1">Create your first invoice to get started</p>
              </div>
            ) : (
              <div className="divide-y divide-[#1E1E1E]">
                {invoices.map((inv, idx) => {
                  const StatusIcon = statusIcons[inv.status] || Clock;
                  return (
                    <button
                      key={inv.id}
                      onClick={() => setSelectedInvoice(inv)}
                      className="w-full flex items-center justify-between p-4 hover:bg-[#0A0A0A] transition-colors text-left"
                      data-testid={`invoice-row-${idx}`}
                    >
                      <div className="flex items-center gap-4">
                        <div className="w-10 h-10 rounded-xl bg-[#3B82F6]/10 flex items-center justify-center">
                          <FileText className="w-5 h-5 text-[#3B82F6]" />
                        </div>
                        <div>
                          <p className="font-medium text-white">{inv.invoice_number}</p>
                          <p className="text-sm text-[#A1A1AA]">{inv.customer_name}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-4">
                        <div className="text-right">
                          <p className="font-bold text-white">{fmt(inv.total_amount || inv.total || 0)}</p>
                          <p className="text-xs text-[#555]">Due {fmtDate(inv.due_date)}</p>
                        </div>
                        <Badge className={`${statusColors[inv.status]} text-xs capitalize`}>
                          {inv.status}
                        </Badge>
                      </div>
                    </button>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Invoice Detail Modal */}
        <Dialog open={!!selectedInvoice} onOpenChange={() => setSelectedInvoice(null)}>
          <DialogContent className="sm:max-w-md">
            <DialogHeader>
              <DialogTitle>{selectedInvoice?.invoice_number}</DialogTitle>
            </DialogHeader>
            {selectedInvoice && (
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-[#A1A1AA] text-sm">Customer</span>
                  <span className="text-white font-medium">{selectedInvoice.customer_name}</span>
                </div>
                {selectedInvoice.customer_phone && (
                  <div className="flex justify-between items-center">
                    <span className="text-[#A1A1AA] text-sm">Phone</span>
                    <span className="text-white">{selectedInvoice.customer_phone}</span>
                  </div>
                )}
                <div className="flex justify-between items-center">
                  <span className="text-[#A1A1AA] text-sm">Status</span>
                  <Badge className={`${statusColors[selectedInvoice.status]} capitalize`}>{selectedInvoice.status}</Badge>
                </div>
                {selectedInvoice.items?.map((item, idx) => (
                  <div key={idx} className="flex justify-between items-center p-3 bg-[#0A0A0A] rounded-xl">
                    <div>
                      <p className="text-sm text-white">{item.description || `Item ${idx + 1}`}</p>
                      <p className="text-xs text-[#555]">{item.quantity} x {fmt(item.unit_price)}</p>
                    </div>
                    <span className="text-sm text-white font-medium">{fmt(item.line_total || item.quantity * item.unit_price)}</span>
                  </div>
                ))}
                <div className="border-t border-[#1E1E1E] pt-3 space-y-1">
                  <div className="flex justify-between text-sm">
                    <span className="text-[#A1A1AA]">Subtotal</span>
                    <span className="text-white">{fmt(selectedInvoice.subtotal || selectedInvoice.amount || 0)}</span>
                  </div>
                  {selectedInvoice.vat_amount > 0 && (
                    <div className="flex justify-between text-sm">
                      <span className="text-[#A1A1AA]">VAT (7.5%)</span>
                      <span className="text-white">{fmt(selectedInvoice.vat_amount)}</span>
                    </div>
                  )}
                  <div className="flex justify-between font-bold">
                    <span className="text-white">Total</span>
                    <span className="text-[#00C896]">{fmt(selectedInvoice.total_amount || selectedInvoice.total || 0)}</span>
                  </div>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-[#A1A1AA]">Issued</span>
                  <span className="text-white">{fmtDate(selectedInvoice.issue_date || selectedInvoice.created_at)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-[#A1A1AA]">Due</span>
                  <span className="text-white">{fmtDate(selectedInvoice.due_date)}</span>
                </div>
                {selectedInvoice.status !== 'paid' && (
                  <Button onClick={() => handleMarkPaid(selectedInvoice.id)} className="w-full bg-[#00C896] hover:bg-[#00dba6] text-white rounded-xl" data-testid="mark-paid-btn">
                    <CheckCircle className="w-4 h-4 mr-2" /> Mark as Paid
                  </Button>
                )}
              </div>
            )}
          </DialogContent>
        </Dialog>
      </div>
    </Layout>
  );
}
