import React, { useState } from 'react';
import Viewport3D from '../components/Viewport3D.js';
import { ResultCard, KV } from '../components/Charts.js';
import { Lang, t } from '../i18n.js';

export default function CadWorkspace({ lang }: { lang: Lang }) {
  const [playing, setPlaying] = useState(true);
  const [speed, setSpeed] = useState(1);
  const [freq, setFreq] = useState(2);
  const [stats, setStats] = useState({ cageAngleDeg: 0, balanceAngleDeg: 0, escapeAngleDeg: 0 });
  const [feature, setFeature] = useState('Tourbillon cage');
  return (
    <div className="page">
      <h2>{t(lang, 'cad')}</h2>
      <div className="cad-layout">
        <div className="cad-tree">
          <h4>Feature tree</h4>
          {['Main plate', 'Barrel Ø120', 'Gear train', 'Tourbillon cage Ø70', 'Balance wheel', 'Hairspring', 'Escape wheel z15', 'Fixed wheel'].map((f) => (
            <button key={f} className={feature === f ? 'tree active' : 'tree'} onClick={() => setFeature(f)}>{f}</button>
          ))}
          <h4 style={{ marginTop: 16 }}>Assembly</h4>
          <div className="hint">300 mm wall clock · cage Ø70 mm · 60 s/rev · skeleton tourbillon</div>
          <ResultCard title="Simulation controls">
            <div className="row">
              <button className="btn" onClick={() => setPlaying(!playing)}>{playing ? t(lang, 'pause') : t(lang, 'play')}</button>
            </div>
            <label className="field"><span>{t(lang, 'speed')} ×{speed}</span>
              <input type="range" min={0.1} max={5} step={0.1} value={speed} onChange={(e) => setSpeed(Number(e.target.value))} />
            </label>
            <label className="field"><span>Balance freq (Hz)</span>
              <input type="number" step={0.1} value={freq} onChange={(e) => setFreq(Number(e.target.value))} />
            </label>
            <KV k="Cage angle" v={`${stats.cageAngleDeg.toFixed(1)}°`} />
            <KV k="Balance angle" v={`${stats.balanceAngleDeg.toFixed(1)}°`} />
            <KV k="Escape angle" v={`${stats.escapeAngleDeg.toFixed(1)}°`} />
            <KV k="State" v={playing ? t(lang, 'running') : t(lang, 'paused')} />
          </ResultCard>
        </div>
        <div className="cad-main">
          <Viewport3D playing={playing} speed={speed} balanceFreqHz={freq} cagePeriodS={60} escapeTeeth={15} onStats={setStats} />
          <div className="cad-props">
            <ResultCard title={`Properties — ${feature}`}>
              <KV k="Geometry" v="True involute (engineering-core)" />
              <KV k="Units" v="SI (mm display)" />
              <KV k="CAD backend" v="SolidCraft adapter / built-in mesh" />
              <p className="hint">Edit parameters in the engineering modules; the 3D view updates from the same calculation engine. Exploded view &amp; assembly sequence: see docs/CAD.md (roadmap).</p>
            </ResultCard>
          </div>
        </div>
      </div>
    </div>
  );
}
