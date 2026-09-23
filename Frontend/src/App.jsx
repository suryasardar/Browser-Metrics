import React, { useState } from 'react';
import { Play, Database, RefreshCw, Activity, Clock, Filter, Zap, Sun, Moon } from 'lucide-react';
import WarningsBanner from './components/WarningsBanner';
import LiveConsole from './components/LiveConsole';

function FilterTestRow({ test }) {
  const ok = test.status === "OK" || typeof test.refresh_seconds === 'number';
  
  return (
    <div className="flex items-center justify-between text-xs py-2 border-b border-neutral-800/60 last:border-0">
      <div className="flex items-center gap-2 text-neutral-300 truncate pr-2">
        <div className={`w-2 h-2 rounded-full shrink-0 ${ok ? 'bg-emerald-500' : 'bg-yellow-400'}`} />
        <span className="truncate font-medium">
          {test.filter_name}
          {test.selected_option ? ` = ${test.selected_option}` : ''}
        </span>
      </div>
      <span className={`font-mono shrink-0 ${ok ? 'text-neutral-100' : 'text-neutral-300'}`}>
        {ok && test.refresh_seconds ? `${test.refresh_seconds}s` : test.status}
      </span>
    </div>
  );
}

function MetricsCard({ metrics, title }) {
  if (!metrics) return null;

  return (
    <div className="bg-[#111111] border border-neutral-800 rounded-lg p-5 flex-1 min-w-[300px]">
      <h3 className="text-xs font-bold text-yellow-400 uppercase tracking-wider mb-5 flex items-center gap-2">
        <Database className="w-4 h-4" /> {title || metrics.dashboard}
      </h3>

      <div className="space-y-4 text-sm">
        <div className="flex items-center justify-between">
          <span className="text-neutral-400 flex items-center gap-2"><Clock className="w-4 h-4" /> Load time</span>
          <span className="text-neutral-100 font-mono font-medium">{metrics.load_time_seconds}s</span>
        </div>

        <div className="flex items-center justify-between">
          <span className="text-neutral-400 flex items-center gap-2"><Filter className="w-4 h-4" /> Filters found</span>
          <span className="text-neutral-100 font-mono font-medium">{metrics.filter_count}</span>
        </div>

        <div className="flex items-center justify-between pb-3 border-b border-neutral-800/80">
          <span className="text-neutral-400 flex items-center gap-2"><Zap className="w-4 h-4" /> Avg refresh time</span>
          <span className="text-neutral-100 font-mono font-medium">
            {metrics.avg_refresh_seconds !== null ? `${metrics.avg_refresh_seconds}s` : '—'}
          </span>
        </div>

        {metrics.filter_tests?.length > 0 && (
          <div className="pt-1">
            <div className="text-neutral-500 text-xs mb-2">Sampled filter tests</div>
            {metrics.filter_tests.map((t, i) => (
              <FilterTestRow key={i} test={t} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default function App() {
  const [sourceUrl, setSourceUrl] = useState('');
  const [targetUrl, setTargetUrl] = useState('');
  const [isTesting, setIsTesting] = useState(false);

  const [logs, setLogs] = useState([]);
  const [warnings, setWarnings] = useState([]);
  const [sourceMetrics, setSourceMetrics] = useState(null);
  const [targetMetrics, setTargetMetrics] = useState(null);

  const handleStartValidation = () => {
    if (!sourceUrl || !targetUrl) {
      alert("Please enter both Snowflake and BigQuery Power BI URLs.");
      return;
    }

    setIsTesting(true);
    setLogs([]);
    setWarnings([]);
    setSourceMetrics(null);
    setTargetMetrics(null);

    const ws = new WebSocket("ws://127.0.0.1:8000/ws/validate");

    ws.onopen = () => {
      ws.send(JSON.stringify({ source_url: sourceUrl, target_url: targetUrl }));
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.event === "INFO" || data.event === "PERFORMANCE") {
        setLogs((prev) => [...prev, { type: "info", msg: data.message }]);
      } else if (data.event === "WARNING") {
        setLogs((prev) => [...prev, { type: "warning", msg: data.message }]);
        setWarnings((prev) => [...prev, data.message]);
      } else if (data.event === "METRICS") {
        setLogs((prev) => [...prev, { type: "info", msg: data.message }]);
        if (data.dashboard?.includes("Snowflake")) {
          setSourceMetrics(data);
        } else if (data.dashboard?.includes("BigQuery")) {
          setTargetMetrics(data);
        }
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
    <div className="min-h-screen bg-[#0a0a0a] text-neutral-200 p-8 font-sans">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <header className="flex items-center justify-between mb-8 pb-4 border-b border-neutral-800/50">
          <div className="flex items-center gap-4">
            <div className="p-2.5 bg-yellow-400 rounded text-black shadow-sm">
              <Activity className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white tracking-tight">Power BI QA Agent</h1>
              <p className="text-sm text-neutral-400 mt-0.5">Load Time & Filter Refresh Metrics</p>
            </div>
          </div>
          
          <div className="flex items-center gap-2 bg-[#111111] border border-neutral-800 rounded-full p-1">
            <button className="p-2 rounded-full text-neutral-400 hover:text-white transition-colors"><Sun className="w-4 h-4" /></button>
            <button className="p-2 rounded-full bg-yellow-400 text-black"><Moon className="w-4 h-4" /></button>
          </div>
        </header>

        {/* Input Form */}
        <div className="bg-[#111111] border border-neutral-800 rounded-lg p-6 mb-8">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            <div>
              <label className="block text-xs font-bold text-yellow-400 mb-2">
                Snowflake Dashboard URL (Source)
              </label>
              <input
                type="text"
                placeholder="https://app.powerbi.com/groups/..."
                value={sourceUrl}
                onChange={(e) => setSourceUrl(e.target.value)}
                className="w-full bg-[#1a1a1a] border border-neutral-800 rounded-md px-4 py-2.5 text-sm text-neutral-200 placeholder-neutral-600 focus:outline-none focus:border-yellow-400 font-mono transition-colors"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-yellow-400 mb-2">
                BigQuery Dashboard URL (Target)
              </label>
              <input
                type="text"
                placeholder="https://app.powerbi.com/groups/..."
                value={targetUrl}
                onChange={(e) => setTargetUrl(e.target.value)}
                className="w-full bg-[#1a1a1a] border border-neutral-800 rounded-md px-4 py-2.5 text-sm text-neutral-200 placeholder-neutral-600 focus:outline-none focus:border-yellow-400 font-mono transition-colors"
              />
            </div>
          </div>

          <button
            onClick={handleStartValidation}
            disabled={isTesting}
            className="w-full bg-yellow-400 hover:bg-yellow-500 disabled:bg-neutral-800 disabled:text-neutral-500 text-black font-bold py-3 rounded-md transition-all flex items-center justify-center gap-2 shadow-[0_0_15px_rgba(250,204,21,0.15)] disabled:shadow-none"
          >
            {isTesting ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span>Collecting Metrics...</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-current" />
                <span>Run Metrics Check</span>
              </>
            )}
          </button>
        </div>

        {/* Metrics */}
        <div className="flex flex-col md:flex-row gap-6 mb-8">
          <MetricsCard metrics={sourceMetrics} title="SNOWFLAKE (SOURCE)" />
          <MetricsCard metrics={targetMetrics} title="BIGQUERY (TARGET)" />
        </div>

        <WarningsBanner warnings={warnings} />
        <LiveConsole logs={logs} isTesting={isTesting} />
      </div>
    </div>
  );
}