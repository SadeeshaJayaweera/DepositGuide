import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, MessageSquare, FileText, CreditCard } from 'lucide-react';
import Dashboard from './pages/Dashboard';
import Chat from './pages/Chat';

function Statements() {
  return (
    <div className="p-8">
      <h2 className="text-3xl font-bold mb-6 text-white">Statements</h2>
      <div className="bg-slate-800 rounded-xl p-8 border border-slate-700/50 shadow-xl backdrop-blur-sm">
        <p className="text-slate-300">Your uploaded statements will appear here. Backend processing is currently driving the main dashboard.</p>
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
          <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700/50">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-gradient-to-r from-indigo-500 to-purple-600 flex items-center justify-center text-white font-bold shadow-inner">
                JD
              </div>
              <div>
                <p className="text-sm font-medium text-slate-200">John Doe</p>
                <p className="text-xs text-slate-500">Premium Member</p>
              </div>
            </div>
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

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/statements" element={<Statements />} />
          <Route path="/chat" element={<Chat />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}

export default App;
