import React, { useEffect, useState } from 'react';
import { api } from '../api.js';
import { ResultCard, KV, Warnings, LabelBadge } from '../components/Charts.js';
import { Lang, t } from '../i18n.js';

export function Dashboard({ lang, onOpen }: { lang: Lang; onOpen: (p: string) => void }) {
  const [health, setHealth] = useState('');
  const [checks, setChecks] = useState<{ module: string; status: string; message: string; label: string }[]>([]);
  const [cad, setCad] = useState<Record<string, unknown> | null>(null);
  useEffect(() => {
    api.health().then((h) => setHealth(h.ok ? 'OK' : '—')).catch(() => setHealth('backend offline'));
    api.validationSuite().then((c) => setChecks(c as never)).catch(() => {});
    api.cadStatus().then((c) => setCad(c as Record<string, unknown>)).catch(() => {});
  }, []);
  const pass = checks.filter((c) => c.status === 'PASS').length;
  return (
    <div className="page">
      <h2>{t(lang, 'dashboard')}</h2>
      <p className="hint">{t(lang, 'referenceProject')} — {t(lang, 'note')}</p>
      <div className="grid3">
        <ResultCard title="Backend">
          <KV k="Status" v={health} />
          <KV k="Validation checks" v={`${pass}/${checks.length} PASS`} />
          <KV k="CAD backend" v={String(cad?.backend ?? '…')} />
          <KV k="SolidCraft" v={cad?.solidcraftDetected ? 'detected' : 'not detected (built-in mesh)'} />
        </ResultCard>
        <ResultCard title="Reference design targets">
          <KV k="Case Ø" v="300 mm" />
          <KV k="Cage Ø" v="70 mm" />
          <KV k="Cage period" v="60 s/rev" />
          <KV k="Power reserve target" v="31 days (744 h)" />
          <KV k="Status" v="Targets — not verified results" />
        </ResultCard>
        <ResultCard title="Quick actions">
          <div className="row wrap">
            <button className="btn" onClick={() => onOpen('cad')}>{t(lang, 'cad')}</button>
            <button className="btn" onClick={() => onOpen('tourbillon')}>{t(lang, 'tourbillon')}</button>
            <button className="btn" onClick={() => onOpen('energy')}>{t(lang, 'energy')}</button>
            <button className="btn" onClick={() => onOpen('reports')}>{t(lang, 'reports')}</button>
          </div>
        </ResultCard>
      </div>
      <ResultCard title="Validation suite">
        {checks.map((c, i) => (
          <div key={i} className="kv"><span>{c.module} — {c.message}</span><LabelBadge label={c.label} /></div>
        ))}
        {checks.length === 0 && <div className="empty">Loading…</div>}
      </ResultCard>
    </div>
  );
}

export function ProjectsPage({ lang }: { lang: Lang }) {
  const [projects, setProjects] = useState<Record<string, unknown>[]>([]);
  const [name, setName] = useState('My wall clock');
  const [selected, setSelected] = useState<Record<string, unknown> | null>(null);
  const [report, setReport] = useState<Record<string, unknown> | null>(null);
  const load = () => api.projects().then((p) => setProjects(p as Record<string, unknown>[])).catch(() => {});
  useEffect(() => { load(); }, []);
  return (
    <div className="page">
      <h2>{t(lang, 'projects')}</h2>
      <div className="grid2">
        <ResultCard title={t(lang, 'create')}>
          <label className="field"><span>Name</span><input value={name} onChange={(e) => setName(e.target.value)} /></label>
          <button className="btn" onClick={async () => { await api.createProject({ name, watch: { type: 'wall-clock', targetPowerReserveHours: 744 } }); load(); }}>{t(lang, 'create')}</button>
          <div style={{ marginTop: 12 }}>
            {projects.map((p) => (
              <div key={String(p.id)} className="kv">
                <span>{String(p.name)} · {String(p.id)}</span>
                <span className="row">
                  <button className="btn sm" onClick={() => api.getProject(String(p.id)).then((x) => setSelected(x as Record<string, unknown>))}>{t(lang, 'load')}</button>
                  <button className="btn sm" onClick={() => api.report(String(p.id)).then((x) => setReport(x as Record<string, unknown>))}>Report</button>
                </span>
              </div>
            ))}
          </div>
        </ResultCard>
        <ResultCard title="Selected">
          {selected ? (
            <>
              <KV k="Name" v={String(selected.name)} />
              <KV k="Schema" v={`v${String(selected.schemaVersion)}`} />
              <KV k="Components" v={String((selected.components as unknown[])?.length ?? 0)} />
              <KV k="Updated" v={String(selected.updatedAt)} />
            </>
          ) : <div className="empty">—</div>}
          {report && (
            <>
              <h4>Engineering report</h4>
              <KV k="Pass / Warn / Fail" v={`${String((report.summary as Record<string, number>).pass)} / ${String((report.summary as Record<string, number>).warn)} / ${String((report.summary as Record<string, number>).fail)}`} />
              <Warnings items={(report.warnings as string[]) ?? []} />
            </>
          )}
        </ResultCard>
      </div>
    </div>
  );
}

export function LibraryPage({ lang }: { lang: Lang }) {
  const [items, setItems] = useState<Record<string, unknown>[]>([]);
  const [q, setQ] = useState('');
  const load = (query = '') => api.components(query).then((c) => setItems(c as Record<string, unknown>[])).catch(() => {});
  useEffect(() => { load(); }, []);
  return (
    <div className="page">
      <h2>{t(lang, 'library')}</h2>
      <div className="row">
        <input className="search" placeholder={t(lang, 'search')} value={q} onChange={(e) => { setQ(e.target.value); load(e.target.value); }} />
        <button className="btn" onClick={() => api.createComponent({ name: 'Custom part', category: 'custom', materialId: 'brass', dimensions: { diameterM: 0.01, thicknessM: 0.001 } }).then(() => load(q))}>{t(lang, 'create')}</button>
      </div>
      <div className="grid3">
        {items.map((c) => (
          <ResultCard key={String(c.id)} title={String(c.name)}>
            <KV k="ID" v={String(c.id)} />
            <KV k="Category" v={String(c.category)} />
            <KV k="Material" v={String(c.materialId)} />
            <KV k="Mass (g)" v={(((c.massKg as number) ?? 0) * 1000).toFixed(3)} />
            <KV k="Revision" v={String(c.revision)} />
            <div className="row">
              <button className="btn sm" onClick={() => api.duplicateComponent(String(c.id)).then(() => load(q))}>{t(lang, 'duplicate')}</button>
              <button className="btn sm danger" onClick={() => api.deleteComponent(String(c.id)).then(() => load(q))}>{t(lang, 'delete')}</button>
            </div>
          </ResultCard>
        ))}
      </div>
    </div>
  );
}

export function ManufacturingPage({ lang }: { lang: Lang }) {
  const [cad, setCad] = useState<Record<string, unknown> | null>(null);
  const [format, setFormat] = useState<'stl' | 'obj' | 'step' | 'dxf'>('stl');
  const [msg, setMsg] = useState('');
  useEffect(() => { api.cadStatus().then((c) => setCad(c as Record<string, unknown>)).catch(() => {}); }, []);
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
  return (
    <div className="page">
      <h2>{t(lang, 'manufacturing')}</h2>
      <div className="grid2">
        <ResultCard title="CAD export (true involute)">
          <KV k="Backend" v={String(cad?.backend ?? '…')} />
          <KV k="Note" v={String(cad?.note ?? '')} />
          <label className="field"><span>Format</span>
            <select value={format} onChange={(e) => setFormat(e.target.value as never)}>
              <option value="stl">STL</option><option value="obj">OBJ</option><option value="step">STEP (faceted)</option><option value="dxf">DXF</option>
            </select>
          </label>
          <button className="btn" onClick={download}>{t(lang, 'download')} gear m1 z24</button>
          {msg && <div className="hint">{msg}</div>}
        </ResultCard>
        <ResultCard title={t(lang, 'bom')}>
          <p className="hint">BOM is generated per project (Projects → Report/BOM via API <code>GET /api/projects/:id/bom</code>). Drawings, section views and inspection plans are on the roadmap — see docs/LIMITATIONS.md.</p>
        </ResultCard>
      </div>
    </div>
  );
}

export function ReportsPage({ lang }: { lang: Lang }) {
  const [checks, setChecks] = useState<{ module: string; status: string; message: string; label: string }[]>([]);
  useEffect(() => { api.validationSuite().then((c) => setChecks(c as never)).catch(() => {}); }, []);
  return (
    <div className="page">
      <h2>{t(lang, 'reports')}</h2>
      <ResultCard title="Automated validation (never label untested as Validated)">
        {checks.map((c, i) => (
          <div key={i} className="kv"><span>{c.module} — {c.message}</span><span className="row"><LabelBadge label={c.label} /><strong>{c.status}</strong></span></div>
        ))}
      </ResultCard>
      <ResultCard title="Assumptions & equations">
        <p className="hint">See docs/ENGINEERING.md for full equations, units, assumptions and uncertainty. Example report: docs/EXAMPLE-REPORT.md.</p>
      </ResultCard>
    </div>
  );
}

export function SettingsPage({ lang, setLang, units, setUnits }: { lang: Lang; setLang: (l: Lang) => void; units: string; setUnits: (u: string) => void }) {
  return (
    <div className="page">
      <h2>{t(lang, 'settings')}</h2>
      <div className="grid2">
        <ResultCard title={t(lang, 'language')}>
          <div className="row">
            <button className={lang === 'en' ? 'btn' : 'btn ghost'} onClick={() => setLang('en')}>English</button>
            <button className={lang === 'fa' ? 'btn' : 'btn ghost'} onClick={() => setLang('fa')}>فارسی (RTL)</button>
          </div>
        </ResultCard>
        <ResultCard title="Units">
          <div className="row">
            <button className={units === 'metric' ? 'btn' : 'btn ghost'} onClick={() => setUnits('metric')}>{t(lang, 'metric')}</button>
            <button className={units === 'imperial' ? 'btn' : 'btn ghost'} onClick={() => setUnits('imperial')}>{t(lang, 'imperial')}</button>
          </div>
          <p className="hint">Internal calculations are always SI; display converts (see engineering-core units).</p>
        </ResultCard>
      </div>
    </div>
  );
}
