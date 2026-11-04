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
