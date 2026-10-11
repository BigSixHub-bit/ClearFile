import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import Layout from '../components/Layout';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Progress } from '../components/ui/progress';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { toast } from 'sonner';
import { 
  Award, CheckCircle, Circle, Download, FileText, 
  ArrowRight, Shield, AlertCircle
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

export default function TCCTracker() {
  const { user } = useAuth();
  const { t } = useLanguage();
  const [tccData, setTccData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => { fetchTCCProgress(); }, []);

  const fetchTCCProgress = async () => {
    try {
      const { data } = await axios.get(`${API}/api/tcc/progress`, { withCredentials: true });
      setTccData(data);
    } catch (error) {
      toast.error('Failed to load TCC progress');
    } finally {
      setLoading(false);
    }
  };

  const downloadLetter = () => {
    window.open(`${API}/api/tcc/generate-letter`, '_blank');
  };

  const getProgressColor = (pct) => {
    if (pct >= 100) return 'text-[#00C896]';
    if (pct >= 60) return 'text-[#F59E0B]';
    return 'text-red-500';
  };

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
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white" style={{ fontFamily: 'Clash Display, Satoshi, sans-serif' }}>
            TCC Progress
          </h1>
          <p className="text-[#A1A1AA]">Track your Tax Clearance Certificate readiness</p>
        </div>

        {/* Progress Card */}
        <Card className="card-dark overflow-hidden" data-testid="tcc-progress-card">
          <div className={`p-6 ${tccData?.tcc_ready ? 'bg-[#00C896]' : 'bg-gradient-to-r from-[#006400] to-[#228B22]'} text-white`}>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="w-14 h-14 bg-[#111111]/20 rounded-2xl flex items-center justify-center">
                  <Award className="w-8 h-8" />
                </div>
                <div>
                  <h2 className="text-xl font-bold">TCC Readiness</h2>
                  <p className="text-white/70 text-sm">{tccData?.completed_count}/{tccData?.total_count} requirements met</p>
                </div>
              </div>
              <div className="text-right">
                <span className="text-5xl font-bold" data-testid="tcc-progress-value">{tccData?.progress}%</span>
              </div>
            </div>
            <Progress value={tccData?.progress || 0} className="h-3 bg-[#111111]/20" />
          </div>
          <CardContent className="p-6">
            {tccData?.tcc_ready ? (
              <div className="text-center py-6">
                <div className="w-20 h-20 bg-[#00C896]/10 rounded-full flex items-center justify-center mx-auto mb-4">
                  <CheckCircle className="w-12 h-12 text-[#00C896]" />
                </div>
                <h3 className="text-2xl font-bold text-[#00C896] mb-2">You're TCC Ready!</h3>
                <p className="text-[#A1A1AA] mb-6">All requirements met. Generate your NRS/LIRS Application Pack now.</p>
                <Button onClick={downloadLetter} size="lg" className="bg-[#00C896] hover:bg-[#00dba6] text-white rounded-xl px-8 py-6 text-lg" data-testid="download-tcc-letter">
                  <Download className="w-5 h-5 mr-2" />
                  Generate NRS/LIRS Application Pack
                </Button>
              </div>
            ) : (
              <div className="flex items-start gap-3 p-4 bg-[#F59E0B]/10 rounded-xl">
                <AlertCircle className="w-5 h-5 text-[#F59E0B] flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-medium text-white">Complete all requirements to qualify</p>
                  <p className="text-sm text-[#A1A1AA] mt-1">
                    You need {tccData?.total_count - tccData?.completed_count} more items. Complete them to generate your TCC letter.
                  </p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Checklist */}
        <Card className="card-dark">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2" style={{ fontFamily: 'Clash Display, Satoshi, sans-serif' }}>
              <FileText className="w-5 h-5 text-[#00C896]" />
              TCC Requirements Checklist
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {tccData?.checklist?.map((item, idx) => (
              <div key={item.id} className={`flex items-start gap-4 p-4 rounded-xl border ${item.completed ? 'bg-[#00C896]/10 border-[#00C896]/20' : 'bg-[#111111] border-[#1E1E1E]'}`} data-testid={`tcc-checklist-${idx}`}>
                <div className="mt-0.5">
                  {item.completed ? (
                    <CheckCircle className="w-6 h-6 text-[#00C896]" />
                  ) : (
                    <Circle className="w-6 h-6 text-slate-300" />
                  )}
                </div>
                <div className="flex-1">
                  <p className={`font-medium ${item.completed ? 'text-[#00C896]' : 'text-white'}`}>{item.item}</p>
                  <p className="text-sm text-[#A1A1AA] mt-1">{item.description}</p>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant={item.completed ? "default" : "outline"} className={item.completed ? "bg-[#00C896]" : ""}>
                    {item.weight}%
                  </Badge>
                  {!item.completed && item.fix_route && (
                    <Link to={item.fix_route}>
                      <Button size="sm" variant="destructive" className="rounded-lg text-xs" data-testid={`fix-now-${item.id}`}>
                        Fix Now
                      </Button>
                    </Link>
                  )}
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Security */}
        <Card className="card-dark bg-[#00C896]/10">
          <CardContent className="p-6">
            <div className="flex items-center gap-4">
              <Shield className="w-10 h-10 text-[#00C896]" />
              <div>
                <h3 className="font-bold text-[#00C896]">Your TCC data is secure</h3>
                <p className="text-sm text-[#A1A1AA]">256-bit encryption. NDPR compliant. Your financial data never leaves our secure servers.</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </Layout>
  );
}
