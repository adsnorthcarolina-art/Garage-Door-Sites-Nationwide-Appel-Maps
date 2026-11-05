# Weekly blog post — runbook for the scheduled task

Every post in `template/blog/` is rendered on all 109 city sites (`/blog/<slug>/`), with
`{{city}}`, `{{cityst}}`, `{{business}}`, `{{phone}}`, `{{phone_digits}}`, `{{since}}` substituted
per site. The home page shows the 3 newest posts; the sitemap updates on build.

## Steps

1. Take the first non-comment line of `data/blog_topics.txt`: `slug | title | angle`.
   If the file has no topics left, invent a useful garage-door topic a homeowner would search
   for (repair, maintenance, openers, springs, safety, buying a door, seasonal) that is not
   already covered by an existing file in `template/blog/`.
2. Write `template/blog/<slug>.html`:
   - First three lines, exactly this format:
     `<!-- title: ... -->`, `<!-- desc: ... (one sentence, 140-160 chars, mention {{city}}) -->`,
     `<!-- date: YYYY-MM-DD -->` (today).
   - Then 600-900 words of body HTML: `<p>`, `<h2>`, `<ul>/<li>`, `<strong>`. No `<h1>`,
     no inline styles, no images. Plain, specific, practical; written by the company
     ("our technicians", "we carry"). Use `{{city}}` 3-6 times naturally. Link 1-2 service
     pages: `/garage-door-spring-repair/`, `/garage-door-opener-repair/`,
     `/garage-door-off-track-repair/`, `/new-garage-door-installation/`,
     `/emergency-garage-door-repair/`. End with a call line:
     `<a href="tel:+1{{phone_digits}}">{{phone}}</a>`.
   - No prices stated as exact figures for a city (ranges like "a few hundred dollars" are fine).
   - Do not claim certifications, awards, reviews or years beyond "since {{since}}".
3. Delete that topic line from `data/blog_topics.txt`.
4. `python3 scripts/build.py` — must print `built 109 site(s)`.
5. Spot-check one rendered post, e.g. `sites/charlottegaragedoorrepair.net/blog/<slug>/index.html`
   contains the title and no leftover `{{` placeholders.
6. Commit and push to all three Pages repos (each is a separate Cloudflare Pages project):
   `git add -A && git commit -m "Blog: <title>" && git push origin main && git push part2 main && git push part3 main`
   ("remote: This repository moved" notices are harmless.)

Cloudflare Pages deploys automatically within ~2 minutes. Nothing else to do.
