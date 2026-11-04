#!/usr/bin/env python3
"""Build one static site per location from template/index.html + data/locations.json.

Usage:
  python3 scripts/build.py            # build all
  python3 scripts/build.py charlotte  # build only domains containing "charlotte"
"""
import json, re, sys, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = (ROOT / "template" / "index.html").read_text()
LOCATIONS = json.loads((ROOT / "data" / "locations.json").read_text())
OUT = ROOT / "sites"

ROBOTS = "User-agent: *\nAllow: /\nSitemap: https://www.{domain}/sitemap.xml\n"
SITEMAP = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
           '  <url><loc>https://www.{domain}/</loc><lastmod>{date}</lastmod></url>\n'
           '</urlset>\n')
# Cloudflare Pages / Netlify style redirect: apex -> www
REDIRECTS = "https://{domain}/* https://www.{domain}/:splat 301!\n"


def fields(loc):
    addr = loc["address"].strip()
    m = re.search(r",\s*([A-Z]{2})\s+\d{5}\s*$", addr)
    st = m.group(1) if m else ""
    street = addr.rsplit(",", 2)[0].strip()  # drop ", City, ST ZIP"
    phone = loc["phone"]
    return {
        "domain": loc["domain"],
        "business": loc["business"],
        "city": loc["city"],
        "state": loc["state"],
        "st": st,
        "zip": loc["zip"],
        "street": street,
        "phone": phone,
        "phone_digits": re.sub(r"\D", "", phone),
        "hours_label": "24 hours a day",
        "year": str(datetime.date.today().year),
    }


def render(loc):
    f = fields(loc)
    html = TEMPLATE
    for k, v in f.items():
        html = html.replace("{{" + k + "}}", v)
    leftover = re.findall(r"{{\w+}}", html)
    if leftover:
        raise SystemExit(f"{loc['domain']}: unreplaced placeholders {leftover}")
    return f, html


def main():
    flt = sys.argv[1].lower() if len(sys.argv) > 1 else ""
    today = datetime.date.today().isoformat()
    n = 0
    for loc in LOCATIONS:
        if flt and flt not in loc["domain"]:
            continue
        f, html = render(loc)
        d = OUT / f["domain"]
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(html)
        (d / "robots.txt").write_text(ROBOTS.format(domain=f["domain"]))
        (d / "sitemap.xml").write_text(SITEMAP.format(domain=f["domain"], date=today))
        (d / "_redirects").write_text(REDIRECTS.format(domain=f["domain"]))
        n += 1
    print(f"built {n} site(s) into {OUT}")


if __name__ == "__main__":
    main()
