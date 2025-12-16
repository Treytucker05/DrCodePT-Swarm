
import React, { useMemo } from 'react';
import { Task, Priority } from '../types';
import { TaskCard } from './TaskCard';
import { Calendar, CheckCircle2, AlertCircle, Sun } from 'lucide-react';

interface DashboardProps {
  tasks: Task[];
  onToggleComplete: (id: string) => void;
  onDelete: (id: string) => void;
  onToggleSubtask: (taskId: string, subtaskId: string) => void;
  onUpdateTask: (id: string, updates: Partial<Task>) => void;
}

export const Dashboard: React.FC<DashboardProps> = ({ 
  tasks, 
  onToggleComplete, 
  onDelete, 
  onToggleSubtask,
  onUpdateTask 
}) => {
  
  const { overdue, today, upcoming, completed, stats } = useMemo(() => {
    const now = new Date();
    const todayStart = new Date(now.setHours(0,0,0,0)).getTime();
    const todayEnd = new Date(now.setHours(23,59,59,999)).getTime();

    const overdue: Task[] = [];
    const todayTasks: Task[] = [];
    const upcoming: Task[] = [];
    const completed: Task[] = [];

    // Sort helper: Order -> Priority (High>Med>Low) -> Date
    const sorter = (a: Task, b: Task) => {
        // Primary sort: Custom Order
        if (a.order !== undefined && b.order !== undefined) {
            return a.order - b.order;
        }
        // Fallback for missing orders (shouldn't happen with new logic)
        return 0;
    };

    tasks.forEach(t => {
      if (t.isCompleted) {
        completed.push(t);
        return;
      }

      const d = t.dueDate ? new Date(t.dueDate).getTime() : null;
      
      // If no date, put in upcoming/backlog unless High Priority
      if (!d) {
        if (t.priority === 'High') todayTasks.push(t); // Treat undated High priority as "Do Today"
        else upcoming.push(t);
        return;
      }

      if (d < todayStart) overdue.push(t);
      else if (d <= todayEnd) todayTasks.push(t);
      else upcoming.push(t);
    });

    const totalActive = overdue.length + todayTasks.length;
    
    return {
      overdue: overdue.sort(sorter),
      today: todayTasks.sort(sorter),
      upcoming: upcoming.sort(sorter),
      completed: completed.sort((a,b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()),
      stats: {
        total: tasks.length,
        done: completed.length,
        percent: tasks.length === 0 ? 0 : Math.round((completed.length / tasks.length) * 100)
      }
    };
  }, [tasks]);

  const greeting = useMemo(() => {
    const hour = new Date().getHours();
    if (hour < 12) return "Good morning";
    if (hour < 18) return "Good afternoon";
    return "Good evening";
  }, []);

  // --- Drag and Drop Logic ---

  const handleDragStart = (e: React.DragEvent, id: string) => {
    e.dataTransfer.setData("text/plain", id);
    e.dataTransfer.effectAllowed = "move";
  };

  const handleDrop = (e: React.DragEvent, targetId: string | null, sectionName: 'overdue' | 'today' | 'upcoming') => {
    e.preventDefault();
    const dragId = e.dataTransfer.getData("text/plain");
    
    // Prevent dropping on self
    if (dragId === targetId) return;

    // Find the task being dragged
    const dragTask = tasks.find(t => t.id === dragId);
    if (!dragTask) return;

    const updates: Partial<Task> = {};
    const now = new Date();
    
    // 1. Determine Section updates (Dates/Priority)
    // Only update if moving to a DIFFERENT section effectively
    if (sectionName === 'today') {
        updates.dueDate = new Date().toISOString();
    } else if (sectionName === 'upcoming') {
        const tomorrow = new Date();
        tomorrow.setDate(tomorrow.getDate() + 1);
        updates.dueDate = tomorrow.toISOString();
    } else if (sectionName === 'overdue') {
        // Dragging to "Critical" means make it High Priority Today (or keep date if already overdue)
        updates.priority = Priority.High;
        if (!dragTask.dueDate || new Date(dragTask.dueDate) > now) {
            updates.dueDate = new Date().toISOString();
        }
    }

    // 2. Determine Order
    let newOrder = 0;
    const targetSectionList = sectionName === 'overdue' ? overdue 
                            : sectionName === 'today' ? today 
                            : upcoming;

    if (targetId) {
        // Dropped onto a task -> insert before it
        const targetIndex = targetSectionList.findIndex(t => t.id === targetId);
        if (targetIndex !== -1) {
            const targetTask = targetSectionList[targetIndex];
            const prevTask = targetIndex > 0 ? targetSectionList[targetIndex - 1] : null;
            
            if (prevTask) {
                newOrder = (targetTask.order + prevTask.order) / 2;
            } else {
                newOrder = targetTask.order - 1000;
            }
        }
    } else {
        // Dropped at the end of the list
        if (targetSectionList.length > 0) {
            const lastTask = targetSectionList[targetSectionList.length - 1];
            newOrder = lastTask.order + 1000;
        } else {
            newOrder = 1000;
        }
    }

    updates.order = newOrder;
    onUpdateTask(dragId, updates);
  };

  const renderSection = (title: string, list: Task[], icon: React.ReactNode, colorClass: string, sectionId: 'overdue' | 'today' | 'upcoming') => {
    if (list.length === 0 && sectionId !== 'today') return null;

    return (
        <div 
            className="animate-in fade-in slide-in-from-bottom-2 duration-500 mb-6"
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => handleDrop(e, null, sectionId)} // Handle drop on empty section
        >
             <div className={`flex items-center gap-2 mb-3 ${colorClass}`}>
                {icon}
                <h3 className="font-bold text-sm uppercase tracking-wider">{title}</h3>
                <span className={`text-xs px-2 py-0.5 rounded-full border opacity-70`}>{list.length}</span>
             </div>
             
             {list.length === 0 ? (
                 <div className="border border-dashed border-zinc-800 rounded-xl p-8 text-center text-zinc-300 italic">
                    Drag tasks here to schedule for {title.toLowerCase()}.
                 </div>
             ) : (
                 <div className="space-y-3">
                   {list.map(task => (
                     <TaskCard 
                        key={task.id} 
                        task={task} 
                        onToggleComplete={onToggleComplete} 
                        onDelete={onDelete} 
                        onToggleSubtask={onToggleSubtask}
                        isDraggable={true}
                        onDragStart={handleDragStart}
                        onDrop={(e, targetId) => handleDrop(e, targetId, sectionId)}
                     />
                   ))}
                 </div>
             )}
          </div>
    );
  };

  return (
    <div className="flex flex-col h-full overflow-hidden relative">
      
      {/* 1. Velocity Header */}
      <div className="flex-shrink-0 mb-6 px-1">
        <div className="flex justify-between items-end mb-2">
            <div>
                <h2 className="text-2xl font-bold text-zinc-100 tracking-tight">{greeting}.</h2>
                <p className="text-zinc-200 text-sm font-medium">You have <span className="text-zinc-200">{overdue.length + today.length} tasks</span> to focus on today.</p>
            </div>
            <div className="text-right">
                <span className="text-3xl font-bold text-zinc-200">{stats.percent}%</span>
            </div>
        </div>
        
        {/* Progress Bar */}
        <div className="h-2 w-full bg-zinc-800 rounded-full overflow-hidden">
            <div 
                className="h-full bg-gradient-to-r from-red-600 to-amber-600 transition-all duration-1000 ease-out"
                style={{ width: `${stats.percent}%` }}
            ></div>
        </div>
      </div>

      {/* 2. Scrollable Task Sections */}
      <div className="flex-1 overflow-y-auto pr-2 pb-20 custom-scrollbar">
        {renderSection(
            "Critical Attention", 
            overdue, 
            <AlertCircle size={18} />, 
            "text-red-400 border-red-900/30 bg-red-950/20", 
            "overdue"
        )}

        {renderSection(
            "Action Plan (Today)", 
            today, 
            <Sun size={18} />, 
            "text-amber-400 border-amber-900/30 bg-amber-950/20", 
            "today"
        )}

        {renderSection(
            "On The Horizon", 
            upcoming, 
            <Calendar size={18} />, 
            "text-zinc-200 border-zinc-700 bg-zinc-800/20", 
            "upcoming"
        )}

        {/* SECTION: COMPLETED (No DnD) */}
        {completed.length > 0 && (
            <div className="pt-8 border-t border-zinc-900 mt-8">
                <div className="flex items-center gap-2 mb-3 text-zinc-300">
                    <CheckCircle2 size={18} />
                    <h3 className="font-bold text-sm uppercase tracking-wider">Recently Completed</h3>
                </div>
                <div className="space-y-3 opacity-60 hover:opacity-100 transition-opacity">
                    {completed.slice(0, 5).map(task => (
                        <TaskCard 
                            key={task.id} 
                            task={task} 
                            onToggleComplete={onToggleComplete} 
                            onDelete={onDelete} 
                            onToggleSubtask={onToggleSubtask}
                            isDraggable={false} 
                        />
                    ))}
                    {completed.length > 5 && (
                        <div className="text-center text-xs text-zinc-200 py-2">
                            + {completed.length - 5} more completed tasks hidden
                        </div>
                    )}
                </div>
            </div>
        )}

      </div>
    </div>
  );
};

