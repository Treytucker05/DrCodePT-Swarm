import React, { useState, useEffect, useRef } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { InputSection } from './components/InputSection';
import { Dashboard } from './components/Dashboard';
import { DataControls } from './components/DataControls';
import { parseTasksFromText } from './services/geminiService';
import { useLocalStorage } from './hooks/useLocalStorage';
import { Task, Priority, Subtask, AISubtask } from './types';
import { BrainCircuit, Info, Copy, Check, Command, Keyboard } from 'lucide-react';

const EXTERNAL_AI_PROMPT = `Analyze the provided content (calendar, notes, or list) and organize it into a strict hierarchical to-do list.

Formatting Rules:
- Start every line with a simple dash (-).
- Use exactly 2 spaces for indentation to show subtasks.
- Do not use bold text, markdown headers, or conversational filler.
- Group related items logically.
- Output ONLY the final list.`;

const App: React.FC = () => {
  const [tasks, setTasks] = useLocalStorage<Task[]>('smartdo-tasks', []);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  
  // Refs for keyboard shortcuts
  const inputSectionRef = useRef<HTMLTextAreaElement>(null);
  const hiddenFileInputRef = useRef<HTMLInputElement>(null);

  // Ensure all tasks have an order property (migration for existing data)
  useEffect(() => {
    let changed = false;
    const maxOrder = tasks.length > 0 ? Math.max(...tasks.map(t => t.order || 0)) : 0;
    const updated = tasks.map((t, idx) => {
      if (t.order === undefined) {
        changed = true;
        return { ...t, order: maxOrder + (idx + 1) * 1000 };
      }
      return t;
    });
    if (changed) {
      setTasks(updated);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Run once on mount/load

  // Keyboard Shortcuts Listener
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // CMD/CTRL + S (Save/Backup)
      if ((e.metaKey || e.ctrlKey) && e.key === 's') {
        e.preventDefault();
        handleExport();
      }
      // CMD/CTRL + O (Open/Restore)
      if ((e.metaKey || e.ctrlKey) && e.key === 'o') {
        e.preventDefault();
        hiddenFileInputRef.current?.click();
      }
      // CMD/CTRL + / (Focus Input)
      if ((e.metaKey || e.ctrlKey) && e.key === '/') {
        e.preventDefault();
        inputSectionRef.current?.focus();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tasks]); // Re-bind if tasks change (for export closure)

  // Recursive helper to map AI subtasks to application Subtasks with UUIDs
  const mapSubtasks = (items?: AISubtask[]): Subtask[] => {
    if (!items) return [];
    return items.map(item => ({
      id: (item.id && item.id !== 'NEW') ? item.id : uuidv4(),
      title: item.title,
      // @ts-ignore - The AI result might have isCompleted, forcing type check ignore for simplicity
      isCompleted: item.isCompleted === true, 
      subtasks: mapSubtasks(item.subtasks)
    }));
  };

  const handleProcess = async (text: string) => {
    setIsProcessing(true);
    setError(null);
    setSuccessMsg(null);
    try {
      const result = await parseTasksFromText(text, tasks);
      
      const currentMaxOrder = tasks.length > 0 ? Math.max(...tasks.map(t => t.order || 0)) : 0;
      let newCount = 0;

      const updatedTasks: Task[] = result.tasks.map((t, idx) => {
        const existingTask = tasks.find(old => old.id === t.id);
        const finalId = (t.id && t.id !== 'NEW' && existingTask) ? t.id : uuidv4();

        // @ts-ignore
        const aiCompletedStatus = t.isCompleted; 
        let finalIsCompleted = false;

        if (typeof aiCompletedStatus === 'boolean') {
          finalIsCompleted = aiCompletedStatus;
        } else if (existingTask) {
          finalIsCompleted = existingTask.isCompleted;
        }

        // Preserve order if existing, else assign new order at the end
        let finalOrder = existingTask ? existingTask.order : (currentMaxOrder + (++newCount * 1000));
        if (finalOrder === undefined) finalOrder = (idx + 1) * 1000;

        return {
          id: finalId,
          title: t.title,
          description: t.description,
          dueDate: t.dueDate,
          priority: t.priority as Priority,
          category: t.category,
          isCompleted: finalIsCompleted,
          createdAt: existingTask ? existingTask.createdAt : new Date().toISOString(),
          subtasks: mapSubtasks(t.subtasks),
          order: finalOrder
        };
      });

      setTasks(updatedTasks);
      setSuccessMsg("List updated successfully.");
      setTimeout(() => setSuccessMsg(null), 3000);
    } catch (err) {
      console.error(err);
      setError("Failed to process tasks. Please try again. Make sure your API Key is valid.");
    } finally {
      setIsProcessing(false);
    }
  };

  const toggleComplete = (id: string) => {
    setTasks(prev => prev.map(t => 
      t.id === id ? { ...t, isCompleted: !t.isCompleted } : t
    ));
  };

  const deleteTask = (id: string) => {
    setTasks(prev => prev.filter(t => t.id !== id));
  };

  const handleUpdateTask = (id: string, updates: Partial<Task>) => {
    setTasks(prev => prev.map(t => t.id === id ? { ...t, ...updates } : t));
  };

  const handleClearData = () => {
    setTasks([]);
    setSuccessMsg("All tasks cleared.");
    setTimeout(() => setSuccessMsg(null), 3000);
  };

  const toggleSubtask = (taskId: string, subtaskId: string) => {
    setTasks(prev => prev.map(t => {
      if (t.id !== taskId) return t;

      const updateSubtasks = (items: Subtask[]): Subtask[] => {
        return items.map(item => {
          if (item.id === subtaskId) {
            return { ...item, isCompleted: !item.isCompleted };
          }
          if (item.subtasks && item.subtasks.length > 0) {
            return { ...item, subtasks: updateSubtasks(item.subtasks) };
          }
          return item;
        });
      };

      return {
        ...t,
        subtasks: updateSubtasks(t.subtasks)
      };
    }));
  };

  const handleCopyPrompt = () => {
    navigator.clipboard.writeText(EXTERNAL_AI_PROMPT);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleExport = () => {
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(tasks, null, 2));
    const downloadAnchorNode = document.createElement('a');
    downloadAnchorNode.setAttribute("href", dataStr);
    downloadAnchorNode.setAttribute("download", `smartdo_backup_${new Date().toISOString().slice(0,10)}.json`);
    document.body.appendChild(downloadAnchorNode); 
    downloadAnchorNode.click();
    downloadAnchorNode.remove();
    setSuccessMsg("Backup saved. Upload this to your Drive.");
    setTimeout(() => setSuccessMsg(null), 4000);
  };

  const handleImport = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const json = JSON.parse(event.target?.result as string);
        if (Array.isArray(json)) {
             // Ensure imported tasks have order
             const imported = json.map((t: any, i: number) => ({
                 ...t,
                 order: t.order ?? i * 1000
             }));
             setTasks(imported);
             setSuccessMsg("Tasks restored successfully.");
             setTimeout(() => setSuccessMsg(null), 3000);
        } else {
            setError("Invalid file format. Expected a list of tasks.");
            setTimeout(() => setError(null), 4000);
        }
      } catch (err) {
        setError("Failed to parse file.");
        setTimeout(() => setError(null), 4000);
      }
    };
    reader.readAsText(file);
    e.target.value = '';
  };

  return (
    <div className="h-screen w-full flex flex-col bg-black">
      {/* Hidden file input for Shortcut CMD+O */}
      <input 
        type="file" 
        ref={hiddenFileInputRef}
        onChange={handleImport}
        accept=".json"
        className="hidden" 
      />

      <header className="bg-zinc-950 border-b border-zinc-800 px-6 py-4 flex justify-between items-center sticky top-0 z-10 select-none">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-red-600 rounded-lg text-white shadow-lg shadow-red-900/30">
            <BrainCircuit size={24} />
          </div>
          <h1 className="text-xl font-bold text-zinc-100 tracking-tight">SmartDo</h1>
        </div>
        <div className="flex items-center gap-4">
            <div className="hidden lg:flex items-center gap-3 text-xs text-zinc-300 font-mono">
                <span className="flex items-center gap-1"><Command size={10} />S Save</span>
                <span className="flex items-center gap-1"><Command size={10} />O Open</span>
                <span className="flex items-center gap-1"><Command size={10} />/ Focus</span>
            </div>
            <div className="hidden sm:flex items-center gap-2 text-xs text-zinc-300 bg-zinc-900 px-3 py-1.5 rounded-full border border-zinc-800">
                <Keyboard size={12} />
                <span>Pro Shortcuts Active</span>
            </div>
        </div>
      </header>

      <main className="flex-1 overflow-hidden flex flex-col md:flex-row">
        <div className="w-full md:w-[450px] p-6 overflow-y-auto border-r border-zinc-800 bg-black">
          <InputSection 
            ref={inputSectionRef} 
            onProcess={handleProcess} 
            isProcessing={isProcessing} 
          />
          
          <DataControls onExport={handleExport} onImport={handleImport} onClear={handleClearData} />

          {error && (
            <div className="bg-red-950/30 text-red-400 p-4 rounded-xl border border-red-900/50 text-sm mb-6 animate-pulse">
              {error}
            </div>
          )}

          {successMsg && (
            <div className="bg-green-950/30 text-green-400 p-4 rounded-xl border border-green-900/50 text-sm mb-6 flex items-center gap-2 animate-in slide-in-from-left-2">
              <Check size={16} /> {successMsg}
            </div>
          )}

          <div className="bg-zinc-900 p-4 rounded-xl border border-zinc-800 text-sm text-zinc-200 mb-6">
            <h4 className="font-semibold mb-2 text-zinc-200">AI Capabilities</h4>
            <ul className="list-disc pl-4 space-y-1 text-zinc-300">
              <li>"Paste my Anatomy exam outline"</li>
              <li>"I finished the Stats homework"</li>
              <li>"Move Groceries to the top of the list"</li>
              <li>"Rename 'Study' to 'Deep Work'"</li>
            </ul>
          </div>

          <div className="bg-zinc-900 p-4 rounded-xl border border-zinc-800">
            <div className="flex justify-between items-center mb-2">
                <h4 className="font-semibold text-zinc-200 text-sm">Helper Prompt</h4>
                <button 
                    onClick={handleCopyPrompt}
                    className="flex items-center gap-1.5 text-xs font-medium bg-zinc-800 hover:bg-red-900/30 text-zinc-300 hover:text-red-400 px-2 py-1 rounded border border-zinc-700 transition-all"
                >
                    {copied ? <Check size={12} /> : <Copy size={12} />}
                    {copied ? 'Copied!' : 'Copy'}
                </button>
            </div>
            <p className="text-xs text-zinc-300 mb-2 leading-relaxed">
                Paste this instruction into your AI (ChatGPT/Gemini) so it knows how to format your calendar or notes for this app.
            </p>
            <textarea
                readOnly
                value={EXTERNAL_AI_PROMPT}
                className="w-full h-48 bg-black border border-zinc-800 rounded p-3 text-xs text-zinc-200 font-mono resize-none focus:outline-none focus:border-zinc-700 cursor-text"
                onClick={(e) => e.currentTarget.select()}
            />
          </div>
        </div>

        <div className="flex-1 p-6 bg-black overflow-hidden">
          <Dashboard 
            tasks={tasks} 
            onToggleComplete={toggleComplete} 
            onDelete={deleteTask} 
            onToggleSubtask={toggleSubtask}
            onUpdateTask={handleUpdateTask}
          />
        </div>
      </main>
    </div>
  );
};

export default App;
