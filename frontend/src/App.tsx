import React, { useState } from 'react';
import { BrowserRouter, Routes, Route, Link, useLocation, Navigate } from 'react-router-dom';
import { LayoutDashboard, MessageSquare, FileText, CreditCard, LogOut } from 'lucide-react';
import Dashboard from './pages/Dashboard';
import Chat from './pages/Chat';
import Login from './pages/Login';
import { AuthProvider, useAuth } from './contexts/AuthContext';

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
    formData.append('issuing_bank', 'Chase'); // default for prototype
    
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
      <h2 className="text-3xl font-bold mb-6 text-white">Upload Statement</h2>
      <div className="bg-slate-800 rounded-xl p-8 border border-slate-700/50 shadow-xl backdrop-blur-sm max-w-xl">
        <form onSubmit={handleUpload} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-2">Statement PDF</label>
            <input 
              type="file" 
              accept=".pdf"
              onChange={e => setFile(e.target.files?.[0] || null)}
              className="block w-full text-slate-400 file:mr-4 file:py-2.5 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-indigo-500/10 file:text-indigo-400 hover:file:bg-indigo-500/20 transition-colors"
            />
          </div>
          <button 
            type="submit" 
            disabled={!file || loading}
            className="w-full bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-medium py-3 rounded-xl transition-all shadow-lg"
          >
            {loading ? 'Uploading...' : 'Upload & Analyze'}
          </button>
          
          {message && (
            <div className={`p-4 rounded-lg text-sm ${message.startsWith('Error') ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20' : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'}`}>
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
  const isActive = location.pathname === to || (to === '/dashboard' && location.pathname === '/');
  
  return (
    <li>
      <Link 
        to={to} 
        className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 ${
          isActive 
            ? 'bg-indigo-500/10 text-indigo-400 font-medium border border-indigo-500/20 shadow-[0_0_15px_rgba(99,102,241,0.1)]' 
            : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
        }`}
      >
        <Icon size={20} className={isActive ? 'text-indigo-400' : 'text-slate-500'} />
        {children}
      </Link>
    </li>
  );
}

function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-slate-950 flex font-sans selection:bg-indigo-500/30 text-slate-200">
      {/* Sidebar */}
      <nav className="w-72 bg-slate-900 border-r border-slate-800 p-6 flex flex-col relative overflow-hidden">
        {/* Glow effect */}
        <div className="absolute top-0 -left-4 w-72 h-72 bg-indigo-500 opacity-5 rounded-full blur-[100px] pointer-events-none"></div>
        
        <div className="flex items-center gap-3 mb-10 z-10">
          <div className="p-2 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg shadow-lg shadow-indigo-500/20">
            <CreditCard size={24} className="text-white" />
          </div>
          <h1 className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-white to-slate-400 tracking-tight">DepositGuide</h1>
        </div>
        
        <ul className="space-y-2 flex-1 z-10">
          <NavItem to="/dashboard" icon={LayoutDashboard}>Dashboard</NavItem>
          <NavItem to="/statements" icon={FileText}>Statements</NavItem>
          <NavItem to="/chat" icon={MessageSquare}>AI Advisor</NavItem>
        </ul>
        
        <div className="mt-auto z-10">
          <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700/50 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-gradient-to-r from-indigo-500 to-purple-600 flex items-center justify-center text-white font-bold shadow-inner">
                <CreditCard size={18} />
              </div>
              <div>
                <p className="text-sm font-medium text-slate-200">User Account</p>
                <p className="text-xs text-slate-500">Premium Member</p>
              </div>
            </div>
            <LogoutButton />
          </div>
        </div>
      </nav>
      
      {/* Main Content */}
      <main className="flex-1 relative overflow-y-auto">
        <div className="absolute top-0 right-0 w-96 h-96 bg-indigo-500 opacity-[0.03] rounded-full blur-[120px] pointer-events-none"></div>
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
      className="text-slate-400 hover:text-rose-400 p-2 rounded-lg hover:bg-slate-700/50 transition-colors"
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
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          
          <Route path="/" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
          <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
          <Route path="/statements" element={<ProtectedRoute><Statements /></ProtectedRoute>} />
          <Route path="/chat" element={<ProtectedRoute><Chat /></ProtectedRoute>} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
