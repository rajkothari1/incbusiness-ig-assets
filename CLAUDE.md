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
- Reel top = incbusiness logo, then the 2-line headline. No kicker, no hook/sub-line above the cards (hook is used on covers only).
- If a tool's square icon isn't recognisable (e.g. ElevenLabs "II"), add its wordmark as `logos/<key>-wordmark.png` and set `"wordmark"` on the reel entry (spotlight uses it on cover + card).
- Spotlight reels: logo + one-line headline ("Tool Spotlight"), then a browser-framed screenshot of the tool's website (`reels/screenshots/<key>.png`, 1440x1080 Playwright capture; set `"screenshot"` + `"line"` on the entry) then the tool name big in amber, then one white line. Sites behind Cloudflare (e.g. gamma.app) can't be captured here — pick a different tool whose site can be captured (owner's call: Gamma was swapped for Pitch).
- Every reel shows plain white text "Follow for more AI content" with Instagram + LinkedIn icons from 3s (slides in under the cards; no pill, no arrow).
- Covers: `out/<id>-cover.png` (1080x1920) — all key content sits inside the 3:4 profile-grid crop (y 240..1680). Upload it as the reel cover.

## AI tools reels pipeline (`reels/`)
- Data: `reels/data/reels.json` — one entry per reel: id (`NN-slug`), type (`top4` | `top3` | `spotlight`), category, title (2 lines), hook, bg clip, tools `[name, company, logo key, one-liner, link]`, `points` (3 bullets, spotlight only), caption.
- Template: `reels/template/theme.html` (reel + cover modes).
- Logos: `reels/logos/<domain_with_underscores>.png` (fetched via `https://www.google.com/s2/favicons?domain=<domain>&sz=256`).
- Background clips: Mixkit free stock video (Mixkit License, free for commercial/social use). Download to `reels/bg-videos/<id>.mp4` from `https://assets.mixkit.co/videos/<id>/<id>-1080.mp4` (gitignored; `render-reels.sh` re-downloads any missing clip by its Mixkit id; sources listed in `reels.json`). Unsplash/Pexels/Pixabay block this container.
- Render: `reels/render-reels.sh [id...]` → `reels/out/<id>.mp4`, `<id>-cover.png`, `<id>-caption.txt`, plus `out/grid-preview.png` (profile grid mock).
- `reels/archive/` holds the earlier (pre-theme) versions.

## Captions
- Built by `render-reels.sh` into `out/<id>-caption.txt`: body from `caption`, then one `🔹 Tool: one-liner (📍 City, Country)` line per tool (one-liner from `tools`, company HQ from the entry's `hq` list), then 20-25 hashtags.
- Hashtags always start with the fixed set `#aitools #ai #business #tech #startup #follow #instagram #incbusiness`, then the reel's own tags (last paragraph of `caption`), then generic fillers; capped at 23.
- Instagram's real location tag can't be set through Metricool — the HQ location lives in the caption only.

## Publishing (Metricool)
- Brand: `incbusiness.official` (Instagram), blogId `6752944`, timezone Asia/Calcutta. Best slots: 10:00 and 18:00 IST, in id order.
- Media URLs: public raw GitHub links pinned to a commit, e.g. `https://raw.githubusercontent.com/rajkothari1/incbusiness-ig-assets/<commit>/reels/out/<id>.mp4`; cover via `videoThumbnailUrl` (`<id>-cover.png`).
- Music: every reel has a Mixkit Music Free License track baked in (rotate the pool in `reels.json` → `music`; tracks live in `reels/music/`, gitignored, auto-downloaded by id; loudnorm -14 LUFS, fades). The Instagram audio catalog via Metricool returns 403 (account is Creator, not Business+FB Page) and trending songs can't be embedded (copyright), so this is the owner's chosen "automatic" option.
- Schedule with `autoPublish: true` (fully automatic). Slots: 10:00 and 18:00 IST, in id order.
