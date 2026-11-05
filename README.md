# Precision Garage Door Pros — nationwide city sites

One static website per city/domain, all generated from a single template.

```
data/locations.json      source of truth: city, phone, address, domain (exported from the xlsx)
data/*.xlsx              original spreadsheet
template/base.html       shared header/footer/schema; template/pages/*.html = each page body; template/styles.css
scripts/build.py         generates sites/<domain>/ from template + data
sites/<domain>/          ready-to-host static site (index.html, robots.txt, sitemap.xml, _redirects)
```

Build everything: `python3 scripts/build.py`  
Build one city: `python3 scripts/build.py charlotte`

To change a phone number or address: edit `data/locations.json`, rebuild.  
To change the design or copy for all cities: edit `template/index.html`, rebuild.  
To make one city different: edit its `sites/<domain>/index.html` directly (it will be overwritten on the next full build unless you also change the template logic).

## Hosting (Cloudflare Pages)

One Pages project serves every site: `sites/_worker.js` looks at the request hostname and serves
`sites/<domain>/...`. Apex domains 301 to `www.`.

Pages settings: Framework = None · Build command = *(empty)* · Build output directory = `sites`.
Then add each domain under Custom domains (both `domain.com` and `www.domain.com`).
Free plan allows 100 custom domains per project, so the 109 domains are split across two projects
that deploy the same repo.

Deployed on Cloudflare Pages: project `garage-door-sites-nationwide-appel-maps`.

## Two Cloudflare Pages projects

Cloudflare Pages allows 100 custom domains per project, and one GitHub repo can only be
connected to one Pages project. So the same code lives in two GitHub repos:

- `Garage-Door-Sites-Nationwide-Appel-Maps` → Pages project `garage-door-sites-nationwide-appel-maps` (sites 1–50)
- `Garage-Door-Sites-Part-2` → Pages project `garage-door-sites-part-2` (sites 51+)

After any change, push to both remotes so both projects rebuild:

    git push origin main && git push part2 main
