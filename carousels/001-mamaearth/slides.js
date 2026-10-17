// Business Model #001 — Mamaearth (Honasa Consumer). Copy + sources: content/001-mamaearth.md
const L = (n) => `logos/${n}-logo.png`;
const fileUrl = (p) => 'file://' + require('path').resolve(__dirname, '../..', p);

const logoCard = (n, label) => `
  <div class="lc"><img src="${fileUrl(L(n))}" alt="${label}"></div>`;

module.exports = {
  brandLogo: L('mamaearth'),
  ownLogo: 'logos/incbusiness-logo-white.png',
  seriesTag: 'BUSINESS MODEL #001',
  slides: [
    // 1 — Hook
    {
      css: `
        .cover { position:absolute; left:0; right:0; top:-420px; height:1350px;
          background:url('${fileUrl('carousels/001-mamaearth/images/cover.png')}') center/cover; }
        .fade { position:absolute; left:0; right:0; top:0; height:1350px;
          background:linear-gradient(180deg, rgba(40,39,90,0) 0%, rgba(40,39,90,0) 40%, rgba(40,39,90,.85) 56%, #3a3778 66%, #48409a 100%); }
        .content { top: 700px; }
        h1 { font-size: 64px; }
        .big { font-size: 76px; color: var(--amber); font-weight: 900; letter-spacing:-2px; line-height:1.05; margin-top:14px; }
      `,
      html: `
        <div style="position:fixed;inset:0;z-index:-1"><div class="cover"></div><div class="fade"></div></div>
        <h1>Two parents couldn't find a safe baby lotion in India.</h1>
        <div class="big">So they built a ₹2,392 Cr company.</div>
        <div class="lead">How Mamaearth makes money →</div>`,
      source: 'Revenue: FY26 (Apr 2025 – Mar 2026), Honasa Consumer. Sources: Inc42, Bajaj Broking, Ventura Securities',
    },

    // 2 — The problem
    {
      css: `
        .tl { margin-top: 60px; position: relative; padding-left: 64px; }
        .tl:before { content:''; position:absolute; left:20px; top:14px; bottom:30px; width:4px; background:rgba(249,203,66,.35); border-radius:4px; }
        .step { position: relative; margin-bottom: 52px; }
        .step:before { content:''; position:absolute; left:-56px; top:8px; width:28px; height:28px; border-radius:50%;
          background: var(--amber); box-shadow: 0 0 0 8px rgba(249,203,66,.18); }
        .yr { color: var(--amber); font-weight: 800; font-size: 28px; letter-spacing: 2px; }
        .tx { font-size: 38px; line-height: 1.38; margin-top: 8px; }
        .badge { display:inline-block; margin-top:10px; background:#fff; color:#1c1b3a; font-weight:800; font-size:26px; padding:10px 22px; border-radius:14px; }
      `,
      html: `
        <div class="eyebrow">The problem</div>
        <h1>It started with a <span class="hl">newborn</span>.</h1>
        <div class="tl">
          <div class="step"><div class="yr">2014</div>
            <div class="tx">Varun &amp; Ghazal Alagh's son is born. They can't find <b>toxin-free baby products</b> in India.</div></div>
          <div class="step"><div class="yr">THE WORKAROUND</div>
            <div class="tx">Friends &amp; family bring baby products back <b>from the US</b>. Costly and slow.</div></div>
          <div class="step"><div class="yr">2016</div>
            <div class="tx">They launch Mamaearth with <b>6 toxin-free baby products</b>.</div></div>
          <div class="step"><div class="yr">THE TRUST BADGE</div>
            <div class="tx">Asia's first <b>MADE SAFE</b>-certified brand.</div></div>
        </div>`,
      source: 'Sources: Business Today, Entrepreneur India, 5paisa, Images RetailME, exchange4media',
    },

    // 3 — The model
    {
      css: `
        .flow { display:flex; flex-direction:column; gap:0; margin-top:40px; }
        .node { display:flex; align-items:center; gap:26px; }
        .num { flex:none; width:70px; height:70px; border-radius:20px; background:var(--amber); color:var(--dark);
          font-weight:900; font-size:34px; display:flex; align-items:center; justify-content:center; }
        .node .card { flex:1; padding:22px 30px; }
        .node b { font-size: 32px; display:block; }
        .node span { font-size: 25px; color: var(--sub); }
        .down { margin-left: 24px; height: 34px; width: 4px; background: rgba(249,203,66,.5); }
        .hob { margin-top: 40px; }
        .hob .t { font-size: 26px; font-weight:800; letter-spacing:3px; color:var(--amber); margin-bottom:18px; }
        .grid { display:grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
        .lc { background:#fff; border-radius:18px; height:92px; display:flex; align-items:center; justify-content:center; padding:12px 18px; }
        .lc img { max-height:58px; max-width:100%; }
      `,
      html: `
        <div class="eyebrow">The business model</div>
        <h1>Own the brand.<br><span class="hl">Outsource the factory.</span></h1>
        <div class="flow">
          <div class="node"><div class="num">1</div><div class="card"><b>Honasa owns the brand</b><span>Formulas, marketing &amp; the customer</span></div></div>
          <div class="down"></div>
          <div class="node"><div class="num">2</div><div class="card"><b>Contract manufacturers make it</b><span>Third-party factories produce the products</span></div></div>
          <div class="down"></div>
          <div class="node"><div class="num">3</div><div class="card"><b>Sold online + offline</b><span>Marketplaces, quick commerce, own website &amp; shops</span></div></div>
        </div>
        <div class="hob"><div class="t">A HOUSE OF BRANDS</div>
          <div class="grid">
            ${logoCard('mamaearth', 'Mamaearth')}${logoCard('thedermaco', 'The Derma Co')}${logoCard('aqualogica', 'Aqualogica')}
            ${logoCard('drsheths', "Dr. Sheth's")}${logoCard('bblunt', 'BBlunt')}${logoCard('staze', 'Staze')}
          </div></div>`,
      source: 'Sources: IPO filings via Swastika & DSIJ, Lapaas, Inc42, Outlook Business, Medianama',
    },

    // 4 — How they make money
    {
      css: `
        .stat { margin-top: 34px; display:flex; gap: 36px; align-items:center; }
        .donut { flex:none; width: 250px; height: 250px; border-radius: 50%;
          background: conic-gradient(var(--amber) 0 32.9%, rgba(207,201,242,.18) 32.9% 100%);
          display:flex; align-items:center; justify-content:center; }
        .donut div { width: 172px; height: 172px; border-radius:50%; background:#33316c; display:flex; align-items:center; justify-content:center;
          font-size: 42px; font-weight: 900; color: var(--amber); letter-spacing:-1px; }
        .stat .card { flex:1; }
        .k { font-size: 36px; font-weight: 800; line-height:1.2; }
        .s { font-size: 25px; color: var(--sub); margin-top: 10px; line-height:1.35; }
        .growth { font-size: 120px; font-weight: 900; color: var(--green); letter-spacing:-4px; line-height:1; }
        .mini { display:flex; gap:12px; margin-top:16px; flex-wrap:wrap; }
        .mini .lc { background:#fff; border-radius:12px; height:60px; padding:8px 14px; display:flex; align-items:center; }
        .mini img { max-height:38px; max-width:150px; }
      `,
      html: `
        <div class="eyebrow">How they make money</div>
        <h1>Sell products.<br><span class="hl">Spend big on ads.</span></h1>
        <div class="lead">Revenue comes from selling beauty &amp; personal-care products, online and in shops.</div>
        <div class="stat">
          <div class="donut"><div>32.9%</div></div>
          <div class="card"><div class="k">of revenue went to advertising</div><div class="s">Nearly ₹1 of every ₹3 earned, in Q4 FY26 (Jan–Mar 2026).</div></div>
        </div>
        <div class="card" style="margin-top:30px; display:flex; gap:30px; align-items:center;">
          <div class="growth">40%+</div>
          <div><div class="k">growth of the younger brands in FY26</div>
            <div class="mini">${logoCard('thedermaco', 'The Derma Co')}${logoCard('aqualogica', 'Aqualogica')}${logoCard('drsheths', "Dr. Sheth's")}</div></div>
        </div>`,
      source: 'Sources: Bajaj Broking, Multibagg, Inc42, Outlook Business',
    },

    // 5 — Crash & comeback
    {
      css: `
        .row { display:flex; gap:22px; margin-top: 30px; }
        .row .card { flex:1; padding: 24px 26px; }
        .d { color: var(--amber); font-weight:800; font-size: 22px; letter-spacing:2px; }
        .v { font-size: 50px; font-weight: 900; margin-top: 6px; letter-spacing:-1px; }
        .n { font-size: 23px; color: var(--sub); margin-top: 6px; line-height:1.35; }
        .crash { margin-top: 22px; border-color: rgba(255,90,95,.6); background: rgba(255,90,95,.10); display:flex; align-items:center; gap:28px; }
        .crash .v { font-size: 104px; color: var(--red); line-height:1; }
        .fix { margin-top: 22px; }
        .chain { display:flex; align-items:center; gap:10px; margin-top: 14px; font-size: 23px; font-weight: 700; flex-wrap: nowrap; }
        .chip { background: rgba(255,255,255,.12); border-radius: 12px; padding: 10px 14px; white-space: nowrap; }
        .chip.x { text-decoration: line-through; text-decoration-thickness: 4px; text-decoration-color: var(--red); color: rgba(255,255,255,.5); }
        .chip.ok { background: var(--amber); color: var(--dark); }
        .lbl { font-size: 20px; color: var(--sub); font-weight: 700; letter-spacing: 2px; width: 92px; flex:none; }
      `,
      html: `
        <div class="eyebrow">The crash &amp; the comeback</div>
        <h1>From IPO to a <span class="red">20% crash</span> in a year.</h1>
        <div class="row">
          <div class="card"><div class="d">NOV 2023</div><div class="v">₹324</div><div class="n">IPO price per share</div></div>
          <div class="card"><div class="d">NOV 2024</div><div class="v">−₹18.6 Cr</div><div class="n">First quarterly loss. Distributors held too much stock.</div></div>
        </div>
        <div class="card crash"><div class="v">−20%</div><div class="n" style="font-size:30px;color:#fff;font-weight:700">Stock fell in one day, below the IPO price</div></div>
        <div class="card fix"><div class="d">THE FIX: PROJECT NEEV</div>
          <div class="chain"><div class="lbl">BEFORE</div><div class="chip">Honasa</div>→<div class="chip x">Super-stockist</div>→<div class="chip">Distributor</div>→<div class="chip">Shop</div></div>
          <div class="chain"><div class="lbl">AFTER</div><div class="chip">Honasa</div>→<div class="chip ok">Direct distributor</div>→<div class="chip">Shop</div></div>
          <div class="n" style="margin-top:12px">Rolled out across India's top 50 cities</div>
        </div>`,
      source: 'Q2 FY25 = Jul–Sep 2024, reported Nov 2024. Sources: Business Standard, BusinessWorld, YourStory, Medianama, Outlook Business',
    },

    // 6 — Numbers
    {
      css: `
        .charts { display:flex; gap: 26px; margin-top: 40px; }
        .charts .card { flex:1; padding: 28px; }
        .ct { font-size: 26px; font-weight: 800; letter-spacing: 2px; color: var(--sub); }
        .bars { display:flex; align-items:flex-end; gap: 26px; height: 330px; margin-top: 22px; }
        .bar { flex:1; display:flex; flex-direction:column; align-items:center; justify-content:flex-end; height:100%; }
        .bar .b { width:100%; border-radius: 14px 14px 4px 4px; background: rgba(207,201,242,.35); }
        .bar.now .b { background: linear-gradient(180deg, var(--amber), var(--amber-deep)); }
        .bar .val { font-size: 32px; font-weight: 900; margin-bottom: 10px; }
        .bar.now .val { color: var(--amber); }
        .bar .yr { font-size: 22px; color: var(--sub); margin-top: 10px; font-weight:700; }
        .chg { font-size: 30px; font-weight: 900; color: var(--green); margin-top: 16px; }
        .div { margin-top: 26px; display:flex; align-items:center; justify-content:space-between; }
        .div .v { font-size: 64px; font-weight: 900; color: var(--amber); }
        .div .n { font-size: 28px; font-weight: 700; }
      `,
      html: `
        <div class="eyebrow">The numbers · FY26</div>
        <h1>Growth is back.<br><span class="hl">Profit nearly tripled.</span></h1>
        <div class="charts">
          <div class="card"><div class="ct">REVENUE</div>
            <div class="bars">
              <div class="bar"><div class="val">₹2,067 Cr</div><div class="b" style="height:${(2067/2392*230).toFixed(0)}px"></div><div class="yr">FY25</div></div>
              <div class="bar now"><div class="val">₹2,392 Cr</div><div class="b" style="height:230px"></div><div class="yr">FY26</div></div>
            </div><div class="chg">▲ 16%</div></div>
          <div class="card"><div class="ct">NET PROFIT</div>
            <div class="bars">
              <div class="bar"><div class="val">₹73 Cr</div><div class="b" style="height:${(73/200*230).toFixed(0)}px"></div><div class="yr">FY25</div></div>
              <div class="bar now"><div class="val">₹200 Cr</div><div class="b" style="height:230px"></div><div class="yr">FY26</div></div>
            </div><div class="chg">▲ 2.75x</div></div>
        </div>
        <div class="card div"><div class="n">First-ever dividend</div><div class="v">₹3 / share</div></div>
        <div class="lead" style="margin-top:26px;color:#fff;font-weight:700">Follow for Business Model #002 →</div>`,
      source: 'FY26 = Apr 2025 – Mar 2026. Sources: Inc42, Bajaj Broking, Ventura Securities, Multibagg',
    },
  ],
};
