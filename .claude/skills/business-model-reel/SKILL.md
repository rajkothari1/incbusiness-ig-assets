---
name: business-model-reel
description: Make one episode of the incbusiness "India's Top 100 Business Models" Instagram reel series (1080x1920, ~35-45s, Hinglish female voice-over, English subtitles, code-animated). Use when the user asks for the next episode, a business model reel for a company, or "reel banao" for any company in the 100-company list. Covers fact-checking, script, voice, animation, music, cover image and Metricool scheduling.
---

# Business model reel (incbusiness, 100-episode series)

Reference episodes, copy the closest one as the starting point:
- `reels/ep01-naukri/`: Info Edge. Business-wise revenue split (each business gets ₹ and %).
- `reels/ep02-mamaearth/`: Honasa. House of brands, founders' photos, marketing section, own colour theme. **Newest template, start from this.**

Shared tools: `reels/music.py` (royalty-free music bed), `logos/` (brand logos, see `logos/README.md`), `carousels/build.js` (carousels).

## Rules the user has set (do not break)

1. **Fact-check everything with 2+ sources.** The company's own earnings-call transcript, press release or annual report (NSE/BSE PDFs) is source 1. Download the PDF (Playwright with an nseindia.com referer works) and grep it, do not trust search summaries.
2. **Latest numbers only.** Use the latest full financial year (FY26 now) and the latest quarter. Marketing and products must be 2025-2026, never old campaigns.
3. **No invented numbers.** If a number (e.g. "500+ influencers") is only on blogs, do not use it. Say so to the user.
4. **Wording must match what the number covers.** If revenue is for the parent company, say "the company behind X" or "X's parent". If a segment includes other brands, don't call it one brand's revenue.
5. **Round numbers the user's way:** headline numbers as "₹2,000 Cr+", "₹200 Cr+", "3 Lakh+", "9 brands" (digits on screen). Check the "+" is true. Keep the exact figure in a small line (e.g. "FY26, on ₹2,392 Cr revenue").
6. **No opinions or assumptions** in script or subtitles. No "every ₹100" breakdowns.
7. **Show the script first and wait for approval** before spending credits. Show cost first (`get_cost: true`).
8. **Never post or update Metricool without the user's explicit approval** of the final video.
9. Hinglish words the user dislikes: say "men", not "mardon". Brand names in English pronunciation (write "नाइंटी नाइन एकर्स", not "निन्यानवे").

## Steps

### 1. Research and fact-check
- Revenue, profit, business/brand split, outlets, latest marketing, latest products.
- Present a fact table (claim, source 1, source 2) with links.

### 2. Script (~35-45s)
Structure that works:
1. "Episode N of 100! Aaj ka business model: X!"
2. Hook: a surprising fact plus the revenue number, then "Kaise?"
3. How it makes money: each business/brand, one short line each, what customers pay for.
4. Optional: how it sells / marketing (latest, fact-checked).
5. Payoff number (profit or biggest earner).
6. "Follow karo, aisi aur business stories ke liye!" (no "Episode N+1" promise).
Give the voice-over in Hinglish (romanised) and the English subtitles. Numbers as digits on screen.

### 3. Voice (Higgsfield, ~3 credits)
- `generate_audio` with `model: "elevenlabs_v4"`, `stability: 0.3`, `dialogue: [{text, voice_id: "4b2dc8f3-5e8b-59a9-9a5c-85620e44c033", voice_type: "preset"}]` (voice "Anika", same as the news reels).
- Text in Devanagari, numbers written as words, `[excited]` / `[energetic]` tags.
- Generate **one take for the whole script**. Never splice single words from another take (the voice changes).
- Download, then `silencedetect=noise=-35dB:d=0.25`, list speech segments, cut each segment, keep 0.14-0.2s gaps, `atempo` 1.22-1.4 so it lands at ~35-43s (see the python block used in ep02). Print each segment's new start time.

### 4. Animation (free, code)
- Copy the template folder. `reel.html` has a `T` object (scene start times) and `K` (moments inside scenes). Set them from the segment start times.
- Each scene is a `<div class="scene">`. Keep text big and centered, sound-off friendly. Subtitles at the bottom, word-by-word amber highlight (already built in).
- Background: rotating rays all through (brighter on end card). Give each company its own colour theme (ep02 overrides the `:root` colours with Mamaearth green).
- Founder photos: full-screen faded background (`.bgimg`) and/or big framed `.photo` cards. Use only photos the user sent; remind them about photo credit/rights.
- Logos: from the brand's own website via Playwright; recolour white logos dark for white cards; save to `logos/` and note the source in `logos/README.md`.
- Preview frames with `node render.js --preview t1,t2,...` and check every scene before rendering (no overlaps, nothing behind the Instagram UI at the bottom/right).
- Mock UI (like a ChatGPT ad) must carry a small "Illustration" label.

### 5. Sound (free)
- `python3 reels/music.py music.wav <DUR> <build_start> <end_card_time>`.
- `mixdown.sh`: voice + music ducked under voice + whoosh on every cut + soft riser into the end card + boom. Update `CUTS`, `DUR`, the ramp start.
- Check loudness per section with `volumedetect`; no sudden jumps at the end.

### 6. Render and deliver
- `node render.js` (30fps, ~2-3 min). Send the mp4 with SendUserFile.
- Commit and push every version to the working branch.

### 7. Cover (free)
- `cover.html` + `cover.js` in the episode folder. 1080x1920: "EPISODE NN/100" badge, small logos row, founder photo, "How does [logo] make ₹X Cr+ a year?", "BUSINESS MODEL" stamp, incbusiness logo.
- Keep key text inside the centre 1080x1440 (profile-grid crop).

### 8. Schedule (only after approval)
- Metricool brand `incbusiness.official`, blogId `6752944`, timezone `Asia/Calcutta`.
- Media must be a public URL: use the GitHub raw URL pinned to the commit SHA (`raw.githubusercontent.com/rajkothari1/incbusiness-ig-assets/<sha>/...`).
- Instagram REEL, `showReelOnFeed: true`, `isAiGenerated: true` (AI voice), `videoThumbnailUrl` = cover.
- Caption: first line "Business Model #N - Company 📊", hook, the businesses as numbered emoji lines, "Source: ... results", follow line, ~25-30 hashtags including #business #startups #tech #AI #businessmodel plus company/brand tags.
- Use `getBestTimeToPostByNetwork` to suggest a time.

## Credits per episode (Higgsfield)
- Voice ~3 credits. Everything else is free. Lip-sync video ~55 credits per reel (user declined it as too costly).
