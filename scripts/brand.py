"""Generate per-city brand assets (logo PNGs + Open Graph share image) into template/brand/<domain>/.

Usage: python3 scripts/brand.py [domain-filter]
Needs node + playwright (pre-installed in the build container) and the Barlow Condensed
woff2 at template/fonts/BarlowCondensed-Bold.woff2.
"""
import base64
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build  # noqa: E402

ROOT = build.ROOT
FONT = ROOT / "template" / "fonts" / "BarlowCondensed-Bold.woff2"
OUT = ROOT / "template" / "brand"
MARK_PATH = 'M32 3 62 24v37H2V24z'


def mark_svg(f, size):
    signal, ink = f["c_signal"], f["c_ink"]
    signal2 = build.mix(signal, "#000000", 0.12)
    return (f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64' width='{size}' height='{size}'>"
            f"<path d='M32 3 62 24v37H2V24z' fill='{signal}'/><path d='M32 3 62 24H2z' fill='{signal2}'/>"
            f"<rect x='11' y='27' width='42' height='34' fill='{ink}'/>"
            f"<rect x='15' y='31' width='34' height='6' rx='1' fill='{signal}'/><rect x='15' y='41' width='34' height='6' rx='1' fill='{signal}'/><rect x='15' y='51' width='34' height='6' rx='1' fill='{signal}'/></svg>")


def page_html(f, font_b64):
    city = f["city"].upper()
    big = len(city) > 12
    return f"""<!doctype html><meta charset="utf-8"><style>
@font-face{{font-family:BC;src:url(data:font/woff2;base64,{font_b64}) format('woff2');font-weight:700}}
*{{margin:0;padding:0;box-sizing:border-box}} body{{background:transparent;font-family:BC,'DejaVu Sans Condensed','Arial Narrow',sans-serif;font-weight:700}}
.fit{{white-space:nowrap}}
.sq{{width:512px;height:512px;display:grid;place-items:center;background:{f['c_ink']};border-radius:96px}}
.sq svg{{width:360px;height:360px}}
.wm{{width:1024px;height:256px;display:flex;align-items:center;gap:36px;padding:0 48px;background:{f['c_ink']}}}
.wm.t{{background:transparent}}
.wm svg{{width:176px;height:176px;flex:none}} .wm>div{{flex:1;min-width:0}}
.wm .city{{font-size:{"66px" if big else "80px"};line-height:.95;color:{f['c_signal']};letter-spacing:1px}}
.wm .gdr{{font-size:{"54px" if big else "62px"};line-height:1;color:#fff;letter-spacing:1px;margin-top:4px}}
.wm .sub{{font-size:21px;letter-spacing:4px;color:{f['c_mist']};margin-top:12px;font-family:'DejaVu Sans',Arial,sans-serif;font-weight:700}}
.og{{width:1200px;height:630px;background:{f['c_ink']};position:relative;overflow:hidden;color:#fff}}
.og .stripe{{position:absolute;left:0;right:0;bottom:0;height:22px;background:{f['c_signal']}}}
.og .door{{position:absolute;right:-40px;top:60px;width:470px;height:560px;background:{build.mix(f['c_ink'], '#FFFFFF', 0.07)};border-radius:12px 12px 0 0;box-shadow:0 0 0 14px {build.mix(f['c_ink'], '#FFFFFF', 0.12)}}}
.og .door i{{display:block;height:70px;margin:26px 34px;background:{build.mix(f['c_ink'], '#FFFFFF', 0.16)};border-radius:8px}}
.og .in{{position:absolute;left:72px;top:0;height:608px;display:flex;flex-direction:column;justify-content:center;gap:0;width:690px}}
.og .mk{{display:flex;align-items:center;gap:20px;margin-bottom:34px}}
.og .mk svg{{width:92px;height:92px}}
.og .mk span{{font-size:30px;letter-spacing:5px;color:{f['c_mist']};font-family:'DejaVu Sans',Arial,sans-serif}}
.og .city{{font-size:{"96px" if big else "120px"};line-height:.9;color:{f['c_signal']}}}
.og .gdr{{font-size:{"72px" if big else "84px"};line-height:1;margin-top:10px}}
.og .ph{{font-size:60px;margin-top:34px;color:#fff;background:{f['c_signal']};color:{f['c_signal_ink']};padding:10px 28px;border-radius:12px;align-self:flex-start}}
.og .ft{{font-size:24px;letter-spacing:4px;color:{f['c_mist']};margin-top:30px;font-family:'DejaVu Sans',Arial,sans-serif}}
</style>
<div id="sq" class="sq">{mark_svg(f, 360)}</div>
<div id="wm" class="wm">{mark_svg(f, 176)}<div><div class="city fit">{city}</div><div class="gdr fit">GARAGE DOOR REPAIR</div><div class="sub fit">SINCE {f['since']} · {f['cityst'].upper()} · 24 HOURS</div></div></div>
<div id="wmt" class="wm t">{mark_svg(f, 176)}<div><div class="city fit">{city}</div><div class="gdr fit">GARAGE DOOR REPAIR</div><div class="sub fit">SINCE {f['since']} · {f['cityst'].upper()} · 24 HOURS</div></div></div>
<div id="og" class="og"><div class="door"><i></i><i></i><i></i><i></i><i></i><i></i></div><div class="in">
<div class="mk">{mark_svg(f, 92)}<span>SINCE {f['since']} · 24 HOURS</span></div>
<div class="city fit">{city}</div><div class="gdr fit">GARAGE DOOR REPAIR</div>
<div class="ph">{f['phone']}</div>
<div class="ft fit">SAME-DAY SERVICE IN {f['cityst'].upper()}</div></div><div class="stripe"></div></div>
<script>for(const e of document.querySelectorAll(".fit")){{let fs=parseFloat(getComputedStyle(e).fontSize);const max=e.parentElement.clientWidth;while(e.scrollWidth>max&&fs>20){{fs-=2;e.style.fontSize=fs+"px"}}}}</script>
"""


NODE = r"""
const { chromium } = require('playwright');
const fs = require('fs');
(async () => {
  const jobs = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1300, height: 2200 }, deviceScaleFactor: 1 });
  for (const j of jobs) {
    await page.setContent(j.html);
    await page.evaluate(() => document.fonts.ready);
    fs.mkdirSync(j.dir, { recursive: true });
    const shot = async (id, file, omit) => page.locator('#' + id).screenshot({ path: j.dir + '/' + file, omitBackground: !!omit });
    await shot('sq', 'icon-512.png');
    await shot('wm', 'logo-1024.png');
    await shot('wmt', 'logo-1024-transparent.png', true);
    await shot('og', 'og.png');
    process.stdout.write('.');
  }
  await browser.close();
  console.log('\ndone', jobs.length);
})();
"""


def main():
    flt = sys.argv[1] if len(sys.argv) > 1 else ""
    font_b64 = base64.b64encode(FONT.read_bytes()).decode()
    jobs = []
    for loc in build.LOCATIONS:
        if flt and flt not in loc["domain"]:
            continue
        f = build.fields(loc)
        jobs.append({"html": page_html(f, font_b64), "dir": str(OUT / loc["domain"])})
    tmp = ROOT / "template" / "brand" / "_jobs.json"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_text(json.dumps(jobs))
    js = tmp.with_suffix(".js")
    js.write_text(NODE)
    subprocess.run(["node", str(js), str(tmp)], check=True)
    tmp.unlink(); js.unlink()


if __name__ == "__main__":
    main()
