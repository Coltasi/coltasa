#!/usr/bin/env python3
"""Prerender the Design Component pages into static HTML for crawlers and AI answer engines.

The home page, Insights list and posts are rendered in the browser by support.js (React).
Search engines that run JavaScript see the finished page, but AI crawlers (GPTBot, ClaudeBot,
PerplexityBot) and link-preview bots only read the raw HTML, where the content sits inside
an <x-dc> template full of {{ holes }}. This script renders each page in headless Chromium
and writes the result into the same file:

  <head>: <!--prerender-head:start--> ... <!--prerender-head:end-->
          hides the raw template and removes the static copy once the live page mounts
  <body>: <!--prerender:start--> <div id="dc-prerender"> rendered markup </div> <!--prerender:end-->
          right after </x-dc>

Title, meta tags and structured data are written separately by publish.py (static-seo block).
Re-running is safe: old blocks are stripped first. Fails if any {{ }} hole is left.

Setup is the same as check.py (local React in .cdn/, Playwright Chromium).
Usage (repo root): PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers python3 editorial/prerender.py
Run it after publish.py and after any change to index.html, insights.html or a post.
"""
import functools, http.server, os, re, ssl, sys, threading, urllib.request
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEPLOY = os.path.join(ROOT, "deploy")
HEAD_START, HEAD_END = "<!--prerender-head:start-->", "<!--prerender-head:end-->"
BODY_START, BODY_END = "<!--prerender:start-->", "<!--prerender:end-->"

# Removes the static copy once the live page has mounted, so visitors never see it twice.
CLEANUP = ("<script data-prerender-keep>(function(){function done(){var r=document.getElementById('dc-root');"
           "if(!r||!r.firstElementChild)return false;var n=document.querySelectorAll('[data-prerender]');"
           "for(var i=0;i<n.length;i++){n[i].parentNode&&n[i].parentNode.removeChild(n[i])}return true}"
           "new MutationObserver(function(m,o){if(done())o.disconnect()})"
           ".observe(document.documentElement,{childList:true,subtree:true})})();</script>")
HIDE_TEMPLATE = "<style data-prerender-keep>x-dc{display:none!important}</style>"


class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def translate_path(self, path):  # mimic Vercel cleanUrls
        p = super().translate_path(path.split("?")[0]).rstrip("/")
        if os.path.exists(p + ".html") and not os.path.isfile(p):
            return p + ".html"
        return p


def strip(src):
    for a, b in ((HEAD_START, HEAD_END), (BODY_START, BODY_END)):
        src = re.sub(r"\n?" + re.escape(a) + r".*?" + re.escape(b) + r"\n?", "\n" if a == BODY_START else "", src, flags=re.S)
    return src


def pages():
    out = ["index.html", "insights.html"]
    out += ["insights/" + f for f in sorted(os.listdir(os.path.join(DEPLOY, "insights"))) if f.endswith(".html")]
    return out


def url_for(rel):
    return "/" if rel == "index.html" else "/" + rel[:-5]


def main():
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 8766), functools.partial(Handler, directory=DEPLOY))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    sources = {}
    for rel in pages():
        path = os.path.join(DEPLOY, rel)
        sources[rel] = strip(open(path, encoding="utf-8").read())
        open(path, "w", encoding="utf-8").write(sources[rel])

    failed = 0
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        cafile = "/root/.ccr/ca-bundle.crt"
        ctx = ssl.create_default_context(cafile=cafile) if os.path.exists(cafile) else ssl.create_default_context()
        cache = {}

        def external(route):  # same CDN handling as check.py
            url = route.request.url
            if re.search(r"fonts\.(googleapis|gstatic)\.com|calendly\.com", url):
                return route.abort()  # no effect on markup
            m = re.match(r"https://unpkg\.com/(@?[^@]+)@[^/]+/(.*)", url)
            local = os.path.join(ROOT, ".cdn", "node_modules", m.group(1), m.group(2)) if m else ""
            if local and os.path.isfile(local):
                return route.fulfill(path=local, headers={"Content-Type": "application/javascript", "Access-Control-Allow-Origin": "*"})
            try:
                if url not in cache:
                    r = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), context=ctx, timeout=30)
                    cache[url] = (r.status, r.read(), r.headers.get("Content-Type", ""))
                st, body, ct = cache[url]
                route.fulfill(status=st, body=body, headers={"Content-Type": ct, "Access-Control-Allow-Origin": "*"})
            except Exception:
                route.abort()

        context = b.new_context(viewport={"width": 1280, "height": 900}, reduced_motion="reduce")
        for rel in pages():
            pg = context.new_page()
            pg.route(re.compile(r"^https://(?!127\.0\.0\.1)"), external)
            # The globe iframe (map.html) loads its own CDN data; it is not part of the static copy.
            pg.route(re.compile(r"/map(\.html)?$"), lambda r: r.fulfill(status=200, body="<!doctype html><title>map</title>", headers={"Content-Type": "text/html"}))
            errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)))
            try:
                pg.goto("http://127.0.0.1:8766" + url_for(rel), wait_until="load")
                pg.wait_for_function("""() => { const r = document.getElementById('dc-root');
                    return r && r.firstElementChild && !r.querySelector('.sc-placeholder,.sc-missing,.sc-unresolved,.sc-logic-error'); }""",
                                     timeout=20000)
                pg.wait_for_timeout(500)
                body = pg.evaluate("""() => {
                    const root = document.getElementById('dc-root').cloneNode(true);
                    root.querySelectorAll('[data-dc-tpl]').forEach(e => e.removeAttribute('data-dc-tpl'));
                    root.querySelectorAll('script,sc-helmet,helmet').forEach(e => e.remove());
                    return root.innerHTML; }""")
                if errs:
                    raise RuntimeError("page errors: " + " | ".join(errs))
                holes = re.findall(r"\{\{[^}]*\}\}", body)
                if holes:
                    raise RuntimeError(f"{len(holes)} unrendered holes, e.g. {holes[0]}")
                if body.count("<h1") != 1:
                    raise RuntimeError(f"expected one h1, found {body.count('<h1')}")
                html = sources[rel].replace("</head>", f"{HEAD_START}\n{HIDE_TEMPLATE}\n{CLEANUP}\n{HEAD_END}\n</head>", 1)
                k = html.rindex("</x-dc>") + len("</x-dc>")
                html = html[:k] + f"\n{BODY_START}\n<div id=\"dc-prerender\" data-prerender>{body}</div>\n{BODY_END}" + html[k:]
                open(os.path.join(DEPLOY, rel), "w", encoding="utf-8").write(html)
                print(f"ok   {rel} ({len(body) // 1024} KB)")
            except Exception as e:
                failed += 1
                print(f"FAIL {rel}: {e}")
            finally:
                pg.close()
        b.close()
    srv.shutdown()
    if failed:
        print(f"{failed} page(s) failed and were left without a prerendered copy.")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
