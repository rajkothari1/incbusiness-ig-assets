# incbusiness IG assets

Instagram page **incbusiness** — Indian startup / business news (funding, IPO, layoffs, mutual funds, earnings, AI) plus AI-tool reels for founders.

## Brand (always use)
- Logo: `brand/incbusiness-logo-original.png` (black, transparent bg). Wordmark is "**inc**business®" — "inc" bold, "business" regular.
  - On dark backgrounds use `brand/incbusiness-logo-white.png`; on light use `brand/incbusiness-logo-black.png`.
  - Never retype the logo as text — always place the PNG.
- On-screen text in English (headlines, one-liners). Chat with the owner in Hinglish.
- Reels: 1080x1920, 5s, keep content between y≈150 and y≈1600 (IG UI covers the bottom).
- **Theme (fixed for the whole series — do not change per reel):** "AI Toolkit" look — black & white graded footage, black scrim, single amber accent `#FFC21A`, tool cards on white (dark text) for readability, Poppins (headings) + Inter (body), white incbusiness logo.
- **Grid pattern:** posts go in rows of 3 in this order: `top4` (4 tools) → `top3` (3 tools) → `spotlight` (1 tool). Keep the count a multiple of 3 so the profile grid columns stay aligned. Variety comes from category, title, hook and background clip, not from colors/fonts.
- Covers alternate dark / light (white) by post index → checkerboard on the 3-column grid. Never break the alternation.
- Every reel shows a "↓ Follow for more AI content" amber pill from 3s (slides in under the cards).
- Covers: `out/<id>-cover.png` (1080x1920) — all key content sits inside the 3:4 profile-grid crop (y 240..1680). Upload it as the reel cover.

## AI tools reels pipeline (`reels/`)
- Data: `reels/data/reels.json` — one entry per reel: id (`NN-slug`), type (`top4` | `top3` | `spotlight`), category, title (2 lines), hook, bg clip, tools `[name, company, logo key, one-liner, link]`, `points` (3 bullets, spotlight only), caption.
- Template: `reels/template/theme.html` (reel + cover modes).
- Logos: `reels/logos/<domain_with_underscores>.png` (fetched via `https://www.google.com/s2/favicons?domain=<domain>&sz=256`).
- Background clips: Mixkit free stock video (Mixkit License, free for commercial/social use). Download to `reels/bg-videos/<id>.mp4` from `https://assets.mixkit.co/videos/<id>/<id>-1080.mp4` (gitignored; sources listed in `reels.json`). Unsplash/Pexels/Pixabay block this container.
- Render: `reels/render-reels.sh [id...]` → `reels/out/<id>.mp4`, `<id>-cover.png`, `<id>-caption.txt`, plus `out/grid-preview.png` (profile grid mock).
- `reels/archive/` holds the earlier (pre-theme) versions.
