#!/usr/bin/env python3
"""Build one static multi-page site per location.

  python3 scripts/build.py            # all locations
  python3 scripts/build.py charlotte  # only domains containing "charlotte"

Inputs:  template/base.html, template/pages/*.html, template/styles.css, data/locations.json
Output:  sites/<domain>/...
"""
import json, re, sys, datetime, shutil, html as htmlmod
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
from suburbs import render_suburb, suburb_slug
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
T = ROOT / "template"
BASE = (T / "base.html").read_text()
STYLES = T / "styles.css"
LOCATIONS = json.loads((ROOT / "data" / "locations.json").read_text())
OUT = ROOT / "sites"
SINCE = "2004"

# (ink, signal, signal_ink, paper) — the rest is derived
PALETTES = [
    ("#1B2733", "#F2B705", "#1B2733", "#F3F5F7"),  # steel + signal yellow
    ("#14281D", "#B7D94A", "#14281D", "#F2F5EF"),  # forest + lime
    ("#3B1219", "#E8B04B", "#3B1219", "#F7F3F1"),  # burgundy + gold
    ("#202124", "#FF7A1A", "#1B1B1B", "#F4F4F4"),  # charcoal + safety orange
    ("#0F3A3F", "#5FD3C7", "#0F3A3F", "#EFF5F5"),  # deep teal + aqua
    ("#0D1F3C", "#FFD166", "#0D1F3C", "#F1F4F9"),  # midnight + warm gold
    ("#2B1D14", "#E39A4F", "#2B1D14", "#F6F2EC"),  # espresso + copper
    ("#26282B", "#E63946", "#FFFFFF", "#F5F5F5"),  # graphite + red
    ("#2E3A1F", "#E8D28A", "#2E3A1F", "#F5F4EE"),  # olive + sand
    ("#2A1E4A", "#FFB347", "#2A1E4A", "#F4F2F8"),  # royal purple + amber
    ("#123C5A", "#FF8C69", "#123C5A", "#EFF4F8"),  # ocean + coral
    ("#4A2318", "#F2D16B", "#4A2318", "#F7F4EE"),  # brick + cream yellow
]


def _hex(rgb):
    return "#%02X%02X%02X" % tuple(max(0, min(255, round(v))) for v in rgb)


def _rgb(h):
    h = h.lstrip("#")
    return [int(h[i:i + 2], 16) for i in (0, 2, 4)]


def mix(a, b, t):
    return _hex([x + (y - x) * t for x, y in zip(_rgb(a), _rgb(b))])


def palette_for(idx):
    ink, signal, signal_ink, paper = PALETTES[idx % len(PALETTES)]
    return {
        "c_ink": ink,
        "c_ink2": mix(ink, "#FFFFFF", 0.07),
        "c_ink3": mix(ink, "#FFFFFF", 0.16),
        "c_steel": mix(ink, "#FFFFFF", 0.22),
        "c_mist": mix(ink, "#FFFFFF", 0.52),
        "c_panel": mix(paper, ink, 0.07),
        "c_paper": paper,
        "c_signal": signal,
        "c_signal_hover": mix(signal, "#FFFFFF", 0.14),
        "c_signal_ink": signal_ink,
        "c_ondark": mix(ink, "#FFFFFF", 0.78),
    }


def assign_palettes(locs):
    """Spread palettes so sites in the same state never share one."""
    by_state = {}
    out = {}
    for i, loc in enumerate(locs):
        st = loc["state"]
        used = by_state.setdefault(st, set())
        k = i % len(PALETTES)
        while k in used:
            k = (k + 1) % len(PALETTES)
        used.add(k)
        out[loc["domain"]] = k
    return out


PALETTE_OF = assign_palettes(LOCATIONS)
MARK = """<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'><path d='M32 3 62 24v37H2V24z' fill='{signal}'/><path d='M32 3 62 24H2z' fill='{signal2}'/><rect x='11' y='27' width='42' height='34' fill='{ink}'/><rect x='15' y='31' width='34' height='6' rx='1' fill='{signal}'/><rect x='15' y='41' width='34' height='6' rx='1' fill='{signal}'/><rect x='15' y='51' width='34' height='6' rx='1' fill='{signal}'/></svg>"""

# slug -> (page template, nav key)
PAGES = {
    "": ("home", "home"),
    "garage-door-spring-repair": ("spring", "spring"),
    "garage-door-opener-repair": ("opener", "opener"),
    "garage-door-off-track-repair": ("offtrack", "offtrack"),
    "new-garage-door-installation": ("newdoor", "newdoor"),
    "emergency-garage-door-repair": ("emergency", "emergency"),
    "service-areas": ("areas", "areas"),
    "gallery": ("gallery", "gallery"),
    "about": ("about", "about"),
    "contact": ("contact", "contact"),
    "thank-you": ("thankyou", "contact"),
    "404": ("404", "home"),
}
FORM_KEY = (ROOT / "data" / "form_key.txt").read_text().strip() if (ROOT / "data" / "form_key.txt").exists() else "YOUR-WEB3FORMS-ACCESS-KEY"
NAV_KEYS = ["home", "spring", "opener", "offtrack", "newdoor", "emergency", "areas", "blog", "gallery", "about", "contact"]

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
<rect width="640" height="160" fill="{ink}"/>
<g transform="translate(28,24) scale(1.75)"><path d="M32 3 62 24v37H2V24z" fill="{signal}"/><path d="M32 3 62 24H2z" fill="{signal2}"/><rect x="11" y="27" width="42" height="34" fill="{ink}"/><rect x="15" y="31" width="34" height="6" rx="1" fill="{signal}"/><rect x="15" y="41" width="34" height="6" rx="1" fill="{signal}"/><rect x="15" y="51" width="34" height="6" rx="1" fill="{signal}"/></g>
<text x="156" y="78" font-family="'Barlow Condensed','Arial Narrow',sans-serif" font-weight="700" font-size="46" fill="{signal}" letter-spacing="0.5">{city}</text>
<text x="156" y="116" font-family="'Barlow Condensed','Arial Narrow',sans-serif" font-weight="700" font-size="38" fill="#FFFFFF" letter-spacing="0.5">GARAGE DOOR REPAIR</text>
<text x="156" y="142" font-family="Barlow,sans-serif" font-weight="500" font-size="13" fill="{mist}" letter-spacing="2.5">SINCE {since} · {cityc}, {st} · 24 HOURS</text>
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
            "page_title": htmlmod.escape(sub(p["title"], f) + f" - {f['cityst']} | " + f["business"], quote=True),
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
        "page_title": htmlmod.escape(f"Blog - {f['cityst']} {f['zip']} | {f['business']}", quote=True),
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


SUBURB_PAGES = 8

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
        "cityst": ("Washington, DC" if city == "Washington DC" else f"{city}, {st}"),
        "city_slug": re.sub(r"[^a-z0-9]+", "-", f"{city} {st}".lower()).strip("-"),
        "since": SINCE,
        "form_key": FORM_KEY,
        "wiki": wiki_url(loc),
        "year": str(datetime.date.today().year),
        "nearby_inline": ", ".join(nearby[:-1]) + (" and " + nearby[-1] if len(nearby) > 1 else (nearby[0] if nearby else "the surrounding area")),
        "nearby_short": ", ".join(nearby[:4]) if nearby else "the surrounding area",
        "nearby_list": "\n      ".join((f'<li><a href="/{suburb_slug(n)}/">{htmlmod.escape(n)}</a></li>' if i < SUBURB_PAGES else f"<li>{htmlmod.escape(n)}</li>") for i, n in enumerate(nearby)) or "<li>Surrounding communities</li>",
        "nearby_inline_links": ", ".join(f'<a href="/{suburb_slug(n)}/">{htmlmod.escape(n)}</a>' for n in nearby[:SUBURB_PAGES]) + (", " + ", ".join(htmlmod.escape(n) for n in nearby[SUBURB_PAGES:-1]) + " and " + htmlmod.escape(nearby[-1]) if len(nearby) > SUBURB_PAGES else ""),
        "styles": STYLES.read_text().strip(),  # colors substituted later in sub()
        **palette_for(PALETTE_OF[loc["domain"]]),
        "favicon": "data:image/svg+xml," + MARK.format(signal=palette_for(PALETTE_OF[loc["domain"]])["c_signal"], signal2=mix(palette_for(PALETTE_OF[loc["domain"]])["c_signal"], "#000000", 0.12), ink=palette_for(PALETTE_OF[loc["domain"]])["c_ink"]).replace("#", "%23").replace("<", "%3C").replace(">", "%3E"),
        "areas_schema": "".join(f',{{"@type":"City","name":"{htmlmod.escape(n)}"}}' for n in nearby),
    }
    return f


def sub(text, f):
    for _ in range(2):
        for k, v in f.items():
            text = text.replace("{{" + k + "}}", v)
    return text


IMG_META = json.loads((T / "img" / "meta.json").read_text())

def img_dir(f):
    return f"/img/garage-door-repair-{f['city_slug']}"

def img_tag(name, alt, f, cls="", eager=False, link=False):
    m = IMG_META[name]
    d = img_dir(f)
    srcset = f"{d}/{name}-600.webp 600w, {d}/{name}.webp {m['w']}w" if m["w"] > 600 else f"{d}/{name}.webp {m['w']}w"
    sizes = "(max-width: 700px) 100vw, 600px"
    lazy = "" if eager else ' loading="lazy" decoding="async"'
    tag = (f'<img src="{d}/{name}.webp" srcset="{srcset}" sizes="{sizes}" width="{m["w"]}" height="{m["h"]}" '
           f'alt="{htmlmod.escape(alt, quote=True)}"{(" class=" + chr(34) + cls + chr(34)) if cls else ""}{lazy}>')
    if link:
        tag = f'<a href="{d}/{name}.webp" class="zoom" data-alt="{htmlmod.escape(alt, quote=True)}">{tag}</a>'
    return tag

def expand_imgs(body, f):
    def rep(m):
        name, alt = m.group(1), sub(m.group(2), f)
        eager = name.startswith("!")
        link = name.startswith("+")
        return img_tag(name.lstrip("!+"), alt, f, eager=eager, link=link)
    return re.sub(r"{{img:([^|}]+)\|([^}]*)}}", rep, body)

def video_schema(f):
    base = f"https://www.{f['domain']}/video/garage-door-repair-{f['city_slug']}/"
    obj = {"@context": "https://schema.org", "@type": "VideoObject",
           "name": f"Garage door repair in {f['cityst']} - {f['business']}",
           "description": f"Opener installation, torsion spring replacement, wall control programming and sectional and commercial door repairs by {f['business']} technicians serving {f['cityst']}.",
           "thumbnailUrl": base + "poster.webp", "contentUrl": base + "garage-door-repair.mp4",
           "uploadDate": datetime.date.today().isoformat(), "duration": "PT48S",
           "publisher": {"@id": f"https://www.{f['domain']}/#business"}}
    return '<script type="application/ld+json">' + json.dumps(obj) + "</script>"


def gallery_schema(f):
    src = (T / "pages" / "gallery.html").read_text()
    items = []
    for name, alt in re.findall(r"{{img:\+([^|}]+)\|([^}]*)}}", src):
        m = IMG_META[name]
        items.append({"@type": "ImageObject", "contentUrl": f"https://www.{f['domain']}{img_dir(f)}/{name}.webp",
                      "name": sub(alt, f), "width": m["w"], "height": m["h"],
                      "contentLocation": {"@type": "Place", "name": f["cityst"]},
                      "creator": {"@type": "Organization", "name": f["business"]}})
    data = {"@context": "https://schema.org", "@type": "ImageGallery", "name": f"Garage door repair photos - {f['cityst']}",
            "url": f"https://www.{f['domain']}/gallery/", "about": {"@id": f"https://www.{f['domain']}/#business"}, "image": items}
    return '<script type="application/ld+json">' + json.dumps(data) + "</script>"

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
        "content": expand_imgs(sub(body, f), f),
        "schema_extra": (sub(FAQ_SCHEMA, f) + video_schema(f) if slug == "" else "") + (gallery_schema(f) if slug == "gallery" else "") + ('<meta name="robots" content="noindex">' if slug in ("thank-you", "404") else ""),
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
    page_imgs = {}
    for slug in PAGES:
        path, out = render_page(slug, f)
        page_imgs[path] = [(src, alt) for src, alt in re.findall(r'<img src="([^"]+)"[^>]*alt="([^"]*)"', out)]
        target = d / "404.html" if slug == "404" else (d / slug / "index.html" if slug else d / "index.html")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(out)
        if slug not in ("thank-you", "404"):
            urls.append(path)
    for suburb in (loc.get("nearby") or [])[:SUBURB_PAGES]:
        title, desc, body, schema = render_suburb(f, suburb)
        path = f"/{suburb_slug(suburb)}/"
        pf = dict(f)
        pf.update({"page_title": htmlmod.escape(title, quote=True), "page_desc": htmlmod.escape(desc, quote=True), "path": path,
                   "content": expand_imgs(sub(body, f), f), "schema_extra": schema})
        for k in NAV_KEYS:
            pf[f"cur_{k}"] = 'aria-current="page"' if k == "areas" else ""
        out = sub(BASE, pf)
        target = d / suburb_slug(suburb) / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(out)
        urls.append(path)
        page_imgs[path] = [(src, alt) for src, alt in re.findall(r'<img src="([^"]+)"[^>]*alt="([^"]*)"', out)]
    (d / "robots.txt").write_text(ROBOTS.format(domain=f["domain"]))
    brand = T / "brand" / f["domain"]
    if brand.exists():
        shutil.copytree(brand, d / "brand", dirs_exist_ok=True)
    (d / "logo.svg").write_text(LOGO.format(city=htmlmod.escape(f["city"].upper()), since=f["since"], st=f["st"], cityc=htmlmod.escape(f["city"]), ink=f["c_ink"], signal=f["c_signal"], signal2=mix(f["c_signal"], "#000000", 0.12), mist=f["c_mist"]))
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">']
    for u in urls:
        imgs = "".join(f"<image:image><image:loc>https://www.{f['domain']}{src}</image:loc><image:title>{alt}</image:title></image:image>" for src, alt in page_imgs.get(u, []))
        sm.append(f"  <url><loc>https://www.{f['domain']}{u}</loc><lastmod>{today}</lastmod>{imgs}</url>")
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
    shutil.copy(T / "_worker.js", OUT / "_worker.js")
    shared = OUT / "_shared" / "img"
    if shared.exists():
        shutil.rmtree(shared)
    shutil.copytree(T / "img", shared, ignore=shutil.ignore_patterns("meta.json"))
    vid = OUT / "_shared" / "video"
    if vid.exists():
        shutil.rmtree(vid)
    shutil.copytree(T / "video", vid)
    (OUT / "index.html").write_text('<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=/charlottegaragedoorrepair.net/">')
    print(f"built {n} site(s), {pages} pages, into {OUT}")


if __name__ == "__main__":
    main()
