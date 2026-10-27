# Coltasa Insights: editorial playbook

This folder is how new posts get written and published to coltasa.com/insights.
A scheduled Claude task follows it once a week. Anyone (or any Claude session) can follow it by hand.

Files:
- `topics.md`: the topic backlog. Take the first unchecked topic, tick it when published.
- `publish.py`: adds a post to the site (post page, blog list in every file, sitemap, llms.txt, structured data).
- `prerender.py`: renders the home page, Insights list and every post into static HTML for crawlers. Run after any page change.
- `check.py`: renders every page in headless Chromium and fails on anything broken.
- `drafts/<post-id>.json`: the source for each post. Keep them; they are the record of what was published.
- `faq/<post-id>.json`: FAQ entries per post, used for FAQ structured data.

## Weekly procedure

1. `git pull` on `main`.
2. Open `topics.md`. Take the first unchecked topic. Skip it (and note why on the line) only if it now overlaps an existing post in `deploy/insights.html` POSTS.
3. Research for 10 minutes with web search: what people search for on this topic, what the top results and AI answers say, and what they miss. Use this to pick the search query the post targets and the angle that adds something.
4. Write the post as `editorial/drafts/<post-id>.json` (format in `publish.py`). Follow the voice, structure and checklist below.
5. `python3 editorial/publish.py add editorial/drafts/<post-id>.json`
6. Link the new post from one or two older related posts: in each, wrap an existing phrase (or extend one sentence minimally) with `<a href="/insights/<new-id>">`. Edit only inside that post's article body.
7. `PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers python3 editorial/prerender.py`, then `PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers python3 editorial/check.py` (setup steps are at the top of `check.py`). Fix anything that fails. The prerender writes a static copy of every page so AI crawlers, which do not run JavaScript, can read the post. Never skip it: a post without it is invisible to ChatGPT, Claude and Perplexity.
8. Tick the topic in `topics.md`, adding the post id and date.
9. Commit and push to `main`. Vercel deploys production automatically in about a minute.
10. Confirm the live URL returns the post (WebFetch `https://www.coltasa.com/insights/<post-id>` and check the headline is in the raw HTML).

## Voice

- Author is Colin Constantine, Principal at Coltasa: a decade-plus of enterprise sales at Salesforce, Sitecore, Algolia, Bloomberg and WordPress VIP. Write as an experienced practitioner advising founders and early sales leaders at B2B tech companies.
- Plain, direct, opinionated. Short sentences. Practical over theoretical. Take a clear position, then explain it.
- British spelling (prioritise, organisation, behaviour). Spell out "percent".
- Never use em dashes or en dashes. Use commas, colons, full stops or parentheses.
- No hype words (game-changer, unlock, supercharge, leverage as a verb, in today's fast-paced world), no emoji, no exclamation marks.
- Never invent statistics, studies, quotes, client stories or personal anecdotes about Colin. Use frameworks, worked examples with clearly illustrative numbers ("say your win rate is 25 percent"), and checklists. If you cite a real figure, it must come from a source you found and the post names the source.
- No mention of Automattic or any current employer or client.

## Structure

- 1,000 to 1,500 words. `mins` = words / 230, rounded, as "N min read".
- Opening paragraph answers the core question directly in two or three sentences. No warm-up.
- 4 to 7 `<h2>` sections. Phrase at least half as the questions a buyer of consulting would type or ask an AI ("How do you...", "When should you...", "What is...").
- Each section opens with its answer in the first sentence, then explains.
- At least one concrete list a reader can act on (steps, checklist, questions to ask).
- Link naturally to 2 or 3 existing posts with `<a href="/insights/<id>">`, on descriptive phrases (never "click here").
- Cite 2 to 4 credible external sources inline, where they support a specific claim: research firms (Gartner, Forrester, McKinsey), official documentation, original studies or data reports, and the recognised home of any framework you name (for example meddicc.com for MEDDPICC). Prefer the primary source over articles that summarise it. Avoid competitor consultancies and vendor listicles.
- Open every source page during the run and check the figure or claim is on it before citing. Never cite a URL you have not opened, and never cite from memory. If a source cannot be verified, drop the claim.
- External link format: `<a href="https://..." target="_blank" rel="noopener">descriptive text</a>`. A short quote from a source must be under 15 words and in quotation marks.
- Finish `body_html` with a `Sources and further reading` `<h2>` and a `<ul>` listing each external source once as `Publisher (year): Title`, linked the same way. The FAQ is added after it automatically.
- End with a short practical close (what to do this week). The site already adds the diagnostic and booking CTAs, so do not add your own.
- 3 to 4 FAQ entries in `faq`: real follow-up questions, 40 to 80 word answers that stand alone when quoted.

HTML in `body_html` uses exactly these patterns (copied from existing posts):
- Paragraph: `<p>...</p>`
- Heading: `<h2 style="margin:18px 0 0;font-size:30px;line-height:1.15;letter-spacing:-0.02em">...</h2>`
- List: `<ul style="padding-left:22px"><li>...</li></ul>` (or `<ol style="padding-left:22px">`)
- `<strong>` for a bold lead-in on a list item is fine. No other tags or inline styles. No images.

## SEO and GEO checklist

- `seo` title: the target query in natural words, under 60 characters, front-loaded keyword. It becomes the page `<title>`.
- `title`: the on-page headline, can be punchier than `seo`.
- `dek`: 140 to 160 characters, includes the target phrase, reads as a complete answer. It is the meta description and the standfirst.
- `id`: short, keyword-based slug, 2 to 5 words.
- Target query appears in the first paragraph and at least one `<h2>`.
- Definitions are stated plainly ("A mutual action plan is..."), because AI engines quote definitions.
- Specific, extractable answers: numbers, steps, named frameworks, clear recommendations.
- Categories rotate: do not publish two posts in a row in the same category. Categories are fixed: Strategy, Pipeline, Negotiation, Methodology, Forecasting, Outbound.
- `publish.py` handles canonical, Open Graph, Twitter cards, BlogPosting, BreadcrumbList and FAQPage structured data, the home page's static head, sitemap, RSS feed (`feed.xml`), `llms.txt` and `llms-full.txt`. Do not hand-edit those.
