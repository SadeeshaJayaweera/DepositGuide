import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';
import { CreditCard, Mail, Lock, ArrowRight, Sun, Moon } from 'lucide-react';
import { GoogleLogin } from '@react-oauth/google';

export default function Login() {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  
  const { login } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
      
      let res;
      if (isLogin) {
        const formData = new URLSearchParams();
        formData.append('username', email);
        formData.append('password', password);
        
        res = await fetch(`${API_BASE}/auth/login`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          body: formData
        });
      } else {
        res = await fetch(`${API_BASE}/auth/register`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password })
        });
      }

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Authentication failed');
      }

      const data = await res.json();
      login(data.access_token);
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSuccess = async (credentialResponse: any) => {
    setError('');
    setLoading(true);
    try {
      const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
      const res = await fetch(`${API_BASE}/auth/google`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token: credentialResponse.credential })
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Google Authentication failed');
      }

      const data = await res.json();
      login(data.access_token);
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleError = () => {
    setError('Google Sign-In was unsuccessful. Please try again.');
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex flex-col justify-center items-center font-sans selection:bg-indigo-500/30 text-slate-900 dark:text-slate-200 relative overflow-hidden p-4 transition-colors duration-300">
      
      {/* Theme Toggle */}
      <button 
        onClick={toggleTheme} 
        className="absolute top-6 right-6 text-slate-400 hover:text-slate-900 dark:hover:text-white transition-colors p-2 hover:bg-slate-200 dark:hover:bg-slate-800 rounded-full z-50"
      >
        {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
      </button>

      {/* Background Glows */}
      <div className="absolute top-1/4 -left-64 w-96 h-96 bg-indigo-500/10 dark:bg-indigo-500/20 rounded-full blur-[120px] pointer-events-none"></div>
      <div className="absolute bottom-1/4 -right-64 w-96 h-96 bg-purple-500/10 dark:bg-purple-500/20 rounded-full blur-[120px] pointer-events-none"></div>

      <div className="w-full max-w-md z-10">
        <div className="flex flex-col items-center mb-8">
          <div className="p-3 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-2xl shadow-xl shadow-indigo-500/20 mb-5">
            <CreditCard size={32} className="text-white" />
          </div>
          <h1 className="text-3xl font-extrabold text-slate-900 dark:text-transparent dark:bg-clip-text dark:bg-gradient-to-r dark:from-white dark:to-slate-400 tracking-tight transition-colors">
            DepositGuide
          </h1>
          <p className="text-slate-500 dark:text-slate-400 mt-2 text-center font-medium transition-colors">Smart credit card debt optimization.</p>
        </div>

        <div className="bg-white/80 dark:bg-slate-900/60 backdrop-blur-xl border border-slate-200 dark:border-slate-700/50 rounded-3xl p-8 shadow-2xl shadow-slate-200/50 dark:shadow-none transition-colors duration-300">
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-6 transition-colors">
            {isLogin ? 'Welcome back' : 'Create your account'}
          </h2>

          {error && (
            <div className="bg-rose-50 dark:bg-rose-500/10 border border-rose-200 dark:border-rose-500/20 text-rose-600 dark:text-rose-400 px-4 py-3 rounded-xl mb-6 text-sm font-medium transition-colors">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-semibold text-slate-700 dark:text-slate-400 mb-1.5 transition-colors">Email</label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <Mail size={18} className="text-slate-400 dark:text-slate-500" />
                </div>
                <input 
                  type="email" 
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full bg-slate-50 dark:bg-slate-950/50 border border-slate-200 dark:border-slate-700 rounded-xl pl-11 pr-4 py-3 text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition-all shadow-sm"
                  placeholder="you@example.com"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-semibold text-slate-700 dark:text-slate-400 mb-1.5 transition-colors">Password</label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <Lock size={18} className="text-slate-400 dark:text-slate-500" />
                </div>
                <input 
                  type="password" 
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full bg-slate-50 dark:bg-slate-950/50 border border-slate-200 dark:border-slate-700 rounded-xl pl-11 pr-4 py-3 text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition-all shadow-sm"
                  placeholder="••••••••"
                  required
                />
              </div>
            </div>

            <button 
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white font-medium py-3.5 px-4 rounded-xl shadow-lg shadow-indigo-500/25 transition-all disabled:opacity-50 mt-2"
            >
              {loading ? 'Processing...' : (isLogin ? 'Sign In' : 'Create Account')}
              {!loading && <ArrowRight size={18} />}
            </button>
          </form>

          <div className="mt-8 flex items-center justify-center space-x-4">
            <div className="h-px bg-slate-200 dark:bg-slate-700 flex-1 transition-colors"></div>
            <span className="text-slate-400 dark:text-slate-500 text-sm font-medium transition-colors">or continue with</span>
            <div className="h-px bg-slate-200 dark:bg-slate-700 flex-1 transition-colors"></div>
          </div>

          <div className="mt-6 flex justify-center">
            <GoogleLogin
              onSuccess={handleGoogleSuccess}
              onError={handleGoogleError}
              theme={theme === 'dark' ? 'filled_black' : 'outline'}
              shape="rectangular"
              size="large"
              width="300"
            />
          </div>
        </div>

        <div className="mt-8 text-center">
          <p className="text-slate-600 dark:text-slate-400 transition-colors">
            {isLogin ? "Don't have an account? " : "Already have an account? "}
            <button 
              onClick={() => { setIsLogin(!isLogin); setError(''); }}
              className="text-indigo-600 dark:text-indigo-400 hover:text-indigo-500 dark:hover:text-indigo-300 font-semibold transition-colors"
            >
              {isLogin ? 'Sign up' : 'Log in'}
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}
