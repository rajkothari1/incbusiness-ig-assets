# incbusiness IG assets

Instagram page **incbusiness** — Indian startup / business news (funding, IPO, layoffs, mutual funds, earnings, AI) plus AI-tool reels for founders.

## Brand (always use)
- Logo: `brand/incbusiness-logo-original.png` (black, transparent bg). Wordmark is "**inc**business®" — "inc" bold, "business" regular.
  - On dark backgrounds use `brand/incbusiness-logo-white.png`; on light use `brand/incbusiness-logo-black.png`.
  - Never retype the logo as text — always place the PNG.
- On-screen text in English (headlines, one-liners). Chat with the owner in Hinglish.
- Reels: 1080x1920, 5s, keep content between y≈150 and y≈1600 (IG UI covers the bottom).
- Each reel must look different from the previous one: rotate layout, accent color, title font and background clip.

## AI tools reels pipeline (`reels/`)
- Data: `reels/data/reels.json` — one entry per reel: id, layout (`stack` | `grid` | `light` | `center`), accent, font, kicker, title lines, bg clip, 4 tools `[name, company, logo key, one-liner, link]`, caption.
- Logos: `reels/logos/<domain_with_underscores>.png` (fetched via `https://www.google.com/s2/favicons?domain=<domain>&sz=256`).
- Background clips: Mixkit free stock video (Mixkit License, free for commercial/social use). Download to `reels/bg-videos/<id>.mp4` from `https://assets.mixkit.co/videos/<id>/<id>-1080.mp4` (gitignored; sources listed in `reels.json`). Unsplash/Pexels/Pixabay block this container.
- Render: `reels/render-reels.sh [id...]` → `reels/out/<id>.mp4`, `<id>-cover.png`, `<id>-caption.txt`.
