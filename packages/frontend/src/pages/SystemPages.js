import { jsx as _jsx, jsxs as _jsxs, Fragment as _Fragment } from "react/jsx-runtime";
import { useEffect, useState } from 'react';
import { api } from '../api.js';
import { ResultCard, KV, Warnings, LabelBadge } from '../components/Charts.js';
import { t } from '../i18n.js';
export function Dashboard({ lang, onOpen }) {
    const [health, setHealth] = useState('');
    const [checks, setChecks] = useState([]);
    const [cad, setCad] = useState(null);
    useEffect(() => {
        api.health().then((h) => setHealth(h.ok ? 'OK' : '—')).catch(() => setHealth('backend offline'));
        api.validationSuite().then((c) => setChecks(c)).catch(() => { });
        api.cadStatus().then((c) => setCad(c)).catch(() => { });
    }, []);
    const pass = checks.filter((c) => c.status === 'PASS').length;
    return (_jsxs("div", { className: "page", children: [_jsx("h2", { children: t(lang, 'dashboard') }), _jsxs("p", { className: "hint", children: [t(lang, 'referenceProject'), " \u2014 ", t(lang, 'note')] }), _jsxs("div", { className: "grid3", children: [_jsxs(ResultCard, { title: "Backend", children: [_jsx(KV, { k: "Status", v: health }), _jsx(KV, { k: "Validation checks", v: `${pass}/${checks.length} PASS` }), _jsx(KV, { k: "CAD backend", v: String(cad?.backend ?? '…') }), _jsx(KV, { k: "SolidCraft", v: cad?.solidcraftDetected ? 'detected' : 'not detected (built-in mesh)' })] }), _jsxs(ResultCard, { title: "Reference design targets", children: [_jsx(KV, { k: "Case \u00D8", v: "300 mm" }), _jsx(KV, { k: "Cage \u00D8", v: "70 mm" }), _jsx(KV, { k: "Cage period", v: "60 s/rev" }), _jsx(KV, { k: "Power reserve target", v: "31 days (744 h)" }), _jsx(KV, { k: "Status", v: "Targets \u2014 not verified results" })] }), _jsx(ResultCard, { title: "Quick actions", children: _jsxs("div", { className: "row wrap", children: [_jsx("button", { className: "btn", onClick: () => onOpen('cad'), children: t(lang, 'cad') }), _jsx("button", { className: "btn", onClick: () => onOpen('tourbillon'), children: t(lang, 'tourbillon') }), _jsx("button", { className: "btn", onClick: () => onOpen('energy'), children: t(lang, 'energy') }), _jsx("button", { className: "btn", onClick: () => onOpen('reports'), children: t(lang, 'reports') })] }) })] }), _jsxs(ResultCard, { title: "Validation suite", children: [checks.map((c, i) => (_jsxs("div", { className: "kv", children: [_jsxs("span", { children: [c.module, " \u2014 ", c.message] }), _jsx(LabelBadge, { label: c.label })] }, i))), checks.length === 0 && _jsx("div", { className: "empty", children: "Loading\u2026" })] })] }));
}
export function ProjectsPage({ lang }) {
    const [projects, setProjects] = useState([]);
    const [name, setName] = useState('My wall clock');
    const [selected, setSelected] = useState(null);
    const [report, setReport] = useState(null);
    const load = () => api.projects().then((p) => setProjects(p)).catch(() => { });
    useEffect(() => { load(); }, []);
    return (_jsxs("div", { className: "page", children: [_jsx("h2", { children: t(lang, 'projects') }), _jsxs("div", { className: "grid2", children: [_jsxs(ResultCard, { title: t(lang, 'create'), children: [_jsxs("label", { className: "field", children: [_jsx("span", { children: "Name" }), _jsx("input", { value: name, onChange: (e) => setName(e.target.value) })] }), _jsx("button", { className: "btn", onClick: async () => { await api.createProject({ name, watch: { type: 'wall-clock', targetPowerReserveHours: 744 } }); load(); }, children: t(lang, 'create') }), _jsx("div", { style: { marginTop: 12 }, children: projects.map((p) => (_jsxs("div", { className: "kv", children: [_jsxs("span", { children: [String(p.name), " \u00B7 ", String(p.id)] }), _jsxs("span", { className: "row", children: [_jsx("button", { className: "btn sm", onClick: () => api.getProject(String(p.id)).then((x) => setSelected(x)), children: t(lang, 'load') }), _jsx("button", { className: "btn sm", onClick: () => api.report(String(p.id)).then((x) => setReport(x)), children: "Report" })] })] }, String(p.id)))) })] }), _jsxs(ResultCard, { title: "Selected", children: [selected ? (_jsxs(_Fragment, { children: [_jsx(KV, { k: "Name", v: String(selected.name) }), _jsx(KV, { k: "Schema", v: `v${String(selected.schemaVersion)}` }), _jsx(KV, { k: "Components", v: String(selected.components?.length ?? 0) }), _jsx(KV, { k: "Updated", v: String(selected.updatedAt) })] })) : _jsx("div", { className: "empty", children: "\u2014" }), report && (_jsxs(_Fragment, { children: [_jsx("h4", { children: "Engineering report" }), _jsx(KV, { k: "Pass / Warn / Fail", v: `${String(report.summary.pass)} / ${String(report.summary.warn)} / ${String(report.summary.fail)}` }), _jsx(Warnings, { items: report.warnings ?? [] })] }))] })] })] }));
}
export function LibraryPage({ lang }) {
    const [items, setItems] = useState([]);
    const [q, setQ] = useState('');
    const load = (query = '') => api.components(query).then((c) => setItems(c)).catch(() => { });
    useEffect(() => { load(); }, []);
    return (_jsxs("div", { className: "page", children: [_jsx("h2", { children: t(lang, 'library') }), _jsxs("div", { className: "row", children: [_jsx("input", { className: "search", placeholder: t(lang, 'search'), value: q, onChange: (e) => { setQ(e.target.value); load(e.target.value); } }), _jsx("button", { className: "btn", onClick: () => api.createComponent({ name: 'Custom part', category: 'custom', materialId: 'brass', dimensions: { diameterM: 0.01, thicknessM: 0.001 } }).then(() => load(q)), children: t(lang, 'create') })] }), _jsx("div", { className: "grid3", children: items.map((c) => (_jsxs(ResultCard, { title: String(c.name), children: [_jsx(KV, { k: "ID", v: String(c.id) }), _jsx(KV, { k: "Category", v: String(c.category) }), _jsx(KV, { k: "Material", v: String(c.materialId) }), _jsx(KV, { k: "Mass (g)", v: ((c.massKg ?? 0) * 1000).toFixed(3) }), _jsx(KV, { k: "Revision", v: String(c.revision) }), _jsxs("div", { className: "row", children: [_jsx("button", { className: "btn sm", onClick: () => api.duplicateComponent(String(c.id)).then(() => load(q)), children: t(lang, 'duplicate') }), _jsx("button", { className: "btn sm danger", onClick: () => api.deleteComponent(String(c.id)).then(() => load(q)), children: t(lang, 'delete') })] })] }, String(c.id)))) })] }));
}
export function ManufacturingPage({ lang }) {
    const [cad, setCad] = useState(null);
    const [format, setFormat] = useState('stl');
    const [msg, setMsg] = useState('');
    useEffect(() => { api.cadStatus().then((c) => setCad(c)).catch(() => { }); }, []);
    const download = async () => {
        const res = await api.exportGear({ gear: { type: 'spur', moduleM: 0.001, teeth: 24, pressureAngleDeg: 20, faceWidthM: 0.002, materialId: 'brass' }, format, name: 'gear-m1-z24' });
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `gear-m1-z24.${format === 'step' ? 'step' : format}`;
        a.click();
        URL.revokeObjectURL(url);
        setMsg(`Exported via ${res.headers.get('X-Cad-Backend') ?? 'unknown'} backend`);
    };
    return (_jsxs("div", { className: "page", children: [_jsx("h2", { children: t(lang, 'manufacturing') }), _jsxs("div", { className: "grid2", children: [_jsxs(ResultCard, { title: "CAD export (true involute)", children: [_jsx(KV, { k: "Backend", v: String(cad?.backend ?? '…') }), _jsx(KV, { k: "Note", v: String(cad?.note ?? '') }), _jsxs("label", { className: "field", children: [_jsx("span", { children: "Format" }), _jsxs("select", { value: format, onChange: (e) => setFormat(e.target.value), children: [_jsx("option", { value: "stl", children: "STL" }), _jsx("option", { value: "obj", children: "OBJ" }), _jsx("option", { value: "step", children: "STEP (faceted)" }), _jsx("option", { value: "dxf", children: "DXF" })] })] }), _jsxs("button", { className: "btn", onClick: download, children: [t(lang, 'download'), " gear m1 z24"] }), msg && _jsx("div", { className: "hint", children: msg })] }), _jsx(ResultCard, { title: t(lang, 'bom'), children: _jsxs("p", { className: "hint", children: ["BOM is generated per project (Projects \u2192 Report/BOM via API ", _jsx("code", { children: "GET /api/projects/:id/bom" }), "). Drawings, section views and inspection plans are on the roadmap \u2014 see docs/LIMITATIONS.md."] }) })] })] }));
}
export function ReportsPage({ lang }) {
    const [checks, setChecks] = useState([]);
    useEffect(() => { api.validationSuite().then((c) => setChecks(c)).catch(() => { }); }, []);
    return (_jsxs("div", { className: "page", children: [_jsx("h2", { children: t(lang, 'reports') }), _jsx(ResultCard, { title: "Automated validation (never label untested as Validated)", children: checks.map((c, i) => (_jsxs("div", { className: "kv", children: [_jsxs("span", { children: [c.module, " \u2014 ", c.message] }), _jsxs("span", { className: "row", children: [_jsx(LabelBadge, { label: c.label }), _jsx("strong", { children: c.status })] })] }, i))) }), _jsx(ResultCard, { title: "Assumptions & equations", children: _jsx("p", { className: "hint", children: "See docs/ENGINEERING.md for full equations, units, assumptions and uncertainty. Example report: docs/EXAMPLE-REPORT.md." }) })] }));
}
export function SettingsPage({ lang, setLang, units, setUnits }) {
    return (_jsxs("div", { className: "page", children: [_jsx("h2", { children: t(lang, 'settings') }), _jsxs("div", { className: "grid2", children: [_jsx(ResultCard, { title: t(lang, 'language'), children: _jsxs("div", { className: "row", children: [_jsx("button", { className: lang === 'en' ? 'btn' : 'btn ghost', onClick: () => setLang('en'), children: "English" }), _jsx("button", { className: lang === 'fa' ? 'btn' : 'btn ghost', onClick: () => setLang('fa'), children: "\u0641\u0627\u0631\u0633\u06CC (RTL)" })] }) }), _jsxs(ResultCard, { title: "Units", children: [_jsxs("div", { className: "row", children: [_jsx("button", { className: units === 'metric' ? 'btn' : 'btn ghost', onClick: () => setUnits('metric'), children: t(lang, 'metric') }), _jsx("button", { className: units === 'imperial' ? 'btn' : 'btn ghost', onClick: () => setUnits('imperial'), children: t(lang, 'imperial') })] }), _jsx("p", { className: "hint", children: "Internal calculations are always SI; display converts (see engineering-core units)." })] })] })] }));
}
