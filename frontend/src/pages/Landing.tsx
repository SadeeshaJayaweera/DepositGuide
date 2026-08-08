import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { UploadCloud, Zap, Shield, ArrowRight, CheckCircle2, Moon, Sun } from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';

export default function Landing() {
  const { theme, toggleTheme } = useTheme();
  
  return (
    <div className="min-h-screen bg-white dark:bg-slate-950 transition-colors duration-300 font-sans selection:bg-indigo-500/30">
      
      {/* Navigation */}
      <nav className="border-b border-slate-200 dark:border-slate-800 bg-white/80 dark:bg-slate-950/80 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl flex items-center justify-center shadow-lg shadow-indigo-500/20">
              <span className="text-white font-bold text-xl">D</span>
            </div>
            <span className="text-xl font-bold text-slate-900 dark:text-white tracking-tight">DepositGuide</span>
          </div>
          
          <div className="flex items-center gap-6">
            <button onClick={toggleTheme} className="text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white transition-colors">
              {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
            </button>
            <Link to="/login" className="text-slate-600 hover:text-slate-900 dark:text-slate-300 dark:hover:text-white font-medium transition-colors">
              Log in
            </Link>
            <Link to="/login" className="bg-indigo-600 hover:bg-indigo-500 text-white px-5 py-2.5 rounded-full font-medium transition-all shadow-md shadow-indigo-500/20">
              Get Started
            </Link>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-6 pb-24">
        {/* Hero Section */}
        <div className="py-24 md:py-32 flex flex-col items-center text-center relative">
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-indigo-500/20 dark:bg-indigo-500/10 rounded-full blur-[100px] pointer-events-none"></div>
          
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-indigo-50 dark:bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 font-medium text-sm mb-8 border border-indigo-100 dark:border-indigo-500/20 shadow-sm">
            <Zap size={16} />
            <span>AI-Powered Credit Optimization</span>
          </div>
          
          <h1 className="text-5xl md:text-7xl font-extrabold text-slate-900 dark:text-white tracking-tight mb-8 leading-tight">
            Stop guessing.<br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-600 to-purple-600 dark:from-indigo-400 dark:to-purple-500">
              Start optimizing.
            </span>
          </h1>
          
          <p className="text-xl text-slate-600 dark:text-slate-400 max-w-2xl mb-12 leading-relaxed">
            DepositGuide analyzes your credit card statements, models your spending habits, and recommends exactly when and how much to pay to minimize interest.
          </p>
          
          <Link to="/login" className="group flex items-center gap-3 bg-slate-900 hover:bg-slate-800 dark:bg-white dark:hover:bg-slate-100 text-white dark:text-slate-900 px-8 py-4 rounded-full font-semibold text-lg transition-all shadow-xl shadow-slate-900/10 dark:shadow-white/10 hover:-translate-y-1">
            Analyze My Statement
            <ArrowRight size={20} className="group-hover:translate-x-1 transition-transform" />
          </Link>
        </div>

        {/* How It Works */}
        <div className="py-24 border-t border-slate-100 dark:border-slate-800/50">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-slate-900 dark:text-white mb-4">How it works</h2>
            <p className="text-slate-600 dark:text-slate-400">Three simple steps to unlock your financial potential.</p>
          </div>
          
          <div className="grid md:grid-cols-3 gap-8">
            {[
              { icon: UploadCloud, title: 'Upload Statement', desc: 'Securely upload your PDF credit card statements. Our system parses the line items instantly.' },
              { icon: Shield, title: 'AI Analysis', desc: 'We build a behavioral profile of your spending and categorize everything automatically.' },
              { icon: Zap, title: 'Optimize Payments', desc: 'Get a precise recommendation on when to make your deposit to save the most on interest.' }
            ].map((step, i) => (
              <div key={i} className="bg-white dark:bg-slate-900 p-8 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-xl shadow-slate-200/50 dark:shadow-none hover:border-indigo-500/30 dark:hover:border-indigo-500/30 transition-colors relative overflow-hidden group">
                <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-500/5 rounded-bl-full -z-10 group-hover:bg-indigo-500/10 transition-colors"></div>
                <div className="w-14 h-14 bg-indigo-50 dark:bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 rounded-2xl flex items-center justify-center mb-6">
                  <step.icon size={28} />
                </div>
                <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-3">{step.title}</h3>
                <p className="text-slate-600 dark:text-slate-400 leading-relaxed">{step.desc}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Demo Section */}
        <div className="py-24 border-t border-slate-100 dark:border-slate-800/50">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            <div>
              <h2 className="text-3xl font-bold text-slate-900 dark:text-white mb-6">Experience the Dashboard</h2>
              <p className="text-slate-600 dark:text-slate-400 text-lg mb-8 leading-relaxed">
                See exactly where your money goes. Our premium dashboard gives you actionable insights at a glance, highlighting high-value behaviors and potential savings.
              </p>
              <ul className="space-y-4">
                {['Predictive Cash-flow Modeling', 'Plain-language statement explanations', 'Interactive AI Advisor Chat'].map((item, i) => (
                  <li key={i} className="flex items-center gap-3 text-slate-700 dark:text-slate-300 font-medium">
                    <CheckCircle2 size={20} className="text-emerald-500" />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
            
            <div className="relative">
              <div className="absolute -inset-1 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-3xl blur opacity-20 dark:opacity-40"></div>
              <div className="relative bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 shadow-2xl">
                {/* Mock Dashboard UI */}
                <div className="flex items-center justify-between mb-6 border-b border-slate-200 dark:border-slate-800 pb-4">
                  <div className="font-semibold text-slate-900 dark:text-white">Monthly Summary</div>
                  <div className="text-sm text-slate-500">Aug 2026</div>
                </div>
                
                <div className="grid grid-cols-2 gap-4 mb-6">
                  <div className="bg-white dark:bg-slate-800 p-4 rounded-2xl border border-slate-100 dark:border-slate-700">
                    <div className="text-sm text-slate-500 mb-1">Total Spent</div>
                    <div className="text-2xl font-bold text-slate-900 dark:text-white">$3,450</div>
                  </div>
                  <div className="bg-white dark:bg-slate-800 p-4 rounded-2xl border border-slate-100 dark:border-slate-700">
                    <div className="text-sm text-slate-500 mb-1">Potential Savings</div>
                    <div className="text-2xl font-bold text-emerald-500">$120</div>
                  </div>
                </div>

                <div className="bg-indigo-50 dark:bg-indigo-500/10 border border-indigo-100 dark:border-indigo-500/20 p-4 rounded-2xl">
                  <div className="flex items-start gap-3">
                    <Zap size={20} className="text-indigo-600 dark:text-indigo-400 mt-0.5" />
                    <div>
                      <div className="font-semibold text-indigo-900 dark:text-indigo-300 mb-1">Optimization Ready</div>
                      <div className="text-sm text-indigo-700 dark:text-indigo-400/80">Pay $1,500 by Aug 12 to reduce this cycle's interest by 33%.</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
