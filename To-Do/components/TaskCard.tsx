
import React, { useState } from 'react';
import { Task, Priority, Subtask } from '../types';
import { Trash2, CheckCircle, Circle, ChevronDown, ChevronUp, Clock, AlertTriangle, GripVertical } from 'lucide-react';

interface TaskCardProps {
  task: Task;
  onToggleComplete: (id: string) => void;
  onDelete: (id: string) => void;
  onToggleSubtask: (taskId: string, subtaskId: string) => void;
  isDraggable?: boolean;
  onDragStart?: (e: React.DragEvent, id: string) => void;
  onDrop?: (e: React.DragEvent, targetId: string) => void;
}

// Recursive Subtask Component
const SubtaskItem: React.FC<{ 
  subtask: Subtask; 
  taskId: string; 
  onToggle: (taskId: string, subtaskId: string) => void; 
  level?: number 
}> = ({ subtask, taskId, onToggle, level = 0 }) => {
  const [isExpanded, setIsExpanded] = useState(true);
  const hasChildren = subtask.subtasks && subtask.subtasks.length > 0;

  return (
    <div className="flex flex-col">
      <div className={`flex items-start gap-3 py-1.5 ${level > 0 ? 'ml-2' : ''} group/item`}>
        {/* Indentation Visual Guide */}
        {level > 0 && (
          <div className="w-4 border-l-2 border-zinc-800 h-6 -translate-y-2 translate-x-0"></div>
        )}
        
        <button 
          onClick={() => onToggle(taskId, subtask.id)}
          className={`mt-0.5 flex-shrink-0 transition-all duration-200 ${subtask.isCompleted ? 'text-zinc-400 scale-90' : 'text-zinc-300 hover:text-green-400 hover:scale-110'}`}
        >
          {subtask.isCompleted ? <CheckCircle size={14} /> : <Circle size={14} />}
        </button>
        
        <div className="flex-1 min-w-0">
           <div className="flex items-center gap-2">
             <span 
               className={`text-sm transition-colors cursor-pointer select-none ${subtask.isCompleted ? 'line-through text-zinc-400' : 'text-zinc-300 group-hover/item:text-zinc-100'}`}
               onClick={() => hasChildren && setIsExpanded(!isExpanded)}
             >
               {subtask.title}
             </span>
             {hasChildren && (
               <button 
                 onClick={() => setIsExpanded(!isExpanded)}
                 className="text-zinc-300 hover:text-zinc-100"
               >
                 {isExpanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
               </button>
             )}
           </div>
        </div>
      </div>

      {/* Recursive Children */}
      {hasChildren && isExpanded && (
        <div className={`pl-2 ${level > 0 ? 'ml-2' : ''}`}>
          {subtask.subtasks.map(child => (
            <SubtaskItem 
              key={child.id} 
              subtask={child} 
              taskId={taskId} 
              onToggle={onToggle}
              level={level + 1}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export const TaskCard: React.FC<TaskCardProps> = ({ 
  task, 
  onToggleComplete, 
  onDelete, 
  onToggleSubtask,
  isDraggable,
  onDragStart,
  onDrop
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [isDragOver, setIsDragOver] = useState(false);

  const priorityConfig = {
    [Priority.High]: { 
        bg: 'bg-red-500/10', 
        text: 'text-red-400', 
        border: 'border-red-500/20', 
        icon: <AlertTriangle size={12} className="text-red-500" /> 
    },
    [Priority.Medium]: { 
        bg: 'bg-amber-500/10', 
        text: 'text-amber-400', 
        border: 'border-amber-500/20', 
        icon: null 
    },
    [Priority.Low]: { 
        bg: 'bg-zinc-800', 
        text: 'text-zinc-200', 
        border: 'border-zinc-700', 
        icon: null 
    },
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return null;
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return null;
    
    // Logic for "Today", "Tomorrow", etc.
    const now = new Date();
    const isToday = date.toDateString() === now.toDateString();
    const tomorrow = new Date(now);
    tomorrow.setDate(tomorrow.getDate() + 1);
    const isTomorrow = date.toDateString() === tomorrow.toDateString();

    if (isToday) return 'Today';
    if (isTomorrow) return 'Tomorrow';

    try {
      return new Intl.DateTimeFormat('en-US', { 
        month: 'short', day: 'numeric'
      }).format(date);
    } catch (e) {
      return null;
    }
  };

  const isOverdue = task.dueDate 
    && !isNaN(new Date(task.dueDate).getTime()) 
    && new Date(task.dueDate) < new Date(new Date().setHours(0,0,0,0)) 
    && !task.isCompleted;

  const counts = ((items: Subtask[]) => {
    let total = 0;
    let completed = 0;
    const count = (list: Subtask[]) => {
      for (const item of list) {
        total++;
        if (item.isCompleted) completed++;
        if (item.subtasks) count(item.subtasks);
      }
    }
    count(items);
    return { total, completed };
  })(task.subtasks);

  const pStyle = priorityConfig[task.priority];

  const handleDragStart = (e: React.DragEvent) => {
    setIsDragging(true);
    if (onDragStart) onDragStart(e, task.id);
  };

  const handleDragEnd = () => {
    setIsDragging(false);
    setIsDragOver(false);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    if (!isDraggable) return;
    setIsDragOver(true);
  };

  const handleDragLeave = () => {
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    if (onDrop) onDrop(e, task.id);
  };

  return (
    <div 
      draggable={isDraggable}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className={`
        group relative bg-zinc-900 rounded-xl border transition-all duration-300
        ${task.isCompleted ? 'border-zinc-800/50 opacity-60' : 'border-zinc-800 hover:border-zinc-600 hover:shadow-lg hover:shadow-black/20'}
        ${isOverdue && !task.isCompleted ? 'border-red-900/40' : ''}
        ${isDragging ? 'opacity-30 scale-95' : 'opacity-100'}
        ${isDragOver ? 'border-t-2 border-t-red-500 translate-y-2' : ''}
    `}>
        {/* Priority Stripe for High Priority */}
        {task.priority === Priority.High && !task.isCompleted && (
            <div className="absolute left-0 top-0 bottom-0 w-1 bg-red-600 rounded-l-xl"></div>
        )}

      <div className="p-4 flex items-start gap-4">
        {/* Drag Handle (Only visible on hover if draggable) */}
        {isDraggable && (
          <div className="mt-1.5 -ml-1 text-zinc-400 cursor-grab active:cursor-grabbing opacity-0 group-hover:opacity-100 transition-opacity">
            <GripVertical size={16} />
          </div>
        )}

        {/* Checkbox Area */}
        <button 
          onClick={() => onToggleComplete(task.id)}
          className={`
            mt-1 flex-shrink-0 transition-all duration-300 transform
            ${task.isCompleted 
                ? 'text-zinc-400'
                : 'text-zinc-300 hover:text-green-400 hover:scale-110 active:scale-95'
            }
          `}
        >
          {task.isCompleted ? <CheckCircle size={24} className="opacity-50" /> : <Circle size={24} />}
        </button>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex justify-between items-start gap-2">
            <h3 className={`font-medium text-base leading-snug break-words transition-colors ${task.isCompleted ? 'line-through text-zinc-400' : 'text-zinc-100 group-hover:text-white'}`}>
              {task.title}
            </h3>
            
            {/* Action Menu (Visible on Hover) */}
            <button 
              onClick={() => onDelete(task.id)}
              className="text-zinc-300 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-all p-1 hover:bg-zinc-800 rounded"
              title="Delete Task"
            >
              <Trash2 size={16} />
            </button>
          </div>

          {/* Meta Badges */}
          <div className="flex flex-wrap gap-2 mt-2.5 items-center">
            
            {/* Category */}
            <span className="text-[10px] uppercase tracking-wider font-semibold px-2 py-0.5 rounded text-zinc-200 bg-zinc-800/50 border border-zinc-800/50">
                {task.category}
            </span>

            {/* Date */}
            {task.dueDate && (
              <span className={`text-xs px-2 py-0.5 rounded-full border flex items-center gap-1.5 font-medium ${isOverdue ? 'bg-red-950/30 text-red-400 border-red-900/50' : 'bg-zinc-800/50 text-zinc-200 border-zinc-800'}`}>
                <Clock size={11} />
                {formatDate(task.dueDate)}
              </span>
            )}

            {/* Priority (Only show if High or Medium) */}
            {task.priority !== Priority.Low && (
                 <span className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded border flex items-center gap-1 ${pStyle.bg} ${pStyle.text} ${pStyle.border}`}>
                    {pStyle.icon}
                    {task.priority}
                 </span>
            )}
            
          </div>

          {/* Description & Subtasks Toggle */}
          {(task.description || task.subtasks.length > 0) && (
            <div className="mt-3 pt-2 border-t border-zinc-800/50">
              <button 
                onClick={() => setIsExpanded(!isExpanded)}
                className="text-xs text-zinc-300 font-medium hover:text-zinc-100 flex items-center gap-1.5 transition-colors"
              >
                {isExpanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                {counts.total > 0 
                    ? `${counts.completed}/${counts.total} Subtasks` 
                    : (isExpanded ? 'Hide Note' : 'Show Note')}
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Expanded View */}
      {isExpanded && (
        <div className="px-4 pb-4 pt-0 ml-11">
          {task.description && (
            <div className="text-sm text-zinc-200 mb-3 pl-3 border-l-2 border-zinc-700 italic">
              {task.description}
            </div>
          )}
          
          {task.subtasks.length > 0 && (
            <div className="mt-2 space-y-1">
              {task.subtasks.map(sub => (
                <SubtaskItem 
                  key={sub.id} 
                  subtask={sub} 
                  taskId={task.id} 
                  onToggle={onToggleSubtask}
                />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};



