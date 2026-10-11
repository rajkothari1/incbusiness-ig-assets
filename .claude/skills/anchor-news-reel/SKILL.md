---
name: anchor-news-reel
description: Daily 25-second hook-first business news reel with the AI news anchor. Takes the stories and cards the daily-news-reels run already made, voices them in energetic Hinglish (Higgsfield ElevenLabs, voice Anika), lip-syncs the anchor for the intro and the sign-off (Higgsfield MiniMax H3), builds the reel with news music, schedules it on Metricool and emails the person. Use when asked for the anchor reel, the 60s news reel or the AI reporter reel.
---

# Anchor news reel (25 s, Hinglish, AI anchor)

The tools live on branch `claude/zen-pasteur-oyaapa`; the day's stories, cards and the Metricool URLs live on `claude/nice-ptolemy-9ilnvh`. You have explicit permission to commit and push to `claude/nice-ptolemy-9ilnvh`.

Budget: the person has a small Higgsfield balance. One reel costs about 21 credits (voice ~3, hook clip 10, sign-off clip 8). Never generate anything you have not costed with `get_cost` first, never generate test samples, and never retry a clip more than once.

## 0. Setup and guards
```bash
git fetch origin claude/nice-ptolemy-9ilnvh claude/zen-pasteur-oyaapa
git checkout claude/nice-ptolemy-9ilnvh && git pull origin claude/nice-ptolemy-9ilnvh
git checkout origin/claude/zen-pasteur-oyaapa -- reels/build_reel.py reels/make_voice.py reels/check_sync.py reels/make_music.py anchor/anchor.jpg .claude/skills/anchor-news-reel
DAY=$(TZ=Asia/Kolkata date +%F); OUT=daily/$DAY/anchor; mkdir -p $OUT/cards $OUT/voice-lines
pip install -q edge-tts 2>/dev/null || true
```
Stop (and still send the email in step 7) when any of these is true:
- `daily/$DAY/stories.json` or `daily/$DAY/cards/` does not exist: the daily run has not finished. Subject `incbusiness anchor reel <DAY>: daily cards missing`.
- Metricool `getScheduledPosts` (blogId `6752944`) for today already has a post whose text starts with `Aaj ki Top`: the anchor reel is already scheduled. Don't post twice.
- Higgsfield `balance` is below 30 credits. Subject `incbusiness anchor reel <DAY>: recharge Higgsfield`, and say the balance.

## 1. Script (25 seconds, hook first, countdown)
Viewers decide in the first 2 seconds. The 60 s "Namaste, top 9 news" version averaged 2 s watch time, so the reel is now short and opens on the most shocking number.

Read `daily/$DAY/stories.json` and `daily/$DAY/posts.md`. Pick:
- **Hook story:** the single most surprising, number-led story (jobs cut, a huge raise, a crash). It is only spoken in the hook, not repeated as a card.
- **4 more stories** for a countdown 4 → 1, with the biggest of them as number 1. Copy their cards: `cp daily/$DAY/cards/<slug>.png $OUT/cards/`.

Write `$OUT/script.json` like `reels/2026-10-11-short/script.json` on `claude/zen-pasteur-oyaapa`:
```json
{"date": "11 OCT 2026",
 "intro": {"say": "Netflix आठ सौ नौकरियाँ काट सकता है! और चार बड़ी खबरें!", "title": "800 JOBS", "subtitle": "NETFLIX MEIN CHHATNI?", "tagline": "+ 4 aur badi khabrein"},
 "items": [{"num": 4, "card": "05-funding-nat-habit.png", "say": "फोर! आयुर्वेदिक ब्रांड Nat Habit ने एक सौ बयालीस करोड़ जुटाए!", "caption": "Nat Habit ne ₹142 crore jutaye"},
           {"num": 1, "card": "01-earnings-dmart.png", "say": "और नंबर वन! DMart का प्रॉफिट साढ़े आठ परसेंट बढ़कर सात सौ तैंतालीस करोड़!", "caption": "DMart profit 8.5% badhkar ₹743 crore"}],
 "outro": {"say": "रोज़ ऐसी ही न्यूज़ के लिए फॉलो कीजिए!", "title": "FOLLOW", "subtitle": "& SHARE", "tagline": "@incbusiness.official"}}
```
Rules:
- Hook `say`: the shock fact in under 10 words, then "और चार बड़ी खबरें!". No greeting. `title` is the hook number in 2 words or fewer (`800 JOBS`, `₹142 CR`), `subtitle` names the company as a question or claim. Stay inside the fact check: "काट सकता है" for a plan, not "काट दिया".
- Story `say`: starts with the countdown number ("फोर!", "थ्री!", "टू!", "और नंबर वन!"), at most 10 words, one fact.
- Hindi in Devanagari, company names in Latin script, every number in words ("सात सौ तैंतालीस करोड़"); no digits or ₹/% in `say`. Never say "incbusiness" in the voice.
- `caption`: the same fact in Roman Hinglish with digits, 4 to 7 words.
- Target 25 s. Step 2 uses `--tempo 1.12`; if `voice.mp3` is still over 28 s, shorten the longest lines and regenerate only those.

The builder keeps everything inside Instagram's safe area (no top bar; text clear of the username, caption and button overlays), so don't add elements near the top 170 px, the bottom 440 px or the right edge.

## 2. Voice (Higgsfield, ~0.5 credit per line)
For each line i (0 = hook, 1..4 = stories, 5 = outro) generate speech with `generate_audio`, model `elevenlabs_v4`, `stability: 0.3`, and
`dialogue: [{"text": "<tag> <say>", "voice_type": "preset", "voice_id": "4b2dc8f3-5e8b-59a9-9a5c-85620e44c033"}]` (voice Anika),
where `<tag>` is `[excited]` for the intro and outro and `[energetic]` for stories.
- ElevenLabs rate-limits bursts: submit with `generate_audio_batch` in groups of at most 3 and wait for each group. A `rate_limit_reached` item was not charged; resubmit it in the next group.
- Download each result to `$OUT/voice-lines/line_XX.mp3` (two digits, XX = i).
- Run `python3 reels/make_voice.py $OUT --tempo 1.12`. It trims the silences, joins the lines and writes `voice.mp3` and `segments.json` with each line's timing.

## 3. Lip-synced intro and sign-off (Higgsfield MiniMax H3)
Upload `anchor/anchor.jpg` cropped to 9:16 without the bottom 12% (that strip has the image generator's watermark):
```bash
python3 -c "
from PIL import Image
im=Image.open('anchor/anchor.jpg').convert('RGB'); im=im.crop((0,0,im.width,int(im.height*0.88)))
w=im.width; h=int(w*16/9)
if h>im.height: h=im.height; w=int(h*9/16)
x=(im.width-w)//2; im.crop((x,0,x+w,h)).resize((1080,1920)).save('/tmp/anchor_916.jpg',quality=95)"
# Cut the hook and sign-off from voice.mp3 itself (it is tempo-adjusted, the raw lines are not).
python3 -c "
import json,subprocess
d=json.load(open('$OUT/segments.json'))
dur=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0','$OUT/voice.mp3']))
for name,s in (('intro',d['intro']),('outro',d['outro'])):
    e=min(s['end'],dur)-0.15
    subprocess.run(['ffmpeg','-y','-loglevel','error','-ss',str(s['start']),'-to',str(e),'-i','$OUT/voice.mp3','/tmp/%s.mp3'%name],check=True)
    print(name, round(e-s['start'],2))"
```
Upload `/tmp/anchor_916.jpg`, `/tmp/intro.mp3` and `/tmp/outro.mp3` with `media_upload` (curl PUT, then `media_confirm`).
For the intro and for the outro, call `generate_video` with `get_cost: true` first, then for real:
- model `minimax_h3`, `aspect_ratio: "9:16"`, `duration` = the printed length rounded up, but never below 5 (4-second MiniMax jobs with audio failed twice)
- medias: `{"role": "image_references", "value": <anchor id>}` and `{"role": "audio_references", "value": <line id>}`. `start_image` cannot be combined with audio here.
- prompt: `The exact woman from the reference image, same face, same beige blazer, same office with window, sitting at her desk with laptop. She looks into the camera and speaks the reference audio with accurate lip sync, energetic and friendly news anchor delivery, natural head movement, blinking. Static camera, vertical medium shot, photorealistic.`
- If the tool answers with a preset recommendation, decline it with `declined_preset_id` and generate literally.
- Save the results as `$OUT/intro.mp4` and `$OUT/outro.mp4`.

Check each clip: `python3 reels/check_sync.py $OUT/intro.mp4 /tmp/intro.mp3` (and `$OUT/outro.mp4` with `/tmp/outro.mp3`). It prints where our line starts inside the clip (MiniMax sometimes adds a silent lead-in, e.g. 1.1 s; the builder skips it) and must say `OK`. On `MISMATCH`, or if a job fails, regenerate that clip once (a failed job is not charged). If it still fails, delete that mp4: the builder then shows the anchor photo with a slow zoom for that line, and the email must say so.

Do not use Seedance or any other model for lip-sync: they treat the audio as a loose reference and the lips drift.

## 4. Build
```bash
python3 reels/build_reel.py $OUT
ffmpeg -y -loglevel error -ss 2 -i $OUT/reel.mp4 -frames:v 1 -vf scale=540:-2 -q:v 4 $OUT/snap.jpg
```
QA: grab frames at 2 s, at the middle of a story and at the end with `ffmpeg -ss <t> -i $OUT/reel.mp4 -frames:v 1 /tmp/f.png` and look at them. Check the subtitles are spelled right and match the cards, nothing overflows, and the reel is 60 s or less (`ffprobe`). Fix and rebuild if needed.

## 5. Push
Commit `$OUT` (not `$OUT/build`, which the `.gitignore` covers; add `daily/*/anchor/build/` to `.gitignore` if it is missing) plus the tool files from step 0, then `git push -u origin claude/nice-ptolemy-9ilnvh` (retry 2s, 4s, 8s, 16s on network errors). Confirm `https://raw.githubusercontent.com/rajkothari1/incbusiness-ig-assets/claude/nice-ptolemy-9ilnvh/daily/$DAY/anchor/reel.mp4` returns HTTP 200.

## 6. Schedule on Metricool
- `getScheduledPosts` for today and `getBestTimeToPostByNetwork` for Instagram.
- Pick the best slot between 09:00 and 22:00 IST that is at least 45 minutes from now and at least 30 minutes away from every post already scheduled today.
- `createScheduledPost` with blogId `6752944` and the same `info` JSON as the daily-news-reels skill (step 5), except:
  - `"media": ["<raw mp4 url>"]`, `"videoCoverMilliseconds": 2000`
  - `"instagramData": {"type": "REEL", "collaborators": [], "showReelOnFeed": true, "isAiGenerated": true}`. The anchor is AI-generated, so this label must be on.
  - `text` (no dashes anywhere), in this shape:
    ```
    Aaj ki Top <N> Business News, sirf 60 seconds mein 👇

    1️⃣ <story 1 in Roman Hinglish with its key number, one line>
    2️⃣ <story 2> … one line per story, keycap emojis 1️⃣ to 🔟

    Kaunsi news sabse badi lagi? Comment karo 💬

    Follow @incbusiness.official for daily business news, simplified.

    <18 hashtags>
    ```
    Hashtags: the 7 fixed ones `#startups #business #incbusiness #tech #AI #news #Today`, then `#BusinessNews #NewsIn60Seconds #HindiNews`, then 8 picked from the day's stories (biggest company names and topics, e.g. `#TCS #Netflix #StockMarketIndia #StartupIndia #IndianEconomy`). 18 in total. Every number in the caption must match the fact-checked `posts.md`.
- Confirm with `getScheduledPosts`. Never report the reel as scheduled unless it shows there. Write `$OUT/post.md` with the time, post id and Higgsfield credits used and left, then commit and push.

## 7. Email and report
Always send one email, including when the run stopped early. Use Resend when `curl -s -o /dev/null -w '%{http_code}' https://api.resend.com/domains` gives 200, otherwise the Gmail connector `send_message`, to raj.kothari90@gmail.com.
- Subject: `incbusiness anchor reel <DAY>: scheduled <HH:MM>` (or the stop subjects from step 0, or `needs attention` on any error).
- Body (simple Hinglish, HTML): the status line, a **▶ Reel dekho** link `https://cdn.jsdelivr.net/gh/rajkothari1/incbusiness-ig-assets@claude/nice-ptolemy-9ilnvh/daily/<DAY>/anchor/reel.mp4` (check it with `curl -sI`: 200 and `video/mp4`), the Metricool post id, the sync check result for both clips, credits used today and the balance left with roughly how many reels it still covers (balance ÷ 25), and any error. With Resend, embed `$OUT/snap.jpg` inline.

End with a short Hinglish summary of the same points.
