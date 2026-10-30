(() => {
  const $ = id => document.getElementById(id);
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const inr = n => '₹' + Math.round(n).toLocaleString('en-IN');
  const root = document.documentElement;

  // theme toggle (initial theme is set inline in <head> to avoid a flash)
  document.querySelectorAll('.theme-btn').forEach(b => b.addEventListener('click', () => {
    const next = root.dataset.theme === 'dark' ? 'light' : 'dark';
    root.dataset.theme = next;
    try { localStorage.setItem('lk-theme', next); } catch (e) {}
  }));

  // mobile menu
  const menu = $('menuBtn'), drawer = $('drawer');
  if (menu) menu.addEventListener('click', () => {
    const open = drawer.classList.toggle('open');
    menu.setAttribute('aria-expanded', open);
  });
  if (drawer) drawer.addEventListener('click', e => { if (e.target.closest('a')) drawer.classList.remove('open'); });

  // scale the hero devices stage to its container
  const box = document.querySelector('.stage-box');
  if (box) {
    const fit = () => box.style.setProperty('--s', Math.min(1, box.clientWidth / 640));
    fit();
    addEventListener('resize', fit);
  }

  // rotating hero word
  const rot = $('rot');
  if (rot && !reduce) {
    const words = rot.dataset.words.split('|');
    let i = 0;
    setInterval(() => { i = (i + 1) % words.length; rot.innerHTML = '<span>' + words[i] + '</span>'; }, 2400);
  }

  // live numbers + notifications in the hero mockups
  const sales = $('sales'), wsales = $('wsales');
  if (sales) {
    let target = 248650;
    const paint = v => { sales.textContent = inr(v); if (wsales) wsales.textContent = inr(v); };
    const t0 = performance.now();
    (function up(t) {
      const p = Math.min(1, (t - t0) / 1600);
      paint(target * (1 - Math.pow(1 - p, 3)));
      if (p < 1 && !reduce) requestAnimationFrame(up); else paint(target);
    })(reduce ? t0 + 2000 : t0);

    const toast = $('toast'), tt = $('tt'), ts = $('ts');
    const tabs = document.querySelectorAll('.tabs span');
    const events = [
      ['Invoice synced to Tally', 'INV-1042 · Gupta Traders', 38500, 0],
      ['Payment received', '₹12,900 · Mehta & Kumar', 12900, 1],
      ['Reminder sent on WhatsApp', 'Rao Enterprises · ₹24,000 due', 0, 0],
      ['e-Way Bill generated', 'EWB for INV-1043 · Pune', 21200, 1]
    ];
    let ei = 0;
    const fire = () => {
      const [a, b, add, tab] = events[ei++ % events.length];
      tt.textContent = a; ts.textContent = b;
      toast.classList.add('on');
      tabs.forEach((s, i) => s.classList.toggle('on', i === tab));
      if (add) {
        target += add; paint(target);
        [sales, wsales].forEach(el => el && el.animate && el.animate([{ color: '#a6f16a' }, { color: getComputedStyle(el).color }], { duration: 900 }));
      }
      setTimeout(() => toast.classList.remove('on'), 2600);
    };
    if (!reduce) { setTimeout(fire, 2000); setInterval(fire, 4200); }
  }

  // before / after switch
  const sw = $('sw'), list = $('baList');
  if (sw) {
    const data = {
      old: { cls: 'no', mark: '✕', items: [
        'Call the accountant every time you need a number',
        'Sales and dues only visible on one office computer',
        'Bills and e-Way Bills wait until someone is at the desk',
        'Collections slip because nobody followed up'
      ]},
      lk: { cls: 'yes', mark: '✓', items: [
        'Live sales, dues and stock on your phone and browser',
        'Owner, CA and sales team see the same numbers',
        'Create vouchers, e-Invoices and e-Way Bills on the go',
        'Automatic payment reminders do the chasing'
      ]}
    };
    const show = v => {
      sw.classList.toggle('lk', v === 'lk');
      sw.querySelectorAll('button').forEach(b => b.setAttribute('aria-pressed', b.dataset.v === v));
      const d = data[v];
      list.innerHTML = d.items.map(x => `<li class="${d.cls}"><i>${d.mark}</i>${x}</li>`).join('');
    };
    sw.addEventListener('click', e => { const b = e.target.closest('button'); if (b) show(b.dataset.v); });
    show('old');
    let flipped = false;
    new IntersectionObserver(([en], ob) => {
      if (en.isIntersecting && !flipped) { flipped = true; ob.disconnect(); setTimeout(() => show('lk'), 1400); }
    }, { threshold: .6 }).observe(sw);
  }

  // scroll reveal
  const io = new IntersectionObserver(es => es.forEach(e => { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } }), { threshold: .12 });
  document.querySelectorAll('.rv').forEach(el => io.observe(el));

  // nav background + mobile dock
  const top = $('top'), dock = $('dock'), dl = $('download');
  const onScroll = () => {
    top.classList.toggle('solid', scrollY > 20);
    if (dock) dock.classList.toggle('on', scrollY > innerHeight * .9 && !(dl && dl.getBoundingClientRect().top < innerHeight * .8));
  };
  addEventListener('scroll', onScroll, { passive: true });
  onScroll();
})();
