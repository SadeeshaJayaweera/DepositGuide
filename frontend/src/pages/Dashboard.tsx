import { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { TrendingDown, AlertCircle, Calendar, CreditCard, Loader2, FileText, UploadCloud } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';

interface DashboardData {
  statement_summary: {
    balance: number;
    due_date: string;
    minimum_payment: number;
  };
  explanations: Array<{
    line_item_name: string;
    plain_language_explanation: string;
  }>;
  recommendation: {
    schedule: Record<string, number>;
    projected_interest: number;
    baseline_interest: number;
    savings_summary: string;
  } | null;
  low_value_subscriptions: Array<{
    name: string;
    amount: number;
    reason: string;
  }>;
}

export default function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const { token } = useAuth();
  const { theme } = useTheme();

  useEffect(() => {
    if (!token) return;
    const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
    fetch(`${API_BASE}/dashboard`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
      .then(res => {
        if (res.status === 404) {
          throw new Error('empty_state');
        }
        if (!res.ok) throw new Error('Failed to load dashboard data');
        return res.json();
      })
      .then(json => {
        setData(json);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });
  }, [token]);

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="flex flex-col items-center gap-4 text-indigo-500 dark:text-indigo-400">
          <Loader2 className="animate-spin" size={48} />
          <p className="text-lg font-medium animate-pulse">Analyzing your finances...</p>
        </div>
      </div>
    );
  }

  if (error === 'empty_state') {
    return (
      <div className="flex h-full items-center justify-center p-8">
        <div className="bg-white dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/50 backdrop-blur-xl p-10 rounded-3xl max-w-lg text-center shadow-2xl relative overflow-hidden transition-colors duration-300">
          <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-500/5 dark:bg-indigo-500/10 rounded-full blur-[80px] pointer-events-none"></div>
          <div className="p-4 bg-indigo-50 dark:bg-slate-900/80 inline-block rounded-2xl mb-6 shadow-inner transition-colors">
            <UploadCloud size={48} className="text-indigo-500 dark:text-indigo-400" />
          </div>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-4 transition-colors">Welcome to DepositGuide</h2>
          <p className="text-slate-600 dark:text-slate-400 mb-8 leading-relaxed transition-colors">
            Upload your first credit card statement to generate AI-powered insights, profile your financial behavior, and discover the smartest deposit schedule.
          </p>
          <a href="/statements" className="inline-flex items-center gap-2 bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-400 hover:to-purple-500 text-white font-medium py-3 px-6 rounded-xl shadow-lg shadow-indigo-500/25 transition-all">
            Upload Statement
          </a>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/20 text-red-600 dark:text-red-400 p-8 rounded-2xl max-w-md text-center">
          <AlertCircle size={48} className="mx-auto mb-4 opacity-80" />
          <h2 className="text-xl font-bold mb-2">Failed to load insights</h2>
          <p className="opacity-80">{error || "Unknown error occurred"}</p>
        </div>
      </div>
    );
  }

  const { statement_summary, explanations, recommendation, low_value_subscriptions } = data;

  const chartData = recommendation ? [
    { name: 'Baseline', value: recommendation.baseline_interest, color: '#ef4444' },
    { name: 'Recommended', value: recommendation.projected_interest, color: '#10b981' }
  ] : [];

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      <header className="mb-10">
        <h1 className="text-4xl font-bold text-slate-900 dark:text-white mb-2 tracking-tight transition-colors">Your Financial Overview</h1>
        <p className="text-slate-600 dark:text-slate-400 text-lg transition-colors">AI-powered insights for your latest statement.</p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left Column */}
        <div className="lg:col-span-2 space-y-8">
          
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-white dark:bg-slate-800/80 rounded-3xl p-6 border border-slate-200 dark:border-slate-700/50 shadow-xl shadow-slate-200/50 dark:shadow-lg backdrop-blur-xl relative overflow-hidden group transition-colors">
              <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/5 dark:from-indigo-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
              <div className="flex items-center gap-4 mb-4 text-slate-500 dark:text-slate-400">
                <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-900/80 shadow-inner">
                  <CreditCard size={20} className="text-indigo-500 dark:text-indigo-400" />
                </div>
                <h3 className="font-semibold tracking-wide uppercase text-sm">Statement Balance</h3>
              </div>
              <p className="text-3xl font-bold text-slate-900 dark:text-white transition-colors">LKR {statement_summary.balance.toLocaleString(undefined, {minimumFractionDigits: 2})}</p>
            </div>

            <div className="bg-white dark:bg-slate-800/80 rounded-3xl p-6 border border-slate-200 dark:border-slate-700/50 shadow-xl shadow-slate-200/50 dark:shadow-lg backdrop-blur-xl relative overflow-hidden group transition-colors">
              <div className="absolute inset-0 bg-gradient-to-br from-orange-500/5 dark:from-orange-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
              <div className="flex items-center gap-4 mb-4 text-slate-500 dark:text-slate-400">
                <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-900/80 shadow-inner">
                  <Calendar size={20} className="text-orange-500 dark:text-orange-400" />
                </div>
                <h3 className="font-semibold tracking-wide uppercase text-sm">Due Date</h3>
              </div>
              <p className="text-3xl font-bold text-slate-900 dark:text-white transition-colors">{new Date(statement_summary.due_date).toLocaleDateString()}</p>
            </div>

            <div className="bg-white dark:bg-slate-800/80 rounded-3xl p-6 border border-slate-200 dark:border-slate-700/50 shadow-xl shadow-slate-200/50 dark:shadow-lg backdrop-blur-xl relative overflow-hidden group transition-colors">
              <div className="absolute inset-0 bg-gradient-to-br from-rose-500/5 dark:from-rose-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
              <div className="flex items-center gap-4 mb-4 text-slate-500 dark:text-slate-400">
                <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-900/80 shadow-inner">
                  <AlertCircle size={20} className="text-rose-500 dark:text-rose-400" />
                </div>
                <h3 className="font-semibold tracking-wide uppercase text-sm">Min Payment</h3>
              </div>
              <p className="text-3xl font-bold text-rose-500 dark:text-rose-300">LKR {statement_summary.minimum_payment.toLocaleString(undefined, {minimumFractionDigits: 2})}</p>
            </div>
          </div>

          {/* Deposit Recommendation */}
          {recommendation && (
            <div className="bg-slate-900 dark:bg-slate-800/90 rounded-3xl p-8 border border-slate-800 dark:border-slate-700 shadow-2xl backdrop-blur-xl relative overflow-hidden text-white">
              <div className="absolute top-0 right-0 w-64 h-64 bg-emerald-500/10 rounded-full blur-[80px] pointer-events-none"></div>
              
              <div className="flex items-center gap-4 mb-8">
                <div className="p-4 rounded-2xl bg-gradient-to-br from-emerald-400 to-emerald-600 shadow-lg shadow-emerald-500/20">
                  <TrendingDown size={28} className="text-white" />
                </div>
                <div>
                  <h2 className="text-2xl font-bold text-white tracking-tight">Smart Deposit Recommendation</h2>
                  <p className="text-emerald-400 font-medium mt-1">{recommendation.savings_summary}</p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-center">
                <div className="space-y-4">
                  <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4">Recommended Schedule</h3>
                  {Object.entries(recommendation.schedule).map(([date, amount]) => (
                    <div key={date} className="flex justify-between items-center bg-slate-800/50 dark:bg-slate-900/50 p-4 rounded-xl border border-slate-700/50 hover:border-emerald-500/30 transition-colors">
                      <span className="text-slate-300 font-medium flex items-center gap-3">
                        <Calendar size={16} className="text-slate-500"/>
                        {new Date(date).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })}
                      </span>
                      <span className="text-emerald-400 font-bold">LKR {amount.toLocaleString(undefined, {minimumFractionDigits: 2})}</span>
                    </div>
                  ))}
                </div>

                <div className="h-64 w-full bg-slate-800/50 dark:bg-slate-900/30 rounded-2xl p-4 border border-slate-700/30">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={chartData} margin={{ top: 20, right: 20, left: -20, bottom: 0 }}>
                      <XAxis dataKey="name" stroke="#64748b" tick={{fill: '#94a3b8'}} axisLine={false} tickLine={false} />
                      <YAxis stroke="#64748b" tick={{fill: '#64748b'}} axisLine={false} tickLine={false} tickFormatter={(v) => `LKR ${v/1000}k`} />
                      <Tooltip 
                        cursor={{fill: theme === 'dark' ? '#1e293b' : '#334155', opacity: 0.4}}
                        contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '12px', color: '#f8fafc' }}
                        formatter={(value: any) => [`LKR ${Number(value).toLocaleString()}`, 'Interest']}
                      />
                      <Bar dataKey="value" radius={[6, 6, 0, 0]} maxBarSize={60}>
                        {chartData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Right Column */}
        <div className="space-y-8">
          
          {/* Explainability */}
          <div className="bg-white dark:bg-slate-800/60 rounded-3xl p-6 border border-slate-200 dark:border-slate-700/50 shadow-xl shadow-slate-200/50 dark:shadow-none backdrop-blur-md transition-colors">
            <h2 className="text-lg font-bold text-slate-900 dark:text-white mb-6 flex items-center gap-2 transition-colors">
              <FileText size={20} className="text-indigo-500 dark:text-indigo-400" />
              Statement Explained
            </h2>
            <div className="space-y-4">
              {explanations.map((exp, i) => (
                <div key={i} className="group">
                  <h4 className="text-slate-800 dark:text-slate-200 font-medium mb-1 group-hover:text-indigo-500 dark:group-hover:text-indigo-300 transition-colors">{exp.line_item_name}</h4>
                  <p className="text-slate-500 dark:text-slate-400 text-sm leading-relaxed">{exp.plain_language_explanation}</p>
                  {i < explanations.length - 1 && <div className="h-px bg-slate-100 dark:bg-slate-700/50 mt-4"></div>}
                </div>
              ))}
            </div>
          </div>

          {/* Subscriptions */}
          {low_value_subscriptions.length > 0 && (
            <div className="bg-white dark:bg-slate-800/60 rounded-3xl p-6 border border-slate-200 dark:border-slate-700/50 shadow-xl shadow-slate-200/50 dark:shadow-none backdrop-blur-md transition-colors">
              <h2 className="text-lg font-bold text-slate-900 dark:text-white mb-6 flex items-center gap-2 transition-colors">
                <AlertCircle size={20} className="text-amber-500 dark:text-amber-400" />
                Flagged Subscriptions
              </h2>
              <div className="space-y-4">
                {low_value_subscriptions.map((sub, i) => (
                  <div key={i} className="bg-slate-50 dark:bg-slate-900/50 p-4 rounded-xl border border-slate-100 dark:border-slate-700/50 border-l-4 border-l-amber-500">
                    <div className="flex justify-between items-start mb-2">
                      <h4 className="text-slate-800 dark:text-slate-200 font-medium">{sub.name}</h4>
                      <span className="text-amber-500 dark:text-amber-400 font-bold text-sm">LKR {sub.amount.toLocaleString()}</span>
                    </div>
                    <p className="text-slate-500 text-xs leading-relaxed">{sub.reason}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

        </div>
      </div>
    </div>
  );
}
