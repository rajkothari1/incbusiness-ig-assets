---
name: daily-news-reels
description: Daily incbusiness run. Finds up to 10 fact-checked Indian business news stories from the last 24h IST, builds 9:16 reels with news music, schedules them as Instagram Reels on Metricool for the same day, and emails a summary. Use when asked for the daily news, daily reels, or the incbusiness daily run.
---

# Daily news → reels → Metricool

The editorial rules (categories, the 24h window, the 2-source fact check, ranking, headline, caption and hashtag format, image choice) live in `prompts/daily-news-canva.md`. Read that file first and follow it. This skill covers the order of work and the automation details. Skip the Canva steps unless the person asks for them.

## 0. Setup
- Work on branch `claude/nice-ptolemy-9ilnvh`: `git fetch origin claude/nice-ptolemy-9ilnvh && git checkout claude/nice-ptolemy-9ilnvh && git pull origin claude/nice-ptolemy-9ilnvh`. You have explicit permission to commit and push to this branch, because the reel URLs on Metricool point to it.
- `DAY=$(TZ=Asia/Kolkata date +%F)`. Put everything in `daily/$DAY/`.
- Call Metricool `getScheduledPosts` (blogId `6752944`) for today in IST. If Instagram Reels are already scheduled for today, stop and report that today is already done. Don't post twice.

## 1. News (prompt Steps 1–3)
- Search the last 24h IST across the 10 categories, with up to 10 stories. Never pad.
- Fact-check every number and every caption claim in 2+ independent outlets. Drop single-source claims from captions.
- For each story, write:
  - the 10–12 word headline
  - the 6–9 word card headline with `[[red words]]`
  - the ~40-word paragraph
  - the sources
  - the caption, with 18 hashtags (the 6 fixed tags plus 12 for the story)
- Rank by importance.

## 2. Images (prompt Step 4)
- Download a founder photo, an official logo (SVG/PNG), or nothing, into `daily/$DAY/assets/`. When there is no usable image, use `pillText` with `backgrounds/<category>.jpg`.
- Write `daily/$DAY/stories.json` in rank order. Use slugs `01-<category>-<company>`, `02-…`. Paths are relative to the repo root. See `daily/2026-10-10/stories.json` for the format.

## 3. Reels
```bash
node generator/render.js daily/$DAY/stories.json daily/$DAY/cards
REEL=1 node generator/render.js daily/$DAY/stories.json daily/$DAY/reels/cards
python3 generator/make-reels.py daily/$DAY/stories.json daily/$DAY/reels
mkdir -p daily/$DAY/reels-final
i=0; for f in daily/$DAY/reels/*.mp4; do s=$(basename $f .mp4)
  python3 generator/make-music.py /tmp/music-$i.wav 8 news $i
  ffmpeg -y -loglevel error -i $f -i /tmp/music-$i.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 128k -shortest daily/$DAY/reels-final/$s.mp4
  i=$((i+1)); done
```
- Each reel gets its own music variant (0–9), so no two reels in a day share a tune.
- Make one snapshot per reel (used by the summary email): `mkdir -p daily/$DAY/reels-final/snaps && for f in daily/$DAY/reels-final/*.mp4; do ffmpeg -y -loglevel error -ss 3 -i $f -frames:v 1 -vf scale=540:-2 -q:v 4 daily/$DAY/reels-final/snaps/$(basename $f .mp4).jpg; done`.
- QA: grab a frame from 2 or 3 reels with `ffmpeg -ss 3 -i <mp4> -frames:v 1 /tmp/f.png` and look at it. Check that the text is spelled correctly, the numbers match the fact check, there are no dashes, nothing overflows, and the logo isn't stretched. Fix any problem and re-render.

## 4. Write up and push
- Write `daily/$DAY/posts.md` as described in prompt Step 6, including the fact-check table and the dropped stories.
- Commit and push: `git add daily/$DAY && git commit && git push -u origin claude/nice-ptolemy-9ilnvh`. Retry on network errors (2s, 4s, 8s, 16s).
- Confirm that each `https://raw.githubusercontent.com/rajkothari1/incbusiness-ig-assets/claude/nice-ptolemy-9ilnvh/daily/$DAY/reels-final/<slug>.mp4` returns HTTP 200 (`curl -sI`) before scheduling.

## 5. Schedule on Metricool
- Call `getBestTimeToPostByNetwork` for Instagram for today.
- Pick one slot per reel, each meeting these rules:
  - between 09:00 and 21:00 IST
  - at least 45 minutes from now
  - at least 1 hour after the previous slot
- Put rank 1 in the best slot, rank 2 in the next best, and so on.
- For each reel, call `createScheduledPost` with blogId `6752944`, date `<DAY>T<HH:MM>:00+05:30`, and this `info` JSON:
  ```json
  {"autoPublish": true, "descendants": [], "draft": false, "firstCommentText": "", "hasNotReadNotes": false,
   "media": ["<raw mp4 url>"], "mediaAltText": [], "videoCoverMilliseconds": 3000,
   "providers": [{"network": "instagram"}],
   "publicationDate": {"dateTime": "<DAY>T<HH:MM>:00", "timezone": "Asia/Calcutta"},
   "shortener": false, "smartLinkData": {"ids": []}, "text": "<caption without ** markers>",
   "instagramData": {"type": "REEL", "collaborators": [], "showReelOnFeed": true, "isAiGenerated": false}}
  ```
- Call `getScheduledPosts` to confirm the posts. Add a table of time, reel and post id to `posts.md`, then commit and push.

## 6. Report
End with a short Hinglish summary covering:
- the number of reels scheduled, with each time and headline
- the stories that were dropped, and why
- any problem that needs the person, for example a Metricool error or fewer than 3 stories qualifying

If Metricool fails, leave the reels pushed and say so plainly. Never report a post as scheduled unless `getScheduledPosts` shows it.

## 7. Email the summary
**Preferred: real reel snapshots inside the email.** Resend works when the `RESEND_API_KEY` environment variable is set, or when an api.resend.com network secret exists. To check, run `curl -s -o /dev/null -w '%{http_code}' https://api.resend.com/domains`: 200 means the key is available. If it is, take these steps and skip the Gmail steps below.
- Make the snapshots (step 3) and write `/tmp/schedule.json` as `[{"slug","time","caption"}]` in time order.
- Run `python3 generator/send-summary.py daily/$DAY/stories.json /tmp/schedule.json daily/$DAY/reels-final/snaps "incbusiness reels <DAY>: <N> scheduled" "<status line>" [extra.html]`.
- `extra.html` can hold the dropped stories, any errors and the posts.md link.
- The script embeds each real snapshot as an inline image, one below the other, with its caption under it.
- Check that it prints an id. If it fails, fall back to the Gmail method below.

**Fallback (no key):**
Send one email with the Gmail connector (`send_message`) to `raj.kothari90@gmail.com` at the end of every run, including runs that fail or stop early. Use an HTML body.

- **Subject:** `incbusiness reels <DAY>: <N> scheduled`. If the run stopped early, use `incbusiness reels <DAY>: already scheduled` or `incbusiness reels <DAY>: needs attention` instead.
- **Body:**
  1. A one-line status: how many reels are scheduled out of how many stories were found.
  2. A table with one row per reel. Columns: time (IST), category, headline, a **▶ Reel dekho** link, and the Metricool post id.
     - The link must play on a phone. Use the jsDelivr URL, which serves the file as `video/mp4`: `https://cdn.jsdelivr.net/gh/rajkothari1/incbusiness-ig-assets@claude/nice-ptolemy-9ilnvh/daily/<DAY>/reels-final/<slug>.mp4`.
     - Don't use the raw.githubusercontent.com URL here. It downloads on mobile instead of playing.
     - Check each link with `curl -sI` before sending; it should return 200 with `content-type: video/mp4`.
  3. **Reel cards, one below the other, inside the email.** The person checks reels from these without clicking anything.
     - The Gmail connector strips `<img>` tags that point outside the email.
     - Image attachments need base64 copied by hand, which corrupts the data, so don't use images.
     - Instead, write `/tmp/schedule.json` as `[{"slug","time","caption"}]` in time order, using the full caption without `**`.
     - Run `python3 generator/email-cards.py daily/$DAY/stories.json /tmp/schedule.json /tmp/cards.html`. It draws each card in HTML (brand pill, red category tag, headline with red keywords, READ MORE banner) and puts the caption under it.
     - Paste the contents of `/tmp/cards.html` into the email body.
     - Steps 3 and 4 are covered by these cards.
  5. Fact check: the number of claims checked, plus any claim dropped for having one source.
  6. Dropped stories, each with its reason.
  7. Errors or anything that needs the person, for example a Metricool failure, a missing image, or a reel that didn't schedule.
  8. A link to `posts.md` on GitHub: `https://github.com/rajkothari1/incbusiness-ig-assets/blob/claude/nice-ptolemy-9ilnvh/daily/<DAY>/posts.md`.
  9. A reminder that posts auto-publish, and that a wrong post can be edited or deleted in Metricool before its time.

Write the email in simple Hinglish, the same as the chat summary.
