const en = {
    appTitle: 'Horology Engineering',
    appSubtitle: 'Parametric Mechanical Watch Design & Simulation Environment',
    dashboard: 'Dashboard', projects: 'Projects', cad: 'CAD Workspace', library: 'Component Library',
    gear: 'Gear Engineering', mainspring: 'Mainspring', balance: 'Balance & Hairspring',
    escapement: 'Escapement', tourbillon: 'Tourbillon', simulation: 'Simulation',
    energy: 'Energy Analysis', tolerance: 'Tolerance Analysis', manufacturing: 'Manufacturing',
    reports: 'Reports', settings: 'Settings',
    calculate: 'Calculate', simulate: 'Simulate', export: 'Export', save: 'Save', load: 'Load',
    results: 'Results', warnings: 'Warnings', parameters: 'Parameters',
    metric: 'Metric', imperial: 'Imperial', language: 'Language',
    running: 'Running', paused: 'Paused', play: 'Play', pause: 'Pause', step: 'Step', speed: 'Speed',
    resultType: 'Result type', validated: 'Validated', calculated: 'Calculated', estimated: 'Estimated',
    simulated: 'Simulated', measured: 'Measured',
    powerReserve: 'Power reserve', feasible: 'Feasible', infeasible: 'Infeasible',
    search: 'Search…', create: 'Create', duplicate: 'Duplicate', delete: 'Delete', update: 'Update',
    bom: 'Bill of Materials', download: 'Download',
    referenceProject: '300 mm Wall Clock with One-Minute Tourbillon',
    note: 'Design targets — verify with calculations before manufacturing.'
};
const fa = {
    appTitle: 'مهندسی ساعت‌سازی',
    appSubtitle: 'محیط طراحی و شبیه‌سازی پارامتریک ساعت مکانیکی',
    dashboard: 'داشبورد', projects: 'پروژه‌ها', cad: 'محیط CAD', library: 'کتابخانه قطعات',
    gear: 'مهندسی چرخ‌دنده', mainspring: 'فنر اصلی', balance: 'تعادل و فنر مو',
    escapement: 'چرخ گریز', tourbillon: 'توربیون', simulation: 'شبیه‌سازی',
    energy: 'تحلیل انرژی', tolerance: 'تحلیل تلرانس', manufacturing: 'ساخت',
    reports: 'گزارش‌ها', settings: 'تنظیمات',
    calculate: 'محاسبه', simulate: 'شبیه‌سازی', export: 'خروجی', save: 'ذخیره', load: 'بارگذاری',
    results: 'نتایج', warnings: 'هشدارها', parameters: 'پارامترها',
    metric: 'متریک', imperial: 'امپریال', language: 'زبان',
    running: 'در حال اجرا', paused: 'متوقف', play: 'پخش', pause: 'توقف', step: 'گام', speed: 'سرعت',
    resultType: 'نوع نتیجه', validated: 'تأییدشده', calculated: 'محاسباتی', estimated: 'برآوردی',
    simulated: 'شبیه‌سازی‌شده', measured: 'اندازه‌گیری‌شده',
    powerReserve: 'ذخیره توان', feasible: 'امکان‌پذیر', infeasible: 'غیرامکان‌پذیر',
    search: 'جستجو…', create: 'ایجاد', duplicate: 'کپی', delete: 'حذف', update: 'به‌روزرسانی',
    bom: 'فهرست قطعات', download: 'دانلود',
    referenceProject: 'ساعت دیواری ۳۰۰ میلی‌متری با توربیون یک‌دقیقه‌ای',
    note: 'اهداف طراحی — پیش از ساخت با محاسبات راستی‌آزمایی کنید.'
};
export const dict = { en, fa };
export function t(lang, key) {
    return dict[lang][key] ?? en[key];
}
