import React from 'react';
import { Gauge, ArrowRight } from 'lucide-react';

export default function PerformanceCard({ performance }) {
  if (!performance) return null;

  const { snowflake, bigquery } = performance;
  const winner = snowflake < bigquery ? 'Snowflake' : 'BigQuery';
  const diff = Math.abs(snowflake - bigquery).toFixed(2);

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg mb-6">
      <div className="flex items-center gap-2 mb-4">
        <Gauge className="w-5 h-5 text-indigo-400" />
        <h2 className="text-lg font-semibold text-white">Dashboard Performance Check</h2>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Snowflake Card */}
        <div className="bg-slate-950/60 border border-slate-800/80 rounded-lg p-4 flex justify-between items-center">
          <div>
            <p className="text-xs font-semibold text-cyan-400 uppercase tracking-wider">Snowflake Dashboard</p>
            <p className="text-2xl font-bold text-white mt-1">{snowflake} <span className="text-sm font-normal text-slate-400">sec</span></p>
          </div>
          <span className="text-xs bg-cyan-950 text-cyan-300 px-2.5 py-1 rounded-full border border-cyan-800/50">Source</span>
        </div>

        {/* BigQuery Card */}
        <div className="bg-slate-950/60 border border-slate-800/80 rounded-lg p-4 flex justify-between items-center">
          <div>
            <p className="text-xs font-semibold text-blue-400 uppercase tracking-wider">BigQuery Dashboard</p>
            <p className="text-2xl font-bold text-white mt-1">{bigquery} <span className="text-sm font-normal text-slate-400">sec</span></p>
          </div>
          <span className="text-xs bg-blue-950 text-blue-300 px-2.5 py-1 rounded-full border border-blue-800/50">Target</span>
        </div>
      </div>

      <div className="mt-3 text-xs text-slate-400 flex items-center gap-1.5">
        <span>⚡ <strong>{winner}</strong> loaded <strong>{diff}s</strong> faster.</span>
      </div>
    </div>
  );
}