"""The Hospitality Signals newsletter: the welcome email and the Monday letter.

    python3 newsletter.py welcome                 -> emails/welcome.html (+ .txt)
    python3 newsletter.py weekly [YYYY-MM-DD]     -> emails/week-<monday>.html (+ .txt)
    python3 newsletter.py draft  [YYYY-MM-DD]     -> same, then a Brevo campaign DRAFT
                                                     and a test email; nothing is sent
                                                     to subscribers.

build.py also calls write_public() so that /email/welcome.html and
/email/logo.png are online: the Netlify function that greets each new
subscriber reads the welcome email from there.

Email HTML is table-based with inline styles, so it holds in Gmail and Outlook.
Instrument Sans in spaced capitals for labels and titles; the only red is the
dot of the logo. Standard library only.
"""
import json
import os
import sys
import urllib.request
from datetime import date, timedelta

import build
from build import CONTENT, FORMATS, SITE, e, fmt_of, image_for

ROOT = os.path.dirname(os.path.abspath(__file__))
EMAILS = os.path.join(ROOT, "emails")
LINKEDIN = "https://www.linkedin.com/company/hospitality-signals"

INK, GREY, RULE = "#0B0B0B", "#6B6863", "#E4E1DB"
SANS = "'Instrument Sans','Helvetica Neue',Helvetica,Arial,sans-serif"
CAPS = f"font-family:{SANS};text-transform:uppercase;letter-spacing:3px;font-weight:500;"
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


# ---------- content ----------

def articles(include_future=True):
    """Articles that are (or will be) on the site: same rules as build.load(),
    without the date cut-off when include_future is set."""
    out = []
    d = os.path.join(CONTENT, "articles")
    for f in sorted(os.listdir(d)):
        if not f.endswith(".json"):
            continue
        a = json.load(open(os.path.join(d, f), encoding="utf-8"))
        if a.get("status") not in build.PUBLIC_STATUS or not image_for(a, "photo"):
            continue
        if not include_future and (a.get("date_iso") or "") > date.today().isoformat():
            continue
        a["id"] = f[:-5]
        a["fmt"] = fmt_of(a)
        a["url"] = f"{SITE}/{a['fmt']}/{a['id']}/"
        out.append(a)
    return out


def week_of(day):
    monday = day - timedelta(days=day.weekday())
    return monday, monday + timedelta(days=6)


def next_monday(today=None):
    today = today or date.today()
    return today + timedelta(days=(7 - today.weekday()) % 7 or 7)


def span(monday, sunday):
    if monday.month == sunday.month:
        return f"{monday.day} to {sunday.day} {sunday.strftime('%B %Y')}"
    return f"{monday.day} {monday.strftime('%B')} to {sunday.day} {sunday.strftime('%B %Y')}"


# ---------- shell ----------

def shell(title, preheader, inner, footer_note):
    return f'''<!doctype html>
<html lang="en-GB" xmlns="http://www.w3.org/1999/xhtml">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="x-apple-disable-message-reformatting">
<meta name="color-scheme" content="light only">
<meta name="robots" content="noindex">
<title>{e(title)}</title>
<link href="https://fonts.googleapis.com/css2?family=Instrument+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  body {{ margin:0; padding:0; background:#FFFFFF; }}
  a {{ color:{INK}; }}
  @media (max-width:620px) {{
    .px {{ padding-left:20px !important; padding-right:20px !important; }}
    .h1 {{ font-size:24px !important; letter-spacing:2px !important; }}
    .thumb {{ width:96px !important; }}
    .thumb img {{ width:96px !important; height:auto !important; }}
  }}
</style>
</head>
<body style="margin:0;padding:0;background:#FFFFFF;color:{INK};">
<div style="display:none;max-height:0;overflow:hidden;mso-hide:all;">{e(preheader)}&#8199;&#847;&#8199;&#847;&#8199;&#847;&#8199;&#847;&#8199;&#847;&#8199;&#847;</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#FFFFFF;">
<tr><td align="center" style="padding:0;">
<table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0" style="width:100%;max-width:600px;">
  <tr><td class="px" align="center" style="padding:40px 40px 28px;">
    <a href="{SITE}/" style="text-decoration:none;"><img src="{SITE}/email/logo.png" width="200" alt="Hospitality Signals" style="display:block;width:200px;height:auto;border:0;color:{INK};font-family:{SANS};font-size:20px;letter-spacing:4px;text-transform:uppercase;"></a>
  </td></tr>
  <tr><td class="px" style="padding:0 40px;"><div style="border-top:1px solid {INK};font-size:0;line-height:0;">&nbsp;</div></td></tr>
{inner}
  <tr><td class="px" style="padding:40px 40px 0;"><div style="border-top:1px solid {RULE};font-size:0;line-height:0;">&nbsp;</div></td></tr>
  <tr><td class="px" align="center" style="padding:24px 40px 8px;{CAPS}font-size:11px;color:{GREY};">
    Independent &middot; Dated &middot; Sourced
  </td></tr>
  <tr><td class="px" align="center" style="padding:0 40px 8px;{CAPS}font-size:11px;color:{GREY};">
    <a href="{LINKEDIN}" style="color:{GREY};text-decoration:none;">LinkedIn</a> &middot; <a href="{SITE}/" style="color:{GREY};text-decoration:none;">hospitality-signals.com</a>
  </td></tr>
  <tr><td class="px" align="center" style="padding:8px 40px 48px;font-family:{SANS};font-size:12px;line-height:1.6;color:{GREY};">
    {footer_note}
  </td></tr>
</table>
</td></tr>
</table>
</body>
</html>
'''


def label(text, pad="36px 40px 12px"):
    return f'  <tr><td class="px" style="padding:{pad};{CAPS}font-size:12px;color:{GREY};">{text}</td></tr>\n'


def heading(text, pad="0 40px 20px"):
    return (f'  <tr><td class="px h1" style="padding:{pad};{CAPS}font-weight:600;font-size:28px;line-height:1.25;'
            f'letter-spacing:3px;color:{INK};">{e(text)}</td></tr>\n')


def para(text, pad="0 40px 16px", colour=INK):
    return (f'  <tr><td class="px" style="padding:{pad};font-family:{SANS};font-size:16px;line-height:1.6;'
            f'color:{colour};">{text}</td></tr>\n')


def button(text, href):
    return f'''  <tr><td class="px" align="left" style="padding:12px 40px 0;">
    <table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr>
      <td style="background:{INK};"><a href="{href}" style="display:inline-block;padding:16px 28px;{CAPS}font-size:12px;color:#FFFFFF;text-decoration:none;">{e(text)}</a></td>
    </tr></table>
  </td></tr>
'''


def credit(a):
    return f'<span style="font-size:11px;color:{GREY};">Photograph: {e(a.get("photo_credit"))}</span>'


def lead_item(a, kicker, link):
    img = f'<img src="{SITE}{image_for(a, "photo")}" width="520" alt="{e(a.get("title"))}" style="display:block;width:100%;height:auto;border:0;">'
    if link:
        img = f'<a href="{a["url"]}">{img}</a>'
    title = f'<a href="{a["url"]}" style="color:{INK};text-decoration:none;">{e(a.get("title"))}</a>' if link else e(a.get("title"))
    return f'''  <tr><td class="px" style="padding:28px 40px 0;">{img}</td></tr>
  <tr><td class="px" style="padding:6px 40px 0;font-family:{SANS};">{credit(a)}</td></tr>
  <tr><td class="px" style="padding:16px 40px 8px;{CAPS}font-size:11px;color:{GREY};">{kicker}</td></tr>
  <tr><td class="px" style="padding:0 40px 10px;font-family:{SANS};font-weight:600;font-size:22px;line-height:1.3;color:{INK};">{title}</td></tr>
{para(e(a.get("summary")), "0 40px 12px", GREY)}{more_line(a, link)}'''


def row_item(a, kicker, link):
    img = f'<img src="{SITE}{image_for(a, "photo")}" width="150" alt="{e(a.get("title"))}" style="display:block;width:150px;height:auto;border:0;">'
    if link:
        img = f'<a href="{a["url"]}">{img}</a>'
    title = f'<a href="{a["url"]}" style="color:{INK};text-decoration:none;">{e(a.get("title"))}</a>' if link else e(a.get("title"))
    return f'''  <tr><td class="px" style="padding:24px 40px 0;"><div style="border-top:1px solid {RULE};font-size:0;line-height:0;">&nbsp;</div></td></tr>
  <tr><td class="px" style="padding:20px 40px 0;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>
      <td class="thumb" width="150" valign="top" style="width:150px;">{img}</td>
      <td valign="top" style="padding-left:20px;">
        <div style="{CAPS}font-size:11px;color:{GREY};padding-bottom:8px;">{kicker}</div>
        <div style="font-family:{SANS};font-weight:600;font-size:17px;line-height:1.35;color:{INK};padding-bottom:6px;">{title}</div>
        <div style="font-family:{SANS};font-size:14px;line-height:1.5;color:{GREY};padding-bottom:8px;">{e(a.get("summary"))}</div>
        <div style="{CAPS}font-size:11px;">{more_inline(a, link)}</div>
      </td>
    </tr></table>
  </td></tr>
'''


def more_inline(a, link):
    if link:
        return f'<a href="{a["url"]}" style="color:{INK};text-decoration:none;border-bottom:1px solid {INK};">Read the article</a>'
    d = date.fromisoformat(a["date_iso"])
    return f'<span style="color:{GREY};">Online {DAYS[d.weekday()]}</span>'


def more_line(a, link):
    return f'  <tr><td class="px" style="padding:0 40px 0;{CAPS}font-size:11px;">{more_inline(a, link)}</td></tr>\n'


def to_text(lines):
    return "\n".join(lines).strip() + "\n"


# ---------- the two emails ----------

WELCOME_SUBJECT = "Welcome to Hospitality Signals"


def welcome():
    latest = sorted(articles(include_future=False), key=lambda a: a["date_iso"], reverse=True)[:3]
    inner = label("Welcome")
    inner += heading("You are on the list")
    inner += para("Thank you for subscribing. Hospitality Signals follows luxury hotels and the people who run them: "
                  "the openings, the appointments, the rankings and the figures that show where the industry is heading.")
    inner += para("Every Monday morning, one short letter: the articles coming out that week, in order. "
                  "No advertising, and nothing else.")
    inner += label("Four formats", "28px 40px 4px")
    for k in build.ORDER:
        f = FORMATS[k]
        inner += (f'  <tr><td class="px" style="padding:12px 40px 0;font-family:{SANS};font-size:15px;line-height:1.5;color:{GREY};">'
                  f'<span style="{CAPS}font-size:12px;font-weight:600;color:{INK};">{e(f["name"])}</span><br>{e(f["desc"])}</td></tr>\n')
    if latest:
        inner += label("Latest on the site", "40px 40px 0")
        for a in latest:
            kicker = f'{e(FORMATS[a["fmt"]]["name"])} &middot; {e(build.long_date(a["date_iso"]))}'
            inner += row_item(a, kicker, True)
    inner += '  <tr><td style="padding:20px 0 0;"></td></tr>\n' + button("Read Hospitality Signals", f"{SITE}/")
    note = ("You are receiving this email because you subscribed at hospitality-signals.com. "
            "Every Monday letter carries a one-click unsubscribe link.")
    html_out = shell(WELCOME_SUBJECT, "Every Monday, the week's articles on luxury hotels and the people who run them.", inner, note)

    text = ["HOSPITALITY SIGNALS", "", "YOU ARE ON THE LIST", "",
            "Thank you for subscribing. Hospitality Signals follows luxury hotels and the people who run them: "
            "the openings, the appointments, the rankings and the figures that show where the industry is heading.", "",
            "Every Monday morning, one short letter: the articles coming out that week, in order. No advertising, and nothing else.", "",
            "FOUR FORMATS"]
    for k in build.ORDER:
        text += [f"- {FORMATS[k]['name']}: {FORMATS[k]['desc']}"]
    if latest:
        text += ["", "LATEST ON THE SITE"]
        for a in latest:
            text += ["", a["title"], a["url"]]
    text += ["", f"{SITE}/", f"LinkedIn: {LINKEDIN}", "", note]
    return WELCOME_SUBJECT, html_out, to_text(text)


def weekly(monday):
    """The Monday letter for the week starting on `monday`. Articles already
    online on the send day (Monday) get a link; the others say which day they
    go online, so the letter never carries a link to a page that is not live yet."""
    monday, sunday = week_of(monday)
    week = [a for a in articles() if monday.isoformat() <= a["date_iso"] <= sunday.isoformat()]
    week.sort(key=lambda a: (a["date_iso"], a["id"]))
    when = span(monday, sunday)
    subject = f"The week ahead: {when.rsplit(' ', 1)[0]}"
    if not week:
        return subject, None, None

    def kicker(a):
        d = date.fromisoformat(a["date_iso"])
        return f'{DAYS[d.weekday()]} {d.day} {d.strftime("%B")} &middot; {e(FORMATS[a["fmt"]]["name"])}'

    live = lambda a: a["date_iso"] <= monday.isoformat()
    n = len(week)
    inner = label("The week ahead")
    inner += heading(when)
    inner += para(f'{"One article" if n == 1 else f"{n} articles"} on hospitality-signals.com this week. '
                  "Each one goes online on its day; follow along here or on LinkedIn.", "0 40px 4px", GREY)
    inner += lead_item(week[0], kicker(week[0]), live(week[0]))
    for a in week[1:]:
        inner += row_item(a, kicker(a), live(a))
    inner += '  <tr><td style="padding:20px 0 0;"></td></tr>\n' + button("Read Hospitality Signals", f"{SITE}/")
    note = ('You are receiving this letter because you subscribed at hospitality-signals.com. '
            f'<a href="{{{{ unsubscribe }}}}" style="color:{GREY};">Unsubscribe</a>.')
    preheader = " · ".join(a["title"] for a in week[:2])
    html_out = shell(subject, preheader, inner, note)

    text = ["HOSPITALITY SIGNALS", "", "THE WEEK AHEAD", when.upper(), ""]
    for a in week:
        d = date.fromisoformat(a["date_iso"])
        text += [f"{DAYS[d.weekday()]} {d.day} {d.strftime('%B')} · {FORMATS[a['fmt']]['name']}", a["title"], a.get("summary") or ""]
        text += [a["url"] if live(a) else f"Online {DAYS[d.weekday()]}", ""]
    text += [f"{SITE}/", f"LinkedIn: {LINKEDIN}", "", "Unsubscribe: {{ unsubscribe }}"]
    return subject, html_out, to_text(text)


# ---------- output ----------

def write_public(out):
    """Called by build.py: the welcome email and the logo, served from the site."""
    os.makedirs(os.path.join(out, "email"), exist_ok=True)
    import shutil
    shutil.copy(os.path.join(build.SRC, "email-logo.png"), os.path.join(out, "email", "logo.png"))
    subject, html_out, text = welcome()
    open(os.path.join(out, "email", "welcome.html"), "w", encoding="utf-8").write(html_out)
    open(os.path.join(out, "email", "welcome.json"), "w", encoding="utf-8").write(
        json.dumps({"subject": subject, "text": text}, ensure_ascii=False))


def save(name, html_out, text):
    os.makedirs(EMAILS, exist_ok=True)
    open(os.path.join(EMAILS, name + ".html"), "w", encoding="utf-8").write(html_out)
    open(os.path.join(EMAILS, name + ".txt"), "w", encoding="utf-8").write(text)
    print(os.path.join(EMAILS, name + ".html"))


def brevo(path, payload):
    req = urllib.request.Request("https://api.brevo.com/v3" + path, data=json.dumps(payload).encode(),
                                 headers={"api-key": os.environ["BREVO_API_KEY"], "content-type": "application/json",
                                          "accept": "application/json"}, method="POST")
    with urllib.request.urlopen(req) as r:
        body = r.read()
        return json.loads(body) if body else {}


def draft(monday, subject, html_out):
    """A campaign draft in Brevo plus a test email to NEWSLETTER_TEST_TO.
    Subscribers get nothing until Natan presses Send (or schedules it) in Brevo."""
    env = os.environ
    camp = brevo("/emailCampaigns", {
        "name": f"Week ahead {monday.isoformat()}",
        "subject": subject,
        "sender": {"name": "Hospitality Signals", "email": env["NEWSLETTER_FROM"]},
        "replyTo": env.get("NEWSLETTER_REPLY_TO") or env["NEWSLETTER_FROM"],
        "htmlContent": html_out,
        "recipients": {"listIds": [int(env["BREVO_LIST_ID"])]},
    })
    print(f"Brevo draft campaign {camp.get('id')} created")
    tests = [t.strip() for t in env.get("NEWSLETTER_TEST_TO", "").split(",") if t.strip()]
    if tests:
        brevo(f"/emailCampaigns/{camp['id']}/sendTest", {"emailTo": tests})
        print("Test sent to " + ", ".join(tests))


def main(argv):
    cmd = argv[1] if len(argv) > 1 else "weekly"
    if cmd == "welcome":
        _, h, t = welcome()
        save("welcome", h, t)
        return
    monday = date.fromisoformat(argv[2]) if len(argv) > 2 else next_monday()
    monday, _ = week_of(monday)
    subject, h, t = weekly(monday)
    if h is None:
        print(f"No article dated in the week of {monday}: no letter.")
        return
    print(subject)
    save(f"week-{monday.isoformat()}", h, t)
    if cmd == "draft":
        draft(monday, subject, h)


if __name__ == "__main__":
    main(sys.argv)
