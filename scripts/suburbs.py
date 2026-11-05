"""Suburb page content: climate-aware, deterministically varied per (city, suburb)."""
import hashlib, html as htmlmod

# Climate / housing notes by state. Used to make each page say something true about the area.
CLIMATE = {
    "coastal_humid": ("humid, salty air", "Salt and humidity corrode springs, cables and bottom brackets faster than almost anywhere else, so we use galvanized hardware and check for rust at every visit."),
    "hot_dry": ("desert heat and dust", "Heat dries out rollers and opener gears, and fine dust works its way into tracks and photo-eyes. Lubrication and a track clean-out are part of every service call."),
    "cold_snow": ("freezing winters", "Cold makes steel springs brittle and ice can freeze the bottom seal to the slab. Most winter calls here are snapped springs and doors that won't lift; we carry cold-rated springs and seals."),
    "storms": ("storm season", "High wind loads and sudden pressure changes flex door panels and knock doors off their tracks. We reinforce struts and can install wind-rated doors where code requires them."),
    "four_season": ("hot summers and cold winters", "Big temperature swings expand and contract the tracks and change spring tension through the year, which is why doors that worked fine in September start sticking in January."),
    "rainy": ("constant damp", "Moisture swells wood doors, rusts hinges and shorts out safety sensors. We seal, lubricate and re-align on every visit."),
    "high_altitude": ("dry air and big temperature swings", "Dry air and large day-to-night swings wear out rollers and crack weather seals early. We replace nylon rollers and seals before they fail."),
    "island": ("sea air", "Salt air is the number-one enemy of garage door hardware here. Stainless and galvanized parts, and a corrosion check on every call."),
}
STATE_CLIMATE = {
    "FL": "coastal_humid", "SC": "coastal_humid", "GA": "coastal_humid", "LA": "coastal_humid", "MS": "coastal_humid", "AL": "coastal_humid", "TX": "storms",
    "AZ": "hot_dry", "NV": "hot_dry", "NM": "hot_dry", "UT": "high_altitude", "CO": "high_altitude", "WY": "high_altitude", "MT": "cold_snow", "ID": "high_altitude",
    "MN": "cold_snow", "WI": "cold_snow", "ND": "cold_snow", "SD": "cold_snow", "NE": "cold_snow", "IA": "cold_snow", "MI": "cold_snow", "ME": "cold_snow", "NH": "cold_snow", "VT": "cold_snow", "AK": "cold_snow",
    "OK": "storms", "KS": "storms", "MO": "storms", "AR": "storms", "TN": "four_season", "KY": "four_season", "NC": "four_season", "VA": "four_season", "WV": "four_season", "MD": "four_season", "DE": "four_season", "DC": "four_season", "PA": "four_season", "NJ": "four_season", "NY": "four_season", "CT": "four_season", "RI": "four_season", "MA": "four_season", "OH": "four_season", "IN": "four_season", "IL": "four_season",
    "WA": "rainy", "OR": "rainy", "CA": "hot_dry", "HI": "island",
}

INTROS = [
    "Need a garage door repaired in {suburb}? {business} sends a technician from our {city} office the same day for most calls, with springs, cables, rollers and opener parts on the truck.",
    "{suburb} homeowners call {business} when the door won't open, won't close, or has come off its track. We're based in {city}, minutes away, and we fix most doors in one visit.",
    "From our {city} office, {business} covers {suburb} every day of the week: broken springs, dead openers, crooked doors and full replacements, usually the same day you call.",
    "If your garage door in {suburb} is stuck, noisy or hanging crooked, call {business}. A {city}-based technician can be at your home today with a firm price before any work starts.",
    "{business} has repaired garage doors in {suburb} and the rest of the {city} area since {since}. Same-day appointments, insured technicians, and a 5-year warranty on the springs and parts we install.",
]

PROBLEMS = [
    ("Broken torsion springs", "The loud bang from the garage followed by a door that's suddenly too heavy to lift. We replace springs in matched pairs, sized to the door's actual weight, so the door balances and the opener stops straining."),
    ("Opener won't respond", "Remote dead, wall button does nothing, or the motor hums but the door doesn't move. We repair logic boards, gears and sensors, and tell you plainly when a new opener is the better value."),
    ("Door off its track", "A door that's crooked, jammed or hanging on one cable. Don't force it. We reset the rollers, straighten or replace bent track, and fix whatever caused it to jump."),
    ("Snapped or frayed cables", "Cables usually fail at the bottom bracket. One side drops, the door racks sideways and panels bend. We replace both cables and check the drums and springs they're attached to."),
    ("Noisy, shaking door", "Grinding, popping and rattling almost always mean worn rollers, loose hinges or a dry chain. A tune-up with new nylon rollers makes the door quiet again."),
    ("Door reverses before closing", "Nine times out of ten the safety sensors are misaligned or dirty. The rest of the time it's a travel-limit or force setting. Quick to diagnose, usually quick to fix."),
    ("Damaged panels", "A bumped bumper or storm debris dents a section. If the rest of the door is sound we replace just the panel, color-matched, instead of the whole door."),
    ("Old door replacement", "When a door is 20+ years old, uninsulated, or several panels are damaged, replacement is the better investment. We measure, order and install, and haul the old door away."),
]

NEIGHBORHOOD_NOTES = [
    "Many homes in {suburb} were built with the original builder-grade door and opener. Those doors are now at the age where springs and cables fail on schedule, and a new insulated door often pays for itself in comfort and curb appeal.",
    "{suburb} has a mix of older houses with wood doors and newer subdivisions with steel doors. We carry parts for both, including the lighter extension springs older single doors use.",
    "A lot of {suburb} garages are attached and share a wall with living space. An insulated door and a quiet belt-drive opener make a real difference in noise and energy bills.",
    "HOA neighborhoods in {suburb} usually need a replacement door to match the street. We bring style and color samples so the new door passes review the first time.",
    "Detached garages and workshops are common around {suburb}. We service those too, including roll-up doors and openers on outbuildings without a wired connection.",
]

FAQS = [
    ("How quickly can you get to {suburb}?", "Most {suburb} calls are handled the same day. Call before noon and you'll usually see a technician that afternoon; emergencies are dispatched first."),
    ("Do you charge extra to come to {suburb}?", "No. {suburb} is inside our regular {city} service area. The service call fee is the same, and it's applied to the repair."),
    ("Can you replace just one spring?", "We can, but we don't recommend it. Springs are installed as a matched pair and the second one fails soon after the first. Replacing both at once costs less than two visits."),
    ("My door is stuck halfway. Should I pull the red cord?", "Not if the door is crooked or a spring looks broken — the door can drop. Leave it, keep people and cars clear, and call us."),
    ("What does a new garage door cost in {suburb}?", "It depends on size, insulation and style. The technician measures on site and gives you a written price for two or three options before you decide."),
    ("Do you work on commercial doors?", "Yes. Roll-up and sectional commercial doors, high-cycle springs and commercial openers for shops and small warehouses around {suburb}."),
    ("Is the work warrantied?", "5 years on springs and parts we install, 1 year on labor. New doors carry the manufacturer's warranty on top."),
    ("Do I need to be home?", "Someone needs to let us into the garage and approve the price. After that you're free to go; we lock up and leave the invoice."),
]


def pick(seq, seed, n):
    """Deterministic selection of n items from seq, order varying with seed."""
    h = int(hashlib.md5(seed.encode()).hexdigest(), 16)
    idx = list(range(len(seq)))
    out = []
    for i in range(n):
        j = (h >> (i * 5)) % len(idx)
        out.append(seq[idx.pop(j)])
    return out


def suburb_slug(name):
    import re
    return "garage-door-repair-" + re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def render_suburb(f, suburb):
    seed = f["domain"] + "|" + suburb
    ctx = dict(f, suburb=suburb)
    def s(t):
        for k, v in ctx.items():
            if isinstance(v, str):
                t = t.replace("{" + k + "}", v)
        return t
    climate_key = STATE_CLIMATE.get(f["st"], "four_season")
    climate_name, climate_text = CLIMATE[climate_key]
    intro = s(pick(INTROS, seed + "i", 1)[0])
    problems = pick(PROBLEMS, seed + "p", 4)
    note = s(pick(NEIGHBORHOOD_NOTES, seed + "n", 1)[0])
    faqs = [(s(q), s(a)) for q, a in pick(FAQS, seed + "f", 4)]
    e = htmlmod.escape
    body = f'''<section class="hero sub" aria-labelledby="h1">
  <div class="wrap">
    <h1 id="h1">Garage door repair in {e(suburb)}, {e(f["st"])}</h1>
    <p class="lede">{e(intro)}</p>
    <a class="bignum" href="tel:+1{f["phone_digits"]}"><span>Same-day service in {e(suburb)}</span>{f["phone"]}</a>
    <ul class="facts">
      <li>Same-day appointments</li>
      <li>Firm price before work starts</li>
      <li>Insured technicians</li>
      <li>5-year parts warranty</li>
    </ul>
  </div>
  <div class="door" aria-hidden="true"><i></i><i></i></div>
</section>

<section aria-labelledby="h2a">
  <div class="wrap two">
    <div>
      <h2 id="h2a">What we fix most in {e(suburb)}</h2>
      <div class="grid">
''' + "".join(f'        <div class="svc"><h3>{e(t)}</h3><p>{e(d)}</p></div>\n' for t, d in problems) + f'''      </div>
      <h3>Garage doors and {e(climate_name)}</h3>
      <p>{e(climate_text)}</p>
      <h3>About homes in {e(suburb)}</h3>
      <p>{e(note)}</p>
    </div>
    <div>
      <figure class="photo">{{{{img:+offtrack-door-crooked|Garage door repair in {e(suburb)}, {e(f["st"])} - off-track door before repair}}}}<figcaption>A door off its track, the most common emergency call we get around {e(suburb)}.</figcaption></figure>
      <h2>Services in {e(suburb)}</h2>
      <ul class="towns">
        <li><a href="/garage-door-spring-repair/">Spring repair</a></li>
        <li><a href="/garage-door-opener-repair/">Opener repair &amp; installation</a></li>
        <li><a href="/garage-door-off-track-repair/">Off-track door repair</a></li>
        <li><a href="/new-garage-door-installation/">New garage doors</a></li>
        <li><a href="/emergency-garage-door-repair/">24-hour emergency repair</a></li>
        <li><a href="/gallery/">Photos of our work</a></li>
      </ul>
      <p>Based at {e(f["street"])}, {e(f["cityst"])}. <a href="/service-areas/">All areas we serve.</a></p>
    </div>
  </div>
</section>

<section class="band" aria-labelledby="h-cta">
  <div class="wrap">
    <h2 id="h-cta">Garage door stuck in {e(suburb)}?</h2>
    <p>Call now and tell the dispatcher what the door is doing. You'll get an arrival window right away, and a firm price before the technician touches anything.</p>
    <a class="bignum" href="tel:+1{f["phone_digits"]}"><span>Call 24 hours a day</span>{f["phone"]}</a>
  </div>
</section>

<section class="seam" aria-labelledby="h-faq">
  <div class="wrap">
    <h2 id="h-faq">Questions from {e(suburb)} customers</h2>
''' + "".join(f'    <details><summary>{e(q)}</summary><p>{e(a)}</p></details>\n' for q, a in faqs) + '''  </div>
</section>
'''
    title = f"Garage Door Repair {suburb}, {f['st']} | Same-Day | {f['business']}"
    desc = f"Garage door repair in {suburb}, {f['st']}: broken springs, openers, off-track doors and new doors, same day from {f['business']}. Call {f['phone']}."
    import json
    faq_schema = '<script type="application/ld+json">' + json.dumps({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faqs]}) + "</script>"
    svc_schema = '<script type="application/ld+json">' + json.dumps({"@context": "https://schema.org", "@type": "Service", "serviceType": "Garage door repair", "provider": {"@id": f"https://www.{f['domain']}/#business"}, "areaServed": {"@type": "City", "name": suburb, "containedInPlace": {"@type": "State", "name": f["state"]}}, "url": f"https://www.{f['domain']}/{suburb_slug(suburb)}/"}) + "</script>"
    return title, desc, body, faq_schema + svc_schema
