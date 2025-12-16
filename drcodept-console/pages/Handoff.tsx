import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { HandoffState } from '../types';
import { Hand, Play, AlertCircle, CheckCircle2 } from 'lucide-react';

const HandoffPage: React.FC = () => {
  const [state, setState] = useState<HandoffState | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchState = async () => {
    setLoading(true);
    const data = await api.getHandoffState();
    setState(data);
    setLoading(false);
  };

  useEffect(() => {
    fetchState();
  }, []);

  const handleResume = async () => {
    await api.createContinueFlag();
    fetchState(); // Refresh to check if continue flag is registered (mock simulation)
  };

  if (loading) return <div className="p-10 text-center"><div className="animate-spin inline-block w-8 h-8 border-4 border-navy-700 border-t-transparent rounded-full"></div></div>;

  return (
    <div className="max-w-2xl mx-auto text-center space-y-8 py-10">
      
      <div className="inline-flex items-center justify-center p-4 bg-navy-50 rounded-full mb-4">
        <Hand size={48} className="text-navy-700" />
      </div>

      <h1 className="text-3xl font-bold text-navy-700">Human Handoff Control</h1>
      
      {!state?.waiting ? (
        <div className="bg-white p-8 rounded-2xl shadow-sm border border-slate-200">
           <div className="flex flex-col items-center gap-4 text-slate-500">
              <CheckCircle2 size={48} className="text-green-500" />
              <p className="text-lg">No active handoff requests.</p>
              <p className="text-sm">The agent is running autonomously or is idle.</p>
           </div>
        </div>
      ) : (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4">
            <div className="bg-white text-left rounded-xl shadow-lg border border-red-100 overflow-hidden">
                <div className="bg-red-50 px-6 py-4 border-b border-red-100 flex items-center gap-3">
                    <AlertCircle className="text-red-500" />
                    <h2 className="font-bold text-red-700">Agent is WAITING</h2>
                </div>
                <div className="p-6">
                    <p className="text-slate-600 mb-4">The agent encountered a blocking issue and needs human assistance.</p>
                    <div className="bg-slate-900 rounded-lg p-4 font-mono text-sm text-slate-300 overflow-x-auto border-l-4 border-red-500">
                        <pre>{state.content}</pre>
                    </div>
                </div>
                <div className="bg-gray-50 px-6 py-4 border-t border-gray-100 flex justify-end">
                    <button 
                        onClick={handleResume}
                        disabled={state.continuePresent}
                        className={`flex items-center gap-2 px-6 py-3 rounded-lg font-bold text-white shadow-md transition-transform active:scale-95 ${
                            state.continuePresent 
                            ? 'bg-slate-400 cursor-not-allowed' 
                            : 'bg-teal-600 hover:bg-teal-700'
                        }`}
                    >
                        {state.continuePresent ? 'Resume Signal Sent' : 'Resume (Create CONTINUE.flag)'}
                        {!state.continuePresent && <Play size={18} fill="currentColor" />}
                    </button>
                </div>
            </div>
            
            <p className="text-slate-500 text-sm max-w-md mx-auto">
                <strong>How it works:</strong> Once you resolve the issue (e.g. solve a captcha manually), click Resume. The supervisor loop detects the <code>CONTINUE.flag</code> and resumes execution.
            </p>
        </div>
      )}
    </div>
  );
};

export default HandoffPage;