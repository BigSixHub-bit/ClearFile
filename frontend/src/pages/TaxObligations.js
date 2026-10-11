import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Layout from '../components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { useAuth } from '../context/AuthContext';
import { toast } from 'sonner';
import { 
  Building2, Landmark, Globe, Calendar, ExternalLink, 
  ArrowRight, Shield, MapPin
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

export default function TaxObligations() {
  const { user } = useAuth();
  const [obligations, setObligations] = useState(null);
  const [states, setStates] = useState([]);
  const [selectedState, setSelectedState] = useState(user?.state_of_residence || 'lagos');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStates();
    fetchObligations();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const fetchStates = async () => {
    try {
      const { data } = await axios.get(`${API}/api/states`, { withCredentials: true });
      setStates(data.states || []);
    } catch (e) { /* ignore */ }
  };

  const fetchObligations = async () => {
    try {
      const { data } = await axios.get(`${API}/api/tax-obligations`, { withCredentials: true });
      setObligations(data);
    } catch (error) {
      toast.error('Failed to load tax obligations');
    } finally {
      setLoading(false);
    }
  };

  const updateState = async (state) => {
    setSelectedState(state);
    try {
      await axios.put(`${API}/api/user/state`, { state_of_residence: state }, { withCredentials: true });
      fetchObligations();
      toast.success('State updated');
    } catch (e) {
      toast.error('Failed to update state');
    }
  };

  const formatCurrency = (v) => new Intl.NumberFormat('en-NG', { style: 'currency', currency: 'NGN', minimumFractionDigits: 0 }).format(v).replace('NGN', 'N');

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-64">
          <div className="w-12 h-12 border-4 border-[#006400] border-t-transparent rounded-full animate-spin"></div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-6 pb-20 lg:pb-0">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold text-white" style={{ fontFamily: 'Clash Display, Satoshi, sans-serif' }}>
              Tax Obligations
            </h1>
            <p className="text-[#A1A1AA]">State vs Federal tax routing for your business</p>
          </div>
          <div className="flex items-center gap-2">
            <MapPin className="w-4 h-4 text-[#A1A1AA]" />
            <Select value={selectedState} onValueChange={updateState}>
              <SelectTrigger className="w-48 rounded-xl" data-testid="state-select">
                <SelectValue placeholder="Select state" />
              </SelectTrigger>
              <SelectContent>
                {states.map(s => (
                  <SelectItem key={s.id} value={s.id}>{s.name} ({s.service})</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Card className="rounded-2xl border-[#3B82F6]/20 bg-[#3B82F6]/10" data-testid="federal-total-card">
            <CardContent className="p-6">
              <div className="flex items-center gap-3 mb-2">
                <Landmark className="w-6 h-6 text-[#3B82F6]" />
                <span className="text-sm font-medium text-[#3B82F6]">Federal (NRS)</span>
              </div>
              <p className="text-3xl font-bold text-[#3B82F6]">{formatCurrency(obligations?.total_federal || 0)}</p>
              <p className="text-xs text-blue-500 mt-1">{obligations?.federal?.length || 0} obligations</p>
            </CardContent>
          </Card>
          <Card className="rounded-2xl border-[#00C896]/20 bg-[#00C896]/10" data-testid="state-total-card">
            <CardContent className="p-6">
              <div className="flex items-center gap-3 mb-2">
                <Building2 className="w-6 h-6 text-[#00C896]" />
                <span className="text-sm font-medium text-[#00C896]">State ({obligations?.state_info?.service})</span>
              </div>
              <p className="text-3xl font-bold text-[#00C896]">{formatCurrency(obligations?.total_state || 0)}</p>
              <p className="text-xs text-[#00C896] mt-1">{obligations?.state?.length || 0} obligations</p>
            </CardContent>
          </Card>
        </div>

        {/* Federal Obligations */}
        {obligations?.federal?.length > 0 && (
          <Card className="rounded-2xl border-[#3B82F6]/20" data-testid="federal-obligations">
            <CardHeader className="border-b border-blue-100">
              <CardTitle className="text-lg flex items-center gap-2" style={{ fontFamily: 'Clash Display, Satoshi, sans-serif' }}>
                <Landmark className="w-5 h-5 text-[#3B82F6]" />
                Federal Tax Obligations (NRS)
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0 divide-y divide-blue-50">
              {obligations.federal.map((ob, idx) => (
                <div key={idx} className="p-5" data-testid={`federal-obligation-${idx}`}>
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="font-bold text-white">{ob.tax_type}</h3>
                        <Badge className="bg-blue-100 text-[#3B82F6]">Federal</Badge>
                      </div>
                      <p className="text-sm text-[#A1A1AA] mt-1">{ob.description}</p>
                    </div>
                    <p className="text-xl font-bold text-[#3B82F6]">{formatCurrency(ob.amount)}</p>
                  </div>
                  <div className="flex flex-wrap gap-4 mt-3 text-xs text-[#A1A1AA]">
                    <div className="flex items-center gap-1"><Calendar className="w-3 h-3" /> {ob.deadline}</div>
                    <div className="flex items-center gap-1"><Globe className="w-3 h-3" /> {ob.frequency}</div>
                    {ob.next_deadline && <div>Next: <span className="font-medium text-white">{ob.next_deadline}</span></div>}
                  </div>
                  <a href={ob.portal} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 mt-3 text-sm text-[#3B82F6] hover:underline">
                    Go to NRS Portal <ExternalLink className="w-3 h-3" />
                  </a>
                </div>
              ))}
            </CardContent>
          </Card>
        )}

        {/* State Obligations */}
        {obligations?.state?.length > 0 && (
          <Card className="rounded-2xl border-[#00C896]/20" data-testid="state-obligations">
            <CardHeader className="border-b border-[#C8E6C9]">
              <CardTitle className="text-lg flex items-center gap-2" style={{ fontFamily: 'Clash Display, Satoshi, sans-serif' }}>
                <Building2 className="w-5 h-5 text-[#00C896]" />
                State Tax Obligations ({obligations.state_info?.service})
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0 divide-y divide-[#E8F5E9]">
              {obligations.state.map((ob, idx) => (
                <div key={idx} className="p-5" data-testid={`state-obligation-${idx}`}>
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="font-bold text-white">{ob.tax_type}</h3>
                        <Badge className="bg-[#00C896]/10 text-[#00C896]">State</Badge>
                      </div>
                      <p className="text-sm text-[#A1A1AA] mt-1">{ob.description}</p>
                    </div>
                    <p className="text-xl font-bold text-[#00C896]">{formatCurrency(ob.amount)}</p>
                  </div>
                  <div className="flex flex-wrap gap-4 mt-3 text-xs text-[#A1A1AA]">
                    <div className="flex items-center gap-1"><Calendar className="w-3 h-3" /> {ob.deadline}</div>
                    <div className="flex items-center gap-1"><Globe className="w-3 h-3" /> {ob.frequency}</div>
                  </div>
                  <a href={obligations.state_info?.portal} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 mt-3 text-sm text-[#00C896] hover:underline">
                    Go to {obligations.state_info?.service} Portal <ExternalLink className="w-3 h-3" />
                  </a>
                </div>
              ))}
            </CardContent>
          </Card>
        )}
      </div>
    </Layout>
  );
}
