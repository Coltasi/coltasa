# coltasa.com

Static marketing site and blog for Coltasa, a B2B sales consultancy led by Colin Constantine. Hosted on Vercel, which deploys automatically on every push to `main`. Vercel's root directory is `deploy/`.

## Files (all inside deploy/)
- `index.html`: landing page (coltasa.com)
- `insights.html`: blog list (coltasa.com/insights)
- `insights/<post-id>.html`: one page per post (coltasa.com/insights/<post-id>)
- `map.html`: world map embedded in the landing page (noindex)
- `sitemap.xml`, `robots.txt`, `vercel.json` (cleanUrls)
- `assets/`: logos, headshot, social preview image
- `support.js`, `_ds/`: runtime and design-system files. Do not edit.

## How pages are built
Each page is a Design Component: markup inside `<x-dc>` with `{{ holes }}`, `<sc-for>` and `<sc-if>`, and a logic class in `<script data-dc-script>`. Styles are inline. Keep this structure.

## Adding a blog post
1. Copy an existing file in `insights/` to `insights/<new-id>.html`.
2. In it: replace the article text inside its `<sc-if value="{{ pN }}">` block, set `state = { view: '<new-id>' }`, and update `<title>`, meta description, canonical and `og:*` tags.
3. Add the post to the `POSTS` list (id, key, cat, date, mins, title, dek) in `insights.html` and every file in `insights/`, so lists and "Keep reading" stay in sync.
4. Add `https://www.coltasa.com/insights/<new-id>` to `sitemap.xml` and update `lastmod`.
Categories: Strategy, Pipeline, Negotiation, Methodology, Forecasting, Outbound.

## Writing rules
- No em dashes and no semicolons anywhere in site copy.
- Voice: practical guidance from an experienced enterprise seller. Plain and specific. Not preachy, no hype, no AI clichés.
- Never invent client names, results or quotes.

## Brand
Colors: ground #f4f1ea, ink #2b3034, leather brown #a0602f (primary buttons), blue #1e8fc4 (hover state and accents). Headings Newsreader, body Hanken Grotesk. No rounded corners. Buttons are brown with white text and turn blue on hover.

## After any change
Test locally if needed (`npx serve deploy`), then commit with a short message and push to `main`.
