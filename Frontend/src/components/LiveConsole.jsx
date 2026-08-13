import React, { useEffect, useRef } from 'react';
import { Terminal, CheckCircle2, AlertCircle, Info, Loader2 } from 'lucide-react';

export default function LiveConsole({ logs, isTesting }) {
  const logEndRef = useRef(null);

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  if (logs.length === 0) return null;

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 mb-6 shadow-lg">
      <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-3">
        <div className="flex items-center gap-2 text-slate-300 font-medium text-sm">
          <Terminal className="w-4 h-4 text-emerald-400" />
          <span>Live Execution Console</span>
        </div>
        {isTesting && (
          <div className="flex items-center gap-2 text-xs text-indigo-400 bg-indigo-950/60 px-2.5 py-1 rounded-full border border-indigo-800/50">
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
            <span>Agent Running...</span>
          </div>
        )}
      </div>

      <div className="bg-slate-950 rounded-lg p-3 font-mono text-xs max-h-48 overflow-y-auto space-y-2 border border-slate-800/60">
        {logs.map((log, index) => {
          let color = "text-slate-300";
          let Icon = Info;

          if (log.type === "warning") {
            color = "text-amber-400";
            Icon = AlertCircle;
          } else if (log.type === "complete") {
            color = "text-emerald-400 font-semibold";
            Icon = CheckCircle2;
          } else if (log.type === "error") {
            color = "text-rose-400 font-semibold";
            Icon = AlertCircle;
          }

          return (
            <div key={index} className={`flex items-start gap-2 ${color}`}>
              <Icon className="w-3.5 h-3.5 mt-0.5 shrink-0" />
              <span>{log.msg}</span>
            </div>
          );
        })}
        <div ref={logEndRef} />
      </div>
    </div>
  );
}