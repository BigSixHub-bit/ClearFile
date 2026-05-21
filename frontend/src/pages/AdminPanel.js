import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Layout from '../components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { useAuth } from '../context/AuthContext';
import { toast } from 'sonner';
import {
  Users, FileText, Clock, CheckCircle, AlertCircle, ArrowRight,
  Search, X, Send, Handshake, Shield, Crown, Activity
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

const STATUS_CONFIG = {
  pending: { label: 'Pending', color: 'bg-amber-100 text-amber-700', icon: Clock },
  reviewing: { label: 'Reviewing', color: 'bg-blue-100 text-blue-700', icon: Search },
  matched: { label: 'Matched', color: 'bg-[#E8F5E9] text-[#006400]', icon: Handshake },
  in_progress: { label: 'In Progress', color: 'bg-purple-100 text-purple-700', icon: Activity },
  completed: { label: 'Completed', color: 'bg-[#006400] text-white', icon: CheckCircle },
  cancelled: { label: 'Cancelled', color: 'bg-red-100 text-red-700', icon: X },
};

const URGENCY_CONFIG = {
  normal: { label: 'Normal', color: 'bg-slate-100 text-slate-600' },
  urgent: { label: 'Urgent', color: 'bg-amber-100 text-amber-700' },
  asap: { label: 'ASAP', color: 'bg-red-100 text-red-700' },
};

export default function AdminPanel() {
  const { user } = useAuth();
  const [tab, setTab] = useState('requests');
  const [stats, setStats] = useState(null);
  const [requests, setRequests] = useState([]);
  const [users, setUsers] = useState([]);
  const [statusFilter, setStatusFilter] = useState('all');
  const [selectedRequest, setSelectedRequest] = useState(null);
  const [matchForm, setMatchForm] = useState({ expert_name: '', expert_email: '', expert_phone: '', expert_specialty: '' });
  const [noteText, setNoteText] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
    fetchRequests();
  }, []);

  const fetchStats = async () => {
    try {
      const { data } = await axios.get(`${API}/api/admin/stats`, { withCredentials: true });
      setStats(data);
    } catch (e) { console.error('Stats failed', e); }
  };

  const fetchRequests = async () => {
    try {
      const params = statusFilter !== 'all' ? `?status=${statusFilter}` : '';
      const { data } = await axios.get(`${API}/api/admin/expert-requests${params}`, { withCredentials: true });
      setRequests(data.requests || []);
    } catch (e) { console.error('Requests failed', e); }
    finally { setLoading(false); }
  };

  const fetchUsers = async () => {
    try {
      const { data } = await axios.get(`${API}/api/admin/users`, { withCredentials: true });
      setUsers(data.users || []);
    } catch (e) { console.error('Users failed', e); }
  };

  useEffect(() => { if (tab === 'users' && users.length === 0) fetchUsers(); }, [tab]);
  useEffect(() => { fetchRequests(); }, [statusFilter]);

  const updateStatus = async (requestId, status, extras = {}) => {
    try {
      await axios.put(`${API}/api/admin/expert-requests/${requestId}/status`,
        { status, ...extras }, { withCredentials: true });
      toast.success(`Status updated to ${status}`);
      fetchRequests();
      fetchStats();
      if (selectedRequest?.id === requestId) {
        setSelectedRequest(prev => ({ ...prev, status }));
      }
    } catch (e) { toast.error('Failed to update status'); }
  };

  const addNote = async (requestId) => {
    if (!noteText.trim()) return;
    try {
      await axios.post(`${API}/api/admin/expert-requests/${requestId}/note`,
        { note: noteText }, { withCredentials: true });
      toast.success('Note added');
      setNoteText('');
      fetchRequests();
    } catch (e) { toast.error('Failed to add note'); }
  };

  const matchExpert = async (requestId) => {
    if (!matchForm.expert_name) { toast.error('Expert name required'); return; }
    await updateStatus(requestId, 'matched', matchForm);
    setMatchForm({ expert_name: '', expert_email: '', expert_phone: '', expert_specialty: '' });
  };

  const updateUserPlan = async (userId, plan) => {
    try {
      await axios.put(`${API}/api/admin/users/${userId}/plan`, { plan }, { withCredentials: true });
      toast.success('Plan updated');
      fetchUsers();
      fetchStats();
    } catch (e) { toast.error('Failed to update plan'); }
  };

  const formatDate = (d) => d ? new Date(d).toLocaleDateString('en-NG', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' }) : '';

  if (user?.role !== 'admin') {
    return (
      <Layout>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <Shield className="w-16 h-16 text-slate-300 mx-auto mb-4" />
            <h2 className="text-xl font-bold text-slate-600">Admin Access Required</h2>
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-6 pb-20 lg:pb-0">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-[#022c22]" style={{ fontFamily: 'Outfit' }}>
            Admin Panel
          </h1>
          <p className="text-slate-500">Manage expert requests and users</p>
        </div>

        {/* Stats */}
        {stats && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <Card className="rounded-2xl border-slate-200">
              <CardContent className="p-4 text-center">
                <Users className="w-6 h-6 text-[#006400] mx-auto mb-1" />
                <p className="text-2xl font-bold text-[#022c22]" data-testid="stat-users">{stats.total_users}</p>
                <p className="text-xs text-slate-500">Users</p>
              </CardContent>
            </Card>
            <Card className="rounded-2xl border-slate-200">
              <CardContent className="p-4 text-center">
                <FileText className="w-6 h-6 text-blue-500 mx-auto mb-1" />
                <p className="text-2xl font-bold text-[#022c22]" data-testid="stat-transactions">{stats.total_transactions}</p>
                <p className="text-xs text-slate-500">Transactions</p>
              </CardContent>
            </Card>
            <Card className="rounded-2xl border-amber-200 bg-amber-50">
              <CardContent className="p-4 text-center">
                <Clock className="w-6 h-6 text-amber-500 mx-auto mb-1" />
                <p className="text-2xl font-bold text-amber-700" data-testid="stat-pending">{stats.expert_requests.pending}</p>
                <p className="text-xs text-amber-600">Pending Requests</p>
              </CardContent>
            </Card>
            <Card className="rounded-2xl border-[#A5D6A7] bg-[#E8F5E9]">
              <CardContent className="p-4 text-center">
                <CheckCircle className="w-6 h-6 text-[#006400] mx-auto mb-1" />
                <p className="text-2xl font-bold text-[#006400]" data-testid="stat-matched">{stats.expert_requests.matched}</p>
                <p className="text-xs text-[#004d00]">Matched</p>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Tabs */}
        <div className="flex gap-2 border-b border-slate-200 pb-1">
          {[
            { id: 'requests', label: 'Expert Requests', icon: Handshake },
            { id: 'users', label: 'Users', icon: Users },
          ].map(t => (
            <button key={t.id} onClick={() => setTab(t.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-t-xl font-medium text-sm transition-all ${
                tab === t.id ? 'bg-[#006400] text-white' : 'text-slate-500 hover:bg-slate-100'
              }`} data-testid={`tab-${t.id}`}
            >
              <t.icon className="w-4 h-4" /> {t.label}
            </button>
          ))}
        </div>

        {/* ===== EXPERT REQUESTS TAB ===== */}
        {tab === 'requests' && (
          <div className="space-y-4">
            {/* Filter */}
            <div className="flex gap-2 flex-wrap">
              {['all', 'pending', 'reviewing', 'matched', 'in_progress', 'completed'].map(s => (
                <Button key={s} size="sm" variant={statusFilter === s ? "default" : "outline"}
                  onClick={() => setStatusFilter(s)}
                  className={`rounded-xl text-xs ${statusFilter === s ? 'bg-[#006400] text-white' : ''}`}
                  data-testid={`filter-${s}`}
                >
                  {s === 'all' ? 'All' : STATUS_CONFIG[s]?.label || s}
                </Button>
              ))}
            </div>

            {/* Request List */}
            {requests.length === 0 ? (
              <div className="text-center py-12 text-slate-400">
                <Handshake className="w-12 h-12 mx-auto mb-3 opacity-50" />
                <p>No expert requests {statusFilter !== 'all' ? `with status "${statusFilter}"` : ''}</p>
              </div>
            ) : (
              <div className="space-y-3">
                {requests.map(req => {
                  const sc = STATUS_CONFIG[req.status] || STATUS_CONFIG.pending;
                  const uc = URGENCY_CONFIG[req.urgency] || URGENCY_CONFIG.normal;
                  const isSelected = selectedRequest?.id === req.id;

                  return (
                    <Card key={req.id} className={`rounded-2xl border-slate-200 overflow-hidden transition-all ${isSelected ? 'ring-2 ring-[#006400]' : ''}`} data-testid={`request-${req.id}`}>
                      <CardContent className="p-0">
                        {/* Summary Row */}
                        <button className="w-full flex items-center justify-between p-4 text-left hover:bg-slate-50 transition-colors"
                          onClick={() => setSelectedRequest(isSelected ? null : req)}
                        >
                          <div className="flex items-center gap-3 min-w-0">
                            <div className="w-10 h-10 bg-[#E8F5E9] rounded-xl flex items-center justify-center flex-shrink-0">
                              <sc.icon className="w-5 h-5 text-[#006400]" />
                            </div>
                            <div className="min-w-0">
                              <p className="font-medium text-[#022c22] truncate">{req.user_name || req.user_email}</p>
                              <p className="text-xs text-slate-500">{req.service_type?.replace('_', ' ')} &middot; {formatDate(req.created_at)}</p>
                            </div>
                          </div>
                          <div className="flex items-center gap-2 flex-shrink-0">
                            <Badge className={`${uc.color} text-xs`}>{uc.label}</Badge>
                            <Badge className={`${sc.color} text-xs`}>{sc.label}</Badge>
                            <ArrowRight className={`w-4 h-4 text-slate-400 transition-transform ${isSelected ? 'rotate-90' : ''}`} />
                          </div>
                        </button>

                        {/* Expanded Detail */}
                        {isSelected && (
                          <div className="border-t border-slate-200 p-4 bg-slate-50 space-y-4">
                            {/* User Info */}
                            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm">
                              <div><span className="text-slate-500 text-xs">Email</span><p className="font-medium">{req.contact_email || req.user_email}</p></div>
                              <div><span className="text-slate-500 text-xs">Phone</span><p className="font-medium">{req.contact_phone || 'N/A'}</p></div>
                              <div><span className="text-slate-500 text-xs">Business</span><p className="font-medium capitalize">{req.business_type}</p></div>
                              <div><span className="text-slate-500 text-xs">Budget</span><p className="font-medium">{req.budget_range?.replace('_', '-') || 'Not set'}</p></div>
                            </div>

                            {req.notes && (
                              <div className="p-3 bg-white rounded-xl border border-slate-200">
                                <p className="text-xs text-slate-500 mb-1">User Notes</p>
                                <p className="text-sm text-slate-700">{req.notes}</p>
                              </div>
                            )}

                            {/* Matched Expert Info */}
                            {req.matched_expert && (
                              <div className="p-3 bg-[#E8F5E9] rounded-xl border border-[#A5D6A7]">
                                <p className="text-xs text-[#006400] font-medium mb-1">Matched Expert</p>
                                <p className="font-bold text-[#022c22]">{req.matched_expert.name}</p>
                                <p className="text-sm text-slate-600">{req.matched_expert.email} &middot; {req.matched_expert.phone}</p>
                              </div>
                            )}

                            {/* Admin Notes */}
                            {req.admin_notes?.length > 0 && (
                              <div className="space-y-2">
                                <p className="text-xs text-slate-500 font-medium">Admin Notes</p>
                                {req.admin_notes.map(n => (
                                  <div key={n.id} className="p-2 bg-white rounded-lg border text-sm">
                                    <p className="text-slate-700">{n.text}</p>
                                    <p className="text-xs text-slate-400 mt-1">{n.admin_name} &middot; {formatDate(n.created_at)}</p>
                                  </div>
                                ))}
                              </div>
                            )}

                            {/* Actions */}
                            <div className="space-y-3">
                              {/* Quick Status Change */}
                              <div className="flex gap-2 flex-wrap">
                                {['reviewing', 'in_progress', 'completed', 'cancelled'].filter(s => s !== req.status).map(s => (
                                  <Button key={s} size="sm" variant="outline"
                                    onClick={() => updateStatus(req.id, s)}
                                    className="rounded-xl text-xs"
                                    data-testid={`status-${s}-${req.id}`}
                                  >
                                    {STATUS_CONFIG[s]?.label || s}
                                  </Button>
                                ))}
                              </div>

                              {/* Match Expert Form */}
                              {req.status !== 'matched' && req.status !== 'completed' && (
                                <div className="p-4 bg-white rounded-xl border border-[#A5D6A7] space-y-3">
                                  <p className="font-medium text-[#006400] text-sm flex items-center gap-2">
                                    <Handshake className="w-4 h-4" /> Match with Expert
                                  </p>
                                  <div className="grid grid-cols-2 gap-2">
                                    <Input placeholder="Expert Name *" value={matchForm.expert_name}
                                      onChange={e => setMatchForm({ ...matchForm, expert_name: e.target.value })}
                                      className="rounded-lg text-sm" data-testid="match-expert-name" />
                                    <Input placeholder="Expert Email" value={matchForm.expert_email}
                                      onChange={e => setMatchForm({ ...matchForm, expert_email: e.target.value })}
                                      className="rounded-lg text-sm" data-testid="match-expert-email" />
                                    <Input placeholder="Expert Phone" value={matchForm.expert_phone}
                                      onChange={e => setMatchForm({ ...matchForm, expert_phone: e.target.value })}
                                      className="rounded-lg text-sm" />
                                    <Input placeholder="Specialty" value={matchForm.expert_specialty}
                                      onChange={e => setMatchForm({ ...matchForm, expert_specialty: e.target.value })}
                                      className="rounded-lg text-sm" />
                                  </div>
                                  <Button size="sm" onClick={() => matchExpert(req.id)}
                                    className="bg-[#006400] hover:bg-[#004d00] text-white rounded-xl w-full"
                                    data-testid={`match-btn-${req.id}`}
                                  >
                                    <Handshake className="w-4 h-4 mr-2" /> Match & Notify User
                                  </Button>
                                </div>
                              )}

                              {/* Add Note */}
                              <div className="flex gap-2">
                                <Input placeholder="Add admin note..." value={noteText}
                                  onChange={e => setNoteText(e.target.value)}
                                  className="rounded-xl text-sm flex-1" data-testid="admin-note-input" />
                                <Button size="sm" onClick={() => addNote(req.id)}
                                  className="rounded-xl bg-slate-700 hover:bg-slate-800 text-white"
                                  data-testid={`add-note-${req.id}`}
                                >
                                  <Send className="w-4 h-4" />
                                </Button>
                              </div>
                            </div>
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* ===== USERS TAB ===== */}
        {tab === 'users' && (
          <div className="space-y-3">
            {users.map((u, idx) => (
              <Card key={u.id} className="rounded-2xl border-slate-200" data-testid={`user-row-${idx}`}>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3 min-w-0">
                      <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${u.role === 'admin' ? 'bg-[#FFD700]' : 'bg-[#E8F5E9]'}`}>
                        {u.role === 'admin' ? <Crown className="w-5 h-5 text-[#422006]" /> : <Users className="w-5 h-5 text-[#006400]" />}
                      </div>
                      <div className="min-w-0">
                        <p className="font-medium text-[#022c22] truncate">{u.name}</p>
                        <p className="text-xs text-slate-500 truncate">{u.email}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge className="capitalize text-xs" variant="outline">{u.business_type?.replace('_', ' ')}</Badge>
                      <Select value={u.subscription_plan || 'starter'} onValueChange={v => updateUserPlan(u.id, v)}>
                        <SelectTrigger className="w-24 h-8 rounded-lg text-xs" data-testid={`plan-select-${idx}`}>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="starter">Starter</SelectItem>
                          <SelectItem value="pro">Pro</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </Layout>
  );
}
