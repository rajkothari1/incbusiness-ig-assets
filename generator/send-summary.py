"""Emails the daily reel summary with each reel's real snapshot embedded in the email.

The Gmail connector strips outside images and cannot take binary attachments reliably,
so this sends through the Resend HTTPS API (key in the RESEND_API_KEY environment variable).
Snapshots go in as inline attachments (cid), so they show inside the email with nothing to click.

Usage: python3 generator/send-summary.py <stories.json> <schedule.json> <snaps_dir> "<subject>" "<status line>" [extra_html_file]
  schedule.json: [{"slug": "...", "time": "09:00", "caption": "full caption text"}, ...] in time order
  snaps_dir: folder with <slug>.jpg for each reel
"""
import base64
import html
import json
import os
import subprocess
import sys
import urllib.request

stories_file, schedule_file, snaps_dir, subject, status = sys.argv[1:6]
extra = open(sys.argv[6]).read() if len(sys.argv) > 6 else ''
TO = os.environ.get('SUMMARY_TO', 'raj.kothari90@gmail.com')
stories = {s['slug']: s for s in json.load(open(stories_file))}
schedule = json.load(open(schedule_file))

parts, attachments = [], []
for i, item in enumerate(schedule, 1):
    s = stories[item['slug']]
    snap = os.path.join(snaps_dir, f"{item['slug']}.jpg")
    small = f"/tmp/email-snap-{i}.jpg"
    # 480px wide keeps the email light while staying sharp on a phone
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', snap, '-vf', 'scale=480:-2', '-q:v', '5', small], check=True)
    cid = f"reel{i}"
    attachments.append({'filename': f"{item['slug']}.jpg", 'content': base64.b64encode(open(small, 'rb').read()).decode(),
                        'content_id': cid, 'content_type': 'image/jpeg'})
    cap = html.escape(item['caption']).replace('\n', '<br>')
    parts.append(f'''<p style="margin:22px 0 8px;font-size:15px"><b>{item['time']} · <span style="color:#D92B2B">{html.escape(s['category'])}</span></b></p>
<img src="cid:{cid}" width="300" alt="{html.escape(item['slug'])}" style="display:block;width:300px;border-radius:12px;border:0">
<p style="margin:10px 0 0;font-size:13px;color:#333">{cap}</p>
<hr style="border:none;border-top:1px solid #eee;margin:18px 0 0">''')

body = f'''<div style="font-family:Arial,sans-serif;font-size:14px;color:#111;max-width:420px">
<h2 style="color:#0B1257;margin:0 0 6px">{html.escape(subject)}</h2>
<p style="margin:0">{html.escape(status)}</p>
{''.join(parts)}
{extra}
<p style="color:#9C1C2B">⚠️ Posts auto-publish hain. Kuch galat lage to time se pehle Metricool me edit ya delete kar dena.</p></div>'''

req = urllib.request.Request('https://api.resend.com/emails', method='POST', data=json.dumps({
    'from': os.environ.get('SUMMARY_FROM', 'incbusiness reels <onboarding@resend.dev>'),
    'to': [TO], 'subject': subject, 'html': body, 'attachments': attachments}).encode(),
    headers={'Authorization': f"Bearer {os.environ['RESEND_API_KEY']}", 'Content-Type': 'application/json',
             'User-Agent': 'incbusiness-reels/1.0'})
print(urllib.request.urlopen(req).read().decode())
