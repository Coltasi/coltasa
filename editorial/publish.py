#!/usr/bin/env python3
"""Coltasa Insights publishing tool. No dependencies.

Usage (run from the repo root):
  python3 editorial/publish.py add editorial/drafts/<post-id>.json   # add a new post
  python3 editorial/publish.py refresh                               # rebuild static SEO for all posts

A draft JSON looks like:
{
  "id": "url-slug",                     # lowercase, hyphens, becomes /insights/<id>
  "cat": "Strategy",                    # one of CATS in deploy/insights.html
  "title": "On-page headline",
  "seo": "Search-style title, under 60 chars",
  "dek": "Meta description and standfirst, 140-160 chars",
  "mins": "6 min read",
  "date": "27 October 2026",            # D Month YYYY
  "body_html": "<p>...</p><h2 ...>...</h2>...",   # article body, no FAQ
  "faq": [{"q": "Question?", "a": "Plain-text answer."}]
}
"""
import html, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEPLOY = os.path.join(ROOT, "deploy")
INDEX = os.path.join(DEPLOY, "insights.html")
POSTS_DIR = os.path.join(DEPLOY, "insights")
FAQ_DIR = os.path.join(ROOT, "editorial", "faq")
SITE = "https://www.coltasa.com"
MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]
H2 = '<h2 style="margin:18px 0 0;font-size:30px;line-height:1.15;letter-spacing:-0.02em">'
H3 = '<h3 style="margin:10px 0 0;font-size:22px;line-height:1.25">'
START, END = "<!-- static-seo:start -->", "<!-- static-seo:end -->"


def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def write(p, s):
    with open(p, "w", encoding="utf-8") as f:
        f.write(s)


def iso(d):
    day, month, year = d.split(" ")
    return f"{year}-{MONTHS.index(month) + 1:02d}-{int(day):02d}"


def js(s):
    return s.replace("\\", "\\\\").replace("'", "\\'")


def parse_posts(src):
    block = re.search(r"POSTS = \[(.*?)\n  \];", src, re.S).group(1) + "\n"
    posts = []
    for entry in re.findall(r"\{(.*?)\},?\n", block, re.S):
        fields = dict((k, v.replace("\\'", "'").replace("\\\\", "\\"))
                      for k, v in re.findall(r"(\w+): '((?:\\.|[^'\\])*)'", entry))
        if "id" in fields:
            posts.append(fields)
    return posts


def entry_js(p):
    return (f"    {{ id: '{js(p['id'])}', key: '{p['key']}', cat: '{js(p['cat'])}', "
            f"date: '{js(p['date'])}', mins: '{js(p['mins'])}',\n"
            f"      title: '{js(p['title'])}',\n"
            f"      seo: '{js(p['seo'])}',\n"
            f"      dek: '{js(p['dek'])}' }},\n")


def faq_for(pid):
    p = os.path.join(FAQ_DIR, pid + ".json")
    return json.loads(read(p)) if os.path.exists(p) else []


def post_ld(p, faq):
    url = f"{SITE}/insights/{p['id']}"
    graph = [{
        "@type": "BlogPosting", "headline": p["title"], "description": p["dek"],
        "datePublished": iso(p["date"]), "dateModified": iso(p.get("modified", p["date"])),
        "url": url, "mainEntityOfPage": url, "articleSection": p["cat"],
        "image": f"{SITE}/assets/og-image.png", "inLanguage": "en",
        "author": {"@type": "Person", "@id": f"{SITE}/#colin", "name": "Colin Constantine",
                   "jobTitle": "Principal", "url": f"{SITE}/",
                   "sameAs": ["https://www.linkedin.com/in/colvcon"]},
        "publisher": {"@type": "Organization", "@id": f"{SITE}/#org", "name": "Coltasa",
                      "url": f"{SITE}/", "logo": {"@type": "ImageObject", "url": f"{SITE}/favicon.svg"}},
    }, {
        "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{SITE}/"},
            {"@type": "ListItem", "position": 2, "name": "Insights", "item": f"{SITE}/insights"},
            {"@type": "ListItem", "position": 3, "name": p["title"], "item": url}]}]
    if faq:
        graph.append({"@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": f["q"],
             "acceptedAnswer": {"@type": "Answer", "text": f["a"]}} for f in faq]})
    return json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False)


def head_block(title, desc, url, ld, kind, post=None):
    e = html.escape
    article = ""
    if post:
        article = (f'<meta property="article:published_time" content="{iso(post["date"])}">\n'
                   f'<meta property="article:modified_time" content="{iso(post.get("modified", post["date"]))}">\n'
                   f'<meta property="article:author" content="https://www.linkedin.com/in/colvcon">\n'
                   f'<meta property="article:section" content="{e(post["cat"])}">\n')
    return (f"{START}\n<title>{e(title)}</title>\n"
            f'<meta name="description" content="{e(desc)}">\n'
            f'<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1">\n'
            f'<link rel="canonical" href="{url}">\n'
            f'<link rel="alternate" type="application/rss+xml" title="Coltasa Insights" href="{SITE}/feed.xml">\n'
            f'<meta property="og:type" content="{kind}">\n'
            f'<meta property="og:site_name" content="Coltasa">\n'
            f'<meta property="og:locale" content="en_GB">\n'
            f'<meta property="og:title" content="{e(title)}">\n'
            f'<meta property="og:description" content="{e(desc)}">\n'
            f'<meta property="og:url" content="{url}">\n'
            f'<meta property="og:image" content="{SITE}/assets/og-image.png">\n'
            f'<meta property="og:image:width" content="1200">\n'
            f'<meta property="og:image:height" content="630">\n'
            f'<meta property="og:image:alt" content="Coltasa: B2B sales strategy and execution">\n'
            f'{article}'
            f'<meta name="twitter:card" content="summary_large_image">\n'
            f'<meta name="twitter:title" content="{e(title)}">\n'
            f'<meta name="twitter:description" content="{e(desc)}">\n'
            f'<meta name="twitter:image" content="{SITE}/assets/og-image.png">\n'
            f'<meta name="author" content="Colin Constantine">\n'
            f'<script type="application/ld+json" id="static-ld">{ld}</script>\n{END}\n')


HOME_TITLE = "B2B Sales Strategy & Execution for Tech Startups | Coltasa"
HOME_DESC = ("Coltasa helps Seed to Series B tech companies build repeatable B2B sales: playbooks, pipeline, "
             "outbound, negotiation, forecasting and sales hiring. Led by Colin Constantine.")
SERVICES = [  # mirrors SVC in deploy/index.html
    ("Sales strategy & GTM plan", "Your ICP, segments, sales motions and targets, tied to the plan for your next round."),
    ("Pricing & packaging", "Pricing that holds up in enterprise negotiations and grows with the customer."),
    ("Sales methodology", "MEDDPICC, Command of the Message, Sandler, Challenger, SPIN or Gap Selling, fitted to how your buyers buy and used by the whole team."),
    ("Pipeline & forecasting", "Stage definitions, CRM discipline and a forecast your board can rely on."),
    ("Outbound campaigns", "Target account lists, messaging and multi-channel sequences that book meetings with the right buyers."),
    ("First sales hires", "Role design, scorecards, interview loops and onboarding for your first AEs and sales leader."),
    ("Founder-led sales coaching", "Working alongside founders on discovery, demos and executive conversations while they are still the closer."),
    ("Enterprise deal support", "Hands-on help with live deals: stakeholder mapping, running evaluations and getting through procurement."),
    ("Negotiation", "Preparing for and running commercial negotiations with executives and procurement, without giving away margin."),
    ("Fractional VP Sales", "Part-time sales leadership until you are ready to hire a full-time head of sales."),
]


def home_ld():
    return json.dumps({"@context": "https://schema.org", "@graph": [
        {"@type": "WebSite", "@id": f"{SITE}/#website", "name": "Coltasa", "url": f"{SITE}/",
         "publisher": {"@id": f"{SITE}/#org"}, "inLanguage": "en"},
        {"@type": "ProfessionalService", "@id": f"{SITE}/#org", "name": "Coltasa", "url": f"{SITE}/",
         "email": "hello@coltasa.com", "logo": f"{SITE}/favicon.svg", "image": f"{SITE}/assets/og-image.png",
         "description": "B2B sales strategy and execution for Seed to Series B tech companies: sales playbooks, "
                        "pipeline, outbound, negotiation, forecasting and sales hiring.",
         "slogan": "Sell with experience on your side.",
         "address": {"@type": "PostalAddress", "addressLocality": "Barcelona", "addressCountry": "ES"},
         "areaServed": ["United States", "United Kingdom", "Europe", "Australia", "Asia"],
         "founder": {"@id": f"{SITE}/#colin"},
         "knowsAbout": ["B2B sales strategy", "Enterprise SaaS sales", "MEDDPICC", "Sandler", "Challenger",
                        "SPIN Selling", "Command of the Message", "Gap Selling", "Mutual action plans",
                        "Sales negotiation", "Outbound prospecting", "Sales forecasting", "Founder-led sales",
                        "Fractional VP Sales"],
         "hasOfferCatalog": {"@type": "OfferCatalog", "name": "B2B sales consulting services",
                             "itemListElement": [{"@type": "Offer", "itemOffered": {
                                 "@type": "Service", "name": n, "description": d, "provider": {"@id": f"{SITE}/#org"}}}
                                 for n, d in SERVICES]}},
        {"@type": "Person", "@id": f"{SITE}/#colin", "name": "Colin Constantine", "jobTitle": "Principal",
         "url": f"{SITE}/", "image": f"{SITE}/assets/colin.jpg", "sameAs": ["https://www.linkedin.com/in/colvcon"],
         "worksFor": {"@id": f"{SITE}/#org"},
         "description": "Enterprise B2B sales leader with more than a decade of experience at Salesforce, Sitecore, "
                        "Algolia, Bloomberg and WordPress VIP.",
         "knowsAbout": ["Enterprise sales", "B2B SaaS sales", "Sales methodology", "Sales negotiation",
                        "Sales forecasting", "Building sales teams"]},
        {"@type": "WebPage", "@id": f"{SITE}/#webpage", "url": f"{SITE}/", "name": HOME_TITLE,
         "description": HOME_DESC, "isPartOf": {"@id": f"{SITE}/#website"}, "about": {"@id": f"{SITE}/#org"},
         "primaryImageOfPage": f"{SITE}/assets/og-image.png", "inLanguage": "en"},
    ]}, ensure_ascii=False)


def article_text(path, key):
    """Plain text of one post's article body, for llms-full.txt."""
    src = read(path)
    m = re.search(r'<sc-if value="\{\{ %s \}\}"[^>]*>(.*?)\n  </sc-if>' % key, src, re.S)
    if not m:
        return ""
    s = m.group(1)
    s = re.sub(r"<h2[^>]*>(.*?)</h2>", r"\n\n## \1\n\n", s, flags=re.S)
    s = re.sub(r"<h3[^>]*>(.*?)</h3>", r"\n\n### \1\n\n", s, flags=re.S)
    s = re.sub(r'<a href="([^"]+)"[^>]*>(.*?)</a>',
               lambda a: f"[{a.group(2)}]({a.group(1) if a.group(1).startswith('http') else SITE + a.group(1)})", s, flags=re.S)
    s = re.sub(r"<li[^>]*>", "\n- ", s)
    s = re.sub(r"</p>", "\n\n", s)
    s = re.sub(r"<[^>]+>", "", s)
    s = html.unescape(s)
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n[ \t]+", "\n", s)
    return re.sub(r"\n{3,}", "\n\n", s).strip()


def rfc822(d):
    from email.utils import format_datetime
    from datetime import datetime, timezone
    y, m, dd = map(int, iso(d).split("-"))
    return format_datetime(datetime(y, m, dd, 9, 0, tzinfo=timezone.utc))


def set_head(src, block):
    if START in src:
        return re.sub(re.escape(START) + ".*?" + re.escape(END) + "\n", lambda m: block, src, flags=re.S)
    return re.sub(r'(<script src="[./]*support\.js"></script>)', lambda m: block + m.group(1), src, count=1)


def staticize_post(p):
    path = os.path.join(POSTS_DIR, p["id"] + ".html")
    src = read(path)
    for f in ("cat", "title", "dek", "date", "mins"):
        src = src.replace("{{ post.%s }}" % f, html.escape(p[f], quote=False))
    title = (p.get("seo") or p["title"]) + " | Coltasa"
    src = set_head(src, head_block(title, p["dek"], f"{SITE}/insights/{p['id']}", post_ld(p, faq_for(p["id"])), "article", p))
    write(path, src)


def refresh(posts):
    for p in posts:
        staticize_post(p)
    # Index: static head + no-JS post list for crawlers
    src = read(INDEX)
    ld = json.dumps({"@context": "https://schema.org", "@type": "Blog", "name": "Coltasa Insights",
                     "url": f"{SITE}/insights",
                     "author": {"@type": "Person", "@id": f"{SITE}/#colin", "name": "Colin Constantine"},
                     "blogPost": [{"@type": "BlogPosting", "headline": p["title"],
                                   "datePublished": iso(p["date"]),
                                   "url": f"{SITE}/insights/{p['id']}"} for p in posts]}, ensure_ascii=False)
    src = set_head(src, head_block("Insights | Coltasa",
                                   "Practical writing on B2B sales strategy, pipeline, outbound, negotiation and forecasting from Colin Constantine, Principal at Coltasa.",
                                   f"{SITE}/insights", ld, "website"))
    # The crawler-readable list now comes from editorial/prerender.py
    src = re.sub(r'<noscript id="static-list">.*?</noscript>\n', "", src, flags=re.S)
    write(INDEX, src)
    # Home page: static head for crawlers and link previews
    home = os.path.join(DEPLOY, "index.html")
    write(home, set_head(read(home), head_block(HOME_TITLE, HOME_DESC, f"{SITE}/", home_ld(), "website")))
    # Sitemap
    urls = [(f"{SITE}/", "2026-10-27"), (f"{SITE}/sales-engine-score", "2026-10-27"), (f"{SITE}/privacy", "2026-10-26"),
            (f"{SITE}/insights", iso(posts[0]["date"]))]
    urls += [(f"{SITE}/insights/{p['id']}", iso(p.get("modified", p["date"]))) for p in posts]
    write(os.path.join(DEPLOY, "sitemap.xml"),
          '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
          + "".join(f"  <url><loc>{u}</loc><lastmod>{d}</lastmod></url>\n" for u, d in urls) + "</urlset>\n")
    # RSS feed
    e = html.escape
    items = "".join(
        f"  <item>\n    <title>{e(p['title'])}</title>\n    <link>{SITE}/insights/{p['id']}</link>\n"
        f"    <guid isPermaLink=\"true\">{SITE}/insights/{p['id']}</guid>\n    <pubDate>{rfc822(p['date'])}</pubDate>\n"
        f"    <category>{e(p['cat'])}</category>\n    <dc:creator>Colin Constantine</dc:creator>\n"
        f"    <description>{e(p['dek'])}</description>\n  </item>\n" for p in posts)
    write(os.path.join(DEPLOY, "feed.xml"),
          '<?xml version="1.0" encoding="UTF-8"?>\n'
          '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:dc="http://purl.org/dc/elements/1.1/">\n<channel>\n'
          f"  <title>Coltasa Insights</title>\n  <link>{SITE}/insights</link>\n"
          f'  <atom:link href="{SITE}/feed.xml" rel="self" type="application/rss+xml"/>\n'
          "  <description>Practical writing on B2B sales strategy, pipeline, outbound, negotiation and forecasting from Colin Constantine.</description>\n"
          f"  <language>en</language>\n  <lastBuildDate>{rfc822(posts[0]['date'])}</lastBuildDate>\n"
          + items + "</channel>\n</rss>\n")
    # llms.txt for AI answer engines
    lines = ["# Coltasa", "",
             "> Coltasa is the B2B sales strategy and execution consultancy of Colin Constantine. "
             "It helps B2B tech companies build repeatable enterprise sales: playbooks, pipeline, "
             "outbound, negotiation and forecasting.", "",
             f"- [Home]({SITE}/): services, background and how to work with Colin",
             f"- [Sales Engine Score]({SITE}/sales-engine-score): a 5-minute assessment that scores a B2B sales engine out of 100 across pipeline, process, people, tools and metrics",
             f"- [Insights]({SITE}/insights): all articles", "", "## Insights", ""]
    lines += [f"- [{p['title']}]({SITE}/insights/{p['id']}): {p['dek']}" for p in posts]
    lines += ["", "## Optional", "",
              f"- [Full text of every article]({SITE}/llms-full.txt): all Insights posts in plain Markdown",
              f"- [RSS feed]({SITE}/feed.xml)"]
    write(os.path.join(DEPLOY, "llms.txt"), "\n".join(lines) + "\n")
    # llms-full.txt: every post's full text, so answer engines can read and quote it without running JavaScript
    full = ["# Coltasa Insights: full text", "",
            "> Articles by Colin Constantine, Principal at Coltasa, on B2B sales strategy and execution "
            "for Seed to Series B tech companies.", "",
            "## About Coltasa", "", HOME_DESC, "",
            "Services: " + ", ".join(n for n, _ in SERVICES) + ".", "",
            f"Website: {SITE}/ · Sales Engine Score: {SITE}/sales-engine-score · Contact: hello@coltasa.com", ""]
    for p in posts:
        body = article_text(os.path.join(POSTS_DIR, p["id"] + ".html"), p["key"])
        full += ["---", "", f"# {p['title']}", "",
                 f"URL: {SITE}/insights/{p['id']}  ", f"Author: Colin Constantine  ",
                 f"Published: {iso(p['date'])}  ", f"Category: {p['cat']}", "",
                 f"> {p['dek']}", "", body, ""]
    write(os.path.join(DEPLOY, "llms-full.txt"), "\n".join(full) + "\n")


def add(spec_path):
    d = json.loads(read(spec_path))
    for k in ("id", "cat", "title", "seo", "dek", "mins", "date", "body_html"):
        assert d.get(k), f"missing {k}"
    assert re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", d["id"]), "id must be a lowercase slug"
    iso(d["date"])
    src = read(INDEX)
    cats = re.search(r"CATS = \[(.*?)\];", src).group(1)
    assert f"'{d['cat']}'" in cats, f"category must be one of {cats}"
    posts = parse_posts(src)
    assert all(p["id"] != d["id"] for p in posts), "id already exists"
    key = "p%d" % (max(int(p["key"][1:]) for p in posts) + 1)
    d["key"] = key
    faq = d.get("faq") or []
    os.makedirs(FAQ_DIR, exist_ok=True)
    write(os.path.join(FAQ_DIR, d["id"] + ".json"), json.dumps(faq, indent=2, ensure_ascii=False) + "\n")

    # New post file from the pipeline-coverage template
    t = read(os.path.join(POSTS_DIR, "pipeline-coverage.html"))
    t = re.sub(re.escape(START) + ".*?" + re.escape(END) + "\n", "", t, flags=re.S)
    # Drop the template post's prerendered copy; prerender.py renders the new post afresh
    t = re.sub(r"<!--prerender-head:start-->.*?<!--prerender-head:end-->\n", "", t, flags=re.S)
    t = re.sub(r"\n<!--prerender:start-->.*?<!--prerender:end-->", "", t, flags=re.S)
    tpl = parse_posts(t)
    old = next(p for p in tpl if p["id"] == "pipeline-coverage")
    for f in ("cat", "title", "dek", "date", "mins"):  # undo staticize so we can refill
        t = t.replace(f">{html.escape(old[f], quote=False)}<", ">{{ post.%s }}<" % f, 1)
    t = re.sub(r"<helmet>\n<title>.*?</title>\n", "<helmet>\n<title>%s</title>\n" % html.escape(d["seo"] + " | Coltasa"), t, flags=re.S)
    e = lambda s: html.escape(s)
    url = f"{SITE}/insights/{d['id']}"
    t = re.sub(r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{e(d["dek"])}">', t, count=1)
    t = re.sub(r'<link rel="canonical" href="[^"]*">', f'<link rel="canonical" href="{url}">', t, count=1)
    t = re.sub(r'<meta property="og:title" content="[^"]*">', f'<meta property="og:title" content="{e(d["seo"] + " | Coltasa")}">', t, count=1)
    t = re.sub(r'<meta property="og:description" content="[^"]*">', f'<meta property="og:description" content="{e(d["dek"])}">', t, count=1)
    t = re.sub(r'<meta property="og:url" content="[^"]*">', f'<meta property="og:url" content="{url}">', t, count=1)
    body = d["body_html"].strip()
    if faq:
        body += "\n    " + H2 + "Frequently asked questions</h2>\n" + "\n".join(
            f"    {H3}{e(f['q'])}</h3>\n    <p>{e(f['a'])}</p>" for f in faq)
    block = (f'  <sc-if value="{{{{ {key} }}}}" hint-placeholder-val="{{{{ false }}}}">\n'
             f'    <div style="display:grid;gap:22px">\n    {body}\n    </div>\n  </sc-if>')
    t = re.sub(r'  <sc-if value="\{\{ p8 \}\}".*?\n  </sc-if>', lambda m: block, t, count=1, flags=re.S)
    t = t.replace("state = { view: 'pipeline-coverage'", f"state = {{ view: '{d['id']}'", 1)
    write(os.path.join(POSTS_DIR, d["id"] + ".html"), t)

    # Prepend the POSTS entry in the index and every post file
    for path in [INDEX, os.path.join(DEPLOY, "index.html")] + [os.path.join(POSTS_DIR, f) for f in os.listdir(POSTS_DIR) if f.endswith(".html")]:
        s = read(path)
        s = s.replace("  POSTS = [\n", "  POSTS = [\n" + entry_js(d), 1)
        write(path, s)
    refresh(parse_posts(read(INDEX)))
    print(f"Added /insights/{d['id']} as {key}")


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "refresh":
        refresh(parse_posts(read(INDEX)))
        print("Refreshed static SEO for all posts")
    elif len(sys.argv) == 3 and sys.argv[1] == "add":
        add(sys.argv[2])
    else:
        print(__doc__)
        sys.exit(1)
