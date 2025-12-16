import React from 'react';
import { BookOpen, Command, LifeBuoy, Terminal } from 'lucide-react';

const HelpPage: React.FC = () => {
  return (
    <div className="max-w-4xl mx-auto space-y-10">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-navy-700 mb-2">Documentation</h1>
        <p className="text-slate-500">How to operate the DrCodePT Autonomous Agent System.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Architecture Card */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
           <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center text-blue-600 mb-4">
              <BookOpen size={24} />
           </div>
           <h2 className="text-lg font-bold text-navy-700 mb-3">How it Works</h2>
           <ul className="space-y-3 text-sm text-slate-600">
              <li className="flex gap-2">
                 <span className="font-bold text-navy-700">Tasks:</span> YAML files defining goals and tools.
              </li>
              <li className="flex gap-2">
                 <span className="font-bold text-navy-700">Tools:</span> Browser, Shell, API adapters.
              </li>
              <li className="flex gap-2">
                 <span className="font-bold text-navy-700">Verifiers:</span> Reusable checks for success.
              </li>
              <li className="flex gap-2">
                 <span className="font-bold text-navy-700">Runs:</span> Every execution is logged with full evidence.
              </li>
           </ul>
        </div>

        {/* Commands Card */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
           <div className="w-10 h-10 bg-slate-100 rounded-lg flex items-center justify-center text-slate-700 mb-4">
              <Terminal size={24} />
           </div>
           <h2 className="text-lg font-bold text-navy-700 mb-3">CLI Reference</h2>
           <div className="space-y-3">
              <div className="bg-slate-900 text-slate-300 p-3 rounded-md font-mono text-xs">
                # Start the console<br/>
                <span className="text-white">Start_Agent_All.bat</span>
              </div>
              <div className="bg-slate-900 text-slate-300 p-3 rounded-md font-mono text-xs">
                # Run a specific task<br/>
                <span className="text-white">python agent/main.py run blackboard_login</span>
              </div>
              <div className="bg-slate-900 text-slate-300 p-3 rounded-md font-mono text-xs">
                # Launch recorder<br/>
                <span className="text-white">python agent/recorder.py</span>
              </div>
           </div>
        </div>
      </div>

      {/* Troubleshooting */}
      <div className="bg-teal-50 border border-teal-100 rounded-xl p-8">
         <div className="flex items-start gap-4">
            <LifeBuoy className="text-teal-600 mt-1" size={24} />
            <div>
               <h2 className="text-lg font-bold text-navy-700 mb-2">Need Assistance?</h2>
               <p className="text-slate-700 mb-4 text-sm">
                 If a task is stuck, check the <strong>Handoff</strong> page to see if the agent is requesting human intervention. 
                 Logs are stored locally in the <code>runs/</code> directory.
               </p>
               <a href="#" className="text-teal-700 font-bold hover:underline text-sm">Open Logs Directory &rarr;</a>
            </div>
         </div>
      </div>
    </div>
  );
};

export default HelpPage;