import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Play, FileText, Terminal, Copy, Search, ArrowRight, FolderOpen, Video } from 'lucide-react';
import { api } from '../services/api';
import { Task, Run } from '../types';
import StatusPill from '../components/StatusPill';
import Modal from '../components/Modal';

const Home: React.FC = () => {
  const navigate = useNavigate();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [runs, setRuns] = useState<Run[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTaskYaml, setSelectedTaskYaml] = useState<{name: string, content: string} | null>(null);
  const [toast, setToast] = useState<{message: string, type: 'success' | 'info'} | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      const [fetchedTasks, fetchedRuns] = await Promise.all([
        api.getTasks(),
        api.getRuns(),
      ]);
      setTasks(fetchedTasks);
      setRuns(fetchedRuns);
    };
    fetchData();
  }, []);

  const showToast = (message: string) => {
    setToast({ message, type: 'success' });
    setTimeout(() => setToast(null), 3000);
  };

  const handleRunTask = async (taskName: string) => {
    showToast(`Starting task: ${taskName}...`);
    const { runId } = await api.runTask(taskName);
    // Optimistic update for UI feel, in real app we'd reload runs
    setRuns(prev => [
      { id: runId, task: taskName, status: 'in-progress', startedAt: 'Just now', duration: '0s' },
      ...prev
    ]);
    // Optional: navigate to run details immediately
    // navigate(`/runs/${runId}`);
  };

  const copyCommand = (taskName: string) => {
    navigator.clipboard.writeText(`python agent/main.py run ${taskName}`);
    showToast('Command copied to clipboard');
  };

  const filteredTasks = tasks.filter(t => 
    t.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    t.goal.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'browser': return <Video size={16} className="text-purple-600" />;
      case 'shell': return <Terminal size={16} className="text-slate-600" />;
      case 'api': return <div className="text-xs font-bold text-blue-600 border border-blue-600 rounded px-1">API</div>;
      case 'fs': return <FolderOpen size={16} className="text-amber-600" />;
      default: return <FileText size={16} className="text-teal-600" />;
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
      {/* Toast Notification */}
      {toast && (
        <div className="fixed bottom-6 right-6 z-50 bg-navy-800 text-white px-4 py-3 rounded-lg shadow-lg animate-in slide-in-from-bottom-4 flex items-center gap-3">
            <div className="w-2 h-2 rounded-full bg-teal-500"></div>
            {toast.message}
        </div>
      )}

      {/* Main Column: Tasks */}
      <div className="lg:col-span-2 space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold text-navy-700">Tasks</h2>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
            <input 
              type="text" 
              placeholder="Filter tasks..." 
              className="pl-9 pr-4 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-navy-700/20 focus:border-navy-700 w-64 transition-all"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-slate-200 divide-y divide-slate-100 overflow-hidden">
          {filteredTasks.map((task) => (
            <div key={task.name} className="p-4 sm:p-5 hover:bg-slate-50 transition-colors group">
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="bg-slate-100 p-1.5 rounded text-slate-600">
                      {getTypeIcon(task.type)}
                    </span>
                    <h3 className="font-semibold text-navy-800">{task.name}</h3>
                  </div>
                  <p className="text-slate-500 text-sm ml-10">{task.goal}</p>
                </div>
                <div className="flex items-center gap-2 opacity-100 sm:opacity-0 group-hover:opacity-100 transition-opacity">
                   <button 
                    onClick={() => copyCommand(task.name)}
                    className="p-2 text-slate-400 hover:text-navy-700 rounded-md hover:bg-slate-200"
                    title="Copy CLI Command"
                  >
                    <Copy size={18} />
                  </button>
                  <button 
                    onClick={() => setSelectedTaskYaml({name: task.name, content: task.yamlContent})}
                    className="p-2 text-slate-400 hover:text-navy-700 rounded-md hover:bg-slate-200"
                    title="View YAML"
                  >
                    <FileText size={18} />
                  </button>
                  <button 
                    onClick={() => handleRunTask(task.name)}
                    className="flex items-center gap-2 bg-navy-700 text-white px-3 py-1.5 rounded-md hover:bg-navy-800 transition-colors shadow-sm text-sm font-medium ml-2"
                  >
                    <Play size={14} /> Run
                  </button>
                </div>
              </div>
            </div>
          ))}
          {filteredTasks.length === 0 && (
            <div className="p-8 text-center text-slate-400">
              No tasks found matching your search.
            </div>
          )}
        </div>
      </div>

      {/* Side Column: Quick Actions & Recent Runs */}
      <div className="space-y-8">
        {/* Quick Actions */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
          <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-4">Quick Actions</h3>
          <div className="grid grid-cols-1 gap-3">
             <button 
                onClick={() => handleRunTask('blackboard_login')}
                className="flex items-center gap-3 p-3 rounded-lg border border-slate-200 hover:border-teal-500 hover:bg-teal-50 transition-all text-left group"
             >
                <div className="bg-teal-100 text-teal-600 p-2 rounded-md">
                  <Play size={16} />
                </div>
                <div>
                  <div className="font-semibold text-navy-800 group-hover:text-teal-700">Run Blackboard Login</div>
                  <div className="text-xs text-slate-500">Fast auth refresh</div>
                </div>
             </button>

             <button 
                onClick={() => showToast('Opening Recorder in separate shell...')}
                className="flex items-center gap-3 p-3 rounded-lg border border-slate-200 hover:border-navy-500 hover:bg-navy-50 transition-all text-left group"
             >
                <div className="bg-slate-100 text-navy-700 p-2 rounded-md">
                  <Video size={16} />
                </div>
                <div>
                  <div className="font-semibold text-navy-800">Open Recorder</div>
                  <div className="text-xs text-slate-500">Capture new workflow</div>
                </div>
             </button>

             <button 
                onClick={() => showToast('Opened local runs folder')}
                className="flex items-center gap-3 p-3 rounded-lg border border-slate-200 hover:border-slate-400 hover:bg-slate-50 transition-all text-left group"
             >
                <div className="bg-slate-100 text-slate-600 p-2 rounded-md">
                  <FolderOpen size={16} />
                </div>
                <div>
                  <div className="font-semibold text-navy-800">Open Runs Folder</div>
                  <div className="text-xs text-slate-500">View raw logs locally</div>
                </div>
             </button>
          </div>
        </div>

        {/* Recent Runs */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
          <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100">
             <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider">Recent Runs</h3>
             <Link to="/runs" className="text-teal-600 hover:text-teal-700 text-sm font-medium flex items-center gap-1">
                View All <ArrowRight size={14} />
             </Link>
          </div>
          <div className="divide-y divide-slate-100">
            {runs.slice(0, 5).map(run => (
              <div key={run.id} className="p-4 hover:bg-slate-50 transition-colors">
                <div className="flex justify-between items-start mb-1">
                   <Link to={`/runs/${run.id}`} className="font-medium text-navy-700 hover:underline text-sm truncate max-w-[150px]">
                      {run.task}
                   </Link>
                   <StatusPill status={run.status} size="sm" />
                </div>
                <div className="flex justify-between items-center text-xs text-slate-400 mt-2">
                   <span>{run.startedAt}</span>
                   <span>{run.duration}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* YAML Viewer Modal */}
      <Modal
        isOpen={!!selectedTaskYaml}
        onClose={() => setSelectedTaskYaml(null)}
        title={`Task Configuration: ${selectedTaskYaml?.name}`}
      >
        <div className="relative">
          <pre className="bg-slate-900 text-slate-50 p-4 rounded-lg font-mono text-sm overflow-x-auto">
            {selectedTaskYaml?.content}
          </pre>
          <button 
             onClick={() => {
               if (selectedTaskYaml) navigator.clipboard.writeText(selectedTaskYaml.content);
               showToast('YAML copied to clipboard');
             }}
             className="absolute top-2 right-2 p-2 bg-white/10 hover:bg-white/20 text-white rounded transition-colors"
          >
            <Copy size={14} />
          </button>
        </div>
      </Modal>
    </div>
  );
};

export default Home;