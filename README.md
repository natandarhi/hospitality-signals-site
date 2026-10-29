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
- Monday letter: `python3 newsletter.py weekly [monday]` writes `emails/week-<monday>.html`. The GitHub workflow `newsletter.yml` drafts it in Brevo every Sunday at 17:00 UTC and sends a test; subscribers get it only when Natan presses Send in Brevo. Articles already online on Monday get a link; the others show the day they go online.
- The same workflow rebuilds the site every morning (Netlify build hook) so each dated article goes online on its day.
