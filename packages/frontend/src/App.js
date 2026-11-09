import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState } from 'react';
import { t } from './i18n.js';
import CadWorkspace from './pages/CadWorkspace.js';
import { GearPage, MainspringPage, BalancePage, EscapementPage, TourbillonPage, SimulationPage, EnergyPage, TolerancePage } from './pages/EngineeringPages.js';
import { Dashboard, ProjectsPage, LibraryPage, ManufacturingPage, ReportsPage, SettingsPage } from './pages/SystemPages.js';
const NAV = [
    { id: 'dashboard', key: 'dashboard' },
    { id: 'projects', key: 'projects' },
    { id: 'cad', key: 'cad' },
    { id: 'library', key: 'library' },
    { id: 'gear', key: 'gear' },
    { id: 'mainspring', key: 'mainspring' },
    { id: 'balance', key: 'balance' },
    { id: 'escapement', key: 'escapement' },
    { id: 'tourbillon', key: 'tourbillon' },
    { id: 'simulation', key: 'simulation' },
    { id: 'energy', key: 'energy' },
    { id: 'tolerance', key: 'tolerance' },
    { id: 'manufacturing', key: 'manufacturing' },
    { id: 'reports', key: 'reports' },
    { id: 'settings', key: 'settings' }
];
export default function App() {
    const [page, setPage] = useState('dashboard');
    const [lang, setLang] = useState('en');
    const [units, setUnits] = useState('metric');
    const rtl = lang === 'fa';
    return (_jsxs("div", { className: "app", dir: rtl ? 'rtl' : 'ltr', children: [_jsxs("aside", { className: "sidebar", children: [_jsxs("div", { className: "brand", children: [_jsx("div", { className: "brand-mark", children: "\u25F7" }), _jsxs("div", { children: [_jsx("div", { className: "brand-title", children: t(lang, 'appTitle') }), _jsx("div", { className: "brand-sub", children: t(lang, 'appSubtitle') })] })] }), _jsx("nav", { children: NAV.map((n) => (_jsx("button", { className: page === n.id ? 'nav active' : 'nav', onClick: () => setPage(n.id), children: t(lang, n.key) }, n.id))) }), _jsx("div", { className: "sidebar-foot", children: _jsxs("div", { className: "row", children: [_jsx("button", { className: "btn sm ghost", onClick: () => setLang(lang === 'en' ? 'fa' : 'en'), children: lang === 'en' ? 'فارسی' : 'EN' }), _jsx("button", { className: "btn sm ghost", onClick: () => setUnits(units === 'metric' ? 'imperial' : 'metric'), children: units === 'metric' ? 'in' : 'mm' })] }) })] }), _jsxs("main", { className: "main", children: [page === 'dashboard' && _jsx(Dashboard, { lang: lang, onOpen: setPage }), page === 'projects' && _jsx(ProjectsPage, { lang: lang }), page === 'cad' && _jsx(CadWorkspace, { lang: lang }), page === 'library' && _jsx(LibraryPage, { lang: lang }), page === 'gear' && _jsx(GearPage, { lang: lang }), page === 'mainspring' && _jsx(MainspringPage, { lang: lang }), page === 'balance' && _jsx(BalancePage, { lang: lang }), page === 'escapement' && _jsx(EscapementPage, { lang: lang }), page === 'tourbillon' && _jsx(TourbillonPage, { lang: lang }), page === 'simulation' && _jsx(SimulationPage, { lang: lang }), page === 'energy' && _jsx(EnergyPage, { lang: lang }), page === 'tolerance' && _jsx(TolerancePage, { lang: lang }), page === 'manufacturing' && _jsx(ManufacturingPage, { lang: lang }), page === 'reports' && _jsx(ReportsPage, { lang: lang }), page === 'settings' && _jsx(SettingsPage, { lang: lang, setLang: setLang, units: units, setUnits: setUnits })] })] }));
}
