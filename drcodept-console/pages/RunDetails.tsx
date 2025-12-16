import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { RunDetails, LogEvent } from '../types';
import StatusPill from '../components/StatusPill';
import { ArrowLeft, Clock, Download, Image as ImageIcon, FileCode, FileText, PauseCircle, PlayCircle, RefreshCw, Terminal } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

const RunDetailsPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [details, setDetails] = useState<RunDetails | null>(null);
  const [loading, setLoading] = useState(true);

  // Auto-refresh logs simulation
  useEffect(() => {
    if (!id) return;

    const fetchDetails = async () => {
      const data = await api.getRunDetails(id);
      setDetails(data);
      setLoading(false);
    };

    fetchDetails();
    const interval = setInterval(fetchDetails, 5000); // 5s refresh
    return () => clearInterval(interval);
  }, [id]);

  if (loading || !details) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-navy-700"></div>
      </div>
    );
  }

  const handleCreateContinueFlag = async () => {
    await api.createContinueFlag();
    // Refresh
    const data = await api.getRunDetails(id!);
    setDetails(data);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <button onClick={() => navigate(-1)} className="p-2 -ml-2 text-slate-400 hover:text-navy-700 rounded-full hover:bg-slate-100">
            <ArrowLeft size={20} />
          </button>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-navy-700">{details.task}</h1>
              <StatusPill status={details.status} />
            </div>
            <div className="flex items-center gap-4 mt-1 text-sm text-slate-500">
              <span className="font-mono text-slate-400">ID: {details.id}</span>
              <span className="flex items-center gap-1"><Clock size={14} /> {details.startedAt}</span>
              <span>Duration: {details.duration}</span>
            </div>
          </div>
        </div>
        
        {details.isWaiting && (
          <div className="flex items-center gap-3 bg-amber-50 border border-amber-200 px-4 py-2 rounded-lg">
             <div className="flex items-center gap-2 text-amber-700 font-medium">
               <PauseCircle size={18} />
               <span>Waiting for Handoff</span>
             </div>
             <button 
              onClick={handleCreateContinueFlag}
              className="px-3 py-1 bg-amber-600 hover:bg-amber-700 text-white text-sm font-medium rounded-md transition-colors shadow-sm"
             >
               Resume Run
             </button>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Summary & Evidence */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* Summary Card */}
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
            <h2 className="text-lg font-semibold text-navy-700 mb-4 border-b border-slate-100 pb-2">Run Summary</h2>
            <div className="prose prose-sm prose-slate max-w-none">
              <ReactMarkdown>{details.summary}</ReactMarkdown>
            </div>
          </div>

          {/* Evidence Card */}
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
            <h2 className="text-lg font-semibold text-navy-700 mb-4 border-b border-slate-100 pb-2">Evidence</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {details.evidence.map((item, idx) => (
                <div key={idx} className="flex items-start gap-3 p-3 rounded-lg border border-slate-100 bg-slate-50 hover:border-slate-300 transition-colors">
                   {item.type === 'image' ? (
                     <div className="w-12 h-12 rounded bg-slate-200 flex-shrink-0 overflow-hidden">
                        <img src={item.url} alt={item.name} className="w-full h-full object-cover" />
                     </div>
                   ) : (
                     <div className="w-12 h-12 rounded bg-white border border-slate-200 flex items-center justify-center flex-shrink-0 text-slate-500">
                        {item.type === 'html' ? <FileCode size={20} /> : <FileText size={20} />}
                     </div>
                   )}
                   <div className="flex-1 min-w-0">
                      <div className="font-medium text-navy-700 text-sm truncate" title={item.name}>{item.name}</div>
                      <div className="text-xs text-slate-500 mt-1">{item.size} • {item.type.toUpperCase()}</div>
                   </div>
                   <button className="text-slate-400 hover:text-teal-600 transition-colors">
                      <Download size={16} />
                   </button>
                </div>
              ))}
              {details.evidence.length === 0 && (
                <div className="text-slate-400 text-sm italic col-span-full">No evidence collected yet.</div>
              )}
            </div>
          </div>
        </div>

        {/* Right Column: Live Events */}
        <div className="lg:col-span-1">
          <div className="bg-navy-900 rounded-xl shadow-lg border border-navy-800 overflow-hidden flex flex-col h-[600px]">
            <div className="px-4 py-3 bg-navy-800 border-b border-navy-700 flex justify-between items-center">
               <h2 className="text-sm font-bold text-slate-200 flex items-center gap-2">
                 <Terminal size={14} className="text-teal-500" /> Live Events
               </h2>
               <div className="flex items-center gap-2">
                  <span className="relative flex h-2 w-2">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-teal-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-teal-500"></span>
                  </span>
                  <span className="text-xs text-slate-400 uppercase font-mono">Tailing</span>
               </div>
            </div>
            <div className="flex-1 overflow-y-auto p-4 font-mono text-xs space-y-2 scrollbar-hide">
               {details.events.map((evt, idx) => (
                 <div key={idx} className="flex gap-3 text-slate-300">
                    <span className="text-slate-500 flex-shrink-0 select-none">{evt.timestamp}</span>
                    <span className={`flex-shrink-0 font-bold ${
                      evt.level === 'ERROR' ? 'text-red-400' :
                      evt.level === 'WARN' ? 'text-amber-400' :
                      evt.level === 'DEBUG' ? 'text-slate-500' : 'text-teal-400'
                    }`}>{evt.level}</span>
                    <span className="break-all">{evt.message}</span>
                 </div>
               ))}
               <div className="h-4"></div> {/* Spacer */}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RunDetailsPage;