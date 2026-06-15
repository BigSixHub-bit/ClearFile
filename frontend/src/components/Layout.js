import React, { useState, useEffect, useCallback } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { 
  LayoutDashboard, Receipt, Calculator, FileText, BookOpen, 
  Settings, MessageCircle, LogOut, Menu, Bell, BellRing,
  Award, TrendingUp, Landmark, ShieldCheck, X
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Switch } from '../components/ui/switch';
import { Sheet, SheetContent, SheetTrigger } from '../components/ui/sheet';
import { Popover, PopoverContent, PopoverTrigger } from '../components/ui/popover';
import { Badge } from '../components/ui/badge';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL;

export default function Layout({ children }) {
  const { user, logout } = useAuth();
  const { language, toggleLanguage, t } = useLanguage();
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = React.useState(false);
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    fetchNotifications();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const fetchNotifications = async () => {
    try {
      const { data } = await axios.get(`${API}/api/notifications`, { withCredentials: true });
      setNotifications(data);
      setUnreadCount(data.filter(n => !n.read).length);
    } catch (error) { /* ignore */ }
  };

  const markAsRead = async () => {
    try {
      await axios.post(`${API}/api/notifications/mark-read`, {}, { withCredentials: true });
      setUnreadCount(0);
      setNotifications(prev => prev.map(n => ({ ...n, read: true })));
    } catch (error) { /* ignore */ }
  };

  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

  const getTimeAgo = (dateStr) => {
    if (!dateStr) return '';
    const diff = Date.now() - new Date(dateStr).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 60) return `${mins}m`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}h`;
    return `${Math.floor(hours / 24)}d`;
  };

  const navItems = [
    { to: '/dashboard', icon: LayoutDashboard, label: 'Command Center' },
    { to: '/transactions', icon: Receipt, label: 'Transactions' },
    { to: '/invoices', icon: FileText, label: 'Invoices' },
    { to: '/tax-calculator', icon: Calculator, label: 'Tax Engine' },
    { to: '/tax-obligations', icon: Landmark, label: 'Tax Routing' },
    { to: '/tax-planner', icon: TrendingUp, label: 'Tax Planner' },
    { to: '/tcc', icon: Award, label: 'TCC Tracker' },
    { to: '/chat', icon: MessageCircle, label: 'AI Assistant' },
    { to: '/settings', icon: Settings, label: 'Settings' },
  ];

  if (user?.role === 'admin') {
    navItems.push({ to: '/admin', icon: ShieldCheck, label: 'Admin' });
  }

  const NavContent = ({ mobile = false }) => (
    <div className="flex flex-col h-full bg-[#0A0A0A]">
      {/* Logo */}
      <div className="p-5 border-b border-[#1E1E1E]">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#00C896] to-[#3B82F6] flex items-center justify-center">
            <span className="text-black font-bold text-sm">C</span>
          </div>
          <span className="text-base font-display font-semibold text-white tracking-tight">ClearFile NG</span>
        </div>
      </div>

      {/* Nav Items */}
      <nav className="flex-1 py-4 px-3 space-y-0.5 overflow-y-auto">
        {navItems.map(item => (
          <NavLink
            key={item.to}
            to={item.to}
            onClick={() => mobile && setMobileMenuOpen(false)}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm transition-all ${
                isActive
                  ? 'bg-white/5 text-white border-l-2 border-[#00C896] ml-0'
                  : 'text-[#A1A1AA] hover:text-white hover:bg-white/[0.03]'
              }`
            }
            data-testid={`nav-${item.to.slice(1)}`}
          >
            <item.icon className="w-[18px] h-[18px]" />
            <span className="font-medium">{item.label}</span>
          </NavLink>
        ))}
      </nav>

      {/* Bottom */}
      <div className="p-4 border-t border-[#1E1E1E] space-y-3">
        <div className="flex items-center justify-between px-2">
          <span className="text-xs text-[#A1A1AA]">Pidgin / EN</span>
          <Switch
            checked={language === 'pidgin'}
            onCheckedChange={toggleLanguage}
            data-testid="pidgin-toggle"
          />
        </div>
        <div className="bg-[#111111] border border-[#1E1E1E] rounded-xl p-3">
          <p className="font-medium text-white text-sm truncate">{user?.name}</p>
          <p className="text-xs text-[#A1A1AA] truncate">{user?.email}</p>
          <div className="flex items-center gap-1.5 mt-1.5">
            <div className="w-1.5 h-1.5 rounded-full bg-[#00C896]"></div>
            <span className="text-xs text-[#00C896] font-medium capitalize">{user?.subscription_plan}</span>
          </div>
        </div>
        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm text-[#A1A1AA] hover:text-red-400 hover:bg-red-500/5 transition-all"
          data-testid="logout-btn"
        >
          <LogOut className="w-[18px] h-[18px]" />
          <span className="font-medium">Sign Out</span>
        </button>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-[#050505]">
      {/* Desktop Sidebar */}
      <aside className="hidden lg:flex fixed left-0 top-0 bottom-0 w-56 border-r border-[#1E1E1E] flex-col z-40">
        <NavContent />
      </aside>

      {/* Mobile Header */}
      <header className="lg:hidden fixed top-0 left-0 right-0 bg-[#050505]/80 backdrop-blur-xl border-b border-[#1E1E1E] z-50">
        <div className="flex items-center justify-between px-4 py-3">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-[#00C896] to-[#3B82F6] flex items-center justify-center">
              <span className="text-black font-bold text-xs">C</span>
            </div>
            <span className="font-display font-semibold text-white text-sm">ClearFile NG</span>
          </div>
          <div className="flex items-center gap-1">
            {/* Notifications */}
            <Popover>
              <PopoverTrigger asChild>
                <button className="relative p-2 rounded-xl hover:bg-white/5 transition-colors" data-testid="notifications-btn">
                  <Bell className="w-[18px] h-[18px] text-[#A1A1AA]" />
                  {unreadCount > 0 && (
                    <span className="absolute top-1 right-1 w-4 h-4 bg-[#00C896] text-black text-[10px] font-bold rounded-full flex items-center justify-center">
                      {unreadCount}
                    </span>
                  )}
                </button>
              </PopoverTrigger>
              <PopoverContent className="w-80 p-0 bg-[#111111] border border-[#1E1E1E] rounded-2xl" align="end">
                <div className="p-3 border-b border-[#1E1E1E] flex items-center justify-between">
                  <h4 className="font-display font-semibold text-white text-sm">Notifications</h4>
                  {unreadCount > 0 && (
                    <button onClick={markAsRead} className="text-xs text-[#00C896] hover:underline" data-testid="mark-all-read-btn">
                      Mark all read
                    </button>
                  )}
                </div>
                <div className="max-h-64 overflow-y-auto">
                  {notifications.length === 0 ? (
                    <p className="p-4 text-center text-[#A1A1AA] text-sm">No notifications</p>
                  ) : (
                    notifications.slice(0, 8).map((notif, idx) => (
                      <div key={notif.id || idx} className={`p-3 border-b border-[#1E1E1E] ${!notif.read ? 'bg-[#00C896]/5' : ''}`}>
                        <div className="flex items-start justify-between">
                          <p className="font-medium text-sm text-white">{notif.title}</p>
                          <span className="text-[10px] text-[#A1A1AA] ml-2">{getTimeAgo(notif.created_at)}</span>
                        </div>
                        <p className="text-xs text-[#A1A1AA] mt-1">{notif.message}</p>
                      </div>
                    ))
                  )}
                </div>
              </PopoverContent>
            </Popover>

            <Sheet open={mobileMenuOpen} onOpenChange={setMobileMenuOpen}>
              <SheetTrigger asChild>
                <button className="p-2 rounded-xl hover:bg-white/5 transition-colors" data-testid="mobile-menu-btn">
                  <Menu className="w-5 h-5 text-[#A1A1AA]" />
                </button>
              </SheetTrigger>
              <SheetContent side="left" className="w-56 p-0 bg-[#0A0A0A] border-[#1E1E1E]">
                <NavContent mobile />
              </SheetContent>
            </Sheet>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="lg:ml-56 pt-14 lg:pt-0 min-h-screen">
        <div className="p-4 lg:p-8 max-w-[1400px] mx-auto">
          {children}
        </div>
      </main>

      {/* Mobile Bottom Nav */}
      <nav className="lg:hidden fixed bottom-0 left-0 right-0 mobile-nav border-t border-[#1E1E1E] z-50">
        <div className="flex justify-around py-2">
          {[navItems[0], navItems[1], navItems[2], navItems[3], navItems[8]].map(item => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex flex-col items-center gap-1 px-3 py-1.5 transition-colors ${
                  isActive ? 'text-[#00C896]' : 'text-[#A1A1AA]'
                }`
              }
              data-testid={`mobile-nav-${item.to.slice(1)}`}
            >
              <item.icon className="w-5 h-5" />
              <span className="text-[10px] font-medium">{item.label.split(' ')[0]}</span>
            </NavLink>
          ))}
        </div>
      </nav>
    </div>
  );
}
