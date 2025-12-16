import React, { useState, forwardRef } from 'react';
import { Sparkles, ArrowRight, Loader2, Command } from 'lucide-react';

interface InputSectionProps {
  onProcess: (text: string) => Promise<void>;
  isProcessing: boolean;
}

export const InputSection = forwardRef<HTMLTextAreaElement, InputSectionProps>(({ onProcess, isProcessing }, ref) => {
  const [input, setInput] = useState('');

  const handleSubmit = async () => {
    if (!input.trim()) return;
    await onProcess(input);
    setInput('');
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && e.metaKey) {
      handleSubmit();
    }
  };

  return (
    <div className="bg-zinc-900 rounded-2xl shadow-xl shadow-black/20 border border-zinc-800 p-6 mb-8 relative overflow-hidden">
      {/* Decorative background gradient */}
      <div className="absolute top-0 right-0 w-64 h-64 bg-gradient-to-br from-red-900/10 to-black/0 rounded-full blur-3xl -z-10 translate-x-1/3 -translate-y-1/3"></div>

      <div className="flex flex-col gap-4">
        <div className="flex justify-between items-center">
          <div className="flex items-center gap-2 text-zinc-100 font-bold text-lg">
            <Sparkles className="text-red-500" size={20} />
            <h2>Smart Input</h2>
          </div>
          <div className="flex items-center gap-3 text-xs font-medium text-zinc-300">
             <span className="flex items-center gap-1 bg-zinc-800 px-2 py-1 rounded border border-zinc-700">
               <Command size={10} /> + / to focus
             </span>
             <span>CMD + Enter to submit</span>
          </div>
        </div>

        <textarea
          ref={ref}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type here to add, update, or complete tasks...
Ex: 'Paste my history notes here...'
Ex: 'I finished the history homework'
Ex: 'Make the exam due next Friday'
Ex: 'Move Gym to the top of the list'"
          className="w-full h-32 p-4 rounded-xl border border-zinc-800 bg-black focus:bg-zinc-950 focus:ring-2 focus:ring-red-900/30 focus:border-red-800 outline-none resize-none transition-all placeholder:text-zinc-400 text-zinc-200"
          disabled={isProcessing}
        />

        <div className="flex justify-end">
          <button
            onClick={handleSubmit}
            disabled={!input.trim() || isProcessing}
            className={`
              flex items-center gap-2 px-6 py-2.5 rounded-lg font-medium text-white shadow-lg shadow-red-900/20
              transition-all transform active:scale-95
              ${!input.trim() || isProcessing ? 'bg-zinc-800 text-zinc-300 cursor-not-allowed shadow-none' : 'bg-red-600 hover:bg-red-700 hover:-translate-y-0.5'}
            `}
          >
            {isProcessing ? (
              <>
                <Loader2 className="animate-spin" size={18} />
                Processing...
              </>
            ) : (
              <>
                Update List
                <ArrowRight size={18} />
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
});

InputSection.displayName = 'InputSection';
