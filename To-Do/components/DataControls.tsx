
import React, { useRef } from 'react';
import { Download, Upload, HardDrive, Trash } from 'lucide-react';

interface DataControlsProps {
  onExport: () => void;
  onImport: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onClear: () => void;
}

export const DataControls: React.FC<DataControlsProps> = ({ onExport, onImport, onClear }) => {
  const fileInputRef = useRef<HTMLInputElement>(null);

  return (
    <div className="bg-zinc-900 rounded-xl border border-zinc-800 p-4 mb-6 relative overflow-hidden group">
      {/* Subtle decorative background */}
      <div className="absolute top-0 right-0 w-32 h-32 bg-zinc-800/20 rounded-full blur-2xl -translate-y-1/2 translate-x-1/2 pointer-events-none"></div>

      <div className="flex items-center gap-2 mb-3 text-zinc-100 font-semibold relative z-10">
        <HardDrive size={18} className="text-zinc-200" />
        <h3>Cloud Sync & Backup</h3>
      </div>
      
      <p className="text-xs text-zinc-300 mb-4 leading-relaxed relative z-10">
        To sync between devices, use your <strong>Google Drive</strong> or <strong>OneDrive</strong>:
        <br/>
        1. <strong>Backup</strong> this list to your Drive folder.
        <br/>
        2. On your other device, <strong>Restore</strong> from that Drive file.
      </p>

      <div className="grid grid-cols-2 gap-3 relative z-10 mb-3">
        <button 
          onClick={onExport}
          className="flex flex-col items-center justify-center gap-2 bg-zinc-800 hover:bg-zinc-700 hover:border-zinc-600 text-zinc-300 text-xs font-medium py-3 px-3 rounded-lg border border-zinc-700 transition-all active:scale-95"
        >
          <Download size={16} className="text-zinc-100" />
          <span>Backup to Drive</span>
        </button>

        <button 
          onClick={() => fileInputRef.current?.click()}
          className="flex flex-col items-center justify-center gap-2 bg-zinc-800 hover:bg-zinc-700 hover:border-zinc-600 text-zinc-300 text-xs font-medium py-3 px-3 rounded-lg border border-zinc-700 transition-all active:scale-95"
        >
          <Upload size={16} className="text-zinc-100" />
          <span>Restore from Drive</span>
        </button>
        <input 
          type="file" 
          ref={fileInputRef}
          onChange={onImport}
          accept=".json"
          className="hidden"
        />
      </div>

      <button
        onClick={() => {
          if (window.confirm("Are you sure you want to delete all tasks? This cannot be undone.")) {
            onClear();
          }
        }}
        className="w-full flex items-center justify-center gap-2 text-red-400 hover:text-red-300 hover:bg-red-950/20 text-xs py-2 rounded transition-colors relative z-10"
      >
        <Trash size={12} />
        Reset / Clear All Data
      </button>
    </div>
  );
};

