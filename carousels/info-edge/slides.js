// Business Model #1: Info Edge (Naukri). Copy + sources: content/blog/info-edge-business-model.md
const path = require('path');
const fileUrl = (p) => 'file://' + path.resolve(__dirname, '../..', p);
const img = (p) => fileUrl(p);

// Real brand logos captured from each brand's own website, shown on their own brand colour.
const LOGO = {
  naukri: ['logos/naukri-logo.png', '#ffffff'],
  acres: ['logos/99acres-logo.png', '#ffffff'],
  jeevansathi: ['logos/jeevansathi-logo.png', '#ffffff'],
  shiksha: ['logos/shiksha-logo.png', '#00706c'],
  jobhai: ['logos/jobhai-logo.png', '#f4f8fb'],
  infoedge: ['logos/infoedge-logo.png', '#ffffff'],
};
const tile = (k, h = 70) => `<div class="lt" style="background:${LOGO[k][1]}"><img src="${img(LOGO[k][0])}" style="height:${h}px"></div>`;

const COMMON = `
  .lt { border-radius: 18px; display:flex; align-items:center; justify-content:center; padding: 10px 18px; overflow:hidden; }
  .lt img { display:block; max-width:100%; object-fit:contain; }
  .pts { margin-top: 44px; display:flex; flex-direction:column; gap: 34px; }
  .pt { display:flex; gap: 22px; align-items:flex-start; }
  .pt .k { flex:none; width: 68px; height: 68px; border-radius: 18px; background: var(--amber); color: var(--dark);
    font-weight: 900; font-size: 30px; display:flex; align-items:center; justify-content:center; }
  .pt .t { font-size: 35px; line-height: 1.38; }
  .pt .t b { color: #fff; }
  .pt .t span { color: var(--sub); }
`;

module.exports = {
  brandLogo: 'logos/naukri-logo.png',
  ownLogo: 'logos/incbusiness-logo-white.png',
  seriesTag: 'BUSINESS MODEL #1',
  slides: [
    // 1. Cover
    {
      css: COMMON + `
        .photo { position:absolute; left:0; right:0; top:0; height: 900px;
          background:url('${img('carousels/info-edge/images/founder.jpg')}') center 18%/cover no-repeat; }
        .fade { position:absolute; left:0; right:0; top:0; height:1350px;
          background:linear-gradient(180deg, rgba(40,39,90,0) 0%, rgba(40,39,90,.05) 35%, rgba(40,39,90,.9) 58%, #3a3778 66%, #48409a 100%); }
        .content { top: 690px; }
        .cap { display:inline-block; background: rgba(28,27,58,.8); border:1.5px solid rgba(249,203,66,.6); color:#fff; font-size: 22px; font-weight:700;
          padding: 8px 18px; border-radius: 999px; margin-bottom: 26px; }
        h1 { font-size: 62px; }
        .big { font-size: 74px; color: var(--amber); font-weight: 900; letter-spacing:-2px; line-height:1.05; margin-top: 12px; }
      `,
      html: `
        <div style="position:fixed;inset:0;z-index:-1"><div class="photo"></div><div class="fade"></div></div>
        <div class="cap">Sanjeev Bikhchandani, Founder</div>
        <h1>It started in a servants' quarter.</h1>
        <div class="big">Now Naukri earns ₹2,256 Cr a year.</div>
        <div class="lead">Info Edge business model, explained →</div>`,
      source: 'FY26 (Apr 2025 to Mar 2026) recruitment revenue. Source: Info Edge Q4 FY26 earnings call',
    },

    // 2. The problem
    {
      css: COMMON,
      html: `
        <div class="eyebrow">The problem it solved</div>
        <h1>Jobs were hidden in <span class="hl">newspapers.</span></h1>
        <div class="pts">
          <div class="pt"><div class="k">a</div><div class="t"><b>Job hunting was slow.</b> <span>In the 1990s, people checked many newspapers for job ads.</span></div></div>
          <div class="pt"><div class="k">b</div><div class="t"><b>Hiring was hard.</b> <span>Companies had no easy way to reach good candidates.</span></div></div>
          <div class="pt"><div class="k">c</div><div class="t"><b>The spark.</b> <span>In 1996, Sanjeev Bikhchandani saw a stall marked "WWW" at an IT fair.</span></div></div>
          <div class="pt"><div class="k">d</div><div class="t"><b>The answer.</b> <span>He decided to put jobs online. Naukri.com went live in 1997.</span></div></div>
        </div>`,
      source: 'Sources: Wikipedia, Outlook India, Finology',
    },

    // 3. Key facts
    {
      css: COMMON + `
        .grid { display:grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 34px; }
        .st { padding: 24px 28px; }
        .st .v { font-size: 52px; font-weight: 900; color: var(--amber); letter-spacing:-1px; }
        .st .l { font-size: 24px; color: var(--sub); margin-top: 4px; line-height:1.3; }
        .row { display:grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-top: 26px; }
        .row .lt { height: 92px; }
      `,
      html: `
        <div class="eyebrow">About Info Edge</div>
        <h1>India's first listed <span class="hl">internet company.</span></h1>
        <div class="grid">
          <div class="card st"><div class="v">1995</div><div class="l">Info Edge founded</div></div>
          <div class="card st"><div class="v">2006</div><div class="l">Listed on the stock market (NSE: NAUKRI)</div></div>
          <div class="card st"><div class="v">115 Mn</div><div class="l">Resumes on Naukri</div></div>
          <div class="card st"><div class="v">21,000</div><div class="l">New resumes added every day</div></div>
        </div>
        <div class="row">${tile('naukri', 50)}${tile('acres', 56)}${tile('jeevansathi', 46)}${tile('shiksha', 74)}</div>`,
      source: 'Sources: Info Edge Q4 FY26 earnings call, exchange4media, Finology',
    },

    // 4. Core pillar: free for users, businesses pay
    {
      css: COMMON + `
        .shot { margin-top: 30px; border-radius: 22px; overflow:hidden; border: 4px solid rgba(255,255,255,.85);
          height: 330px; background:url('${img('carousels/info-edge/images/naukri-home.png')}') top center/cover no-repeat; box-shadow: 0 20px 50px rgba(0,0,0,.35); }
        .two { display:grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 26px; }
        .two .card { padding: 24px 28px; }
        .who { font-size: 24px; font-weight: 800; letter-spacing: 2px; }
        .pay { font-size: 46px; font-weight: 900; margin-top: 6px; }
        .what { font-size: 23px; color: var(--sub); margin-top: 6px; line-height: 1.35; }
      `,
      html: `
        <div class="eyebrow">The core idea</div>
        <h1>Free for users. <span class="hl">Businesses pay.</span></h1>
        <div class="shot"></div>
        <div class="two">
          <div class="card"><div class="who">JOB SEEKERS</div><div class="pay green">FREE</div><div class="what">Search and apply for jobs. Some pay for resume help and profile boosts.</div></div>
          <div class="card"><div class="who">RECRUITERS</div><div class="pay amber">PAY</div><div class="what">Subscriptions to post jobs and search Naukri's resume database.</div></div>
        </div>`,
      source: 'Screenshot: naukri.com homepage. Sources: Info Edge Q4 FY26 earnings call, Finology',
    },

    // 5. How it makes money
    {
      css: COMMON + `
        .rows { margin-top: 30px; display:flex; flex-direction:column; gap: 16px; }
        .r { display:grid; grid-template-columns: 230px 1fr; gap: 22px; align-items:center; padding: 18px 22px; }
        .r .lt { height: 78px; }
        .r .nm { font-size: 24px; color: var(--sub); }
        .r .val { font-size: 40px; font-weight: 900; }
        .bar { height: 14px; border-radius: 8px; background: rgba(207,201,242,.18); margin-top: 8px; overflow:hidden; }
        .bar i { display:block; height:100%; background: linear-gradient(90deg, var(--amber), var(--amber-deep)); }
        .pl { font-size: 21px; margin-top: 6px; }
      `,
      html: `
        <div class="eyebrow">How it makes money</div>
        <h1>Four businesses. <span class="hl">One is the giant.</span></h1>
        <div class="rows">
          <div class="card r">${tile('naukri', 46)}<div><div class="nm">Jobs · 74% of revenue</div><div class="val">₹2,256 Cr</div><div class="bar"><i style="width:74%"></i></div><div class="pl green">₹1,277 Cr profit · 57% margin</div></div></div>
          <div class="card r">${tile('acres', 52)}<div><div class="nm">Property · 16%</div><div class="val">₹488 Cr</div><div class="bar"><i style="width:16%"></i></div><div class="pl red">₹59 Cr loss</div></div></div>
          <div class="card r">${tile('shiksha', 70)}<div><div class="nm">Education · 6%</div><div class="val">₹170 Cr</div><div class="bar"><i style="width:6%"></i></div><div class="pl green">₹13 Cr profit</div></div></div>
          <div class="card r">${tile('jeevansathi', 40)}<div><div class="nm">Matrimony · 5%</div><div class="val">₹138 Cr</div><div class="bar"><i style="width:5%"></i></div><div class="pl red">₹4 Cr loss</div></div></div>
        </div>`,
      source: 'FY26 standalone revenue and operating profit or loss. Source: Info Edge Q4 FY26 earnings call',
    },

    // 6. Naukri: the cash machine
    {
      css: COMMON + `
        .hero { display:grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 34px; }
        .hero .card { padding: 26px 28px; }
        .hero .v { font-size: 82px; font-weight: 900; color: var(--amber); letter-spacing: -2px; line-height:1; }
        .hero .l { font-size: 25px; color: var(--sub); margin-top: 10px; line-height:1.3; }
      `,
      html: `
        <div class="eyebrow">Why Naukri is a cash machine</div>
        <h1>Customers <span class="hl">pay upfront.</span></h1>
        <div class="hero">
          <div class="card"><div class="v">57%</div><div class="l">Operating margin on Naukri's recruitment business</div></div>
          <div class="card"><div class="v">₹4,963 Cr</div><div class="l">Cash in the bank, March 2026</div></div>
        </div>
        <div class="pts">
          <div class="pt"><div class="k">a</div><div class="t"><b>Paid in advance.</b> <span>Recruiters buy subscriptions before they use them.</span></div></div>
          <div class="pt"><div class="k">b</div><div class="t"><b>Billed more than booked.</b> <span>₹3,178 Cr billed in FY26, ₹3,052 Cr booked as revenue.</span></div></div>
          <div class="pt"><div class="k">c</div><div class="t"><b>Most of the money.</b> <span>Recruitment is about 74% of Info Edge's revenue.</span></div></div>
        </div>`,
      source: 'FY26 standalone figures. Source: Info Edge Q4 FY26 earnings call',
    },

    // 7. Product and marketing (latest: 2025 and 2026)
    {
      css: COMMON + `
        .ai { margin-top: 30px; padding: 26px 30px; }
        .ai .h { font-size: 22px; font-weight: 800; letter-spacing: 2px; color: var(--amber); }
        .ai .b { font-size: 40px; font-weight: 900; margin-top: 8px; }
        .ai .s { font-size: 25px; color: var(--sub); margin-top: 8px; line-height: 1.35; }
        .ai .nums { display:flex; gap: 40px; margin-top: 16px; }
        .ai .nums div { font-size: 22px; color: var(--sub); }
        .ai .nums b { display:block; font-size: 44px; color: #fff; }
        .pts { margin-top: 30px; gap: 26px; }
        .pt .t { font-size: 31px; }
      `,
      html: `
        <div class="eyebrow">Product and marketing · 2025 to 2026</div>
        <h1>Betting big on <span class="hl">AI.</span></h1>
        <div class="card ai">
          <div class="h">JULY 2026</div>
          <div class="b">AI-Rex: AI agents for recruiters</div>
          <div class="s">Finds, contacts and screens candidates on its own.</div>
          <div class="nums"><div><b>4,000+</b>companies live</div><div><b>₹150 Cr</b>AI spend planned, FY27</div></div>
        </div>
        <div class="pts">
          <div class="pt"><div class="k">a</div><div class="t"><b>AI for job seekers.</b> <span>Neo job finder, AI resume maker and AI mock interviews.</span></div></div>
          <div class="pt"><div class="k">b</div><div class="t"><b>IPL 2025 campaign.</b> <span>"Naukri, for the ambitious": films backing Gen Z who switch jobs to grow.</span></div></div>
          <div class="pt"><div class="k">c</div><div class="t"><b>Spending less.</b> <span>Marketing spend fell 13% in Q4 FY26 while revenue grew.</span></div></div>
        </div>`,
      source: 'Sources: Naukri press release (July 2026), YourStory, afaqs, exchange4media, Info Edge Q4 FY26 earnings call',
    },

    // 8. Numbers + CTA
    {
      css: COMMON + `
        .tbl { margin-top: 30px; padding: 10px 30px; }
        .tr { display:flex; justify-content:space-between; align-items:center; padding: 20px 0; border-bottom: 1.5px solid rgba(207,201,242,.18); font-size: 30px; }
        .tr:last-child { border-bottom: 0; }
        .tr b { font-size: 40px; color: var(--amber); }
        .comp { margin-top: 24px; font-size: 24px; color: var(--sub); line-height:1.5; }
        .comp b { color:#fff; }
        .cta { margin-top: 26px; font-size: 32px; font-weight: 800; }
      `,
      html: `
        <div class="eyebrow">The numbers · FY26</div>
        <h1>Info Edge <span class="hl">at a glance.</span></h1>
        <div class="card tbl">
          <div class="tr"><span>Revenue</span><b>₹3,052 Cr <span class="green" style="font-size:26px">▲ 15%</span></b></div>
          <div class="tr"><span>Operating profit</span><b>₹1,138 Cr</b></div>
          <div class="tr"><span>Operating margin</span><b>37%</b></div>
          <div class="tr"><span>Dividend</span><b>₹8.4 / share</b></div>
        </div>
        <div class="comp"><b>Rivals:</b> LinkedIn, Indeed, foundit (jobs) · MagicBricks, Housing.com (property) · Shaadi.com, BharatMatrimony (matrimony)</div>
        <div class="cta">Follow for Business Model #2 →</div>`,
      source: 'FY26 standalone figures. Sources: Info Edge Q4 FY26 earnings call, Inc42, Medianama',
    },
  ],
};
