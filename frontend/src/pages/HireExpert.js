import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import Layout from '../components/Layout';
import { Card, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { useAuth } from '../context/AuthContext';
import { toast } from 'sonner';
import { 
  ArrowLeft, Handshake, Shield, CheckCircle, Clock, Send, Star
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

export default function HireExpert() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [form, setForm] = useState({
    phone: '',
    email: user?.email || '',
    service_type: 'full_filing',
    tax_year: String(new Date().getFullYear() - 1),
    urgency: 'normal',
    budget_range: '',
    notes: ''
  });

  const handleSubmit = async () => {
    if (!form.phone) {
      toast.error('Please enter your phone number');
      return;
    }
    setSubmitting(true);
    try {
      await axios.post(`${API}/api/experts/request`, form, { withCredentials: true });
      setSubmitted(true);
      toast.success('Expert request submitted!');
    } catch (error) {
      toast.error('Failed to submit request');
    } finally {
      setSubmitting(false);
    }
  };

  if (submitted) {
    return (
      <Layout>
        <div className="flex flex-col items-center justify-center min-h-[60vh] text-center px-4">
          <div className="w-20 h-20 bg-[#00C896]/10 rounded-full flex items-center justify-center mb-6">
            <CheckCircle className="w-12 h-12 text-[#00C896]" />
          </div>
          <h2 className="text-2xl font-bold text-white mb-2" style={{ fontFamily: 'Clash Display, Satoshi, sans-serif' }}>
            Request Submitted!
          </h2>
          <p className="text-[#A1A1AA] max-w-sm mb-2">
            We're matching you with a verified Pan-African tax professional.
          </p>
          <div className="flex items-center gap-2 text-sm text-[#00C896] font-medium mb-6">
            <Clock className="w-4 h-4" />
            <span>Estimated match time: 24-48 hours</span>
          </div>
          <p className="text-sm text-[#555] mb-6">
            You'll receive a notification and email when your expert is ready.
          </p>
          <div className="flex gap-3">
            <Button variant="outline" onClick={() => navigate('/dashboard')} className="rounded-xl" data-testid="back-to-dashboard">
              Back to Dashboard
            </Button>
            <Button onClick={() => navigate('/tax-calculator')} className="rounded-xl bg-[#00C896] hover:bg-[#00dba6] text-white" data-testid="back-to-tax">
              Back to Tax Calculator
            </Button>
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-6 pb-20 lg:pb-0 max-w-2xl mx-auto">
        {/* Header */}
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="icon" onClick={() => navigate('/tax-calculator')} className="rounded-xl" data-testid="expert-back-btn">
            <ArrowLeft className="w-5 h-5" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold text-white" style={{ fontFamily: 'Clash Display, Satoshi, sans-serif' }}>
              Hire a Verified Expert
            </h1>
            <p className="text-[#A1A1AA] text-sm">Connect with a vetted Pan-African tax professional</p>
          </div>
        </div>

        {/* Trust Signals */}
        <div className="grid grid-cols-3 gap-3">
          {[
            { icon: Shield, text: 'Vetted & Verified', color: 'text-[#00C896]', bg: 'bg-[#00C896]/10' },
            { icon: Star, text: 'Top-Rated Pros', color: 'text-[#D4A017]', bg: 'bg-[#F59E0B]/10' },
            { icon: CheckCircle, text: 'Secure Data', color: 'text-[#3B82F6]', bg: 'bg-[#3B82F6]/10' },
          ].map((item, i) => (
            <div key={i} className={`${item.bg} rounded-xl p-3 flex flex-col items-center gap-1.5 text-center`}>
              <item.icon className={`w-5 h-5 ${item.color}`} />
              <span className={`text-xs font-medium ${item.color}`}>{item.text}</span>
            </div>
          ))}
        </div>

        {/* Form */}
        <Card className="card-dark" data-testid="expert-form">
          <CardContent className="p-6 space-y-5">
            <div className="flex items-center gap-3 p-4 bg-gradient-to-r from-[#006400] to-[#228B22] rounded-xl text-white">
              <Handshake className="w-8 h-8" />
              <div>
                <p className="font-bold">Tell us what you need</p>
                <p className="text-sm text-[#A5D6A7]">We'll match you with the right expert</p>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Phone Number <span className="text-red-500">*</span></Label>
                <Input
                  type="tel"
                  placeholder="080XXXXXXXX"
                  value={form.phone}
                  onChange={e => setForm({ ...form, phone: e.target.value })}
                  className="rounded-xl"
                  data-testid="expert-phone"
                />
              </div>
              <div className="space-y-2">
                <Label>Email</Label>
                <Input
                  type="email"
                  value={form.email}
                  onChange={e => setForm({ ...form, email: e.target.value })}
                  className="rounded-xl"
                  data-testid="expert-email"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Service Type</Label>
                <Select value={form.service_type} onValueChange={v => setForm({ ...form, service_type: v })}>
                  <SelectTrigger className="rounded-xl" data-testid="expert-service">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="full_filing">Full Tax Filing</SelectItem>
                    <SelectItem value="review">Review My Filing</SelectItem>
                    <SelectItem value="advisory">Tax Advisory</SelectItem>
                    <SelectItem value="audit_support">Audit Support</SelectItem>
                    <SelectItem value="tcc_application">TCC Application</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Tax Year</Label>
                <Select value={form.tax_year} onValueChange={v => setForm({ ...form, tax_year: v })}>
                  <SelectTrigger className="rounded-xl" data-testid="expert-year">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value={String(new Date().getFullYear() - 1)}>{new Date().getFullYear() - 1}</SelectItem>
                    <SelectItem value={String(new Date().getFullYear())}>{new Date().getFullYear()}</SelectItem>
                    <SelectItem value="multiple">Multiple Years</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Urgency</Label>
                <Select value={form.urgency} onValueChange={v => setForm({ ...form, urgency: v })}>
                  <SelectTrigger className="rounded-xl" data-testid="expert-urgency">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="normal">Normal (1-2 weeks)</SelectItem>
                    <SelectItem value="urgent">Urgent (2-3 days)</SelectItem>
                    <SelectItem value="asap">ASAP (24 hours)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Budget Range</Label>
                <Select value={form.budget_range} onValueChange={v => setForm({ ...form, budget_range: v })}>
                  <SelectTrigger className="rounded-xl" data-testid="expert-budget">
                    <SelectValue placeholder="Select budget" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="under_10k">Under N10,000</SelectItem>
                    <SelectItem value="10k_25k">N10,000 - N25,000</SelectItem>
                    <SelectItem value="25k_50k">N25,000 - N50,000</SelectItem>
                    <SelectItem value="50k_100k">N50,000 - N100,000</SelectItem>
                    <SelectItem value="above_100k">Above N100,000</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="space-y-2">
              <Label>Additional Notes</Label>
              <Textarea
                placeholder="Any specific requirements or questions for the expert..."
                value={form.notes}
                onChange={e => setForm({ ...form, notes: e.target.value })}
                className="rounded-xl resize-none"
                rows={3}
                data-testid="expert-notes"
              />
            </div>

            <Button
              onClick={handleSubmit}
              disabled={submitting}
              className="w-full bg-[#00C896] hover:bg-[#00dba6] text-white rounded-xl py-6 text-base font-bold"
              data-testid="submit-expert-request"
            >
              {submitting ? (
                <><span className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" /> Submitting...</>
              ) : (
                <><Send className="w-5 h-5 mr-2" /> Submit Expert Request</>
              )}
            </Button>

            <p className="text-center text-xs text-[#555]">
              Your tax data will be securely shared with the matched expert. You can revoke access at any time.
            </p>
          </CardContent>
        </Card>
      </div>
    </Layout>
  );
}
