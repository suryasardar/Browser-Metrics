import React, { useState } from 'react';
import { CheckCircle2, XCircle, ChevronDown, ChevronUp, Layers, Filter } from 'lucide-react';

export default function ResultsMatrix({ results }) {
  if (!results || results.length === 0) return null;

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-bold text-white flex items-center gap-2">
        <Layers className="w-5 h-5 text-indigo-400" />
        Data Comparison Results
      </h2>

      {results.map((res, index) => (
        <PermutationCard key={index} data={res} index={index} />
      ))}
    </div>
  );
}

function PermutationCard({ data, index }) {
  const [isOpen, setIsOpen] = useState(data.summary.status === "FAIL");

  const isPass = data.summary.status === "PASS";
  const filterKey = Object.keys(data.filters_applied)[0];
  const filterVal = data.filters_applied[filterKey];

  return (
    <div className={`border rounded-xl bg-slate-900 transition-all ${
      isPass ? "border-slate-800" : "border-rose-900/50"
    }`}>
      {/* Header */}
      <div 
        onClick={() => setIsOpen(!isOpen)}
        className="p-4 flex items-center justify-between cursor-pointer hover:bg-slate-800/40 rounded-xl"
      >
        <div className="flex items-center gap-3">
          {isPass ? (
            <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
          ) : (
            <XCircle className="w-5 h-5 text-rose-400 shrink-0" />
          )}

          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs bg-slate-800 text-slate-300 px-2 py-0.5 rounded font-medium">
                Page: {data.page}
              </span>
              <span className="text-sm font-semibold text-white flex items-center gap-1">
                <Filter className="w-3.5 h-3.5 text-indigo-400" />
                {filterKey} = <span className="text-indigo-300 font-bold">"{filterVal}"</span>
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Checked {data.summary.total_metrics_checked} metrics ({data.summary.passed_count} Passed, {data.summary.failed_count} Failed)
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <span className={`px-3 py-1 rounded-full text-xs font-bold border ${
            isPass 
              ? "bg-emerald-950/60 text-emerald-400 border-emerald-800/50" 
              : "bg-rose-950/60 text-rose-400 border-rose-800/50"
          }`}>
            {isPass ? "PASS" : `FAIL (${data.summary.failed_count} Mismatch)`}
          </span>
          {isOpen ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
        </div>
      </div>

      {/* Expanded Failure Table */}
      {isOpen && !isPass && data.failures && data.failures.length > 0 && (
        <div className="px-4 pb-4 border-t border-slate-800/60 mt-2 pt-3">
          <h4 className="text-xs font-semibold text-rose-400 uppercase tracking-wider mb-3">
            Mismatched Metrics Breakdown
          </h4>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 font-medium">
                  <th className="py-2 px-3">Metric / KPI Name</th>
                  <th className="py-2 px-3">Snowflake Value</th>
                  <th className="py-2 px-3">BigQuery Value</th>
                  <th className="py-2 px-3">Delta Difference</th>
                  <th className="py-2 px-3">Variance %</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/50">
                {data.failures.map((fail, idx) => (
                  <tr key={idx} className="hover:bg-rose-950/10">
                    <td className="py-2.5 px-3 font-medium text-slate-200">{fail.kpi_name}</td>
                    <td className="py-2.5 px-3 font-mono text-cyan-300">{fail.snowflake_value}</td>
                    <td className="py-2.5 px-3 font-mono text-blue-300">{fail.bigquery_value}</td>
                    <td className="py-2.5 px-3 font-mono text-rose-400 font-semibold">{fail.difference_delta}</td>
                    <td className="py-2.5 px-3 font-mono text-rose-400">{fail.variance_percentage}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}