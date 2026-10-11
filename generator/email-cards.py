"""Builds the daily summary email body with an HTML replica of each reel card.

The Gmail connector strips <img> tags that point outside the email, so each card is
drawn with plain HTML and inline CSS (category tag, red keywords, READ MORE banner).

Usage: python3 generator/email-cards.py <stories.json> <schedule.json> <out.html>
  schedule.json: [{"slug": "...", "time": "09:00", "caption": "full caption text"}, ...]
  Rows are written in schedule order.
"""
import html
import json
import re
import sys

stories = {s['slug']: s for s in json.load(open(sys.argv[1]))}
schedule = json.load(open(sys.argv[2]))
out = sys.argv[3]


def headline(h):
    return re.sub(r'\[\[(.+?)\]\]', r'<span style="color:#E03131">\1</span>', html.escape(h))


def brand(s):
    if s.get('pillText'):
        return s['pillText']
    m = re.search(r'\[\[(.+?)\]\]', s['cardHeadline'])
    return m.group(1) if m else s['category']


def card(s):
    return f'''<table cellpadding="0" cellspacing="0" border="0" width="300" style="width:300px;background:#ffffff;border-radius:16px;border:1px solid #e5e5e5;font-family:Arial,sans-serif">
<tr><td style="padding:10px 10px 0">
  <table cellpadding="0" cellspacing="0" border="0" width="100%" style="background:#0B1257;border-radius:12px">
  <tr><td align="center" style="padding:42px 10px 30px">
    <span style="display:inline-block;background:#ffffff;border-radius:12px;padding:12px 22px;font-size:22px;font-weight:bold;color:#111">{html.escape(brand(s))}</span>
  </td></tr></table>
</td></tr>
<tr><td align="center" style="padding:0">
  <span style="display:inline-block;background:#D92B2B;color:#ffffff;font-size:13px;font-weight:bold;padding:6px 18px;border-radius:4px;margin-top:-14px">{html.escape(s['category'])}</span>
</td></tr>
<tr><td style="padding:14px 16px 16px;font-size:24px;line-height:1.15;font-weight:900;color:#111111">{headline(s['cardHeadline'])}</td></tr>
<tr><td style="padding:0 0 12px">
  <table cellpadding="0" cellspacing="0" border="0" width="100%"><tr>
  <td><span style="display:inline-block;background:#0B1257;color:#ffffff;font-size:12px;font-weight:bold;font-style:italic;padding:6px 26px 6px 14px">READ MORE</span></td>
  <td align="right" style="padding-right:14px;color:#E03131;font-size:12px;font-weight:bold">IG · in</td>
  </tr></table>
</td></tr>
</table>'''


rows = []
for item in schedule:
    s = stories[item['slug']]
    cap = html.escape(item['caption']).replace('\n', '<br>')
    rows.append(f'''<p style="margin:22px 0 8px;font-size:15px"><b>{item['time']} · <span style="color:#D92B2B">{html.escape(s['category'])}</span></b></p>
{card(s)}
<p style="margin:10px 0 0;font-size:13px;color:#333">{cap}</p>
<hr style="border:none;border-top:1px solid #eee;margin:18px 0 0">''')

open(out, 'w').write('\n'.join(rows))
print('wrote', out)
