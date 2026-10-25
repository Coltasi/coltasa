#!/usr/bin/env python3
"""Render every Insights page in headless Chromium and check it looks right.

Setup once per machine (CDN is blocked in some sandboxes, npm is not):
  mkdir -p .cdn && cd .cdn && echo '{"name":"cdn","private":true}' > package.json &&
  npm i react@18.3.1 react-dom@18.3.1 @babel/standalone@7.29.0 && cd ..
Usage (repo root): PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers python3 editorial/check.py [post-id ...]
Checks: page renders, no leftover {{ }} placeholders, h1 present, article body present,
no JS errors, static JSON-LD parses. Exits non-zero on any failure.
"""
import functools, http.server, json, os, re, ssl, sys, threading, urllib.request
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEPLOY = os.path.join(ROOT, "deploy")


class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def translate_path(self, path):  # mimic Vercel cleanUrls
        p = super().translate_path(path.split("?")[0]).rstrip("/")
        if os.path.exists(p + ".html") and not os.path.isfile(p):
            return p + ".html"
        return p


def main():
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 8765), functools.partial(Handler, directory=DEPLOY))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    ids = sys.argv[1:] or [f[:-5] for f in sorted(os.listdir(os.path.join(DEPLOY, "insights"))) if f.endswith(".html")]
    paths = ["/insights"] + [f"/insights/{i}" for i in ids]
    bad = 0
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        cafile = "/root/.ccr/ca-bundle.crt"
        ctx = ssl.create_default_context(cafile=cafile) if os.path.exists(cafile) else ssl.create_default_context()
        cache = {}

        def external(route):  # fetch CDN files from Python so sandbox proxies work
            url = route.request.url
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
        for path in paths:
            pg = b.new_page()
            pg.route(re.compile(r"^https://(?!127\\.0\\.0\\.1)"), external)
            errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)))
            pg.goto("http://127.0.0.1:8765" + path, wait_until="networkidle")
            pg.wait_for_timeout(800)
            text = pg.inner_text("body")
            h1 = pg.locator("h1").first.inner_text() if pg.locator("h1").count() else ""
            raw = open(os.path.join(DEPLOY, path.strip("/") + ".html"), encoding="utf-8").read()
            problems = []
            if "{{" in text:
                problems.append("placeholder text visible")
            if not h1.strip():
                problems.append("no h1")
            if path != "/insights" and len(pg.locator("article").inner_text()) < 1500:
                problems.append("article body short or missing")
            m = re.search(r'id="static-ld">(.*?)</script>', raw, re.S)
            try:
                json.loads(m.group(1)) if m else problems.append("no static JSON-LD")
            except Exception:
                problems.append("static JSON-LD invalid")
            if path != "/insights" and "{{ post." in raw:
                problems.append("raw HTML still has post placeholders")
            problems += [f"js error: {e}" for e in errs]
            print(("FAIL " if problems else "ok   ") + path + "  | " + h1[:70] + ("  | " + "; ".join(problems) if problems else ""))
            bad += bool(problems)
            pg.close()
        b.close()
    srv.shutdown()
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
