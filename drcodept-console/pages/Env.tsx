import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { Lock, Save, AlertTriangle, Key } from 'lucide-react';

const EnvPage: React.FC = () => {
  const [knownKeys, setKnownKeys] = useState<string[]>([]);
  const [newKey, setNewKey] = useState('');
  const [newValue, setNewValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [successMsg, setSuccessMsg] = useState('');

  useEffect(() => {
    api.getEnvKeys().then(setKnownKeys);
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newKey || !newValue) return;
    
    setLoading(true);
    await api.setEnv(newKey, newValue);
    
    // Update known keys if it's new
    if (!knownKeys.includes(newKey)) {
        setKnownKeys([...knownKeys, newKey]);
    }
    
    setSuccessMsg(`Successfully set ${newKey}`);
    setNewKey('');
    setNewValue('');
    setLoading(false);
    setTimeout(() => setSuccessMsg(''), 3000);
  };

  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-navy-700 mb-2">Environment Variables</h1>
        <p className="text-slate-500">Manage secrets and configuration for the agent.</p>
      </div>

      <div className="bg-amber-50 border-l-4 border-amber-400 p-4 rounded-r-lg shadow-sm flex gap-3">
         <AlertTriangle className="text-amber-600 flex-shrink-0" />
         <div className="text-sm text-amber-800">
           <span className="font-bold">Security Notice:</span> Existing values are never displayed for security reasons. Overwriting a key updates it immediately in the running process and <code>.env</code> file.
         </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        
        {/* Write Form */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <h2 className="text-lg font-semibold text-navy-700 mb-6 flex items-center gap-2">
            <Lock size={18} className="text-teal-600" /> Set Variable
          </h2>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Key Name</label>
              <input 
                type="text" 
                value={newKey}
                onChange={(e) => setNewKey(e.target.value)}
                placeholder="e.g. OPENAI_API_KEY"
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-teal-500 outline-none transition-all font-mono text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Value</label>
              <input 
                type="password" 
                value={newValue}
                onChange={(e) => setNewValue(e.target.value)}
                placeholder="••••••••••••••••"
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-teal-500 outline-none transition-all font-mono text-sm"
              />
            </div>
            
            <button 
              type="submit" 
              disabled={loading || !newKey || !newValue}
              className="w-full flex items-center justify-center gap-2 bg-navy-700 hover:bg-navy-800 text-white py-2.5 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"/> : <Save size={18} />}
              Update Variable
            </button>
            {successMsg && <p className="text-green-600 text-sm text-center font-medium animate-in fade-in">{successMsg}</p>}
          </form>
        </div>

        {/* Read List */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <h2 className="text-lg font-semibold text-navy-700 mb-6 flex items-center gap-2">
            <Key size={18} className="text-slate-500" /> Configured Keys
          </h2>
          <div className="space-y-2">
            {knownKeys.length === 0 ? (
                <p className="text-slate-400 italic text-sm">No keys found.</p>
            ) : (
                knownKeys.map(key => (
                    <div key={key} className="flex items-center gap-2 p-2 rounded bg-slate-50 border border-slate-100 font-mono text-xs text-slate-600">
                        <div className="w-2 h-2 rounded-full bg-green-400"></div>
                        {key}
                    </div>
                ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default EnvPage;