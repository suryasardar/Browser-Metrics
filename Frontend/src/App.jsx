import React, { useState } from 'react';
import { Play, Database, RefreshCw, Activity } from 'lucide-react';
import PerformanceCard from './components/PerformanceCard';
import WarningsBanner from './components/WarningsBanner';
import LiveConsole from './components/LiveConsole';
import ResultsMatrix from './components/ResultsMatrix';

export default function App() {
  const [sourceUrl, setSourceUrl] = useState('');
  const [targetUrl, setTargetUrl] = useState('')
  const [isTesting, setIsTesting] = useState(false);

  const [logs, setLogs] = useState([]);
  const [warnings, setWarnings] = useState([]);
  const [performance, setPerformance] = useState(null);
  const [results, setResults] = useState([]);

  const handleStartValidation = () => {
    if (!sourceUrl || !targetUrl) {
      alert("Please enter both Snowflake and BigQuery Power BI URLs.");
      return;
    }

    // Reset State
    setIsTesting(true);
    setLogs([]);
    setWarnings([]);
    setPerformance(null);
    setResults([]);

    const ws = new WebSocket("ws://127.0.0.1:8000/ws/validate");

    ws.onopen = () => {
      ws.send(JSON.stringify({ source_url: sourceUrl, target_url: targetUrl }));
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.event === "INFO") {
        setLogs((prev) => [...prev, { type: "info", msg: data.message }]);
      } else if (data.event === "WARNING") {
        setLogs((prev) => [...prev, { type: "warning", msg: data.message }]);
        setWarnings((prev) => [...prev, data.message]);
      } else if (data.event === "PERFORMANCE") {
        setLogs((prev) => [...prev, { type: "info", msg: data.message }]);
        setPerformance({
          snowflake: data.snowflake_time,
          bigquery: data.bigquery_time,
        });
      } else if (data.event === "FILTER_PERMUTATION_RESULT") {
        setResults((prev) => [...prev, data]);
      } else if (data.event === "COMPLETE") {
        setLogs((prev) => [...prev, { type: "complete", msg: data.message }]);
        setIsTesting(false);
        ws.close();
      } else if (data.event === "ERROR") {
        setLogs((prev) => [...prev, { type: "error", msg: `Error: ${data.message}` }]);
        setIsTesting(false);
        ws.close();
      }
    };

    ws.onerror = () => {
      setLogs((prev) => [...prev, { type: "error", msg: "Failed to connect to backend server at ws://127.0.0.1:8000" }]);
      setIsTesting(false);
    };
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* Header */}
      <header className="flex items-center justify-between pb-6 border-b border-slate-800 mb-8">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-indigo-600/20 border border-indigo-500/30 rounded-xl text-indigo-400">
            <Activity className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white tracking-tight">Power BI QA Agent</h1>
            <p className="text-xs text-slate-400">Automated Data Migration Validation: Snowflake vs. BigQuery</p>
          </div>
        </div>
      </header>

      {/* Input Form */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 mb-8 shadow-lg">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <div>
            <label className="block text-xs font-semibold text-cyan-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
              <Database className="w-3.5 h-3.5" /> Snowflake Dashboard URL (Source)
            </label>
            <input
              type="text"
              placeholder="https://app.powerbi.com/groups/.../reports/..."
              value={sourceUrl}
              onChange={(e) => setSourceUrl(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3.5 py-2 text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-blue-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
              <Database className="w-3.5 h-3.5" /> BigQuery Dashboard URL (Target)
            </label>
            <input
              type="text"
              placeholder="https://app.powerbi.com/groups/.../reports/..."
              value={targetUrl}
              onChange={(e) => setTargetUrl(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3.5 py-2 text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:border-indigo-500"
            />
          </div>
        </div>

        <button
          onClick={handleStartValidation}
          disabled={isTesting}
          className="w-full mt-2 bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 disabled:text-slate-500 text-white font-semibold py-2.5 rounded-lg transition-colors flex items-center justify-center gap-2 shadow-lg shadow-indigo-950/50"
        >
          {isTesting ? (
            <>
              <RefreshCw className="w-4 h-4 animate-spin" />
              <span>Validation Suite Running...</span>
            </>
          ) : (
            <>
              <Play className="w-4 h-4 fill-current" />
              <span>Run Automated QA Suite</span>
            </>
          )}
        </button>
      </div>

      {/* Dynamic Results Sections */}
      <PerformanceCard performance={performance} />
      <WarningsBanner warnings={warnings} />
      <LiveConsole logs={logs} isTesting={isTesting} />
      <ResultsMatrix results={results} />
    </div>
  );
}