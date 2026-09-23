import React, { useState } from 'react';

const THEME_CSS = `
  .qa-app {
    --bg: #0B0B0C;
    --surface: #141414;
    --surface-2: #1B1B1C;
    --border: #2A2A28;
    --text: #F2F1E8;
    --text-dim: #9A988E;
    --yellow: #F4C21A;
    --yellow-dim: #8A7314;
    --danger-bg: #241B0A;
    --danger-border: #4A3A10;
    --ok: #7FB88A;
    --radius: 3px;
    background: var(--bg);
    color: var(--text);
    font-family: 'Space Grotesk', system-ui, sans-serif;
    min-height: 100vh;
    transition: background .25s ease, color .25s ease;
  }
  .qa-app[data-theme="light"] {
    --bg: #FAF9F4;
    --surface: #FFFFFF;
    --surface-2: #F3F1E8;
    --border: #E3E0D2;
    --text: #17160F;
    --text-dim: #6E6C5F;
    --yellow: #B9860A;
    --yellow-dim: #E8C55A;
    --danger-bg: #FFF6E0;
    --danger-border: #E9D08A;
    --ok: #3F7A4C;
  }
  .qa-app .mono { font-family: 'IBM Plex Mono', ui-monospace, monospace; }
  .qa-wrap { max-width: 1040px; margin: 0 auto; padding: 32px 20px 64px; }
  .qa-header { display: flex; align-items: flex-start; justify-content: space-between; padding-bottom: 24px; border-bottom: 1px solid var(--border); margin-bottom: 28px; }
  .qa-brand { display: flex; align-items: center; gap: 14px; }
  .qa-mark { width: 42px; height: 42px; border-radius: var(--radius); background: var(--yellow); color: var(--bg); display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
  .qa-mark svg { width: 22px; height: 22px; }
  .qa-h1 { font-size: 21px; font-weight: 700; margin: 0; letter-spacing: -0.01em; }
  .qa-sub { font-size: 12.5px; color: var(--text-dim); margin-top: 3px; }
  .qa-toggle { display: flex; align-items: center; gap: 8px; border: 1px solid var(--border); border-radius: 20px; padding: 4px; background: var(--surface); cursor: pointer; }
  .qa-pill { width: 30px; height: 30px; border-radius: 50%; display: flex; align-items: center; justify-content: center; transition: background .2s ease, color .2s ease; color: var(--text-dim); }
  .qa-pill svg { width: 15px; height: 15px; }
  .qa-pill.active { background: var(--yellow); color: var(--bg); }
  .qa-panel { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 22px; margin-bottom: 22px; }
  .qa-grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
  @media (max-width: 720px) { .qa-grid-2 { grid-template-columns: 1fr; } }
  .qa-label { display: block; font-size: 11px; font-weight: 600; letter-spacing: .02em; color: var(--yellow); margin-bottom: 8px; }
  .qa-input { width: 100%; background: var(--surface-2); border: 1px solid var(--border); border-radius: var(--radius); color: var(--text); padding: 10px 12px; font-family: 'IBM Plex Mono', monospace; font-size: 12.5px; outline: none; transition: border-color .15s ease, box-shadow .15s ease; }
  .qa-input::placeholder { color: var(--text-dim); opacity: .6; }
  .qa-input:focus { border-color: var(--yellow); box-shadow: 0 0 0 3px color-mix(in srgb, var(--yellow) 18%, transparent); }
  .qa-run { width: 100%; margin-top: 16px; background: var(--yellow); color: var(--bg); border: none; border-radius: var(--radius); font-family: inherit; font-weight: 700; font-size: 14px; padding: 13px; cursor: pointer; position: relative; overflow: hidden; display: flex; align-items: center; justify-content: center; gap: 9px; transition: transform .12s ease, box-shadow .2s ease; }
  .qa-run::before { content: ""; position: absolute; inset: 0; background: linear-gradient(120deg, transparent, rgba(0,0,0,.14), transparent); transform: translateX(-120%); transition: transform .5s ease; }
  .qa-run:hover::before { transform: translateX(120%); }
  .qa-run:hover { box-shadow: 0 6px 20px -6px color-mix(in srgb, var(--yellow) 55%, transparent); transform: translateY(-1px); }
  .qa-run:disabled { opacity: .6; cursor: not-allowed; }
  .qa-run svg { width: 15px; height: 15px; }
  .qa-metrics-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 22px; }
  @media (max-width: 720px) { .qa-metrics-grid { grid-template-columns: 1fr; } }
  .qa-card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 20px; transition: border-color .2s ease, transform .2s ease, box-shadow .2s ease; }
  .qa-card:hover { border-color: var(--yellow-dim); transform: translateY(-3px); box-shadow: 0 12px 28px -14px rgba(0,0,0,.4); }
  .qa-card h3 { font-size: 12px; font-weight: 700; letter-spacing: .03em; color: var(--yellow); margin: 0 0 16px; display: flex; align-items: center; gap: 7px; }
  .qa-card h3 svg { width: 13px; height: 13px; }
  .qa-row { display: flex; align-items: center; justify-content: space-between; padding: 7px 0; font-size: 13.5px; }
  .qa-row .k { color: var(--text-dim); display: flex; align-items: center; gap: 7px; }
  .qa-row .k svg { width: 13px; height: 13px; opacity: .8; }
  .qa-row .v { font-family: 'IBM Plex Mono', monospace; font-weight: 500; }
  .qa-divider { border-top: 1px solid var(--border); margin: 12px 0 8px; }
  .qa-subhead { font-size: 11px; color: var(--text-dim); margin-bottom: 6px; }
  .qa-test-row { display: flex; align-items: center; justify-content: space-between; padding: 8px 6px; margin: 0 -6px; font-size: 12.5px; border-radius: var(--radius); transition: background .15s ease; }
  .qa-test-row:hover { background: var(--surface-2); }
  .qa-test-row .name { display: flex; align-items: center; gap: 7px; overflow: hidden; }
  .qa-test-row .name span { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .qa-test-row .val { font-family: 'IBM Plex Mono', monospace; flex-shrink: 0; padding-left: 10px; }
  .qa-dot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }
  .qa-dot.ok { background: var(--ok); }
  .qa-dot.fail { background: var(--yellow); }
  .qa-empty { color: var(--text-dim); font-size: 12.5px; font-style: italic; padding: 8px 0; }
  .qa-warn-banner { background: var(--danger-bg); border: 1px solid var(--danger-border); border-radius: var(--radius); padding: 18px 20px; margin-bottom: 22px; }
  .qa-warn-title { display: flex; align-items: center; gap: 9px; font-weight: 700; font-size: 13.5px; color: var(--yellow); margin-bottom: 10px; }
  .qa-warn-title svg { width: 15px; height: 15px; }
  .qa-warn-banner ul { margin: 0; padding-left: 20px; }
  .qa-warn-banner li { font-size: 12.5px; color: var(--text); opacity: .85; margin-bottom: 6px; font-family: 'IBM Plex Mono', monospace; transition: opacity .15s ease; }
  .qa-warn-banner li:hover { opacity: 1; }
  .qa-console { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); overflow: hidden; }
  .qa-console-head { display: flex; align-items: center; gap: 9px; padding: 14px 18px; font-weight: 700; font-size: 13px; cursor: pointer; user-select: none; }
  .qa-console-head svg.chev { width: 13px; height: 13px; color: var(--yellow); transition: transform .2s ease; }
  .qa-console-head.open svg.chev { transform: rotate(90deg); }
  .qa-console-body { padding: 0 18px 16px; max-height: 260px; overflow-y: auto; }
  .qa-log-line { font-family: 'IBM Plex Mono', monospace; font-size: 11.5px; padding: 4px 0; color: var(--text-dim); border-bottom: 1px solid var(--border); }
  .qa-log-line:last-child { border-bottom: none; }
  .qa-log-line.complete { color: var(--ok); }
  .qa-log-line.warning { color: var(--yellow); }
  .qa-log-line.error { color: #E0554A; }
  @media (prefers-reduced-motion: reduce) { .qa-app *, .qa-app *::before, .qa-app *::after { transition: none !important; animation: none !important; } }
`;

function ClockIcon() { return <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 3"/></svg>; }
function FilterIcon() { return <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M4 5h16l-6 8v6l-4 2v-8z"/></svg>; }
function ZapIcon() { return <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M13 2 4 14h6l-1 8 9-12h-6z"/></svg>; }
function DbIcon() { return <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="4" width="18" height="4" rx="1"/><rect x="3" y="10" width="18" height="10" rx="1"/></svg>; }
function WarnIcon() { return <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 2 1 21h22z"/><path d="M12 9v5M12 17h.01"/></svg>; }
function ChevIcon() { return <svg className="chev" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4"><path d="M9 6l6 6-6 6"/></svg>; }
function PlayIcon() { return <svg viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>; }
function SpinIcon() { return <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" style={{ animation: 'spin .7s linear infinite' }}><path d="M21 12a9 9 0 1 1-3-6.7"/></svg>; }
function SunIcon() { return <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>; }
function MoonIcon() { return <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>; }

function MetricsCard({ metrics }) {
  if (!metrics) return null;
  return (
    <div className="qa-card">
      <h3><DbIcon /> {metrics.dashboard}</h3>
      <div className="qa-row"><span className="k"><ClockIcon /> Load time</span><span className="v">{metrics.load_time_seconds}s</span></div>
      <div className="qa-row"><span className="k"><FilterIcon /> Filters found</span><span className="v">{metrics.filter_count}</span></div>
      <div className="qa-row">
        <span className="k"><ZapIcon /> Avg render time</span>
        <span className="v">{metrics.avg_refresh_seconds !== null && metrics.avg_refresh_seconds !== undefined ? `${metrics.avg_refresh_seconds}s` : '—'}</span>
      </div>
      {metrics.filter_tests?.length > 0 && (
        <>
          <div className="qa-divider"></div>
          <div className="qa-subhead">Sampled filter tests</div>
          {metrics.filter_tests.map((t, i) => (
            <div className="qa-test-row" key={i}>
              <div className="name">
                <span className={`qa-dot ${t.status === 'OK' ? 'ok' : 'fail'}`}></span>
                <span>{t.filter_name}{t.selected_option ? ` = ${t.selected_option}` : ''}</span>
              </div>
              <div className="val">{t.status === 'OK' ? `${t.refresh_seconds}s` : t.status}</div>
            </div>
          ))}
        </>
      )}
    </div>
  );
}

function WarningsPanel({ warnings }) {
  if (!warnings || warnings.length === 0) return null;
  return (
    <div className="qa-warn-banner">
      <div className="qa-warn-title"><WarnIcon /> UI &amp; Schema Mismatches Detected ({warnings.length})</div>
      <ul>{warnings.map((w, i) => <li key={i}>{w}</li>)}</ul>
    </div>
  );
}

function ConsolePanel({ logs, isTesting }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="qa-console">
      <div className={`qa-console-head ${open ? 'open' : ''}`} onClick={() => setOpen(!open)}>
        <ChevIcon /> Live Execution Console{isTesting ? ' · running' : ''}
      </div>
      {open && (
        <div className="qa-console-body">
          {logs.length === 0 ? (
            <div className="qa-empty">No output yet.</div>
          ) : (
            logs.map((l, i) => <div className={`qa-log-line ${l.type}`} key={i}>{l.msg}</div>)
          )}
        </div>
      )}
    </div>
  );
}

export default function App() {
  const [theme, setTheme] = useState(() => {
    try {
      return localStorage.getItem('qa-agent-theme') || 'dark';
    } catch {
      return 'dark';
    }
  });

  const [sourceUrl, setSourceUrl] = useState('');
  const [targetUrl, setTargetUrl] = useState('');
  const [isTesting, setIsTesting] = useState(false);

  const [logs, setLogs] = useState([]);
  const [warnings, setWarnings] = useState([]);
  const [sourceMetrics, setSourceMetrics] = useState(null);
  const [targetMetrics, setTargetMetrics] = useState(null);

  const toggleTheme = () => {
    const next = theme === 'light' ? 'dark' : 'light';
    setTheme(next);
    try { localStorage.setItem('qa-agent-theme', next); } catch { /* Ignore storage errors. */ }
  };

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
    <div className="qa-app" data-theme={theme}>
      <style>{THEME_CSS}</style>
      <div className="qa-wrap">

        <header className="qa-header">
          <div className="qa-brand">
            <div className="qa-mark">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round"><path d="M3 12h4l3 8 4-16 3 8h4"/></svg>
            </div>
            <div>
              <h1 className="qa-h1">Performance Tracker</h1>
              <div className="qa-sub">Load Time &amp; Render Time Metrics</div>
            </div>
          </div>
          <div className="qa-toggle" onClick={toggleTheme} role="button" aria-label="Toggle theme">
            <div className={`qa-pill ${theme === 'light' ? 'active' : ''}`}><SunIcon /></div>
            <div className={`qa-pill ${theme === 'dark' ? 'active' : ''}`}><MoonIcon /></div>
          </div>
        </header>

        <div className="qa-panel">
          <div className="qa-grid-2">
            <div>
              <label className="qa-label">Snowflake Dashboard URL (Source)</label>
              <input
                type="text"
                className="qa-input"
                placeholder="https://app.powerbi.com/groups/.../reports/..."
                value={sourceUrl}
                onChange={(e) => setSourceUrl(e.target.value)}
              />
            </div>
            <div>
              <label className="qa-label">BigQuery Dashboard URL (Target)</label>
              <input
                type="text"
                className="qa-input"
                placeholder="https://app.powerbi.com/groups/.../reports/..."
                value={targetUrl}
                onChange={(e) => setTargetUrl(e.target.value)}
              />
            </div>
          </div>
          <button className="qa-run" onClick={handleStartValidation} disabled={isTesting}>
            {isTesting ? <><SpinIcon /> Collecting Metrics...</> : <><PlayIcon /> Run Metrics Check</>}
          </button>
        </div>

        <div className="qa-metrics-grid">
          <MetricsCard metrics={sourceMetrics} />
          <MetricsCard metrics={targetMetrics} />
        </div>

        <WarningsPanel warnings={warnings} />
        <ConsolePanel logs={logs} isTesting={isTesting} />

      </div>
    </div>
  );
}