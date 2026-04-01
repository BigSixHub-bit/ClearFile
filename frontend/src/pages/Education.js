import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Layout from '../components/Layout';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { useLanguage } from '../context/LanguageContext';
import { toast } from 'sonner';
import { BookOpen, ChevronRight, Search, FileText } from 'lucide-react';
import { Input } from '../components/ui/input';

const API = process.env.REACT_APP_BACKEND_URL;

export default function Education() {
  const { t } = useLanguage();
  const [articles, setArticles] = useState([]);
  const [selectedArticle, setSelectedArticle] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchArticles();
  }, []);

  const fetchArticles = async () => {
    try {
      const { data } = await axios.get(`${API}/api/education/articles`, { withCredentials: true });
      setArticles(data);
    } catch (error) {
      toast.error('Failed to load articles');
    } finally {
      setLoading(false);
    }
  };

  const filteredArticles = articles.filter(article =>
    article.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    article.summary.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const categoryColors = {
    basics: 'bg-[#E8F5E9] text-[#006400]',
    vat: 'bg-[#FFF8E1] text-[#422006]',
    deductions: 'bg-blue-50 text-blue-700',
    updates: 'bg-purple-50 text-purple-700'
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
            {t('education')}
          </h1>
          <p className="text-slate-500">Learn about Nigerian taxes in plain English</p>
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
          <Input
            placeholder="Search articles..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10 rounded-xl"
            data-testid="search-articles-input"
          />
        </div>

        {/* Articles Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredArticles.map((article, idx) => (
            <Card 
              key={article.id} 
              className="rounded-2xl border-slate-200 hover-lift cursor-pointer"
              onClick={() => setSelectedArticle(article)}
              data-testid={`article-card-${idx}`}
            >
              <CardContent className="p-6">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <Badge className={`mb-3 ${categoryColors[article.category] || 'bg-slate-100 text-slate-600'}`}>
                      {article.category}
                    </Badge>
                    <h3 className="font-bold text-[#022c22] text-lg mb-2" style={{ fontFamily: 'Outfit' }}>
                      {article.title}
                    </h3>
                    <p className="text-slate-600 text-sm line-clamp-2">{article.summary}</p>
                  </div>
                  <ChevronRight className="w-5 h-5 text-slate-400 flex-shrink-0" />
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {filteredArticles.length === 0 && (
          <div className="text-center py-12 text-slate-400">
            <BookOpen className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p>No articles found</p>
          </div>
        )}

        {/* Article Dialog */}
        <Dialog open={!!selectedArticle} onOpenChange={() => setSelectedArticle(null)}>
          <DialogContent className="sm:max-w-2xl max-h-[80vh] overflow-y-auto">
            {selectedArticle && (
              <>
                <DialogHeader>
                  <Badge className={`w-fit mb-2 ${categoryColors[selectedArticle.category] || 'bg-slate-100 text-slate-600'}`}>
                    {selectedArticle.category}
                  </Badge>
                  <DialogTitle className="text-xl" style={{ fontFamily: 'Outfit' }}>
                    {selectedArticle.title}
                  </DialogTitle>
                </DialogHeader>
                <div className="prose prose-slate prose-sm max-w-none">
                  <p className="text-slate-600 font-medium">{selectedArticle.summary}</p>
                  <div className="mt-4 whitespace-pre-wrap text-slate-700">
                    {selectedArticle.content}
                  </div>
                </div>
              </>
            )}
          </DialogContent>
        </Dialog>

        {/* AI Assistant Promo */}
        <Card className="rounded-2xl border-[#006400] bg-[#006400]">
          <CardContent className="p-6">
            <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
              <div className="text-center sm:text-left">
                <h3 className="font-bold text-white text-lg">Have a specific question?</h3>
                <p className="text-[#A5D6A7]">Chat with our AI tax assistant for personalized answers</p>
              </div>
              <Button
                onClick={() => window.location.href = '/chat'}
                className="bg-white text-[#006400] hover:bg-slate-100 rounded-xl"
                data-testid="goto-chat-btn"
              >
                Ask AI Assistant
                <ChevronRight className="w-4 h-4 ml-2" />
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </Layout>
  );
}
