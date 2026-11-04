#!/usr/bin/env python3
"""Build one static multi-page site per location.

  python3 scripts/build.py            # all locations
  python3 scripts/build.py charlotte  # only domains containing "charlotte"

Inputs:  template/base.html, template/pages/*.html, template/styles.css, data/locations.json
Output:  sites/<domain>/...
"""
import json, re, sys, datetime, shutil, html as htmlmod
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
T = ROOT / "template"
BASE = (T / "base.html").read_text()
STYLES = T / "styles.css"
LOCATIONS = json.loads((ROOT / "data" / "locations.json").read_text())
OUT = ROOT / "sites"
SINCE = "2004"

# slug -> (page template, nav key)
PAGES = {
    "": ("home", "home"),
    "garage-door-spring-repair": ("spring", "spring"),
    "garage-door-opener-repair": ("opener", "opener"),
    "garage-door-off-track-repair": ("offtrack", "offtrack"),
    "new-garage-door-installation": ("newdoor", "newdoor"),
    "emergency-garage-door-repair": ("emergency", "emergency"),
    "service-areas": ("areas", "areas"),
    "about": ("about", "about"),
    "contact": ("contact", "contact"),
    "thank-you": ("thankyou", "contact"),
}
FORM_KEY = (ROOT / "data" / "form_key.txt").read_text().strip() if (ROOT / "data" / "form_key.txt").exists() else "YOUR-WEB3FORMS-ACCESS-KEY"
NAV_KEYS = ["home", "spring", "opener", "offtrack", "newdoor", "emergency", "areas", "blog", "about", "contact"]

FAQ_SCHEMA = """<script type="application/ld+json">
{"@context":"https://schema.org","@type":"FAQPage","mainEntity":[
{"@type":"Question","name":"How fast can you get to me in {{city}}?","acceptedAnswer":{"@type":"Answer","text":"Most calls in {{city}} are handled the same day. Tell us what the door is doing when you call and we will give you an arrival window right away."}},
{"@type":"Question","name":"How much does garage door repair cost in {{city}}?","acceptedAnswer":{"@type":"Answer","text":"It depends on the part. Spring, cable and roller repairs are the most common and the most affordable. You get a firm price before any work starts, and the service call fee is applied to the repair."}},
{"@type":"Question","name":"Do you work on all garage door brands?","acceptedAnswer":{"@type":"Answer","text":"Yes. We service every major door and opener brand, including Clopay, Amarr, Wayne Dalton, LiftMaster, Chamberlain, Genie and Craftsman."}},
{"@type":"Question","name":"My door is stuck halfway. Is it safe to force it?","acceptedAnswer":{"@type":"Answer","text":"No. A door stuck part-way usually means a broken spring or cable, and the door can drop. Leave it where it is, keep people and cars clear, and call us."}},
{"@type":"Question","name":"Should I repair or replace my garage door?","acceptedAnswer":{"@type":"Answer","text":"If the panels are sound and it is a spring, cable or opener problem, repair is almost always the better value. If several panels are damaged or the door is 20+ years old and uninsulated, we will walk you through replacement options and prices on site."}},
{"@type":"Question","name":"What warranty do you give?","acceptedAnswer":{"@type":"Answer","text":"5 years on springs and parts we install, 1 year on labor. New doors carry the manufacturer's warranty on top of ours."}}
]}
</script>"""

LOGO = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 160" width="640" height="160" role="img" aria-label="{cityc} Garage Door Repair">
<style>@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@700&amp;family=Barlow:wght@500&amp;display=swap');</style>
<rect width="640" height="160" fill="#1B2733"/>
<g transform="translate(28,24) scale(1.75)"><path d="M32 3 62 24v37H2V24z" fill="#F2B705"/><path d="M32 3 62 24H2z" fill="#D9A300"/><rect x="11" y="27" width="42" height="34" fill="#1B2733"/><rect x="15" y="31" width="34" height="6" rx="1" fill="#F2B705"/><rect x="15" y="41" width="34" height="6" rx="1" fill="#F2B705"/><rect x="15" y="51" width="34" height="6" rx="1" fill="#F2B705"/></g>
<text x="156" y="78" font-family="'Barlow Condensed','Arial Narrow',sans-serif" font-weight="700" font-size="46" fill="#F2B705" letter-spacing="0.5">{city}</text>
<text x="156" y="116" font-family="'Barlow Condensed','Arial Narrow',sans-serif" font-weight="700" font-size="38" fill="#FFFFFF" letter-spacing="0.5">GARAGE DOOR REPAIR</text>
<text x="156" y="142" font-family="Barlow,sans-serif" font-weight="500" font-size="13" fill="#8A9AAA" letter-spacing="2.5">SINCE {since} · {cityc}, {st} · 24 HOURS</text>
</svg>
"""
BLOG_DIR = T / "blog"

def blog_posts():
    posts = []
    for fp in sorted(BLOG_DIR.glob("*.html")):
        src = fp.read_text()
        meta = dict(re.findall(r"<!-- (\w+): (.*?) -->", src))
        body = re.sub(r"<!-- \w+: .*? -->\n?", "", src)
        posts.append({"slug": fp.stem, "title": meta["title"], "desc": meta["desc"], "date": meta["date"], "body": body})
    posts.sort(key=lambda x: x["date"], reverse=True)
    return posts

POSTS = blog_posts()

POST_TPL = """<section class="hero sub" aria-labelledby="h1">
  <div class="wrap">
    <p class="crumb"><a href="/blog/">Blog</a></p>
    <h1 id="h1">{title}</h1>
    <p class="lede">{desc}</p>
    <p class="meta">{datefmt} · {business}</p>
  </div>
  <div class="door" aria-hidden="true"><i></i><i></i></div>
</section>
<section aria-label="Article">
  <div class="wrap two">
    <article class="prose">
{body}
    </article>
    <div>
      <div class="aside">
        <h3>Need it fixed today?</h3>
        <p>Same-day garage door repair across {city} and nearby. Phones answered 24 hours.</p>
        <a class="call" href="tel:+1{phone_digits}">Call {phone}</a>
      </div>
      <div class="aside" style="margin-top:1rem">
        <h3>More from the blog</h3>
        <ul>{others}</ul>
      </div>
    </div>
  </div>
</section>"""

ARTICLE_SCHEMA = """<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"BlogPosting","headline":"{title}","description":"{desc}","datePublished":"{date}","dateModified":"{date}","mainEntityOfPage":"https://www.{domain}/blog/{slug}/","author":{{"@type":"Organization","name":"{business}","url":"https://www.{domain}/"}},"publisher":{{"@type":"Organization","name":"{business}","url":"https://www.{domain}/"}}}}
</script>"""

BLOG_INDEX_TPL = """<section class="hero sub" aria-labelledby="h1">
  <div class="wrap">
    <h1 id="h1">Garage door advice from {city}</h1>
    <p class="lede">Plain answers to the questions {city} homeowners ask us most — what breaks, why, what it costs and what you can check yourself.</p>
  </div>
  <div class="door" aria-hidden="true"><i></i><i></i></div>
</section>
<section aria-label="Articles">
  <div class="wrap">
    <div class="grid">
{cards}
    </div>
  </div>
</section>"""


def datefmt(d):
    return datetime.date.fromisoformat(d).strftime("%B %-d, %Y")


def render_blog(f):
    out = []  # (path, html)
    cards = []
    for p in POSTS:
        pf = dict(f)
        others = "".join(f'<li><a href="/blog/{o["slug"]}/">{htmlmod.escape(sub(o["title"], f))}</a></li>' for o in POSTS if o is not p)
        content = POST_TPL.format(title=htmlmod.escape(sub(p["title"], f)), desc=htmlmod.escape(sub(p["desc"], f)), datefmt=datefmt(p["date"]),
                                  business=f["business"], body=sub(p["body"], f), city=f["city"], phone=f["phone"], phone_digits=f["phone_digits"], others=others)
        pf.update({
            "page_title": htmlmod.escape(sub(p["title"], f) + " | " + f["business"], quote=True),
            "page_desc": htmlmod.escape(sub(p["desc"], f), quote=True),
            "path": f"/blog/{p['slug']}/",
            "content": content,
            "schema_extra": ARTICLE_SCHEMA.format(title=htmlmod.escape(sub(p["title"], f), quote=True), desc=htmlmod.escape(sub(p["desc"], f), quote=True),
                                                  date=p["date"], domain=f["domain"], slug=p["slug"], business=f["business"]),
        })
        for k in NAV_KEYS:
            pf[f"cur_{k}"] = 'aria-current="page"' if k == "blog" else ""
        out.append((f"/blog/{p['slug']}/", sub(BASE, pf)))
        cards.append(f'      <div class="svc"><h3><a href="/blog/{p["slug"]}/">{htmlmod.escape(sub(p["title"], f))}</a></h3><p>{htmlmod.escape(sub(p["desc"], f))}</p><a class="more" href="/blog/{p["slug"]}/">Read the article</a></div>')
    pf = dict(f)
    pf.update({
        "page_title": htmlmod.escape(f"Garage Door Blog | {f['business']}", quote=True),
        "page_desc": htmlmod.escape(f"Garage door repair advice for {f['city']} homeowners: springs, openers, noises, maintenance and when to replace.", quote=True),
        "path": "/blog/",
        "content": BLOG_INDEX_TPL.format(city=f["city"], cards="\n".join(cards)),
        "schema_extra": "",
    })
    for k in NAV_KEYS:
        pf[f"cur_{k}"] = 'aria-current="page"' if k == "blog" else ""
    out.append(("/blog/", sub(BASE, pf)))
    return out


ROBOTS = "User-agent: *\nAllow: /\nSitemap: https://www.{domain}/sitemap.xml\n"
REDIRECTS = "https://{domain}/* https://www.{domain}/:splat 301!\n"


def wiki_url(loc):
    if loc.get("wiki"):
        return loc["wiki"]
    city, state = loc["city"].strip(), loc["state"].strip()
    if city == "Washington DC":
        return "https://en.wikipedia.org/wiki/Washington,_D.C."
    return f"https://en.wikipedia.org/wiki/{city.title().replace(' ', '_')},_{state.replace(' ', '_')}"


def fields(loc):
    addr = loc["address"].strip()
    m = re.search(r",\s*([A-Z]{2})\s+\d{5}\s*$", addr)
    st = m.group(1) if m else ""
    street = addr.rsplit(",", 2)[0].strip()
    phone = loc["phone"]
    nearby = loc.get("nearby") or []
    city = loc["city"].strip().title().replace("Dc", "DC")
    f = {
        "domain": loc["domain"],
        "business": loc["business"],
        "city": city,
        "state": loc["state"].strip(),
        "st": st,
        "zip": loc["zip"],
        "street": street,
        "phone": phone,
        "phone_digits": re.sub(r"\D", "", phone),
        "since": SINCE,
        "form_key": FORM_KEY,
        "wiki": wiki_url(loc),
        "year": str(datetime.date.today().year),
        "nearby_inline": ", ".join(nearby[:-1]) + (" and " + nearby[-1] if len(nearby) > 1 else (nearby[0] if nearby else "the surrounding area")),
        "nearby_short": ", ".join(nearby[:4]) if nearby else "the surrounding area",
        "nearby_list": "\n      ".join(f"<li>{htmlmod.escape(n)}</li>" for n in nearby) or "<li>Surrounding communities</li>",
        "styles": STYLES.read_text().strip(),
        "areas_schema": "".join(f',{{"@type":"City","name":"{htmlmod.escape(n)}"}}' for n in nearby),
    }
    return f


def sub(text, f):
    for k, v in f.items():
        text = text.replace("{{" + k + "}}", v)
    return text


def render_page(slug, f):
    tpl_name, nav_key = PAGES[slug]
    src = (T / "pages" / f"{tpl_name}.html").read_text()
    title = re.search(r"<!-- title: (.*?) -->", src).group(1)
    desc = re.search(r"<!-- desc: (.*?) -->", src).group(1)
    body = re.sub(r"<!-- (title|desc): .*? -->\n?", "", src)
    path = "/" if slug == "" else f"/{slug}/"
    pf = dict(f)
    pf.update({
        "page_title": htmlmod.escape(sub(title, f), quote=True),
        "page_desc": htmlmod.escape(sub(desc, f), quote=True),
        "path": path,
        "content": sub(body, f),
        "schema_extra": (sub(FAQ_SCHEMA, f) if slug == "" else "") + ('<meta name="robots" content="noindex">' if slug == "thank-you" else ""),
    })
    for k in NAV_KEYS:
        pf[f"cur_{k}"] = 'aria-current="page"' if k == nav_key else ""
    out = sub(BASE, pf)
    leftover = re.findall(r"{{\w+}}", out)
    if leftover:
        raise SystemExit(f"{f['domain']}{path}: unreplaced {sorted(set(leftover))}")
    return path, out


def build_site(loc, today):
    f = fields(loc)
    d = OUT / f["domain"]
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    urls = []
    f["blog_teasers"] = "\n".join(
        f'      <div class="svc"><h3><a href="/blog/{p["slug"]}/">{htmlmod.escape(sub(p["title"], f))}</a></h3><p>{htmlmod.escape(sub(p["desc"], f))}</p><a class="more" href="/blog/{p["slug"]}/">Read the article</a></div>'
        for p in POSTS[:3])
    for path, out in render_blog(f):
        target = d / path.strip("/") / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(out)
        urls.append(path)
    for slug in PAGES:
        path, out = render_page(slug, f)
        target = d / slug / "index.html" if slug else d / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(out)
        if slug != "thank-you":
            urls.append(path)
    (d / "robots.txt").write_text(ROBOTS.format(domain=f["domain"]))
    (d / "logo.svg").write_text(LOGO.format(city=htmlmod.escape(f["city"].upper()), since=f["since"], st=f["st"], cityc=htmlmod.escape(f["city"])))
    (d / "_redirects").write_text(REDIRECTS.format(domain=f["domain"]))
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        sm.append(f"  <url><loc>https://www.{f['domain']}{u}</loc><lastmod>{today}</lastmod></url>")
    sm.append("</urlset>")
    (d / "sitemap.xml").write_text("\n".join(sm) + "\n")
    return len(urls)


def main():
    flt = sys.argv[1].lower() if len(sys.argv) > 1 else ""
    today = datetime.date.today().isoformat()
    n = pages = 0
    for loc in LOCATIONS:
        if flt and flt not in loc["domain"]:
            continue
        pages += build_site(loc, today)
        n += 1
    print(f"built {n} site(s), {pages} pages, into {OUT}")


if __name__ == "__main__":
    main()
