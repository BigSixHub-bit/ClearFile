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
    if (pct >= 100) return 'text-[#006400]';
    if (pct >= 60) return 'text-[#FFD700]';
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
          <h1 className="text-2xl sm:text-3xl font-bold text-[#022c22]" style={{ fontFamily: 'Outfit' }}>
            TCC Progress
          </h1>
          <p className="text-slate-500">Track your Tax Clearance Certificate readiness</p>
        </div>

        {/* Progress Card */}
        <Card className="rounded-2xl border-slate-200 overflow-hidden" data-testid="tcc-progress-card">
          <div className={`p-6 ${tccData?.tcc_ready ? 'bg-[#006400]' : 'bg-gradient-to-r from-[#006400] to-[#228B22]'} text-white`}>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="w-14 h-14 bg-white/20 rounded-2xl flex items-center justify-center">
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
            <Progress value={tccData?.progress || 0} className="h-3 bg-white/20" />
          </div>
          <CardContent className="p-6">
            {tccData?.tcc_ready ? (
              <div className="text-center py-4">
                <div className="w-16 h-16 bg-[#E8F5E9] rounded-full flex items-center justify-center mx-auto mb-4">
                  <CheckCircle className="w-10 h-10 text-[#006400]" />
                </div>
                <h3 className="text-xl font-bold text-[#006400] mb-2">You're TCC Ready!</h3>
                <p className="text-slate-600 mb-4">Download your TCC Request Letter and submit to FIRS or your state revenue service.</p>
                <Button onClick={downloadLetter} className="bg-[#006400] hover:bg-[#004d00] text-white rounded-xl" data-testid="download-tcc-letter">
                  <Download className="w-4 h-4 mr-2" />
                  Download TCC Request Letter (PDF)
                </Button>
              </div>
            ) : (
              <div className="flex items-start gap-3 p-4 bg-[#FFF8E1] rounded-xl">
                <AlertCircle className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-medium text-[#422006]">Complete all requirements to qualify</p>
                  <p className="text-sm text-slate-600 mt-1">
                    You need {tccData?.total_count - tccData?.completed_count} more items. Complete them to generate your TCC letter.
                  </p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Checklist */}
        <Card className="rounded-2xl border-slate-200">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2" style={{ fontFamily: 'Outfit' }}>
              <FileText className="w-5 h-5 text-[#006400]" />
              TCC Requirements Checklist
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {tccData?.checklist?.map((item, idx) => (
              <div key={item.id} className={`flex items-start gap-4 p-4 rounded-xl border ${item.completed ? 'bg-[#E8F5E9] border-[#A5D6A7]' : 'bg-white border-slate-200'}`} data-testid={`tcc-checklist-${idx}`}>
                <div className="mt-0.5">
                  {item.completed ? (
                    <CheckCircle className="w-6 h-6 text-[#006400]" />
                  ) : (
                    <Circle className="w-6 h-6 text-slate-300" />
                  )}
                </div>
                <div className="flex-1">
                  <p className={`font-medium ${item.completed ? 'text-[#006400]' : 'text-[#022c22]'}`}>{item.item}</p>
                  <p className="text-sm text-slate-500 mt-1">{item.description}</p>
                </div>
                <Badge variant={item.completed ? "default" : "outline"} className={item.completed ? "bg-[#006400]" : ""}>
                  {item.weight}%
                </Badge>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Security */}
        <Card className="rounded-2xl border-slate-200 bg-[#E8F5E9]">
          <CardContent className="p-6">
            <div className="flex items-center gap-4">
              <Shield className="w-10 h-10 text-[#006400]" />
              <div>
                <h3 className="font-bold text-[#006400]">Your TCC data is secure</h3>
                <p className="text-sm text-slate-600">256-bit encryption. NDPR compliant. Your financial data never leaves our secure servers.</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </Layout>
  );
}
