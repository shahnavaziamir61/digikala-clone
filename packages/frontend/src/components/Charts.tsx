import React from 'react';

export function LineChart({ data, width = 560, height = 220, yLabel = '', color = '#4cc2ff' }: { data: [number, number][]; width?: number; height?: number; yLabel?: string; color?: string }) {
  if (!data || data.length < 2) return <div className="empty">No data</div>;
  const xs = data.map((d) => d[0]);
  const ys = data.map((d) => d[1]);
  const xMin = Math.min(...xs), xMax = Math.max(...xs);
  const yMin = Math.min(...ys), yMax = Math.max(...ys);
  const pad = 36;
  const sx = (x: number) => pad + ((x - xMin) / ((xMax - xMin) || 1)) * (width - pad - 8);
  const sy = (y: number) => height - pad - ((y - yMin) / ((yMax - yMin) || 1)) * (height - pad - 8);
  const pts = data.map((d) => `${sx(d[0]).toFixed(1)},${sy(d[1]).toFixed(1)}`).join(' ');
  return (
    <div className="chart">
      <svg width={width} height={height} role="img" aria-label="line chart">
        <line x1={pad} y1={height - pad} x2={width - 8} y2={height - pad} stroke="#334155" />
        <line x1={pad} y1={8} x2={pad} y2={height - pad} stroke="#334155" />
        <polyline points={pts} fill="none" stroke={color} strokeWidth={2} />
        <text x={pad} y={height - 8} fill="#94a3b8" fontSize={11}>{xMin.toFixed(2)}</text>
        <text x={width - 60} y={height - 8} fill="#94a3b8" fontSize={11}>{xMax.toFixed(2)}</text>
        <text x={4} y={16} fill="#94a3b8" fontSize={11}>{yLabel} max {yMax.toFixed(4)}</text>
      </svg>
    </div>
  );
}

export function ResultCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="card">
      <h3>{title}</h3>
      {children}
    </div>
  );
}

export function KV({ k, v }: { k: string; v: string }) {
  return (
    <div className="kv">
      <span>{k}</span>
      <strong>{v}</strong>
    </div>
  );
}

export function Warnings({ items }: { items: string[] }) {
  if (!items || items.length === 0) return null;
  return (
    <div className="warnings">
      {items.map((w, i) => (
        <div key={i} className="warning">⚠ {w}</div>
      ))}
    </div>
  );
}

export function LabelBadge({ label }: { label: string }) {
  const color = label === 'Validated' ? '#22c55e' : label === 'Calculated' ? '#4cc2ff' : label === 'Simulated' ? '#c084fc' : label === 'Measured' ? '#f59e0b' : '#94a3b8';
  return <span className="badge" style={{ borderColor: color, color }}>{label}</span>;
}
