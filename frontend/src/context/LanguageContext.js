import React, { createContext, useContext, useState, useEffect } from 'react';

const LanguageContext = createContext(null);

const translations = {
  en: {
    // Navigation
    welcome: "Welcome to ClearFile NG",
    tagline: "Your trusted partner for Nigerian tax and expense management",
    dashboard: "Dashboard",
    transactions: "Transactions",
    taxCalculator: "Tax Calculator",
    taxGuide: "Tax Guide",
    education: "Learn",
    settings: "Settings",
    chatAssistant: "Tax Assistant",
    
    // Dashboard
    linkBank: "Link Bank",
    addIncome: "Add Income",
    addExpense: "Add Expense",
    scanReceipt: "Scan Receipt",
    viewReport: "View Report",
    totalIncome: "Total Income",
    totalExpenses: "Total Expenses",
    estimatedTax: "Estimated Tax",
    taxHealthScore: "Tax Health Score",
    bankBalance: "Bank Balance",
    spendingBreakdown: "Spending Breakdown",
    flaggedTransactions: "Flagged Transactions",
    upcomingDeadlines: "Upcoming Deadlines",
    quickActions: "Quick Actions",
    welcomeBack: "Welcome back",
    allTime: "All time",
    accountsLinked: "accounts linked",
    incomeTaxVat: "Income Tax + VAT",
    healthExcellent: "Excellent! Your finances are well organized.",
    healthGood: "Good progress! Keep tracking your expenses.",
    healthLow: "Link your bank and track more transactions to improve.",
    noExpenses: "No expenses tracked yet",
    
    // Insights
    smartInsights: "Smart Insights",
    recurringExpenses: "Recurring Expenses",
    monthlyRecurring: "Monthly Recurring",
    frequency: "Frequency",
    occurrences: "occurrences",
    noRecurring: "No recurring expenses detected yet",
    noInsights: "Add transactions to get spending insights",
    viewAll: "View All",
    
    // Transactions page
    addTransaction: "Add Transaction",
    recentTransactions: "Recent Transactions",
    noTransactions: "No transactions yet. Add your first one!",
    confirmDelete: "Delete this transaction?",
    
    // Auth
    securityBadge: "Read-Only Access -- We Cannot Move Your Money",
    login: "Login",
    register: "Register",
    logout: "Logout",
    email: "Email",
    password: "Password",
    name: "Full Name",
    businessType: "Business Type",
    freelancer: "Freelancer / Self-Employed",
    sme: "Small Business (SME)",
    company: "Registered Company (LLC/Ltd)",
    monthlyIncome: "Monthly Income Range",
    getStarted: "Get Started Free",
    startTrial: "Start 7-Day Free Trial",
    noAccount: "Don't have an account?",
    haveAccount: "Already have an account?",
    forgotPassword: "Forgot password?",
    
    // Settings
    plans: "Subscription Plans",
    starter: "Starter",
    growth: "Growth",
    business: "Business",
    perMonth: "/month",
    currentPlan: "Current Plan",
    upgrade: "Upgrade",
    features: "Features",
    profile: "Profile",
    preferences: "Preferences",
    darkMode: "Dark Mode",
    darkModeDesc: "Switch to dark theme",
    pidginMode: "Pidgin Mode",
    pidginModeDesc: "Switch to Pidgin English",
    bankAccounts: "Bank Accounts",
    exportData: "Export Data",
    exportDesc: "Download your financial data as CSV or JSON",
    teamAccess: "Team Access",
    teamDesc: "Invite your accountant or team members to view your data",
    inviteBtn: "Invite",
    removeBtn: "Remove",
    bankSecurity: "Bank-Level Security",
    bankSecurityDesc: "Your data is protected with 256-bit encryption. We only have read-only access to your bank accounts.",
    manageAccount: "Manage your account and preferences",
    subscriptionPlan: "Subscription Plan",
    
    // Tax Calculator
    askQuestion: "Ask me anything about Nigerian taxes...",
    amount: "Amount",
    category: "Category",
    description: "Description",
    date: "Date",
    type: "Type",
    income: "Income",
    expense: "Expense",
    save: "Save",
    cancel: "Cancel",
    delete: "Delete",
    edit: "Edit",
    search: "Search",
    filter: "Filter",
    all: "All",
    thisMonth: "This Month",
    thisYear: "This Year",
    grossIncome: "Gross Income",
    deductibleExpenses: "Deductible Expenses",
    taxableIncome: "Taxable Income",
    incomeTax: "Income Tax",
    vat: "VAT (7.5%)",
    totalTaxOwed: "Total Tax Owed",
    potentialSavings: "Potential Savings",
    disclaimer: "This estimate is for guidance. Consult a certified tax professional for your final filing.",
    
    // Tax Filing
    filingGuide: "Filing Guide",
    checklist: "Filing Checklist",
    documents: "Documents Needed",
    deadlines: "Deadlines",
    firs: "Go to NRS Portal",
    
    // Notifications
    notifications: "Notifications",
    markAllRead: "Mark all read",
    noNotifications: "No notifications",
    enableBrowserNotifications: "Enable browser notifications for deadline reminders",
    
    // Landing page
    heroTitle: "Take Control of Your Nigerian Taxes",
    heroSubtitle: "Track expenses, auto-categorize transactions, and calculate your NTA 2025, and VAT with confidence.",
    featureTracking: "Auto-Tracking",
    featureTrackingDesc: "Link your bank for automatic expense categorization",
    featureTax: "Smart Tax Engine",
    featureTaxDesc: "Calculate NTA 2025, VAT (7.5%) and WHT accurately",
    featureAssistant: "AI Tax Assistant",
    featureAssistantDesc: "Get instant answers to your Nigerian tax questions",
    featureReceipt: "Receipt Scanner",
    featureReceiptDesc: "Snap receipts and auto-create expense entries",
    pricingTitle: "Simple, Transparent Pricing",
    pricingSubtitle: "Choose the plan that works for your business",
  },
  pidgin: {
    // Navigation
    welcome: "Welcome to ClearFile NG",
    tagline: "Your paddy for Nigerian tax and money wahala",
    dashboard: "Dashboard",
    transactions: "Transactions",
    taxCalculator: "Tax Calculator",
    taxGuide: "Tax Guide",
    education: "Learn",
    settings: "Settings",
    chatAssistant: "Tax Helper",
    
    // Dashboard
    linkBank: "Connect Bank",
    addIncome: "Add Money Wey Enter",
    addExpense: "Add Money Wey Comot",
    scanReceipt: "Snap Receipt",
    viewReport: "See Report",
    totalIncome: "Total Money Wey Enter",
    totalExpenses: "Total Money Wey Comot",
    estimatedTax: "Tax Wey You Go Pay",
    taxHealthScore: "How Your Tax Dey",
    bankBalance: "Bank Balance",
    spendingBreakdown: "How You Take Spend Am",
    flaggedTransactions: "Transactions Wey Need Attention",
    upcomingDeadlines: "Deadlines Wey Dey Come",
    quickActions: "Quick Actions",
    welcomeBack: "Welcome back",
    allTime: "All time",
    accountsLinked: "accounts wey dey linked",
    incomeTaxVat: "Income Tax + VAT",
    healthExcellent: "Sharp sharp! Your money dey well organized.",
    healthGood: "You dey try! Continue to track your expenses.",
    healthLow: "Connect your bank and track more transactions make things better.",
    noExpenses: "You never track any expenses yet",
    
    // Insights
    smartInsights: "Smart Tips",
    recurringExpenses: "Expenses Wey Dey Repeat",
    monthlyRecurring: "Monthly Recurring",
    frequency: "How Often",
    occurrences: "times",
    noRecurring: "We never see any expenses wey dey repeat yet",
    noInsights: "Add transactions make we give you spending tips",
    viewAll: "See All",
    
    // Transactions page
    addTransaction: "Add Transaction",
    recentTransactions: "Recent Transactions",
    noTransactions: "You no get any transaction yet. Add your first one!",
    confirmDelete: "You wan delete this transaction?",
    
    // Auth
    securityBadge: "We No Fit Touch Your Money -- Na Read-Only",
    login: "Enter",
    register: "Create Account",
    logout: "Comot",
    email: "Email",
    password: "Password",
    name: "Your Name",
    businessType: "Your Business Type",
    freelancer: "Freelancer / Self-Employed",
    sme: "Small Business (SME)",
    company: "Registered Company (LLC/Ltd)",
    monthlyIncome: "How Much You Dey Make Per Month",
    getStarted: "Start Free",
    startTrial: "Try Am Free for 7 Days",
    noAccount: "You no get account?",
    haveAccount: "You don get account?",
    forgotPassword: "You forget password?",
    
    // Settings
    plans: "Plans",
    starter: "Starter",
    growth: "Growth",
    business: "Business",
    perMonth: "/month",
    currentPlan: "Your Plan",
    upgrade: "Upgrade",
    features: "Wetin You Go Get",
    profile: "Profile",
    preferences: "Preferences",
    darkMode: "Dark Mode",
    darkModeDesc: "Change to dark theme",
    pidginMode: "Pidgin Mode",
    pidginModeDesc: "Change to Pidgin English",
    bankAccounts: "Bank Accounts",
    exportData: "Export Data",
    exportDesc: "Download your money data as CSV or JSON",
    teamAccess: "Team Access",
    teamDesc: "Invite your accountant or team members to see your data",
    inviteBtn: "Invite",
    removeBtn: "Remove",
    bankSecurity: "Bank-Level Security",
    bankSecurityDesc: "Your data dey protected with strong encryption. We only fit read your bank account, we no fit touch your money.",
    manageAccount: "Manage your account and settings",
    subscriptionPlan: "Subscription Plan",
    
    // Tax Calculator
    askQuestion: "Ask me anything about Nigerian tax...",
    amount: "Amount",
    category: "Category",
    description: "Description",
    date: "Date",
    type: "Type",
    income: "Money In",
    expense: "Money Out",
    save: "Save",
    cancel: "Cancel",
    delete: "Delete",
    edit: "Edit",
    search: "Search",
    filter: "Filter",
    all: "All",
    thisMonth: "This Month",
    thisYear: "This Year",
    grossIncome: "Total Money In",
    deductibleExpenses: "Expenses Wey Fit Reduce Tax",
    taxableIncome: "Money Wey Tax Go Touch",
    incomeTax: "Income Tax",
    vat: "VAT (7.5%)",
    totalTaxOwed: "Total Tax to Pay",
    potentialSavings: "Money You Fit Save",
    disclaimer: "This one na estimate o. Talk to tax person before you file.",
    
    // Tax Filing
    filingGuide: "How to File",
    checklist: "Filing Checklist",
    documents: "Papers Wey You Need",
    deadlines: "Deadlines",
    firs: "Go NRS Website",
    
    // Notifications
    notifications: "Notifications",
    markAllRead: "Mark all as read",
    noNotifications: "No notifications",
    enableBrowserNotifications: "Turn on browser notifications for deadline reminders",
    
    // Landing page
    heroTitle: "Take Control of Your Nigerian Taxes",
    heroSubtitle: "Track spending, auto-sort transactions, calculate NTA 2025, and VAT with peace of mind.",
    featureTracking: "Auto-Tracking",
    featureTrackingDesc: "Connect your bank, we go sort your expenses automatically",
    featureTax: "Smart Tax Engine",
    featureTaxDesc: "Calculate NTA 2025, VAT (7.5%) and WHT sharp sharp",
    featureAssistant: "AI Tax Helper",
    featureAssistantDesc: "Ask any Nigerian tax question, get answer one time",
    featureReceipt: "Receipt Scanner",
    featureReceiptDesc: "Snap receipt, we go create expense entry for you",
    pricingTitle: "Simple Pricing, No Wahala",
    pricingSubtitle: "Pick the plan wey work for your business",
  }
};

export function LanguageProvider({ children }) {
  const [language, setLanguage] = useState('en');

  useEffect(() => {
    const saved = localStorage.getItem('clearfileng_language');
    if (saved) setLanguage(saved);
  }, []);

  const toggleLanguage = () => {
    const newLang = language === 'en' ? 'pidgin' : 'en';
    setLanguage(newLang);
    localStorage.setItem('clearfileng_language', newLang);
  };

  const t = (key) => translations[language][key] || translations['en'][key] || key;

  return (
    <LanguageContext.Provider value={{ language, toggleLanguage, t }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  const context = useContext(LanguageContext);
  if (!context) throw new Error('useLanguage must be used within LanguageProvider');
  return context;
}
