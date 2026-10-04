# coltasa.com

Static site. No build step.

- index.html — landing page (coltasa.com)
- insights.html — blog (coltasa.com/insights)
- sitemap.xml, robots.txt — for Google
- vercel.json — clean URLs (/insights instead of /insights.html)

## Deploy
1. Push this folder to a GitHub repo.
2. In Vercel: Add New Project, import the repo, Framework preset "Other", no build command, output directory "./".
3. Vercel, Project, Settings, Domains: add coltasa.com and www.coltasa.com, then add the DNS records Vercel shows at your domain registrar.

## Pages
- insights.html: blog list (coltasa.com/insights)
- insights/<post-id>.html: one page per post (coltasa.com/insights/<post-id>)

## Adding a blog post
Easiest: ask Claude in the design project to add it and re-export the site files.
By hand:
1. Copy any file in insights/ and rename it to the new post id.
2. Replace the article text block, and update the title, description, canonical and og tags in the head.
3. Add the post's entry to the POSTS list in insights.html and in every file in insights/.
4. Add its URL to sitemap.xml.
