import React, { useState } from 'react';
import { api } from '../api.js';
import { LineChart, ResultCard, KV, Warnings, LabelBadge } from '../components/Charts.js';
import { Lang, t } from '../i18n.js';

function Num({ label, value, set, step = 1 }: { label: string; value: number; set: (v: number) => void; step?: number }) {
  return (
    <label className="field">
      <span>{label}</span>
      <input type="number" step={step} value={value} onChange={(e) => set(Number(e.target.value))} />
    </label>
  );
}

function useCalc<T>(fn: (body: unknown) => Promise<T>) {
  const [result, setResult] = useState<T | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const run = async (body: unknown) => {
    setLoading(true);
    setError('');
    try { setResult(await fn(body)); } catch (e) { setError(String(e)); }
    setLoading(false);
  };
  return { result, error, loading, run };
}

export function GearPage({ lang }: { lang: Lang }) {
  const [moduleMm, setModuleMm] = useState(1);
  const [teeth, setTeeth] = useState(24);
  const [alpha, setAlpha] = useState(20);
  const [faceMm, setFaceMm] = useState(2);
  const [torque, setTorque] = useState(0.001);
  const [speed, setSpeed] = useState(10);
  const gear = useCalc<Record<string, unknown>>((b) => api.calcGear(b));
  const mesh = useCalc<Record<string, unknown>>((b) => api.calcMesh(b));
  const g = gear.result as Record<string, number> | null;
  const m = mesh.result as Record<string, number> | null;
  return (
    <div className="page">
      <h2>{t(lang, 'gear')}</h2>
      <div className="grid2">
        <ResultCard title={t(lang, 'parameters')}>
          <Num label="Module (mm)" value={moduleMm} set={setModuleMm} step={0.1} />
          <Num label="Teeth z" value={teeth} set={setTeeth} />
          <Num label="Pressure angle (°)" value={alpha} set={setAlpha} />
          <Num label="Face width (mm)" value={faceMm} set={setFaceMm} step={0.1} />
          <Num label="Input torque (N·m)" value={torque} set={setTorque} step={0.0001} />
          <Num label="Input speed (rad/s)" value={speed} set={setSpeed} />
          <div className="row">
            <button className="btn" onClick={() => gear.run({ type: 'spur', moduleM: moduleMm / 1000, teeth, pressureAngleDeg: alpha, faceWidthM: faceMm / 1000, materialId: 'brass' })}>{t(lang, 'calculate')}</button>
            <button className="btn" onClick={() => mesh.run({ g1: { type: 'pinion', moduleM: moduleMm / 1000, teeth: 8, pressureAngleDeg: alpha, faceWidthM: faceMm / 1000, materialId: 'steel-hardened' }, g2: { type: 'spur', moduleM: moduleMm / 1000, teeth, pressureAngleDeg: alpha, faceWidthM: faceMm / 1000, materialId: 'brass' }, opts: { inputSpeedRadps: speed, inputTorqueNm: torque } })}>Mesh 8→{teeth}</button>
          </div>
          {gear.error && <div className="error">{gear.error}</div>}
          {mesh.error && <div className="error">{mesh.error}</div>}
        </ResultCard>
        <ResultCard title={t(lang, 'results')}>
          {g && (
            <>
              <LabelBadge label="Calculated" />
              <KV k="Pitch Ø (mm)" v={((g.pitchDiameterM as number) * 1000).toFixed(3)} />
              <KV k="Base Ø (mm)" v={((g.baseDiameterM as number) * 1000).toFixed(3)} />
              <KV k="Outside Ø (mm)" v={((g.outsideDiameterM as number) * 1000).toFixed(3)} />
              <KV k="Root Ø (mm)" v={((g.rootDiameterM as number) * 1000).toFixed(3)} />
              <KV k="Min teeth (no undercut)" v={String(g.minTeethNoUndercut)} />
              <Warnings items={(g.warnings as unknown as string[]) ?? []} />
            </>
          )}
          {m && (
            <>
              <LabelBadge label="Calculated" />
              <KV k="Ratio" v={(m.ratio as number).toFixed(3)} />
              <KV k="Center distance (mm)" v={((m.centerDistanceM as number) * 1000).toFixed(3)} />
              <KV k="Contact ratio" v={(m.transverseContactRatio as number).toFixed(3)} />
              <KV k="Bending stress (MPa)" v={(((m.bendingStressPa as number) / 1e6)).toFixed(1)} />
              <KV k="Contact stress (MPa)" v={(((m.contactStressPa as number) / 1e6)).toFixed(1)} />
              <KV k="Bending SF" v={(m.bendingSafetyFactor as number).toFixed(2)} />
              <KV k="Contact SF" v={(m.contactSafetyFactor as number).toFixed(2)} />
              <Warnings items={(m.warnings as unknown as string[]) ?? []} />
            </>
          )}
          {!g && !m && <div className="empty">—</div>}
        </ResultCard>
      </div>
    </div>
  );
}

export function MainspringPage({ lang }: { lang: Lang }) {
  const [thickUm, setThickUm] = useState(200);
  const [widthMm, setWidthMm] = useState(1);
  const [turns, setTurns] = useState(6);
  const [powerW, setPowerW] = useState(1e-5);
  const [hours, setHours] = useState(744);
  const ms = useCalc<Record<string, unknown>>((b) => api.calcMainspring(b));
  const pr = useCalc<Record<string, unknown>>((b) => api.calcPowerReserve(b));
  const r = ms.result as Record<string, unknown> | null;
  const p = pr.result as Record<string, unknown> | null;
  return (
    <div className="page">
      <h2>{t(lang, 'mainspring')}</h2>
      <div className="grid2">
        <ResultCard title={t(lang, 'parameters')}>
          <Num label="Thickness (µm)" value={thickUm} set={setThickUm} />
          <Num label="Width (mm)" value={widthMm} set={setWidthMm} step={0.1} />
          <Num label="Active turns" value={turns} set={setTurns} />
          <Num label="Avg consumption (W)" value={powerW} set={setPowerW} step={0.000001} />
          <Num label="Target hours" value={hours} set={setHours} />
          <div className="row">
            <button className="btn" onClick={() => ms.run({ thicknessM: thickUm / 1e6, widthM: widthMm / 1000, lengthM: 0.5, innerRadiusM: 0.01, outerRadiusM: 0.05, barrelDiameterM: 0.11, arborDiameterM: 0.015, activeTurns: turns, materialId: 'blued-steel' })}>{t(lang, 'calculate')}</button>
            <button className="btn" disabled={!r} onClick={() => pr.run({ storedEnergyJ: r!.storedEnergyJ, avgPowerConsumptionW: powerW, transmissionEfficiency: 0.8, targetHours: hours })}>{t(lang, 'powerReserve')}</button>
          </div>
          {ms.error && <div className="error">{ms.error}</div>}
          {pr.error && <div className="error">{pr.error}</div>}
        </ResultCard>
        <ResultCard title={t(lang, 'results')}>
          {r && (
            <>
              <LabelBadge label={String(r.resultType)} />
              <KV k="Stored energy (J)" v={(r.storedEnergyJ as number).toFixed(4)} />
              <KV k="Max torque (mN·m)" v={((r.maxTorqueNm as number) * 1000).toFixed(3)} />
              <KV k="Max stress (MPa)" v={((r.maxStressPa as number) / 1e6).toFixed(0)} />
              <KV k="Safety factor" v={(r.safetyFactor as number).toFixed(2)} />
              <LineChart data={r.torqueCurve as [number, number][]} yLabel="T (N·m)" />
              <Warnings items={(r.warnings as string[]) ?? []} />
            </>
          )}
          {p && (
            <>
              <KV k="Achievable (h)" v={(p.achievableHours as number).toFixed(1)} />
              <KV k="Feasible" v={p.feasible ? t(lang, 'feasible') : t(lang, 'infeasible')} />
              <Warnings items={(p.warnings as string[]) ?? []} />
            </>
          )}
          {!r && <div className="empty">—</div>}
        </ResultCard>
      </div>
    </div>
  );
}

export function BalancePage({ lang }: { lang: Lang }) {
  const [kappa, setKappa] = useState(1e-6);
  const [massG, setMassG] = useState(0.2);
  const [amp, setAmp] = useState(270);
  const bal = useCalc<Record<string, unknown>>((b) => api.calcBalance(b));
  const r = bal.result as Record<string, unknown> | null;
  return (
    <div className="page">
      <h2>{t(lang, 'balance')}</h2>
      <div className="grid2">
        <ResultCard title={t(lang, 'parameters')}>
          <Num label="κ hairspring (N·m/rad)" value={kappa} set={setKappa} step={0.0000001} />
          <Num label="Balance mass (g)" value={massG} set={setMassG} step={0.01} />
          <Num label="Amplitude (°)" value={amp} set={setAmp} />
          <button className="btn" onClick={() => bal.run({ diameterM: 0.02, thicknessM: 0.001, massKg: massG / 1000, timingScrewMassKg: 0.00005, timingScrewRadiusM: 0.009, hairspringStiffnessNmPerRad: kappa, hairspringLengthM: 0.05, materialId: 'gilt-brass', amplitudeDeg: amp })}>{t(lang, 'calculate')}</button>
          {bal.error && <div className="error">{bal.error}</div>}
        </ResultCard>
        <ResultCard title={t(lang, 'results')}>
          {r && (
            <>
              <LabelBadge label="Calculated" />
              <KV k="Frequency (Hz)" v={(r.frequencyHz as number).toFixed(3)} />
              <KV k="Period (s)" v={(r.periodS as number).toFixed(4)} />
              <KV k="Beat rate (vph)" v={(r.beatRateVph as number).toFixed(0)} />
              <KV k="Inertia (kg·m²)" v={(r.inertiaKgM2 as number).toExponential(3)} />
              <KV k="Rate per 0.1 g screw (s/day)" v={(r.ratePerTenthGramSecPerDay as number).toFixed(2)} />
              <KV k="Temp shift (s/day/K)" v={(r.temperatureRateShiftSecPerDayPerK as number).toFixed(2)} />
              <Warnings items={(r.warnings as string[]) ?? []} />
            </>
          )}
          {!r && <div className="empty">—</div>}
        </ResultCard>
      </div>
    </div>
  );
}

export function EscapementPage({ lang }: { lang: Lang }) {
  const [freq, setFreq] = useState(2);
  const [teeth, setTeeth] = useState(15);
  const esc = useCalc<Record<string, unknown>>((b) => api.calcEscapement(b));
  const sim = useCalc<Record<string, unknown>>((b) => api.simEscapement(b));
  const params = () => ({ type: 'swiss-lever', escapeTeeth: teeth, escapeDiameterM: 0.012, palletAngleDeg: 180, lockingAngleDeg: 2, dropDeg: 1, liftDeg: 3, drawDeg: 1, impulseAngleDeg: 8, balanceFrequencyHz: freq, balanceInertiaKgM2: 1e-8, hairspringStiffnessNmPerRad: 1.5e-6, amplitudeDeg: 270, escapeWheelTorqueNm: 1e-5 });
  const r = esc.result as Record<string, unknown> | null;
  const s = sim.result as Record<string, unknown> | null;
  return (
    <div className="page">
      <h2>{t(lang, 'escapement')}</h2>
      <div className="grid2">
        <ResultCard title={t(lang, 'parameters')}>
          <Num label="Balance freq (Hz)" value={freq} set={setFreq} step={0.1} />
          <Num label="Escape teeth" value={teeth} set={setTeeth} />
          <div className="row">
            <button className="btn" onClick={() => esc.run(params())}>{t(lang, 'calculate')}</button>
            <button className="btn" onClick={() => sim.run({ params: params(), durationS: 5 })}>{t(lang, 'simulate')} (event-based)</button>
          </div>
          {esc.error && <div className="error">{esc.error}</div>}
          {sim.error && <div className="error">{sim.error}</div>}
        </ResultCard>
        <ResultCard title={t(lang, 'results')}>
          {r && (<><LabelBadge label="Calculated" /><KV k="Tooth pitch (°)" v={(r.toothPitchDeg as number).toFixed(2)} /><Warnings items={(r.warnings as string[]) ?? []} /></>)}
          {s && (
            <>
              <LabelBadge label="Simulated" />
              <KV k="Beats" v={String(s.beats)} />
              <KV k="Energy/beat (µJ)" v={((s.energyPerBeatJ as number) * 1e6).toFixed(2)} />
              <KV k="Avg power (µW)" v={((s.avgPowerW as number) * 1e6).toFixed(2)} />
              <KV k="Wheel revs" v={(s.escapeWheelRevs as number).toFixed(3)} />
              <Warnings items={(s.warnings as string[]) ?? []} />
            </>
          )}
          {!r && !s && <div className="empty">—</div>}
        </ResultCard>
      </div>
    </div>
  );
}

export function TourbillonPage({ lang }: { lang: Lang }) {
  const [freq, setFreq] = useState(2);
  const [fixed, setFixed] = useState(80);
  const [pinion, setPinion] = useState(8);
  const tb = useCalc<Record<string, unknown>>((b) => api.calcTourbillon(b));
  const r = tb.result as Record<string, unknown> | null;
  const body = () => ({ cageDiameterM: 0.07, cageHeightM: 0.012, cageMassKg: 0.005, cageInertiaKgM2: 1e-6, cagePeriodS: 60, balanceDiameterM: 0.02, balanceFrequencyHz: freq, escapeTeeth: 15, fixedWheelTeeth: fixed, pinionTeeth: pinion, shaftDiameterM: 0.0005, bearingInnerDiameterM: 0.0005, radialClearanceM: 0.00001, axialClearanceM: 0.00005, escapeWheelTorqueNm: 1e-5 });
  return (
    <div className="page">
      <h2>{t(lang, 'tourbillon')}</h2>
      <div className="grid2">
        <ResultCard title={t(lang, 'parameters')}>
          <Num label="Balance freq (Hz)" value={freq} set={setFreq} step={0.1} />
          <Num label="Fixed wheel teeth" value={fixed} set={setFixed} />
          <Num label="Pinion teeth" value={pinion} set={setPinion} />
          <button className="btn" onClick={() => tb.run(body())}>{t(lang, 'calculate')}</button>
          {tb.error && <div className="error">{tb.error}</div>}
        </ResultCard>
        <ResultCard title={t(lang, 'results')}>
          {r && (
            <>
              <LabelBadge label="Calculated" />
              <KV k="Cage ω (rad/s)" v={(r.cageAngularVelocityRadps as number).toFixed(5)} />
              <KV k="Required ratio" v={(r.requiredRatio as number).toFixed(2)} />
              <KV k="Actual ratio" v={(r.actualRatio as number).toFixed(2)} />
              <KV k="Ratio error (%)" v={(r.ratioErrorPct as number).toFixed(1)} />
              <KV k="Bearing load (N)" v={(r.bearingLoadN as number).toFixed(3)} />
              <KV k="Avg power (µW)" v={((r.avgPowerW as number) * 1e6).toFixed(2)} />
              <Warnings items={(r.warnings as string[]) ?? []} />
            </>
          )}
          {!r && <div className="empty">—</div>}
        </ResultCard>
      </div>
    </div>
  );
}

export function SimulationPage({ lang }: { lang: Lang }) {
  const [mode, setMode] = useState<'rigid-body' | 'kinematic' | 'contact'>('rigid-body');
  const sim = useCalc<Record<string, unknown>>((b) => api.simDynamics(b));
  const r = sim.result as Record<string, unknown> | null;
  const samples = (r?.samples as { t: number; totalEnergyJ: number }[] | undefined) ?? [];
  return (
    <div className="page">
      <h2>{t(lang, 'simulation')}</h2>
      <div className="grid2">
        <ResultCard title={t(lang, 'parameters')}>
          <label className="field"><span>Mode</span>
            <select value={mode} onChange={(e) => setMode(e.target.value as never)}>
              <option value="rigid-body">Rigid-body dynamics</option>
              <option value="kinematic">Kinematic (not validated)</option>
              <option value="contact">Contact &amp; friction</option>
            </select>
          </label>
          <p className="hint">Spring oscillator (κ=1, I=1) integrated with RK4. Energy drift is reported — a basic animation is never labelled as validated simulation.</p>
          <button className="btn" onClick={() => sim.run({ bodies: [{ id: 'balance', inertiaKgM2: 1, angleRad: 1, angularVelocityRadps: 0, torqueNm: 0, spring: { stiffness: 1, restAngleRad: 0 } }], opts: { mode, durationS: 6.28, dtS: 0.001 } })}>{t(lang, 'simulate')}</button>
          {sim.error && <div className="error">{sim.error}</div>}
        </ResultCard>
        <ResultCard title={t(lang, 'results')}>
          {r && (
            <>
              <LabelBadge label="Simulated" />
              <KV k="Mode" v={String(r.mode)} />
              <KV k="Stable" v={String(r.stable)} />
              <KV k="Energy drift (%)" v={(r.energyDriftPct as number).toFixed(3)} />
              <LineChart data={samples.map((s) => [s.t, s.totalEnergyJ] as [number, number])} yLabel="E (J)" />
              <Warnings items={(r.warnings as string[]) ?? []} />
            </>
          )}
          {!r && <div className="empty">—</div>}
        </ResultCard>
      </div>
    </div>
  );
}

export function EnergyPage({ lang }: { lang: Lang }) {
  const [stored, setStored] = useState(10);
  const [power, setPower] = useState(1e-5);
  const [hours, setHours] = useState(744);
  const en = useCalc<Record<string, unknown>>((b) => api.calcEnergy(b));
  const r = en.result as Record<string, unknown> | null;
  return (
    <div className="page">
      <h2>{t(lang, 'energy')}</h2>
      <div className="grid2">
        <ResultCard title={t(lang, 'parameters')}>
          <Num label="Stored energy (J)" value={stored} set={setStored} step={0.1} />
          <Num label="Avg power (W)" value={power} set={setPower} step={0.000001} />
          <Num label="Target (h)" value={hours} set={setHours} />
          <button className="btn" onClick={() => en.run({ budget: { storedEnergyJ: stored, gearFrictionPct: 10, bearingFrictionPct: 5, escapementLossPct: 20, balanceLossPct: 5, cageLossPct: 5, transmissionEfficiency: 0.8 }, avgPowerConsumptionW: power, targetHours: hours })}>{t(lang, 'calculate')}</button>
          {en.error && <div className="error">{en.error}</div>}
        </ResultCard>
        <ResultCard title={t(lang, 'results')}>
          {r && (
            <>
              <LabelBadge label="Calculated" />
              <KV k="Usable (J)" v={(r.usableJ as number).toFixed(3)} />
              <KV k="Required (J)" v={(r.requiredJ as number).toFixed(3)} />
              <KV k="Reserve (h)" v={(r.powerReserveHours as number).toFixed(1)} />
              <KV k="Feasible" v={r.feasible ? t(lang, 'feasible') : t(lang, 'infeasible')} />
              <Warnings items={(r.warnings as string[]) ?? []} />
            </>
          )}
          {!r && <div className="empty">—</div>}
        </ResultCard>
      </div>
    </div>
  );
}

export function TolerancePage({ lang }: { lang: Lang }) {
  const tol = useCalc<Record<string, unknown>>((b) => api.calcTolerance(b));
  const r = tol.result as Record<string, unknown> | null;
  return (
    <div className="page">
      <h2>{t(lang, 'tolerance')}</h2>
      <div className="grid2">
        <ResultCard title={t(lang, 'parameters')}>
          <p className="hint">Stack: 10.000 ±0.100 mm + 5.000 ±0.100 mm (worst-case / RSS / Monte Carlo, 10k samples).</p>
          <button className="btn" onClick={() => tol.run({ items: [{ name: 'a', nominalM: 0.01, plusTolM: 0.0001, minusTolM: 0.0001 }, { name: 'b', nominalM: 0.005, plusTolM: 0.0001, minusTolM: 0.0001 }], opts: { samples: 10000, seed: 42 } })}>{t(lang, 'calculate')}</button>
          {tol.error && <div className="error">{tol.error}</div>}
        </ResultCard>
        <ResultCard title={t(lang, 'results')}>
          {r && (
            <>
              <LabelBadge label="Calculated" />
              <KV k="Nominal (mm)" v={((r.nominalM as number) * 1000).toFixed(3)} />
              <KV k="Worst-case ± (µm)" v={((r.worstCasePlusM as number) * 1e6).toFixed(1)} />
              <KV k="RSS ± (µm)" v={((r.rssToleranceM as number) * 1e6).toFixed(1)} />
              <KV k="MC σ (µm)" v={((r.monteCarloStdM as number) * 1e6).toFixed(1)} />
              <KV k="MC P99 (mm)" v={`${((r.monteCarloP99LowM as number) * 1000).toFixed(3)} … ${((r.monteCarloP99HighM as number) * 1000).toFixed(3)}`} />
              <Warnings items={(r.warnings as string[]) ?? []} />
            </>
          )}
          {!r && <div className="empty">—</div>}
        </ResultCard>
      </div>
    </div>
  );
}
