import React from 'react';
import { AlertTriangle } from 'lucide-react';

export default function WarningsBanner({ warnings }) {
  if (!warnings || warnings.length === 0) return null;

  return (
    <div className="bg-amber-950/30 border border-amber-500/30 rounded-xl p-4 mb-6">
      <div className="flex items-center gap-2 mb-2 text-amber-400 font-semibold">
        <AlertTriangle className="w-5 h-5 text-amber-400" />
        <h3>UI & Schema Mismatches Detected ({warnings.length})</h3>
      </div>
      <ul className="space-y-1.5 pl-7 list-disc text-sm text-amber-200/90">
        {warnings.map((warn, idx) => (
          <li key={idx}>{warn}</li>
        ))}
      </ul>
    </div>
  );
}