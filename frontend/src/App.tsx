import React, { useState } from 'react';
import { BrowserRouter, Routes, Route, Link, useLocation, Navigate } from 'react-router-dom';
import { LayoutDashboard, MessageSquare, FileText, CreditCard, LogOut, Sun, Moon } from 'lucide-react';
import Dashboard from './pages/Dashboard';
import Chat from './pages/Chat';
import Login from './pages/Login';
import Landing from './pages/Landing';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { ThemeProvider, useTheme } from './contexts/ThemeContext';

function Statements() {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const { token } = useAuth();
  
  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file || !token) return;
    
    setLoading(true);
    setMessage('');
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('issuing_bank', 'Chase');
    
    try {
      const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
      const res = await fetch(`${API_BASE}/statements/upload`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });
      
      if (!res.ok) throw new Error('Upload failed');
      
      setMessage('Statement uploaded successfully! Go to Dashboard to see insights.');
      setFile(null);
    } catch (err: any) {
      setMessage(`Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8">
      <h2 className="text-3xl font-bold mb-6 text-slate-900 dark:text-white">Upload Statement</h2>
      <div className="bg-white dark:bg-slate-900 rounded-3xl p-8 border border-slate-200 dark:border-slate-800 shadow-xl shadow-slate-200/50 dark:shadow-none max-w-xl">
        <form onSubmit={handleUpload} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">Statement PDF</label>
            <input 
              type="file" 
              accept=".pdf"
              onChange={e => setFile(e.target.files?.[0] || null)}
              className="block w-full text-slate-600 dark:text-slate-400 file:mr-4 file:py-2.5 file:px-5 file:rounded-xl file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 dark:file:bg-indigo-500/10 file:text-indigo-600 dark:file:text-indigo-400 hover:file:bg-indigo-100 dark:hover:file:bg-indigo-500/20 transition-colors"
            />
          </div>
          <button 
            type="submit" 
            disabled={!file || loading}
            className="w-full bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-medium py-3.5 rounded-xl transition-all shadow-lg shadow-indigo-500/25"
          >
            {loading ? 'Uploading...' : 'Upload & Analyze'}
          </button>
          
          {message && (
            <div className={`p-4 rounded-xl text-sm font-medium ${message.startsWith('Error') ? 'bg-rose-50 dark:bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-200 dark:border-rose-500/20' : 'bg-emerald-50 dark:bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-500/20'}`}>
              {message}
            </div>
          )}
        </form>
      </div>
    </div>
  );
}

function NavItem({ to, icon: Icon, children }: { to: string, icon: any, children: React.ReactNode }) {
  const location = useLocation();
  const isActive = location.pathname === to;
  
  return (
    <li>
      <Link 
        to={to} 
        className={`flex items-center gap-3 px-4 py-3.5 rounded-xl transition-all duration-200 ${
          isActive 
            ? 'bg-indigo-50 dark:bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 font-semibold shadow-sm' 
            : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-slate-200'
        }`}
      >
        <Icon size={20} className={isActive ? 'text-indigo-600 dark:text-indigo-400' : 'text-slate-400'} />
        {children}
      </Link>
    </li>
  );
}

function Layout({ children }: { children: React.ReactNode }) {
  const { theme, toggleTheme } = useTheme();

  return (
    <div className="flex h-screen bg-slate-50 dark:bg-slate-950 transition-colors duration-300 font-sans selection:bg-indigo-500/30 text-slate-900 dark:text-slate-200">
      {/* Sidebar */}
      <nav className="w-72 bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 p-6 flex flex-col relative transition-colors duration-300 z-10">
        
        <div className="flex items-center justify-between mb-10">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl shadow-lg shadow-indigo-500/20">
              <CreditCard size={24} className="text-white" />
            </div>
            <h1 className="text-xl font-bold text-slate-900 dark:text-white tracking-tight">DepositGuide</h1>
          </div>
          <button onClick={toggleTheme} className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 transition-colors p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-full">
            {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
          </button>
        </div>
        
        <ul className="space-y-2 flex-1">
          <NavItem to="/dashboard" icon={LayoutDashboard}>Dashboard</NavItem>
          <NavItem to="/statements" icon={FileText}>Statements</NavItem>
          <NavItem to="/chat" icon={MessageSquare}>AI Advisor</NavItem>
        </ul>
        
        <div className="mt-auto">
          <div className="bg-slate-50 dark:bg-slate-800/50 rounded-2xl p-4 border border-slate-100 dark:border-slate-700/50 flex items-center justify-between transition-colors">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-gradient-to-r from-indigo-500 to-purple-600 flex items-center justify-center text-white font-bold shadow-sm">
                <CreditCard size={18} />
              </div>
              <div>
                <p className="text-sm font-semibold text-slate-900 dark:text-slate-200">User Account</p>
                <p className="text-xs text-slate-500">Premium Member</p>
              </div>
            </div>
            <LogoutButton />
          </div>
        </div>
      </nav>
      
      {/* Main Content */}
      <main className="flex-1 relative overflow-y-auto w-full">
        <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-indigo-500 opacity-5 dark:opacity-[0.03] rounded-full blur-[120px] pointer-events-none"></div>
        {children}
      </main>
    </div>
  );
}

function LogoutButton() {
  const { logout } = useAuth();
  return (
    <button 
      onClick={logout}
      className="text-slate-400 hover:text-rose-500 dark:hover:text-rose-400 p-2 rounded-xl hover:bg-rose-50 dark:hover:bg-slate-800 transition-colors"
      title="Log out"
    >
      <LogOut size={18} />
    </button>
  );
}

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth();
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return <Layout>{children}</Layout>;
}

function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Landing />} />
            <Route path="/login" element={<Login />} />
            
            <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
            <Route path="/statements" element={<ProtectedRoute><Statements /></ProtectedRoute>} />
            <Route path="/chat" element={<ProtectedRoute><Chat /></ProtectedRoute>} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
