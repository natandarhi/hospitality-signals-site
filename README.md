# hospitality-signals.com

Static site for Hospitality Signals, built from The Signals Library.

- `content/articles/*.json`: one file per article, exported from the library (collection `articles`). Only `status` = `ready` or `published` goes live.
- `content/posts/*.json`: the week's LinkedIn posts (collection `posts`); when an article has one, its text becomes the article body.
- `content/images/<asset id>.jpg`: photos and visuals. A photo appears only when the article's `photo_credit` is confirmed (no "to be confirmed").
- `src/`: styles, script and favicon, taken from the validated design.
- `build.py`: writes the site to `public/`. Netlify runs it on every push (`netlify.toml`).

Build locally: `python3 build.py`, then open `public/index.html` through any static server.
