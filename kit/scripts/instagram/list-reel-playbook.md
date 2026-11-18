# AI Tools list reel playbook (Instagram)

One run makes **one** Instagram reel for @incbusiness.official: the tools of one AI Tools category on incbusiness.in (at most 12, 6 a column, big names and links), each with its website link, on a single screen. A category with more than 12 tools is split evenly into parts (20 tools = Part 1 and Part 2), each its own reel. **Music only, no voice, no Higgsfield.** The list stays still for 16 seconds while the background changes behind it, so people can read and save it. Its cover is a 3D cover (big 3D number, small 3D prop, short title).

Two reels a day: **12:00 PM** and **6:00 PM IST**. The routine runs an hour before each slot.

The kit is in the checked-out repository (running it is expected and allowed): `KIT=/home/user/incbusiness-ig-assets/kit/scripts/instagram`. Run it with `python3.13`. Never modify, commit or push the repository.

Every tool name and link comes from the live site through `list_reel_data.py`. Never type a tool, a link or a number yourself, never research, never use your memory.

## 1. Which slot

Get the IST time with `date -u -d '+330 minutes' '+%F %H:%M'` (the sandbox has no time zone data: `TZ=Asia/Calcutta date` silently prints UTC). The slot is the first of **12:00 (noon)** and **18:00 (evening)** IST that is at least 30 minutes away; if both have passed, stop ("no slot left today").

Call Metricool `getScheduledPosts` (blogId 6752944) for that day. If an Instagram REEL is already at that time (draft or not), stop and report "slot already filled".

## 2. Category and tools

```
python3.13 $KIT/list_reel_data.py pick <date> <noon|evening>          # prints "<slug> <part> <parts>" (takes 1-2 minutes)
python3.13 $KIT/list_reel_data.py fetch <slug> WORK <part>              # WORK/list.json + WORK/src/*.png
```

If `fetch` says there are too few tools, run `pick <date> <slot> 1` (then 2, 3...) for the next one in the rotation and fetch that. Open `WORK/list.json` and check: 6 to 12 tools, each with a name and a link that looks like the tool's own site.

## 3. The reel

**Make the 3D cover first (section 4), then build the reel.** The reel opens on the cover as its hook: it cracks and shatters into the list in the first second. The builder uses `WORK/out/cover.jpg` for that, so it must exist and be the final 3D cover before you start the build. Never start the build before the cover is done.


Add `"music_seed": <date digits><0 for noon, 1 for evening>` to `WORK/list.json` (e.g. `202611190`), so every reel has its own tune. Then:

```
pip install playwright imageio imageio-ffmpeg numpy pillow     (skip if python3.13 already has them)
python3.13 -m playwright install chromium
python3.13 $KIT/ai_list_reel.py build WORK
```

It writes `WORK/out/reel.mp4` (about 17 s, 2160x3840; it prints `"hook": true`) and check frames `WORK/out/check-bg*.jpg`, `check-hook-crack.jpg` and `check-hook-shatter.jpg`. If it prints `"hook": false`, the cover was missing: render the cover and build again. Look at every check frame: the small logo, the title ("AI tools for <Category>") and "Part X" (only when there are parts) on top, all names and links readable, none cut off, nothing overlapping. If a long link is cut, it is still fine as long as it is readable; report it.

## 4. The 3D cover

```
python3.13 $KIT/list_reel_data.py cover <date> <noon|evening> WORK
```

This writes `WORK/cover.json` with the colour world, layout, 3D number (the tools in this reel), "Part X" under the number when there are parts, and 3D prop already chosen, and prints `title_shape`, `blurb` (what the category's tools do, from the site) and the colours. **You only write the title**: replace the two `"WRITE ME"` lines in `cover.json`:

- 2 lines (line 2 in the accent colour, italic). 2 to 5 words in all. A 3rd short line is allowed.
- **Never start with "AI"**, never "Top" or "Best", **no number** (the 3D number is the count), no emoji.
- Use the suggested `title_shape`, so covers in a row look different.
- Only say what the `blurb` says the tools do. No claims the site doesn't make ("free", "best", "#1", rankings).
- Good: "Your marketing stack", "Close deals faster", "Who's talking about you?", "Inbox, sorted", "Not just Canva".

```
python3.13 $KIT/cover3d/cover3d.py WORK/cover.json WORK/out/cover.jpg
```

Look at `cover.jpg`: title fully visible and readable, number not cut, prop visible. Fix `cover.json` (shorter words, smaller `s`) and render again if needed.

## 5. Upload

`POST $SITE_URL/api/instagram/reel/media` (header `Authorization: Bearer $TOKEN`) with
`{"name": "2126-<MM>-<DD>-<morning for noon | evening for evening>", "files": {"reel.mp4": "<base64>", "cover.jpg": "<base64>"}}`
(the year 2126 keeps list reels apart from the news reels' folders). Write the JSON to a file and send it with `curl --data-binary @body.json -H "Content-Type: application/json"`. It returns the public `urls.reel` and `urls.cover`.

## 6. Caption

Plain English, no em dashes, names and links exactly as in `list.json`. Never write "with their website links", "Part X of Y" or "Part 2 comes next":

```
AI tools for {Category}{, Part X when there are parts}. Save this list.

{start}. {Tool}: {link}
{start+1}. {Tool}: {link}
...

Prices and details for every tool: incbusiness.in/ai-tools/{slug} (link in bio)
Follow @incbusiness.official for more AI tools.

#AI #Tech #Business #News #Insta #Follow #AITools #IncBusiness {up to 7 more about the category: #SalesTools #EmailMarketing ...}
```

**Always these 6 first:** `#AI #Tech #Business #News #Insta #Follow`. At most 15 hashtags in all.

## 7. Schedule (Metricool)

`createScheduledPost` with blogId 6752944, `date` the slot (e.g. `2026-11-19T12:00:00+05:30`) and `info`:
`providers: [{"network": "instagram"}]`, `instagramData: {"type": "REEL", "showReelOnFeed": true, "isAiGenerated": true}`, `media: [urls.reel]`, `videoThumbnailUrl: urls.cover`, `text`: the caption, `publicationDate: {"dateTime": "<slot>", "timezone": "Asia/Calcutta"}`, `autoPublish: true`, and `draft` as the routine's **MODE** says (draft = true, live = false).

The response's `media` must point to `static.metricool.com` (Metricool keeps its own copy). Then delete our uploaded copy with
`POST $SITE_URL/api/instagram/reel/posted` and `{"name": "<the same 2126-... name>", "slugs": ["list-reel", "<slug>", "<date>", "<noon|evening>", "tools"], "scheduled_for": "<slot>", "planner_url": "<plannerUrl>"}`.
If scheduling failed, do not call it; report the error.

## 8. Email with the cover

Make a small copy of the cover for the email: `python3.13 -c "from PIL import Image; Image.open('WORK/out/cover.jpg').resize((360, 640)).save('WORK/out/cover-email.jpg', quality=82)"`, then `sha256sum WORK/out/cover-email.jpg`.
Send it with Gmail `send_message` as an **inline image** so the cover shows inside the email: `attachments: [{"filename": "cover.jpg", "mimeType": "image/jpeg", "inline": true, "content": "sha256:<hash>:<absolute path of cover-email.jpg>"}]` and an `htmlBody` that starts with `<img src="cid:att0" width="270" alt="cover">`, followed by the details as simple HTML (`<p>`, `<br>`). Also give a plain-text `body` with the same details. The Gmail tool only accepts files from your session's scratchpad folder (`/tmp/claude-0/<project>/<session>/scratchpad`): copy `cover-email.jpg` there first and use that path and its sha256.

## 9. Report

End with: slot, category, number of tools, the cover title, reel length, the caption and the Metricool planner link. If you stopped early, say why.
