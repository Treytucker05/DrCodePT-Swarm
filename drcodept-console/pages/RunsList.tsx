import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../services/api';
import { Run } from '../types';
import StatusPill from '../components/StatusPill';
import { ArrowRight, Search } from 'lucide-react';

const RunsList: React.FC = () => {
  const [runs, setRuns] = useState<Run[]>([]);
  const [search, setSearch] = useState('');

  useEffect(() => {
    api.getRuns().then(setRuns);
  }, []);

  const filteredRuns = runs.filter(r => r.task.toLowerCase().includes(search.toLowerCase()) || r.id.toLowerCase().includes(search.toLowerCase()));

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <h1 className="text-2xl font-bold text-navy-700">Execution History</h1>
        <div className="relative">
             <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
             <input 
               type="text" 
               placeholder="Search runs..." 
               value={search}
               onChange={e => setSearch(e.target.value)}
               className="pl-9 pr-4 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-navy-700/20 w-full sm:w-64"
             />
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-600">
            <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                    <th className="px-6 py-4 font-semibold text-navy-800">Run ID</th>
                    <th className="px-6 py-4 font-semibold text-navy-800">Task</th>
                    <th className="px-6 py-4 font-semibold text-navy-800">Status</th>
                    <th className="px-6 py-4 font-semibold text-navy-800">Started</th>
                    <th className="px-6 py-4 font-semibold text-navy-800">Duration</th>
                    <th className="px-6 py-4 font-semibold text-navy-800 text-right">Action</th>
                </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
                {filteredRuns.map(run => (
                    <tr key={run.id} className="hover:bg-slate-50 transition-colors">
                        <td className="px-6 py-4 font-mono text-xs">{run.id}</td>
                        <td className="px-6 py-4 font-medium text-navy-700">{run.task}</td>
                        <td className="px-6 py-4"><StatusPill status={run.status} size="sm" /></td>
                        <td className="px-6 py-4">{run.startedAt}</td>
                        <td className="px-6 py-4">{run.duration}</td>
                        <td className="px-6 py-4 text-right">
                             <Link to={`/runs/${run.id}`} className="inline-flex items-center gap-1 text-teal-600 hover:text-teal-700 font-medium text-xs uppercase tracking-wide">
                                Details <ArrowRight size={14} />
                             </Link>
                        </td>
                    </tr>
                ))}
            </tbody>
          </table>
          {filteredRuns.length === 0 && <div className="p-8 text-center text-slate-400">No runs found.</div>}
        </div>
      </div>
    </div>
  );
};

export default RunsList;