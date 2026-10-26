"""Build hospitality-signals.com as a static site.

Reads content/articles/*.json (exported from The Signals Library) and
content/images/, writes the finished site to public/. Standard library only,
so Netlify can run it as the build command: python3 build.py
"""
import html
import json
import os
import shutil
from datetime import date, datetime, timezone
from email.utils import format_datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
CONTENT = os.path.join(ROOT, "content")
SRC = os.path.join(ROOT, "src")
OUT = os.path.join(ROOT, "public")
SITE = "https://hospitality-signals.com"

FORMATS = {
    "signal-of-the-week": {
        "name": "Signal of the Week", "when": "Mondays",
        "strap": "Market, platform and rule changes",
        "desc": "One change in the market, a platform or a rule, and what it means for a hotelier.",
    },
    "new-in-post": {
        "name": "New in Post", "when": "Wednesdays",
        "strap": "The appointments worth knowing",
        "desc": "General managers and leaders taking up new roles across luxury hospitality.",
    },
    "the-list": {
        "name": "The List", "when": "As rankings are published",
        "strap": "Rankings and distinctions, read closely",
        "desc": "Rankings and distinctions, from the 50 Best to Michelin and Forbes, and what sits behind them.",
    },
    "in-conversation": {
        "name": "In Conversation", "when": "Thursdays or Fridays",
        "strap": "Leaders, in their own words",
        "desc": "Interviews with the people who run luxury hotels and groups.",
    },
}
ORDER = ["signal-of-the-week", "new-in-post", "the-list", "in-conversation"]
PUBLIC_STATUS = {"ready", "published"}

e = lambda s: html.escape(str(s or ""), quote=True)


def fmt_of(a):
    c = (a.get("category") or "").lower()
    if c == "appointment":
        return "new-in-post"
    if c == "ranking":
        return "the-list"
    if c == "interview":
        return "in-conversation"
    return "signal-of-the-week"


def long_date(iso):
    try:
        d = date.fromisoformat(iso)
        return f"{d.day} {d.strftime('%B %Y')}"
    except Exception:
        return iso or ""


def credit_ok(a):
    c = (a.get("photo_credit") or "").strip().lower()
    return bool(c) and "confirm" not in c


def image_for(a, kind):
    """Path of a site image, or None. kind: photo | cover_wide | cover_tall."""
    if not credit_ok(a):
        return None
    key = {"photo": a.get("photo_asset"),
           "cover_wide": (a.get("visuals") or {}).get("site_16x9"),
           "cover_tall": (a.get("visuals") or {}).get("linkedin_4x5")}[kind]
    if key and os.path.exists(os.path.join(CONTENT, "images", key + ".jpg")):
        return f"/images/{key}.jpg"
    return None


def load():
    arts = []
    d = os.path.join(CONTENT, "articles")
    for f in sorted(os.listdir(d)):
        if not f.endswith(".json"):
            continue
        a = json.load(open(os.path.join(d, f), encoding="utf-8"))
        if a.get("status") not in PUBLIC_STATUS:
            continue
        a["id"] = f[:-5]
        a["fmt"] = fmt_of(a)
        a["url"] = f"/{a['fmt']}/{a['id']}/"
        arts.append(a)
    posts = {}
    pd = os.path.join(CONTENT, "posts")
    if os.path.isdir(pd):
        for f in os.listdir(pd):
            if f.endswith(".json"):
                p = json.load(open(os.path.join(pd, f), encoding="utf-8"))
                if p.get("article_id"):
                    posts[p["article_id"]] = p
    today = date.today().isoformat()
    # most recent first; upcoming events come after the news of the week
    arts.sort(key=lambda a: ((a.get("date_iso") or "") <= today, a.get("date_iso") or "", a["id"]), reverse=True)
    return arts, posts


# ---------- building blocks ----------

LOGO = ('<span class="logo-kicker">Hospitality</span>'
        '<span class="logo-word">S<span class="logo-i">ı<span class="logo-dot" aria-hidden="true"></span></span>gnals</span>')


def nav(current=None):
    cur = ' aria-current="page"'
    links = "".join(
        f'<a href="/{k}/"{cur if k == current else ""}>{FORMATS[k]["name"]}</a>' for k in ORDER)
    about = '<a href="/about/" aria-current="page">About</a>' if current == "about" else '<a href="/about/">About</a>'
    return f'<nav class="nav" aria-label="Formats">\n    {links}\n    {about}\n  </nav>'


def minibar(current=None):
    return f'''<header class="minibar minibar-sticky">
  <div class="wrap minibar-row">
  <a class="logo small" href="/" aria-label="Hospitality Signals — home">{LOGO}</a>
  {nav(current)}</div>
</header>'''


NEWSLETTER = '''<section class="newsletter" id="newsletter">
    <p class="label">The newsletter</p>
    <h2 class="caps-title">Signals, by email</h2>
    <p class="muted">A short letter when there is something worth reading. No advertising.</p>
    <form name="newsletter" method="POST" data-netlify="true" netlify-honeypot="company" action="/thanks/">
      <input type="hidden" name="form-name" value="newsletter">
      <p class="hp"><label>Company <input name="company"></label></p>
      <label class="sr" for="email">Email address</label>
      <input id="email" type="email" name="email" placeholder="Email address" required autocomplete="email">
      <button type="submit">Subscribe</button>
    </form>
  </section>'''

FOOTER = f'''<footer class="footer">
  <div class="wrap footer-row">
    <span>Independent · Dated · Sourced</span>
    <span><a href="https://www.linkedin.com/company/hospitality-signals">LinkedIn</a> · <a href="/contact/">Contact</a></span>
  </div>
  <div class="wrap footer-row footer-small">
    <span>© {date.today().year} Hospitality Signals</span>
    <span>hospitality-signals.com</span>
  </div>
</footer>'''


def page(title, desc, body, path, image=None, kind="website"):
    full = title if title == "Hospitality Signals" else f"{title} · Hospitality Signals"
    img = f'<meta property="og:image" content="{SITE}{e(image)}">\n<meta name="twitter:card" content="summary_large_image">' if image else '<meta name="twitter:card" content="summary">'
    return f'''<!doctype html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{e(full)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{SITE}{path}">
<meta property="og:type" content="{kind}">
<meta property="og:site_name" content="Hospitality Signals">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{SITE}{path}">
{img}
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Bodoni+Moda:opsz,wght@6..96,400;6..96,500&family=Instrument+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/style.css">
</head>
<body>
{body}
<script src="/site.js" defer></script>
</body>
</html>
'''


def frame(a, kind, n, cls=""):
    """A photo frame: the image if cleared, otherwise a quiet typographic panel."""
    src = image_for(a, kind) if a else None
    if src:
        alt = e(a.get("title"))
        return f'<div class="photo-frame"><img src="{src}" alt="{alt}" loading="lazy" decoding="async"></div>'
    return f'<div class="photo-frame"><div class="photo-ph ph-{n % 4}" role="img" aria-label=""></div></div>'


def meta(a, link_format=False):
    f = FORMATS[a["fmt"]]
    fmt = f'<a href="/{a["fmt"]}/">{f["name"]}</a>' if link_format else f'<span class="meta-format">{f["name"]}</span>'
    return f'<span class="meta">{fmt}<span>{e(long_date(a.get("date_iso")))}</span></span>'


def card(a, n):
    return f'''<li class="card reveal">
    <a href="{a["url"]}">
      <figure class="photo card-photo">{tile(a, n)}</figure>
      {meta(a)}
      <span class="card-title">{e(a.get("title"))}</span>
      <span class="card-summary">{e(a.get("summary"))}</span>
    </a>
  </li>'''


def body_html(a, post):
    """Article body. Uses the LinkedIn post text when there is one, minus mentions, hashtags and the closing question."""
    paras = []
    if post and post.get("post_text"):
        for p in post["post_text"].split("\n\n"):
            p = p.strip()
            if not p or p.startswith("@") or p.startswith("#"):
                continue
            paras.append(p)
        if paras and paras[-1].endswith("?"):
            paras.pop()
        if paras:
            paras.pop(0)  # the hook is already the standfirst's job
    out = []
    if paras:
        for p in paras:
            if p.lower().startswith("the signal:"):
                out.append("<h2>The signal</h2>")
                out.append(f"<p>{e(p.split(':', 1)[1].strip())}</p>")
            else:
                out.append(f"<p>{e(p)}</p>")
    else:
        if a.get("why"):
            out.append("<h2>The signal</h2>")
            out.append(f"<p>{e(a['why'])}</p>")
    return "\n".join(out)


def sources_html(a):
    items = []
    for s in a.get("sources") or []:
        u = s.get("url") or ""
        if u.startswith("https://") or u.startswith("http://"):
            items.append(f'<a href="{e(u)}" rel="noopener">{e(s.get("name") or "Source")}</a>')
        elif s.get("name"):
            items.append(e(s["name"]))
    src = " · ".join(items) or "To be confirmed"
    credit = f'<p class="muted">Photograph: {e(a["photo_credit"])}</p>' if image_for(a, "photo") or image_for(a, "cover_wide") else ""
    return f'''<aside class="source">
      <p class="label">Source</p>
      <p>{src}</p>
      {credit}
    </aside>'''


# ---------- pages ----------

def article_page(a, post, n):
    wide, tall = image_for(a, "cover_wide"), image_for(a, "cover_tall")
    photo = image_for(a, "photo")
    if wide and tall:
        cover = (f'<figure class="photo cover-photo cover-visual"><picture>'
                 f'<source media="(max-width: 760px)" srcset="{tall}">'
                 f'<img src="{wide}" alt="{e(a.get("title"))}"></picture></figure>')
    elif photo:
        cover = f'<figure class="photo cover-photo">{frame(a, "photo", n)}</figure>'
    else:
        cover = ""
    body = f'''{minibar(a["fmt"])}
<main>
  <div class="progress" aria-hidden="true"></div>
  <article>
    <header class="article-head wrap">
      {meta(a, link_format=True)}
      <h1 class="article-title">{e(a.get("title"))}</h1>
      <p class="article-standfirst">{e(a.get("summary"))}</p>
    </header>
    {cover}
    <div class="article wrap">
      <div class="article-body">
{body_html(a, post)}
      </div>
      {sources_html(a)}
    </div>
  </article>
  {NEWSLETTER}
</main>
{FOOTER}'''
    return page(a.get("title"), a.get("summary"), body, a["url"], wide or photo, "article")


def format_page(key, arts):
    f = FORMATS[key]
    lead = next((a for a in arts if image_for(a, "photo")), None)
    if arts:
        lst = "<ol class=\"cards\">" + "".join(card(a, i) for i, a in enumerate(arts)) + "</ol>"
    else:
        lst = '<p class="empty">The first pieces are in preparation. <a href="#newsletter">Subscribe</a> to receive them.</p>'
    body = f'''{minibar(key)}
<main>
  <section class="hero hero-format">
    <figure class="photo hero-photo">{frame(lead, "photo", ORDER.index(key) + 1)}</figure>
    <div class="hero-text wrap">
      <span class="meta"><span class="meta-format">{e(f["when"])}</span></span>
      <h1 class="hero-title hero-title-xl">{e(f["name"])}</h1>
      <span class="hero-strap">{e(f["strap"])}</span>
    </div>
  </section>
  <section class="section-head wrap">
    <p class="section-desc reveal">{e(f["desc"])}</p>
  </section>
  <section class="wrap">{lst}</section>
  {NEWSLETTER}
</main>
{FOOTER}'''
    return page(f["name"], f["desc"], body, f"/{key}/")


def tile(a, n):
    """Image frame for gallery cards: the cleared photo, or a typographic tile."""
    src = image_for(a, "photo")
    if src:
        return f'<div class="tile"><img src="{src}" alt="{e(a.get("title"))}" loading="lazy" decoding="async"></div>'
    try:
        d = date.fromisoformat(a.get("date_iso") or "")
        big = f"{d.day:02d}.{d.month:02d}"
    except Exception:
        big = ""
    return (f'<div class="tile tile-type tone-{n % 3}" aria-hidden="true">'
            f'<span class="tile-date">{big}</span><span class="tile-fmt">{e(FORMATS[a["fmt"]]["name"])}</span></div>')


def home_page(arts, by_fmt, posts):
    week = max((a.get("week") or "" for a in arts), default="")
    issue = f"Week of {long_date(week)}" if week else ""
    # the edition sentence: this week's three posts, else the three latest titles
    wk = sorted((p for p in posts.values() if p.get("week") == week), key=lambda p: p.get("order", 9))
    by_id = {a["id"]: a for a in arts}
    picks = [by_id[p["article_id"]] for p in wk if p.get("article_id") in by_id]
    lead = next((a for a in picks if image_for(a, "photo")), None) or (picks[0] if picks else None) \
        or next((a for a in arts if image_for(a, "photo")), arts[0] if arts else None)
    lines = []
    for p in wk[:3]:
        vt = p.get("visual_text") or {}
        if vt.get("lead") and vt.get("rest"):
            lines.append(f'{vt["lead"]} {vt["rest"]}'.rstrip("."))
    if not lines:
        lines = [a.get("title", "") for a in arts[:3]]
    statement = "This week. " + ". ".join(lines) + "."
    words = "".join(f'<span class="w">{e(w)}</span> ' for w in statement.split())

    window = ""
    if lead:
        img = image_for(lead, "photo")
        media = (f'<img src="{img}" alt="" decoding="async">' if img
                 else '<div class="window-ink" aria-hidden="true"></div>')
        window = f"""<a class="window" href="{lead["url"]}" aria-label="{e(lead.get("title"))}">
      {media}
      <span class="window-dot" aria-hidden="true"></span>
      <div class="window-text wrap">
        {meta(lead)}
        <h2 class="window-title">{e(lead.get("title"))}</h2>
        <span class="more">Read the signal</span>
      </div>
    </a>"""

    reel_items = ([a for a in picks if a is not lead] + [a for a in arts if a is not lead and a not in picks])[:8]
    reel = "".join(f"""<li class="reel-item">
        <a href="{a["url"]}">
          {tile(a, i)}
          {meta(a)}
          <span class="reel-title">{e(a.get("title"))}</span>
        </a>
      </li>""" for i, a in enumerate(reel_items))

    rows = []
    for k in ORDER:
        latest = by_fmt[k][0] if by_fmt[k] else None
        sub = e(latest.get("title")) if latest else "First interview coming soon"
        rows.append(f"""<li><a class="index-row" href="/{k}/">
          <span class="index-name">{e(FORMATS[k]["name"])}</span>
          <span class="index-latest">{sub}</span>
        </a></li>""")

    cities = ["Paris", "Côte d'Azur", "The Alps", "Monaco", "Switzerland", "Saint-Barthélemy", "London", "Dubai", "Hong Kong", "Singapore"]
    half = "".join(f'<span class="city">{c}</span><span class="sep" aria-hidden="true">●</span>' for c in cities)
    ribbon = f'<span class="cities-half">{half}</span><span class="cities-half" aria-hidden="true">{half}</span>'

    body = f"""<header class="sitebar" data-sitebar>
  <div class="wrap minibar-row">
  <a class="logo small" href="/" aria-label="Hospitality Signals — home">{LOGO}</a>
  {nav()}</div>
</header>
<main>
  <section class="opening" data-opening>
    <div class="opening-stage">
      {window}
      <div class="opening-mark">
        <p class="opening-issue"><span>{e(issue)}</span><span>Luxury hospitality</span></p>
        <h1 class="logo large" aria-label="Hospitality Signals">{LOGO}</h1>
        <p class="opening-line">The people, places and deals shaping luxury hotels, dated and sourced.</p>
      </div>
      <span class="scroll-cue" aria-hidden="true">Scroll</span>
    </div>
  </section>

  <section class="statement wrap" data-statement>
    <p class="statement-text">{words}</p>
  </section>

  <section class="reel" data-reel>
    <div class="reel-stage">
      <div class="reel-head wrap"><h2 class="reel-heading">Recent signals</h2></div>
      <ol class="reel-track">{reel}</ol>
    </div>
  </section>

  <section class="cities-band" aria-label="{e(', '.join(cities))}">
    <p class="cities">{ribbon}</p>
  </section>

  <section class="index wrap" data-index>
    <h2 class="index-heading">Four formats</h2>
    <ol class="index-list">{"".join(rows)}</ol>
  </section>
  {NEWSLETTER}
</main>
{FOOTER}"""
    return page("Hospitality Signals",
                "An independent publication about luxury hotels and the people who run them: appointments, openings, deals and rankings, dated and sourced.",
                body, "/", image_for(lead, "photo") if lead else None)


ABOUT = '''<p>The changes that shape luxury hospitality rarely make headlines at first.</p>
<p>A new general manager in Monaco. A booking platform rewriting its rules. A ranking that reshuffles a city. On their own, they are details. Read together, they show where the industry is heading.</p>
<p>Hospitality Signals is an independent publication about luxury hotels and the people who run them. Paris, the Côte d'Azur and the Alps. Monaco, Switzerland and Saint-Barthélemy. London, Dubai, Hong Kong and Singapore. Hotels and groups first, restaurants next.</p>
<h2>Four formats, one standard</h2>
<ul><li><strong>Signal of the Week</strong>: a market, platform or rule change, and what it means for a hotelier.</li><li><strong>New in Post</strong>: the appointments worth knowing.</li><li><strong>The List</strong>: rankings and distinctions, read closely.</li><li><strong>In Conversation</strong>: leaders, in their own words.</li></ul>
<h2>How we work</h2>
<p>No advertising. No gossip. Every fact is dated and sourced, and the source is named at the end of each piece. When something cannot yet be confirmed, we say so.</p>
<p>Corrections, tips and interview requests: <a href="/contact/">write to us</a>.</p>'''


def simple_page(title, inner, path, current=None, newsletter=True, desc=""):
    body = f'''{minibar(current)}
<main>
  <article class="article wrap">
    <header class="article-head"><h1 class="page-title">{e(title)}</h1></header>
    <div class="article-body">{inner}</div>
  </article>
  {NEWSLETTER if newsletter else ""}
</main>
{FOOTER}'''
    return page(title, desc or title, body, path)


CONTACT_FORM = """<form class="contact-form" name="contact" method="POST" action="/contact/sent/"
      data-netlify="true" data-netlify-recaptcha="true" netlify-honeypot="website">
  <input type="hidden" name="form-name" value="contact">
  <p class="hp"><label>Website <input name="website" tabindex="-1" autocomplete="off"></label></p>
  <div class="field">
    <label for="c-first">First name</label>
    <input id="c-first" name="first_name" type="text" autocomplete="given-name" required>
  </div>
  <div class="field">
    <label for="c-last">Last name</label>
    <input id="c-last" name="last_name" type="text" autocomplete="family-name" required>
  </div>
  <div class="field field-wide">
    <label for="c-reason">Reason for contact</label>
    <select id="c-reason" name="reason" required>
      <option value="">Choose one</option>
      <option>News or press release</option>
      <option>Appointment to announce</option>
      <option>Interview request</option>
      <option>Correction</option>
      <option>Partnership</option>
      <option>Other</option>
    </select>
  </div>
  <div class="field">
    <label for="c-email">Email</label>
    <input id="c-email" name="email" type="email" autocomplete="email" required>
  </div>
  <div class="field">
    <label for="c-phone">Phone <span class="opt">(optional)</span></label>
    <input id="c-phone" name="phone" type="tel" autocomplete="tel" inputmode="tel">
  </div>
  <div class="field field-wide">
    <label for="c-message">Message</label>
    <textarea id="c-message" name="message" rows="7" required></textarea>
  </div>
  <div class="field field-wide captcha" data-netlify-recaptcha="true"></div>
  <div class="field-wide form-foot">
    <button type="submit">Send message</button>
    <p class="muted small">Your details are used only to reply to you.</p>
  </div>
</form>"""


def contact_page():
    inner = ('<p>News, an appointment to announce, a correction or an interview request: '
             'write to us and we reply within a few days.</p>' + CONTACT_FORM)
    return simple_page("Contact", inner, "/contact/", newsletter=False,
                       desc="Contact Hospitality Signals: news, appointments, corrections and interview requests.")


def feed(arts):
    now = format_datetime(datetime.now(timezone.utc))
    items = []
    for a in arts[:30]:
        try:
            d = datetime.fromisoformat(a["date_iso"]).replace(tzinfo=timezone.utc)
        except Exception:
            d = datetime.now(timezone.utc)
        items.append(f'''<item><title>{e(a.get("title"))}</title><link>{SITE}{a["url"]}</link><guid>{SITE}{a["url"]}</guid><pubDate>{format_datetime(d)}</pubDate><description>{e(a.get("summary"))}</description></item>''')
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>Hospitality Signals</title><link>{SITE}/</link><description>Luxury hospitality, dated and sourced.</description><language>en-gb</language><lastBuildDate>{now}</lastBuildDate>
{"".join(items)}
</channel></rss>
'''


def write(path, text):
    full = os.path.join(OUT, path.strip("/"), "index.html") if not path.endswith((".xml", ".txt", ".svg", ".html")) else os.path.join(OUT, path.lstrip("/"))
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(text)


def main():
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    arts, posts = load()
    by_fmt = {k: [a for a in arts if a["fmt"] == k] for k in ORDER}

    css = open(os.path.join(SRC, "style.css"), encoding="utf-8").read()
    css += "\n" + open(os.path.join(SRC, "motion.css"), encoding="utf-8").read()
    css += "\n.cover-visual img{width:100%;height:auto;display:block}\n.cover-quiet .photo-frame{height:min(38svh,360px)}\n.photo-frame>img{width:100%;height:100%;object-fit:cover}\n"
    open(os.path.join(OUT, "style.css"), "w", encoding="utf-8").write(css)
    shutil.copy(os.path.join(SRC, "site.js"), os.path.join(OUT, "site.js"))
    shutil.copy(os.path.join(SRC, "favicon.svg"), os.path.join(OUT, "favicon.svg"))
    img_src = os.path.join(CONTENT, "images")
    if os.path.isdir(img_src):
        shutil.copytree(img_src, os.path.join(OUT, "images"))

    write("/", home_page(arts, by_fmt, posts))
    for k in ORDER:
        write(f"/{k}/", format_page(k, by_fmt[k]))
    for i, a in enumerate(arts):
        write(a["url"], article_page(a, posts.get(a["id"]), i))
    write("/about/", simple_page("About", ABOUT, "/about/", "about",
                                 desc="Hospitality Signals is an independent publication about luxury hotels and the people who run them."))
    write("/contact/sent/", simple_page("Message sent", '<p>Thank you. Your message has reached us and we will reply by email.</p><p><a href="/">Back to the front page</a></p>', "/contact/sent/", newsletter=False))
    write("/thanks/", simple_page("Thank you", '<p>You are on the list. The next signal will reach you by email.</p><p><a href="/">Back to the front page</a></p>', "/thanks/", newsletter=False))
    write("/404.html", simple_page("Page not found", '<p>This page does not exist, or it has moved.</p><p><a href="/">Back to the front page</a></p>', "/404.html", newsletter=False))
    write("/contact/", contact_page())
    urls = ["/", "/about/", "/contact/"] + [f"/{k}/" for k in ORDER] + [a["url"] for a in arts]
    write("/sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
          + "".join(f"<url><loc>{SITE}{u}</loc></url>" for u in urls) + "</urlset>\n")
    write("/robots.txt", f"User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n")
    print(f"Built {len(arts)} articles into {OUT}")


if __name__ == "__main__":
    main()
