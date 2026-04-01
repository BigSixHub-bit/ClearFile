import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import Layout from '../components/Layout';
import { Card, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { toast } from 'sonner';
import { Send, Bot, User, Loader2 } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

export default function ChatAssistant() {
  const { user } = useAuth();
  const { t } = useLanguage();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    // Add welcome message
    setMessages([
      {
        role: 'assistant',
        content: `Hello ${user?.name?.split(' ')[0] || 'there'}! I'm your NairaTrack Tax Assistant. I can help you understand Nigerian tax laws, calculate estimates, and answer questions about PITA, CITA, VAT, and WHT. What would you like to know?`
      }
    ]);
  }, [user]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setLoading(true);

    try {
      const { data } = await axios.post(`${API}/api/chat`, {
        message: userMessage,
        session_id: sessionId
      }, { withCredentials: true });

      setSessionId(data.session_id);
      setMessages(prev => [...prev, { role: 'assistant', content: data.response }]);
    } catch (error) {
      toast.error('Failed to get response');
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: "I'm sorry, I couldn't process your request right now. Please try again." 
      }]);
    } finally {
      setLoading(false);
    }
  };

  const suggestedQuestions = [
    "How do I calculate my PITA?",
    "What expenses are tax deductible?",
    "When is the VAT filing deadline?",
    "What's the difference between PITA and CITA?"
  ];

  return (
    <Layout>
      <div className="flex flex-col h-[calc(100vh-180px)] lg:h-[calc(100vh-140px)]">
        {/* Header */}
        <div className="mb-4">
          <h1 className="text-2xl sm:text-3xl font-bold text-[#022c22]" style={{ fontFamily: 'Outfit' }}>
            {t('chatAssistant')}
          </h1>
          <p className="text-slate-500">Ask me anything about Nigerian taxes</p>
        </div>

        {/* Chat Area */}
        <Card className="flex-1 rounded-2xl border-slate-200 flex flex-col overflow-hidden">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map((message, idx) => (
              <div
                key={idx}
                className={`flex items-start gap-3 ${message.role === 'user' ? 'flex-row-reverse' : ''}`}
                data-testid={`chat-message-${idx}`}
              >
                <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                  message.role === 'user' ? 'bg-[#006400]' : 'bg-[#E8F5E9]'
                }`}>
                  {message.role === 'user' ? (
                    <User className="w-4 h-4 text-white" />
                  ) : (
                    <Bot className="w-4 h-4 text-[#006400]" />
                  )}
                </div>
                <div className={`max-w-[80%] rounded-2xl p-4 ${
                  message.role === 'user'
                    ? 'bg-[#006400] text-white'
                    : 'bg-slate-100 text-slate-700'
                }`}>
                  {message.role === 'assistant' ? (
                    <div className="prose prose-sm prose-slate max-w-none overflow-x-auto">
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        components={{
                          h1: ({children}) => <h1 className="text-lg font-bold text-[#022c22] mb-2 mt-0">{children}</h1>,
                          h2: ({children}) => <h2 className="text-base font-bold text-[#022c22] mb-2 mt-3">{children}</h2>,
                          h3: ({children}) => <h3 className="text-sm font-semibold text-[#022c22] mb-1 mt-2">{children}</h3>,
                          p: ({children}) => <p className="text-sm mb-2 last:mb-0">{children}</p>,
                          ul: ({children}) => <ul className="list-disc list-inside text-sm mb-2 space-y-1">{children}</ul>,
                          ol: ({children}) => <ol className="list-decimal list-inside text-sm mb-2 space-y-1">{children}</ol>,
                          li: ({children}) => <li className="text-sm">{children}</li>,
                          strong: ({children}) => <strong className="font-semibold text-[#006400]">{children}</strong>,
                          em: ({children}) => <em className="italic">{children}</em>,
                          code: ({children}) => <code className="bg-slate-200 px-1 py-0.5 rounded text-xs">{children}</code>,
                          table: ({children}) => (
                            <div className="overflow-x-auto my-3">
                              <table className="min-w-full border-collapse border border-slate-300 rounded-lg text-sm">
                                {children}
                              </table>
                            </div>
                          ),
                          thead: ({children}) => <thead className="bg-[#E8F5E9]">{children}</thead>,
                          tbody: ({children}) => <tbody className="divide-y divide-slate-200">{children}</tbody>,
                          tr: ({children}) => <tr className="hover:bg-slate-50">{children}</tr>,
                          th: ({children}) => (
                            <th className="px-3 py-2 text-left font-semibold text-[#006400] border border-slate-300">
                              {children}
                            </th>
                          ),
                          td: ({children}) => (
                            <td className="px-3 py-2 border border-slate-300">
                              {children}
                            </td>
                          ),
                        }}
                      >
                        {message.content}
                      </ReactMarkdown>
                    </div>
                  ) : (
                    <p className="whitespace-pre-wrap text-sm">{message.content}</p>
                  )}
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-full bg-[#E8F5E9] flex items-center justify-center">
                  <Bot className="w-4 h-4 text-[#006400]" />
                </div>
                <div className="bg-slate-100 rounded-2xl p-4">
                  <Loader2 className="w-5 h-5 text-[#006400] animate-spin" />
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Suggestions */}
          {messages.length <= 1 && (
            <div className="px-4 pb-2">
              <p className="text-xs text-slate-400 mb-2">Suggested questions:</p>
              <div className="flex flex-wrap gap-2">
                {suggestedQuestions.map((q, idx) => (
                  <Button
                    key={idx}
                    variant="outline"
                    size="sm"
                    className="rounded-full text-xs border-[#006400] text-[#006400] hover:bg-[#E8F5E9]"
                    onClick={() => setInput(q)}
                    data-testid={`suggestion-${idx}`}
                  >
                    {q}
                  </Button>
                ))}
              </div>
            </div>
          )}

          {/* Input */}
          <form onSubmit={handleSend} className="p-4 border-t border-slate-200">
            <div className="flex gap-2">
              <Input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder={t('askQuestion')}
                className="flex-1 rounded-xl"
                disabled={loading}
                data-testid="chat-input"
              />
              <Button
                type="submit"
                disabled={loading || !input.trim()}
                className="bg-[#006400] hover:bg-[#004d00] text-white rounded-xl"
                data-testid="chat-send-btn"
              >
                <Send className="w-4 h-4" />
              </Button>
            </div>
          </form>
        </Card>
      </div>
    </Layout>
  );
}
