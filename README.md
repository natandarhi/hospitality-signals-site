# hospitality-signals.com

Static site for Hospitality Signals, built from The Signals Library.

- `content/articles/*.json`: one file per article, exported from the library (collection `articles`). Only `status` = `ready` or `published` goes live.
- `content/posts/*.json`: the week's LinkedIn posts (collection `posts`); when an article has one, its text becomes the article body.
- `content/images/<asset id>.jpg`: photos and visuals. A photo appears only when the article's `photo_credit` is confirmed (no "to be confirmed").
- `src/`: styles, script and favicon, taken from the validated design.
- `build.py`: writes the site to `public/`. Netlify runs it on every push (`netlify.toml`).

Build locally: `python3 build.py`, then open `public/index.html` through any static server.

## Newsletter

- Sign-ups: the `newsletter` Netlify form. `netlify/functions/submission-created.mjs` adds each new address to the Brevo list and sends the welcome email (`/email/welcome.html`, written by `newsletter.py` at build time).
- Monday letter: written each week in `content/newsletter/<monday>.json`: `headline`, `subject`, `intro` (a short editorial on last week's luxury hospitality news, every fact with a dated source as `[Source, date](url)`), `expected` (what is coming, with sources), `picks` (3 or 4 article ids from last week, linked) and `coming_up` (our next posts, optional). `python3 newsletter.py weekly [monday]` writes `emails/week-<monday>.html`. Every Sunday at 17:00 UTC the workflow `newsletter.yml` runs `newsletter.py schedule`: if the file says `"status": "ready"` (Natan's validation), the campaign is scheduled in Brevo for Monday 07:00 UTC (08:00 in Paris in winter) and a test goes to Natan; otherwise it stays a Brevo draft. Without the file, the letter falls back to last week's articles, as a draft.
- The same workflow rebuilds the site every morning (Netlify build hook) so each dated article goes online on its day.
