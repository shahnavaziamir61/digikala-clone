import React, { useState } from 'react';
import { Lang, t } from './i18n.js';
import CadWorkspace from './pages/CadWorkspace.js';
import { GearPage, MainspringPage, BalancePage, EscapementPage, TourbillonPage, SimulationPage, EnergyPage, TolerancePage } from './pages/EngineeringPages.js';
import { Dashboard, ProjectsPage, LibraryPage, ManufacturingPage, ReportsPage, SettingsPage } from './pages/SystemPages.js';

const NAV: { id: string; key: keyof typeof import('./i18n.js').dict.en }[] = [
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
  const [lang, setLang] = useState<Lang>('en');
  const [units, setUnits] = useState('metric');
  const rtl = lang === 'fa';

  return (
    <div className="app" dir={rtl ? 'rtl' : 'ltr'}>
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">◷</div>
          <div>
            <div className="brand-title">{t(lang, 'appTitle')}</div>
            <div className="brand-sub">{t(lang, 'appSubtitle')}</div>
          </div>
        </div>
        <nav>
          {NAV.map((n) => (
            <button key={n.id} className={page === n.id ? 'nav active' : 'nav'} onClick={() => setPage(n.id)}>
              {t(lang, n.key)}
            </button>
          ))}
        </nav>
        <div className="sidebar-foot">
          <div className="row">
            <button className="btn sm ghost" onClick={() => setLang(lang === 'en' ? 'fa' : 'en')}>{lang === 'en' ? 'فارسی' : 'EN'}</button>
            <button className="btn sm ghost" onClick={() => setUnits(units === 'metric' ? 'imperial' : 'metric')}>{units === 'metric' ? 'in' : 'mm'}</button>
          </div>
        </div>
      </aside>
      <main className="main">
        {page === 'dashboard' && <Dashboard lang={lang} onOpen={setPage} />}
        {page === 'projects' && <ProjectsPage lang={lang} />}
        {page === 'cad' && <CadWorkspace lang={lang} />}
        {page === 'library' && <LibraryPage lang={lang} />}
        {page === 'gear' && <GearPage lang={lang} />}
        {page === 'mainspring' && <MainspringPage lang={lang} />}
        {page === 'balance' && <BalancePage lang={lang} />}
        {page === 'escapement' && <EscapementPage lang={lang} />}
        {page === 'tourbillon' && <TourbillonPage lang={lang} />}
        {page === 'simulation' && <SimulationPage lang={lang} />}
        {page === 'energy' && <EnergyPage lang={lang} />}
        {page === 'tolerance' && <TolerancePage lang={lang} />}
        {page === 'manufacturing' && <ManufacturingPage lang={lang} />}
        {page === 'reports' && <ReportsPage lang={lang} />}
        {page === 'settings' && <SettingsPage lang={lang} setLang={setLang} units={units} setUnits={setUnits} />}
      </main>
    </div>
  );
}
