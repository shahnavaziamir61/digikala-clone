import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
export function LineChart({ data, width = 560, height = 220, yLabel = '', color = '#4cc2ff' }) {
    if (!data || data.length < 2)
        return _jsx("div", { className: "empty", children: "No data" });
    const xs = data.map((d) => d[0]);
    const ys = data.map((d) => d[1]);
    const xMin = Math.min(...xs), xMax = Math.max(...xs);
    const yMin = Math.min(...ys), yMax = Math.max(...ys);
    const pad = 36;
    const sx = (x) => pad + ((x - xMin) / ((xMax - xMin) || 1)) * (width - pad - 8);
    const sy = (y) => height - pad - ((y - yMin) / ((yMax - yMin) || 1)) * (height - pad - 8);
    const pts = data.map((d) => `${sx(d[0]).toFixed(1)},${sy(d[1]).toFixed(1)}`).join(' ');
    return (_jsx("div", { className: "chart", children: _jsxs("svg", { width: width, height: height, role: "img", "aria-label": "line chart", children: [_jsx("line", { x1: pad, y1: height - pad, x2: width - 8, y2: height - pad, stroke: "#334155" }), _jsx("line", { x1: pad, y1: 8, x2: pad, y2: height - pad, stroke: "#334155" }), _jsx("polyline", { points: pts, fill: "none", stroke: color, strokeWidth: 2 }), _jsx("text", { x: pad, y: height - 8, fill: "#94a3b8", fontSize: 11, children: xMin.toFixed(2) }), _jsx("text", { x: width - 60, y: height - 8, fill: "#94a3b8", fontSize: 11, children: xMax.toFixed(2) }), _jsxs("text", { x: 4, y: 16, fill: "#94a3b8", fontSize: 11, children: [yLabel, " max ", yMax.toFixed(4)] })] }) }));
}
export function ResultCard({ title, children }) {
    return (_jsxs("div", { className: "card", children: [_jsx("h3", { children: title }), children] }));
}
export function KV({ k, v }) {
    return (_jsxs("div", { className: "kv", children: [_jsx("span", { children: k }), _jsx("strong", { children: v })] }));
}
export function Warnings({ items }) {
    if (!items || items.length === 0)
        return null;
    return (_jsx("div", { className: "warnings", children: items.map((w, i) => (_jsxs("div", { className: "warning", children: ["\u26A0 ", w] }, i))) }));
}
export function LabelBadge({ label }) {
    const color = label === 'Validated' ? '#22c55e' : label === 'Calculated' ? '#4cc2ff' : label === 'Simulated' ? '#c084fc' : label === 'Measured' ? '#f59e0b' : '#94a3b8';
    return _jsx("span", { className: "badge", style: { borderColor: color, color }, children: label });
}
