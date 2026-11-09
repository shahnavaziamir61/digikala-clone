import { jsx as _jsx, jsxs as _jsxs, Fragment as _Fragment } from "react/jsx-runtime";
import { useState } from 'react';
import { api } from '../api.js';
import { LineChart, ResultCard, KV, Warnings, LabelBadge } from '../components/Charts.js';
import { t } from '../i18n.js';
function Num({ label, value, set, step = 1 }) {
    return (_jsxs("label", { className: "field", children: [_jsx("span", { children: label }), _jsx("input", { type: "number", step: step, value: value, onChange: (e) => set(Number(e.target.value)) })] }));
}
function useCalc(fn) {
    const [result, setResult] = useState(null);
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const run = async (body) => {
        setLoading(true);
        setError('');
        try {
            setResult(await fn(body));
        }
        catch (e) {
            setError(String(e));
        }
        setLoading(false);
    };
    return { result, error, loading, run };
}
export function GearPage({ lang }) {
    const [moduleMm, setModuleMm] = useState(1);
    const [teeth, setTeeth] = useState(24);
    const [alpha, setAlpha] = useState(20);
    const [faceMm, setFaceMm] = useState(2);
    const [torque, setTorque] = useState(0.001);
    const [speed, setSpeed] = useState(10);
    const gear = useCalc((b) => api.calcGear(b));
    const mesh = useCalc((b) => api.calcMesh(b));
    const g = gear.result;
    const m = mesh.result;
    return (_jsxs("div", { className: "page", children: [_jsx("h2", { children: t(lang, 'gear') }), _jsxs("div", { className: "grid2", children: [_jsxs(ResultCard, { title: t(lang, 'parameters'), children: [_jsx(Num, { label: "Module (mm)", value: moduleMm, set: setModuleMm, step: 0.1 }), _jsx(Num, { label: "Teeth z", value: teeth, set: setTeeth }), _jsx(Num, { label: "Pressure angle (\u00B0)", value: alpha, set: setAlpha }), _jsx(Num, { label: "Face width (mm)", value: faceMm, set: setFaceMm, step: 0.1 }), _jsx(Num, { label: "Input torque (N\u00B7m)", value: torque, set: setTorque, step: 0.0001 }), _jsx(Num, { label: "Input speed (rad/s)", value: speed, set: setSpeed }), _jsxs("div", { className: "row", children: [_jsx("button", { className: "btn", onClick: () => gear.run({ type: 'spur', moduleM: moduleMm / 1000, teeth, pressureAngleDeg: alpha, faceWidthM: faceMm / 1000, materialId: 'brass' }), children: t(lang, 'calculate') }), _jsxs("button", { className: "btn", onClick: () => mesh.run({ g1: { type: 'pinion', moduleM: moduleMm / 1000, teeth: 8, pressureAngleDeg: alpha, faceWidthM: faceMm / 1000, materialId: 'steel-hardened' }, g2: { type: 'spur', moduleM: moduleMm / 1000, teeth, pressureAngleDeg: alpha, faceWidthM: faceMm / 1000, materialId: 'brass' }, opts: { inputSpeedRadps: speed, inputTorqueNm: torque } }), children: ["Mesh 8\u2192", teeth] })] }), gear.error && _jsx("div", { className: "error", children: gear.error }), mesh.error && _jsx("div", { className: "error", children: mesh.error })] }), _jsxs(ResultCard, { title: t(lang, 'results'), children: [g && (_jsxs(_Fragment, { children: [_jsx(LabelBadge, { label: "Calculated" }), _jsx(KV, { k: "Pitch \u00D8 (mm)", v: (g.pitchDiameterM * 1000).toFixed(3) }), _jsx(KV, { k: "Base \u00D8 (mm)", v: (g.baseDiameterM * 1000).toFixed(3) }), _jsx(KV, { k: "Outside \u00D8 (mm)", v: (g.outsideDiameterM * 1000).toFixed(3) }), _jsx(KV, { k: "Root \u00D8 (mm)", v: (g.rootDiameterM * 1000).toFixed(3) }), _jsx(KV, { k: "Min teeth (no undercut)", v: String(g.minTeethNoUndercut) }), _jsx(Warnings, { items: g.warnings ?? [] })] })), m && (_jsxs(_Fragment, { children: [_jsx(LabelBadge, { label: "Calculated" }), _jsx(KV, { k: "Ratio", v: m.ratio.toFixed(3) }), _jsx(KV, { k: "Center distance (mm)", v: (m.centerDistanceM * 1000).toFixed(3) }), _jsx(KV, { k: "Contact ratio", v: m.transverseContactRatio.toFixed(3) }), _jsx(KV, { k: "Bending stress (MPa)", v: ((m.bendingStressPa / 1e6)).toFixed(1) }), _jsx(KV, { k: "Contact stress (MPa)", v: ((m.contactStressPa / 1e6)).toFixed(1) }), _jsx(KV, { k: "Bending SF", v: m.bendingSafetyFactor.toFixed(2) }), _jsx(KV, { k: "Contact SF", v: m.contactSafetyFactor.toFixed(2) }), _jsx(Warnings, { items: m.warnings ?? [] })] })), !g && !m && _jsx("div", { className: "empty", children: "\u2014" })] })] })] }));
}
export function MainspringPage({ lang }) {
    const [thickUm, setThickUm] = useState(200);
    const [widthMm, setWidthMm] = useState(1);
    const [turns, setTurns] = useState(6);
    const [powerW, setPowerW] = useState(1e-5);
    const [hours, setHours] = useState(744);
    const ms = useCalc((b) => api.calcMainspring(b));
    const pr = useCalc((b) => api.calcPowerReserve(b));
    const r = ms.result;
    const p = pr.result;
    return (_jsxs("div", { className: "page", children: [_jsx("h2", { children: t(lang, 'mainspring') }), _jsxs("div", { className: "grid2", children: [_jsxs(ResultCard, { title: t(lang, 'parameters'), children: [_jsx(Num, { label: "Thickness (\u00B5m)", value: thickUm, set: setThickUm }), _jsx(Num, { label: "Width (mm)", value: widthMm, set: setWidthMm, step: 0.1 }), _jsx(Num, { label: "Active turns", value: turns, set: setTurns }), _jsx(Num, { label: "Avg consumption (W)", value: powerW, set: setPowerW, step: 0.000001 }), _jsx(Num, { label: "Target hours", value: hours, set: setHours }), _jsxs("div", { className: "row", children: [_jsx("button", { className: "btn", onClick: () => ms.run({ thicknessM: thickUm / 1e6, widthM: widthMm / 1000, lengthM: 0.5, innerRadiusM: 0.01, outerRadiusM: 0.05, barrelDiameterM: 0.11, arborDiameterM: 0.015, activeTurns: turns, materialId: 'blued-steel' }), children: t(lang, 'calculate') }), _jsx("button", { className: "btn", disabled: !r, onClick: () => pr.run({ storedEnergyJ: r.storedEnergyJ, avgPowerConsumptionW: powerW, transmissionEfficiency: 0.8, targetHours: hours }), children: t(lang, 'powerReserve') })] }), ms.error && _jsx("div", { className: "error", children: ms.error }), pr.error && _jsx("div", { className: "error", children: pr.error })] }), _jsxs(ResultCard, { title: t(lang, 'results'), children: [r && (_jsxs(_Fragment, { children: [_jsx(LabelBadge, { label: String(r.resultType) }), _jsx(KV, { k: "Stored energy (J)", v: r.storedEnergyJ.toFixed(4) }), _jsx(KV, { k: "Max torque (mN\u00B7m)", v: (r.maxTorqueNm * 1000).toFixed(3) }), _jsx(KV, { k: "Max stress (MPa)", v: (r.maxStressPa / 1e6).toFixed(0) }), _jsx(KV, { k: "Safety factor", v: r.safetyFactor.toFixed(2) }), _jsx(LineChart, { data: r.torqueCurve, yLabel: "T (N\u00B7m)" }), _jsx(Warnings, { items: r.warnings ?? [] })] })), p && (_jsxs(_Fragment, { children: [_jsx(KV, { k: "Achievable (h)", v: p.achievableHours.toFixed(1) }), _jsx(KV, { k: "Feasible", v: p.feasible ? t(lang, 'feasible') : t(lang, 'infeasible') }), _jsx(Warnings, { items: p.warnings ?? [] })] })), !r && _jsx("div", { className: "empty", children: "\u2014" })] })] })] }));
}
export function BalancePage({ lang }) {
    const [kappa, setKappa] = useState(1e-6);
    const [massG, setMassG] = useState(0.2);
    const [amp, setAmp] = useState(270);
    const bal = useCalc((b) => api.calcBalance(b));
    const r = bal.result;
    return (_jsxs("div", { className: "page", children: [_jsx("h2", { children: t(lang, 'balance') }), _jsxs("div", { className: "grid2", children: [_jsxs(ResultCard, { title: t(lang, 'parameters'), children: [_jsx(Num, { label: "\u03BA hairspring (N\u00B7m/rad)", value: kappa, set: setKappa, step: 0.0000001 }), _jsx(Num, { label: "Balance mass (g)", value: massG, set: setMassG, step: 0.01 }), _jsx(Num, { label: "Amplitude (\u00B0)", value: amp, set: setAmp }), _jsx("button", { className: "btn", onClick: () => bal.run({ diameterM: 0.02, thicknessM: 0.001, massKg: massG / 1000, timingScrewMassKg: 0.00005, timingScrewRadiusM: 0.009, hairspringStiffnessNmPerRad: kappa, hairspringLengthM: 0.05, materialId: 'gilt-brass', amplitudeDeg: amp }), children: t(lang, 'calculate') }), bal.error && _jsx("div", { className: "error", children: bal.error })] }), _jsxs(ResultCard, { title: t(lang, 'results'), children: [r && (_jsxs(_Fragment, { children: [_jsx(LabelBadge, { label: "Calculated" }), _jsx(KV, { k: "Frequency (Hz)", v: r.frequencyHz.toFixed(3) }), _jsx(KV, { k: "Period (s)", v: r.periodS.toFixed(4) }), _jsx(KV, { k: "Beat rate (vph)", v: r.beatRateVph.toFixed(0) }), _jsx(KV, { k: "Inertia (kg\u00B7m\u00B2)", v: r.inertiaKgM2.toExponential(3) }), _jsx(KV, { k: "Rate per 0.1 g screw (s/day)", v: r.ratePerTenthGramSecPerDay.toFixed(2) }), _jsx(KV, { k: "Temp shift (s/day/K)", v: r.temperatureRateShiftSecPerDayPerK.toFixed(2) }), _jsx(Warnings, { items: r.warnings ?? [] })] })), !r && _jsx("div", { className: "empty", children: "\u2014" })] })] })] }));
}
export function EscapementPage({ lang }) {
    const [freq, setFreq] = useState(2);
    const [teeth, setTeeth] = useState(15);
    const esc = useCalc((b) => api.calcEscapement(b));
    const sim = useCalc((b) => api.simEscapement(b));
    const params = () => ({ type: 'swiss-lever', escapeTeeth: teeth, escapeDiameterM: 0.012, palletAngleDeg: 180, lockingAngleDeg: 2, dropDeg: 1, liftDeg: 3, drawDeg: 1, impulseAngleDeg: 8, balanceFrequencyHz: freq, balanceInertiaKgM2: 1e-8, hairspringStiffnessNmPerRad: 1.5e-6, amplitudeDeg: 270, escapeWheelTorqueNm: 1e-5 });
    const r = esc.result;
    const s = sim.result;
    return (_jsxs("div", { className: "page", children: [_jsx("h2", { children: t(lang, 'escapement') }), _jsxs("div", { className: "grid2", children: [_jsxs(ResultCard, { title: t(lang, 'parameters'), children: [_jsx(Num, { label: "Balance freq (Hz)", value: freq, set: setFreq, step: 0.1 }), _jsx(Num, { label: "Escape teeth", value: teeth, set: setTeeth }), _jsxs("div", { className: "row", children: [_jsx("button", { className: "btn", onClick: () => esc.run(params()), children: t(lang, 'calculate') }), _jsxs("button", { className: "btn", onClick: () => sim.run({ params: params(), durationS: 5 }), children: [t(lang, 'simulate'), " (event-based)"] })] }), esc.error && _jsx("div", { className: "error", children: esc.error }), sim.error && _jsx("div", { className: "error", children: sim.error })] }), _jsxs(ResultCard, { title: t(lang, 'results'), children: [r && (_jsxs(_Fragment, { children: [_jsx(LabelBadge, { label: "Calculated" }), _jsx(KV, { k: "Tooth pitch (\u00B0)", v: r.toothPitchDeg.toFixed(2) }), _jsx(Warnings, { items: r.warnings ?? [] })] })), s && (_jsxs(_Fragment, { children: [_jsx(LabelBadge, { label: "Simulated" }), _jsx(KV, { k: "Beats", v: String(s.beats) }), _jsx(KV, { k: "Energy/beat (\u00B5J)", v: (s.energyPerBeatJ * 1e6).toFixed(2) }), _jsx(KV, { k: "Avg power (\u00B5W)", v: (s.avgPowerW * 1e6).toFixed(2) }), _jsx(KV, { k: "Wheel revs", v: s.escapeWheelRevs.toFixed(3) }), _jsx(Warnings, { items: s.warnings ?? [] })] })), !r && !s && _jsx("div", { className: "empty", children: "\u2014" })] })] })] }));
}
export function TourbillonPage({ lang }) {
    const [freq, setFreq] = useState(2);
    const [fixed, setFixed] = useState(80);
    const [pinion, setPinion] = useState(8);
    const tb = useCalc((b) => api.calcTourbillon(b));
    const r = tb.result;
    const body = () => ({ cageDiameterM: 0.07, cageHeightM: 0.012, cageMassKg: 0.005, cageInertiaKgM2: 1e-6, cagePeriodS: 60, balanceDiameterM: 0.02, balanceFrequencyHz: freq, escapeTeeth: 15, fixedWheelTeeth: fixed, pinionTeeth: pinion, shaftDiameterM: 0.0005, bearingInnerDiameterM: 0.0005, radialClearanceM: 0.00001, axialClearanceM: 0.00005, escapeWheelTorqueNm: 1e-5 });
    return (_jsxs("div", { className: "page", children: [_jsx("h2", { children: t(lang, 'tourbillon') }), _jsxs("div", { className: "grid2", children: [_jsxs(ResultCard, { title: t(lang, 'parameters'), children: [_jsx(Num, { label: "Balance freq (Hz)", value: freq, set: setFreq, step: 0.1 }), _jsx(Num, { label: "Fixed wheel teeth", value: fixed, set: setFixed }), _jsx(Num, { label: "Pinion teeth", value: pinion, set: setPinion }), _jsx("button", { className: "btn", onClick: () => tb.run(body()), children: t(lang, 'calculate') }), tb.error && _jsx("div", { className: "error", children: tb.error })] }), _jsxs(ResultCard, { title: t(lang, 'results'), children: [r && (_jsxs(_Fragment, { children: [_jsx(LabelBadge, { label: "Calculated" }), _jsx(KV, { k: "Cage \u03C9 (rad/s)", v: r.cageAngularVelocityRadps.toFixed(5) }), _jsx(KV, { k: "Required ratio", v: r.requiredRatio.toFixed(2) }), _jsx(KV, { k: "Actual ratio", v: r.actualRatio.toFixed(2) }), _jsx(KV, { k: "Ratio error (%)", v: r.ratioErrorPct.toFixed(1) }), _jsx(KV, { k: "Bearing load (N)", v: r.bearingLoadN.toFixed(3) }), _jsx(KV, { k: "Avg power (\u00B5W)", v: (r.avgPowerW * 1e6).toFixed(2) }), _jsx(Warnings, { items: r.warnings ?? [] })] })), !r && _jsx("div", { className: "empty", children: "\u2014" })] })] })] }));
}
export function SimulationPage({ lang }) {
    const [mode, setMode] = useState('rigid-body');
    const sim = useCalc((b) => api.simDynamics(b));
    const r = sim.result;
    const samples = r?.samples ?? [];
    return (_jsxs("div", { className: "page", children: [_jsx("h2", { children: t(lang, 'simulation') }), _jsxs("div", { className: "grid2", children: [_jsxs(ResultCard, { title: t(lang, 'parameters'), children: [_jsxs("label", { className: "field", children: [_jsx("span", { children: "Mode" }), _jsxs("select", { value: mode, onChange: (e) => setMode(e.target.value), children: [_jsx("option", { value: "rigid-body", children: "Rigid-body dynamics" }), _jsx("option", { value: "kinematic", children: "Kinematic (not validated)" }), _jsx("option", { value: "contact", children: "Contact & friction" })] })] }), _jsx("p", { className: "hint", children: "Spring oscillator (\u03BA=1, I=1) integrated with RK4. Energy drift is reported \u2014 a basic animation is never labelled as validated simulation." }), _jsx("button", { className: "btn", onClick: () => sim.run({ bodies: [{ id: 'balance', inertiaKgM2: 1, angleRad: 1, angularVelocityRadps: 0, torqueNm: 0, spring: { stiffness: 1, restAngleRad: 0 } }], opts: { mode, durationS: 6.28, dtS: 0.001 } }), children: t(lang, 'simulate') }), sim.error && _jsx("div", { className: "error", children: sim.error })] }), _jsxs(ResultCard, { title: t(lang, 'results'), children: [r && (_jsxs(_Fragment, { children: [_jsx(LabelBadge, { label: "Simulated" }), _jsx(KV, { k: "Mode", v: String(r.mode) }), _jsx(KV, { k: "Stable", v: String(r.stable) }), _jsx(KV, { k: "Energy drift (%)", v: r.energyDriftPct.toFixed(3) }), _jsx(LineChart, { data: samples.map((s) => [s.t, s.totalEnergyJ]), yLabel: "E (J)" }), _jsx(Warnings, { items: r.warnings ?? [] })] })), !r && _jsx("div", { className: "empty", children: "\u2014" })] })] })] }));
}
export function EnergyPage({ lang }) {
    const [stored, setStored] = useState(10);
    const [power, setPower] = useState(1e-5);
    const [hours, setHours] = useState(744);
    const en = useCalc((b) => api.calcEnergy(b));
    const r = en.result;
    return (_jsxs("div", { className: "page", children: [_jsx("h2", { children: t(lang, 'energy') }), _jsxs("div", { className: "grid2", children: [_jsxs(ResultCard, { title: t(lang, 'parameters'), children: [_jsx(Num, { label: "Stored energy (J)", value: stored, set: setStored, step: 0.1 }), _jsx(Num, { label: "Avg power (W)", value: power, set: setPower, step: 0.000001 }), _jsx(Num, { label: "Target (h)", value: hours, set: setHours }), _jsx("button", { className: "btn", onClick: () => en.run({ budget: { storedEnergyJ: stored, gearFrictionPct: 10, bearingFrictionPct: 5, escapementLossPct: 20, balanceLossPct: 5, cageLossPct: 5, transmissionEfficiency: 0.8 }, avgPowerConsumptionW: power, targetHours: hours }), children: t(lang, 'calculate') }), en.error && _jsx("div", { className: "error", children: en.error })] }), _jsxs(ResultCard, { title: t(lang, 'results'), children: [r && (_jsxs(_Fragment, { children: [_jsx(LabelBadge, { label: "Calculated" }), _jsx(KV, { k: "Usable (J)", v: r.usableJ.toFixed(3) }), _jsx(KV, { k: "Required (J)", v: r.requiredJ.toFixed(3) }), _jsx(KV, { k: "Reserve (h)", v: r.powerReserveHours.toFixed(1) }), _jsx(KV, { k: "Feasible", v: r.feasible ? t(lang, 'feasible') : t(lang, 'infeasible') }), _jsx(Warnings, { items: r.warnings ?? [] })] })), !r && _jsx("div", { className: "empty", children: "\u2014" })] })] })] }));
}
export function TolerancePage({ lang }) {
    const tol = useCalc((b) => api.calcTolerance(b));
    const r = tol.result;
    return (_jsxs("div", { className: "page", children: [_jsx("h2", { children: t(lang, 'tolerance') }), _jsxs("div", { className: "grid2", children: [_jsxs(ResultCard, { title: t(lang, 'parameters'), children: [_jsx("p", { className: "hint", children: "Stack: 10.000 \u00B10.100 mm + 5.000 \u00B10.100 mm (worst-case / RSS / Monte Carlo, 10k samples)." }), _jsx("button", { className: "btn", onClick: () => tol.run({ items: [{ name: 'a', nominalM: 0.01, plusTolM: 0.0001, minusTolM: 0.0001 }, { name: 'b', nominalM: 0.005, plusTolM: 0.0001, minusTolM: 0.0001 }], opts: { samples: 10000, seed: 42 } }), children: t(lang, 'calculate') }), tol.error && _jsx("div", { className: "error", children: tol.error })] }), _jsxs(ResultCard, { title: t(lang, 'results'), children: [r && (_jsxs(_Fragment, { children: [_jsx(LabelBadge, { label: "Calculated" }), _jsx(KV, { k: "Nominal (mm)", v: (r.nominalM * 1000).toFixed(3) }), _jsx(KV, { k: "Worst-case \u00B1 (\u00B5m)", v: (r.worstCasePlusM * 1e6).toFixed(1) }), _jsx(KV, { k: "RSS \u00B1 (\u00B5m)", v: (r.rssToleranceM * 1e6).toFixed(1) }), _jsx(KV, { k: "MC \u03C3 (\u00B5m)", v: (r.monteCarloStdM * 1e6).toFixed(1) }), _jsx(KV, { k: "MC P99 (mm)", v: `${(r.monteCarloP99LowM * 1000).toFixed(3)} … ${(r.monteCarloP99HighM * 1000).toFixed(3)}` }), _jsx(Warnings, { items: r.warnings ?? [] })] })), !r && _jsx("div", { className: "empty", children: "\u2014" })] })] })] }));
}
