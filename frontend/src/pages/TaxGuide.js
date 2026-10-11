import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Layout from '../components/Layout';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Progress } from '../components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { useLanguage } from '../context/LanguageContext';
import { toast } from 'sonner';
import { 
  FileText, CheckCircle2, Circle, ExternalLink, 
  Calendar, ClipboardList, AlertCircle
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

export default function TaxGuide() {
  const { t } = useLanguage();
  const [guide, setGuide] = useState(null);
  const [checklist, setChecklist] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([fetchGuide(), fetchChecklist()]).finally(() => setLoading(false));
  }, []);

  const fetchGuide = async () => {
    try {
      const { data } = await axios.get(`${API}/api/tax-filing/guide`, { withCredentials: true });
      setGuide(data);
    } catch (error) {
      toast.error('Failed to load filing guide');
    }
  };

  const fetchChecklist = async () => {
    try {
      const { data } = await axios.get(`${API}/api/tax-filing/checklist`, { withCredentials: true });
      setChecklist(data);
    } catch (error) {
      toast.error('Failed to load checklist');
    }
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
        {/* Header */}
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-[#022c22]" style={{ fontFamily: 'Outfit' }}>
            {t('taxGuide')}
          </h1>
          <p className="text-slate-500">Step-by-step guide to filing your taxes</p>
        </div>

        <Tabs defaultValue="guide" className="space-y-6">
          <TabsList className="grid w-full grid-cols-3 bg-slate-100 rounded-xl p-1">
            <TabsTrigger value="guide" className="rounded-lg" data-testid="tab-guide">
              <FileText className="w-4 h-4 mr-2" />
              {t('filingGuide')}
            </TabsTrigger>
            <TabsTrigger value="checklist" className="rounded-lg" data-testid="tab-checklist">
              <ClipboardList className="w-4 h-4 mr-2" />
              {t('checklist')}
            </TabsTrigger>
            <TabsTrigger value="deadlines" className="rounded-lg" data-testid="tab-deadlines">
              <Calendar className="w-4 h-4 mr-2" />
              {t('deadlines')}
            </TabsTrigger>
          </TabsList>

          {/* Filing Guide */}
          <TabsContent value="guide" className="space-y-4">
            {guide?.steps?.map((step, idx) => (
              <Card key={idx} className="rounded-2xl border-slate-200" data-testid={`step-${idx}`}>
                <CardContent className="p-6">
                  <div className="flex items-start gap-4">
                    <div className="w-10 h-10 bg-[#006400] text-white rounded-xl flex items-center justify-center font-bold flex-shrink-0">
                      {step.step}
                    </div>
                    <div>
                      <h3 className="font-bold text-[#022c22] text-lg">{step.title}</h3>
                      <p className="text-slate-600 mt-1">{step.description}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}

            <Card className="rounded-2xl border-slate-200 bg-[#006400]">
              <CardContent className="p-6">
                <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
                  <div className="text-center sm:text-left">
                    <h3 className="font-bold text-white text-lg">Ready to File?</h3>
                    <p className="text-[#A5D6A7]">Go to the official NRS TaxPro-Max portal</p>
                  </div>
                  <Button
                    onClick={() => window.open(guide?.firs_portal, '_blank')}
                    className="bg-white text-[#006400] hover:bg-slate-100 rounded-xl"
                    data-testid="firs-portal-btn"
                  >
                    {t('firs')}
                    <ExternalLink className="w-4 h-4 ml-2" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Checklist */}
          <TabsContent value="checklist" className="space-y-4">
            <Card className="rounded-2xl border-slate-200">
              <CardHeader>
                <CardTitle className="text-lg flex items-center justify-between" style={{ fontFamily: 'Outfit' }}>
                  <span>Filing Checklist</span>
                  <span className="text-sm font-normal text-slate-500">
                    {checklist?.completed_count}/{checklist?.total_count} completed
                  </span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <Progress 
                  value={checklist?.progress_percentage || 0} 
                  className="h-2 mb-6"
                  data-testid="checklist-progress"
                />
                <div className="space-y-3">
                  {checklist?.checklist?.map((item, idx) => (
                    <div
                      key={idx}
                      className={`flex items-center gap-3 p-3 rounded-xl transition-colors ${
                        item.completed ? 'bg-[#E8F5E9]' : 'bg-slate-50'
                      }`}
                      data-testid={`checklist-item-${idx}`}
                    >
                      {item.completed ? (
                        <CheckCircle2 className="w-5 h-5 text-[#006400] flex-shrink-0" />
                      ) : (
                        <Circle className="w-5 h-5 text-slate-300 flex-shrink-0" />
                      )}
                      <span className={item.completed ? 'text-[#006400]' : 'text-slate-600'}>
                        {item.item}
                      </span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card className="rounded-2xl border-slate-200">
              <CardHeader>
                <CardTitle className="text-lg" style={{ fontFamily: 'Outfit' }}>{t('documents')}</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  {guide?.documents_needed?.map((doc, idx) => (
                    <li key={idx} className="flex items-center gap-2 text-slate-600">
                      <div className="w-2 h-2 bg-[#006400] rounded-full"></div>
                      {doc}
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Deadlines */}
          <TabsContent value="deadlines" className="space-y-4">
            <Card className="rounded-2xl border-slate-200">
              <CardHeader>
                <CardTitle className="text-lg" style={{ fontFamily: 'Outfit' }}>Important Deadlines</CardTitle>
                <CardDescription>Mark these dates on your calendar</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {Object.entries(guide?.deadlines || {}).map(([key, value], idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between p-4 bg-[#FFF8E1] rounded-xl"
                    data-testid={`deadline-${key}`}
                  >
                    <div className="flex items-center gap-3">
                      <Calendar className="w-5 h-5 text-[#FFD700]" />
                      <span className="font-medium text-[#422006] capitalize">
                        {key.replace(/_/g, ' ')}
                      </span>
                    </div>
                    <span className="text-slate-600">{value}</span>
                  </div>
                ))}
              </CardContent>
            </Card>

            <Card className="rounded-2xl border-slate-200 bg-red-50">
              <CardContent className="p-4">
                <div className="flex items-start gap-3">
                  <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="font-medium text-red-700">Late Filing Penalties</p>
                    <p className="text-sm text-red-600 mt-1">
                      Filing late may result in penalties of ₦25,000 for individuals or ₦50,000 for companies, 
                      plus interest on unpaid taxes. File on time to avoid these charges.
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </Layout>
  );
}
