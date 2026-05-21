import React, { useState, useEffect, useCallback } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { 
  LayoutDashboard, Receipt, Calculator, FileText, BookOpen, 
  Settings, MessageCircle, LogOut, Menu, Shield, Bell, BellRing,
  Award, TrendingUp, Landmark, ShieldCheck
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
  const [browserNotifEnabled, setBrowserNotifEnabled] = useState(false);

  useEffect(() => {
    fetchNotifications();
    checkDeadlines();
    // Check browser notification permission
    if ('Notification' in window) {
      setBrowserNotifEnabled(Notification.permission === 'granted');
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const fetchNotifications = async () => {
    try {
      const { data } = await axios.get(`${API}/api/notifications`, { withCredentials: true });
      setNotifications(data);
      const unread = data.filter(n => !n.read).length;
      setUnreadCount(unread);

      // Show browser notification for new unread items
      if (unread > 0 && browserNotifEnabled && data.length > 0) {
        const latest = data.find(n => !n.read);
        if (latest) {
          showBrowserNotification(latest.title, latest.message);
        }
      }
    } catch (error) {
      console.error('Failed to fetch notifications');
    }
  };

  const checkDeadlines = async () => {
    try {
      await axios.post(`${API}/api/notifications/check-deadlines`, {}, { withCredentials: true });
      fetchNotifications();
    } catch (error) {
      console.error('Failed to check deadlines');
    }
  };

  const markAsRead = async () => {
    try {
      await axios.post(`${API}/api/notifications/mark-read`, {}, { withCredentials: true });
      setUnreadCount(0);
      setNotifications(prev => prev.map(n => ({ ...n, read: true })));
    } catch (error) {
      console.error('Failed to mark as read');
    }
  };

  const enableBrowserNotifications = useCallback(async () => {
    if (!('Notification' in window)) {
      toast.error('Browser notifications not supported');
      return;
    }
    try {
      const permission = await Notification.requestPermission();
      if (permission === 'granted') {
        setBrowserNotifEnabled(true);
        toast.success('Browser notifications enabled!');
      } else {
        toast.info('Notification permission denied');
      }
    } catch (err) {
      toast.error('Failed to enable notifications');
    }
  }, []);

  const showBrowserNotification = (title, body) => {
    if (browserNotifEnabled && 'Notification' in window && Notification.permission === 'granted') {
      try {
        new Notification(title, {
          body,
          icon: '/favicon.ico',
          badge: '/favicon.ico',
          tag: 'clearfileng-notification'
        });
      } catch (e) {
        // Silently fail for environments that don't support Notification constructor
      }
    }
  };

  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

  const getTimeAgo = (dateStr) => {
    if (!dateStr) return '';
    const diff = Date.now() - new Date(dateStr).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 60) return `${mins}m ago`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}h ago`;
    return `${Math.floor(hours / 24)}d ago`;
  };

  const navItems = [
    { to: '/dashboard', icon: LayoutDashboard, label: t('dashboard') },
    { to: '/transactions', icon: Receipt, label: t('transactions') },
    { to: '/tax-calculator', icon: Calculator, label: t('taxCalculator') },
    { to: '/tax-obligations', icon: Landmark, label: 'Tax Routing' },
    { to: '/tax-planner', icon: TrendingUp, label: 'Tax Planner' },
    { to: '/tcc', icon: Award, label: 'TCC Tracker' },
    { to: '/tax-guide', icon: FileText, label: t('taxGuide') },
    { to: '/education', icon: BookOpen, label: t('education') },
    { to: '/chat', icon: MessageCircle, label: t('chatAssistant') },
    { to: '/settings', icon: Settings, label: t('settings') },
  ];

  // Add admin link for admin users
  if (user?.role === 'admin') {
    navItems.push({ to: '/admin', icon: ShieldCheck, label: 'Admin Panel' });
  }

  const NavContent = ({ mobile = false }) => (
    <div className={`flex flex-col h-full`}>
      <div className="p-4 border-b border-slate-200">
        <div className="flex items-center gap-2">
          <div className="w-10 h-10 bg-[#006400] rounded-xl flex items-center justify-center">
            <span className="text-white font-bold text-lg">₦</span>
          </div>
          <span className="text-xl font-bold text-[#022c22]" style={{ fontFamily: 'Outfit' }}>ClearFile NG</span>
        </div>
      </div>

      <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
        {navItems.map(item => (
          <NavLink
            key={item.to}
            to={item.to}
            onClick={() => mobile && setMobileMenuOpen(false)}
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
                isActive
                  ? 'bg-[#006400] text-white'
                  : 'text-slate-600 hover:bg-[#E8F5E9] hover:text-[#006400]'
              }`
            }
            data-testid={`nav-${item.to.slice(1)}`}
          >
            <item.icon className="w-5 h-5" />
            <span className="font-medium">{item.label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="p-4 border-t border-slate-200 space-y-4">
        <div className="flex items-center justify-between px-4 py-2">
          <span className="text-sm text-slate-600">Pidgin / EN</span>
          <Switch
            checked={language === 'pidgin'}
            onCheckedChange={toggleLanguage}
            data-testid="pidgin-toggle"
          />
        </div>

        <div className="bg-[#E8F5E9] rounded-xl p-3">
          <p className="font-medium text-[#022c22] truncate">{user?.name}</p>
          <p className="text-xs text-slate-500 truncate">{user?.email}</p>
          <p className="text-xs text-[#006400] font-medium mt-1 capitalize">{user?.subscription_plan} Plan</p>
        </div>

        <Button
          variant="ghost"
          onClick={handleLogout}
          className="w-full justify-start text-slate-600 hover:text-red-600 hover:bg-red-50"
          data-testid="logout-btn"
        >
          <LogOut className="w-5 h-5 mr-3" />
          {t('logout')}
        </Button>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-[#FAFAFA]">
      <aside className="hidden lg:flex fixed left-0 top-0 bottom-0 w-64 bg-white border-r border-slate-200 flex-col z-40">
        <NavContent />
      </aside>

      <header className="lg:hidden fixed top-0 left-0 right-0 bg-white/80 backdrop-blur-xl border-b border-slate-200 z-50">
        <div className="flex items-center justify-between px-4 py-3">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-[#006400] rounded-lg flex items-center justify-center">
              <span className="text-white font-bold">₦</span>
            </div>
            <span className="font-bold text-[#022c22]" style={{ fontFamily: 'Outfit' }}>ClearFile NG</span>
          </div>
          <div className="flex items-center gap-2">
            <Popover>
              <PopoverTrigger asChild>
                <Button variant="ghost" size="icon" className="relative" data-testid="notifications-btn">
                  <Bell className="w-5 h-5" />
                  {unreadCount > 0 && (
                    <Badge className="absolute -top-1 -right-1 h-5 w-5 flex items-center justify-center p-0 bg-red-500 text-white text-xs">
                      {unreadCount}
                    </Badge>
                  )}
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-80 p-0" align="end">
                <div className="p-3 border-b border-slate-200 flex items-center justify-between">
                  <h4 className="font-semibold text-[#022c22]">{t('notifications')}</h4>
                  <div className="flex items-center gap-2">
                    {!browserNotifEnabled && (
                      <Button variant="ghost" size="sm" onClick={enableBrowserNotifications} className="text-xs" data-testid="enable-browser-notif">
                        <BellRing className="w-3 h-3 mr-1" />
                        Enable
                      </Button>
                    )}
                    {unreadCount > 0 && (
                      <Button variant="ghost" size="sm" onClick={markAsRead} className="text-xs" data-testid="mark-all-read-btn">
                        {t('markAllRead')}
                      </Button>
                    )}
                  </div>
                </div>
                <div className="max-h-64 overflow-y-auto">
                  {notifications.length === 0 ? (
                    <p className="p-4 text-center text-slate-400 text-sm">{t('noNotifications')}</p>
                  ) : (
                    notifications.slice(0, 8).map((notif, idx) => (
                      <div key={notif.id || idx} className={`p-3 border-b border-slate-100 ${!notif.read ? 'bg-[#E8F5E9]' : ''}`}>
                        <div className="flex items-start justify-between">
                          <p className="font-medium text-sm text-[#022c22]">{notif.title}</p>
                          <span className="text-[10px] text-slate-400 whitespace-nowrap ml-2">{getTimeAgo(notif.created_at)}</span>
                        </div>
                        <p className="text-xs text-slate-500 mt-1">{notif.message}</p>
                      </div>
                    ))
                  )}
                </div>
              </PopoverContent>
            </Popover>
            <Sheet open={mobileMenuOpen} onOpenChange={setMobileMenuOpen}>
              <SheetTrigger asChild>
                <Button variant="ghost" size="icon" data-testid="mobile-menu-btn">
                  <Menu className="w-6 h-6" />
                </Button>
              </SheetTrigger>
              <SheetContent side="left" className="w-72 p-0">
                <NavContent mobile />
              </SheetContent>
            </Sheet>
          </div>
        </div>
      </header>

      <div className="lg:ml-64 bg-[#006400] text-white text-center py-2 text-sm lg:text-base">
        <div className="flex items-center justify-center gap-2">
          <Shield className="w-4 h-4 text-[#FFD700]" />
          <span>{t('securityBadge')}</span>
        </div>
      </div>

      <main className="lg:ml-64 pt-16 lg:pt-0 min-h-screen">
        <div className="p-4 lg:p-8">
          {children}
        </div>
      </main>

      <nav className="lg:hidden fixed bottom-0 left-0 right-0 bg-white/90 backdrop-blur-xl border-t border-slate-200 z-50 mobile-nav">
        <div className="flex justify-around py-2">
          {[navItems[0], navItems[1], navItems[2], navItems[5], navItems[9]].map(item => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex flex-col items-center gap-1 px-3 py-2 ${
                  isActive ? 'text-[#006400]' : 'text-slate-400'
                }`
              }
              data-testid={`mobile-nav-${item.to.slice(1)}`}
            >
              <item.icon className="w-5 h-5" />
              <span className="text-xs">{item.label.split(' ')[0]}</span>
            </NavLink>
          ))}
        </div>
      </nav>
    </div>
  );
}
