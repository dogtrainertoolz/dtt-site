#!/usr/bin/env python3
"""Build Dog Trainer Toolz into ./public.
  content/tools/*.html   interactive tools (front matter + HTML/JS body)

Content:
  content/guides/*.md   front matter: title, date, pillar (topic slug), dek
  content/picks.json    product picks page
Amazon links: in markdown write [text](amzn:search words) and the build turns
it into a tagged Amazon search link marked rel="sponsored".

Run:  python3 scripts/build.py   (needs: pip install markdown)
"""
import datetime as dt
import html
import json
import math
import re
import shutil
from pathlib import Path
from urllib.parse import quote_plus

import markdown

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "public"
SITE = json.loads((ROOT / "site.json").read_text())
PILLARS = SITE["pillars"]
P_BY_SLUG = {p["slug"]: p for p in PILLARS}
PICKS = json.loads((ROOT / "content/picks.json").read_text())
TAG = SITE.get("amazon_tag", "")
TODAY = dt.date.today()
YEAR = TODAY.year
DOMAIN = SITE["domain"].rstrip("/")
esc = html.escape


def amazon(q):
    url = f"https://www.amazon.com/s?k={quote_plus(q)}"
    return url + (f"&tag={TAG}" if TAG else "")


def amzn_links(h):
    return re.sub(r'href="amzn:([^"]+)"',
                  lambda m: f'href="{esc(amazon(html.unescape(m.group(1)).replace("+", " ")))}" rel="sponsored nofollow noopener" target="_blank"', h)


ICONS = {
    "home": '<path d="M8 30 32 10l24 20"/><path d="M14 26v26h36V26"/><path d="M27 52V38h10v14"/>',
    "water": '<path d="M32 8C24 20 16 29 16 38a16 16 0 0 0 32 0c0-9-8-18-16-30z"/><path d="M24 40a8 8 0 0 0 8 8"/>',
    "bowl": '<path d="M8 32h48a24 14 0 0 1-48 0z"/><path d="M14 50h36"/><path d="M24 26c0-6 4-6 4-12M34 26c0-6 4-6 4-12"/>',
    "move": '<circle cx="38" cy="12" r="5"/><path d="M22 54l8-14 8 6v8M30 40l4-16 10 8 8 0M34 24l-10 4-6 8"/>',
    "rest": '<path d="M44 40A20 20 0 1 1 30 12a16 16 0 0 0 14 28z"/><path d="M44 12h8l-8 8h8"/>',
    "shield": '<path d="M32 8l20 8v14c0 13-9 22-20 26-11-4-20-13-20-26V16z"/><path d="M24 32l6 6 11-12"/>',
    "wave": '<path d="M6 40c6-6 10-6 16 0s10 6 16 0 10-6 16 0"/><path d="M6 52c6-6 10-6 16 0s10 6 16 0 10-6 16 0"/><path d="M20 30a12 12 0 0 1 24 0"/>',
    "swim": '<circle cx="44" cy="16" r="5"/><path d="M12 34l14-8 10 6 8-6"/><path d="M6 46c6-5 10-5 16 0s10 5 16 0 10-5 16 0"/>',
    "sun": '<circle cx="32" cy="26" r="9"/><path d="M32 8v4M32 40v4M14 26h4M46 26h4M19 13l3 3M42 36l3 3M45 13l-3 3M22 36l-3 3"/><path d="M6 54c6-5 10-5 16 0s10 5 16 0 10-5 16 0"/>',
    "tree": '<path d="M20 50V36M20 36l-10 0 10-22 10 22z"/><path d="M6 56c6-5 10-5 16 0s10 5 16 0 10-5 16 0"/>',
    "boat": '<path d="M8 40h48l-8 12H16z"/><path d="M32 40V8l16 26H32"/>',
    "pool": '<path d="M20 44V12a6 6 0 0 1 12 0M36 44V12a6 6 0 0 1 12 0M20 20h28M20 30h28"/><path d="M6 54c6-5 10-5 16 0s10 5 16 0 10-5 16 0"/>',
    "towel": '<rect x="14" y="10" width="36" height="44" rx="4"/><path d="M14 22h36M14 44h36"/>',
    "ball": '<circle cx="32" cy="32" r="22"/><path d="M14 20c10 6 26 6 36 0M14 44c10-6 26-6 36 0M32 10c-6 10-6 34 0 44"/>',
    "snow": '<path d="M32 6v52M10 19l44 26M10 45l44-26M26 10l6 6 6-6M26 54l6-6 6 6"/>',
    "puppy": '<ellipse cx="32" cy="38" rx="16" ry="14"/><path d="M18 30l-6-14 12 6M46 30l6-14-12 6"/><circle cx="26" cy="36" r="1.5"/><circle cx="38" cy="36" r="1.5"/><path d="M29 44h6"/>',
    "sit": '<path d="M20 54V36l8-14h10l6 10v22"/><circle cx="34" cy="14" r="6"/><path d="M14 54h36"/>',
    "leash": '<circle cx="14" cy="14" r="6"/><path d="M18 18c10 10 4 22 14 28s20-4 18-14"/><rect x="44" y="40" width="10" height="16" rx="3"/>',
    "alert": '<path d="M32 8l26 46H6z"/><path d="M32 26v12M32 44v2"/>',
    "tools": '<path d="M38 10a10 10 0 0 0-12 13L10 39l7 7 16-16a10 10 0 0 0 13-12l-6 6-6-2-2-6z"/><path d="M40 40l12 12"/>',
    "star": '<path d="M32 8l7 15 16 2-12 11 3 16-14-8-14 8 3-16L9 25l16-2z"/>',
    "paw": '<ellipse cx="32" cy="42" rx="12" ry="10"/><ellipse cx="16" cy="27" rx="5" ry="7"/><ellipse cx="26" cy="16" rx="5" ry="7"/><ellipse cx="38" cy="16" rx="5" ry="7"/><ellipse cx="48" cy="27" rx="5" ry="7"/>',
}


def icon(name, cls="ico"):
    return f'<svg class="{cls}" viewBox="0 0 64 64" aria-hidden="true">{ICONS[name]}</svg>'


LOGO = ('<svg class="logo" viewBox="0 0 64 64" aria-hidden="true"><rect x="2" y="2" width="60" height="60" rx="14"/>'
        '<g><ellipse cx="32" cy="38" rx="10" ry="8.5"/><ellipse cx="19" cy="27" rx="4.2" ry="6"/><ellipse cx="27" cy="18" rx="4.2" ry="6"/>'
        '<ellipse cx="37" cy="18" rx="4.2" ry="6"/><ellipse cx="45" cy="27" rx="4.2" ry="6"/></g></svg>')


# ---------------------------------------------------------------- content ---
def parse(path):
    raw = path.read_text(encoding="utf-8")
    meta, body = {}, raw
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", raw, re.S)
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()
        body = m.group(2)
    meta["slug"] = path.stem
    meta["date"] = dt.date.fromisoformat(meta.get("date", "2026-11-24")[:10])
    meta["html"] = amzn_links(markdown.markdown(body, extensions=["extra", "sane_lists", "toc"]))
    text = re.sub(r"<[^>]+>", " ", meta["html"])
    meta["minutes"] = max(1, math.ceil(len(text.split()) / 220))
    meta["has_aff"] = "rel=\"sponsored" in meta["html"]
    return meta


def parse_tool(path):
    raw = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", raw, re.S)
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    meta["slug"] = path.stem
    body = m.group(2)
    cut = body.rfind("</script>")
    head, tail = (body[:cut + 9], body[cut + 9:]) if cut >= 0 else (body, "")
    meta["html"] = head + '<div class="prose tool-notes">' + markdown.markdown(tail, extensions=["extra"]) + "</div>"
    return meta


guides = [parse(p) for p in sorted((ROOT / "content/guides").glob("*.md"))]
for g in guides:
    assert g.get("pillar") in P_BY_SLUG, f"{g['slug']}: unknown pillar {g.get('pillar')}"
guide_by_slug = {g["slug"]: g for g in guides}
by_pillar = {p["slug"]: sorted([g for g in guides if g["pillar"] == p["slug"]], key=lambda g: int(g.get("order", 50)))
             for p in PILLARS}
IMG_DIR = ROOT / "content/images"
IMGS = {k: v for k, v in json.loads((ROOT / "content/images.json").read_text()).items() if not k.startswith("_")} \
    if (ROOT / "content/images.json").exists() else {}


def has_img(key):
    return (IMG_DIR / f"{key}.jpg").exists() and (IMG_DIR / f"{key}-sm.jpg").exists()


def alt(key):
    return esc(IMGS.get(key, {}).get("alt", ""))


for g in guides:
    g["img"] = has_img(g["slug"])


# ---------------------------------------------------------------- layout ----
def page(title, body, *, path="/", description=None, og_type="website", jsonld=None, active=""):
    full_title = f"{SITE['name']}: {SITE['tagline']}" if title == SITE["name"] else f"{title} | {SITE['name']}"
    desc = esc(description or SITE["description"])
    url = DOMAIN + path
    nav = [("/tools/", "Free Tools", "tools"), ("/topics/", "Training Topics", "pillars"), ("/guides/", "All Guides", "guides"),
           ("/gear/", "Gear", "picks"), ("/about/", "About", "about")]
    nav_html = "".join(f'<a href="{h}"{" aria-current=page" if k == active else ""}>{t}</a>' for h, t, k in nav)
    foot_p = "".join(f'<li><a href="/topics/{p["slug"]}/">{esc(p["name"])}</a></li>' for p in PILLARS)
    ld = f'<script type="application/ld+json">{json.dumps(jsonld)}</script>' if jsonld else ""
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(full_title)}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{url}">
<meta property="og:site_name" content="{esc(SITE['name'])}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{desc}">
<meta property="og:type" content="{og_type}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{DOMAIN}/og.png">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#1D2733">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Archivo:wght@700;800&family=Figtree:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/style.css">
{ld}
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="top">
  <div class="wrap top-row">
    <a class="brand" href="/">{LOGO}<span>Dog Trainer <b>Toolz</b></span></a>
    <button class="menu-btn" aria-expanded="false" aria-controls="nav" onclick="const n=document.getElementById('nav');const o=n.classList.toggle('open');this.setAttribute('aria-expanded',o)">Menu</button>
    <nav id="nav" class="nav" aria-label="Main">{nav_html}</nav>
  </div>
</header>
<main id="main">
{body}
</main>
<footer class="footer">
  <div class="wrap foot-grid">
    <div>
      <a class="brand light" href="/">{LOGO}<span>Dog Trainer <b>Toolz</b></span></a>
      <p>{esc(SITE['description'])}</p>
    </div>
    <div><h4>Topics</h4><ul>{foot_p}</ul></div>
    <div><h4>Site</h4><ul>
      <li><a href="/tools/">Free tools</a></li><li><a href="/guides/">All guides</a></li><li><a href="/gear/">Training gear</a></li>
      <li><a href="/about/">About</a></li><li><a href="/contact/">Contact &amp; advertising</a></li>
      <li><a href="/privacy-policy/">Privacy</a></li><li><a href="/affiliate-disclaimer/">Affiliate disclosure</a></li><li><a href="/terms/">Terms</a></li><li><a href="/photo-credits/">Photo credits</a></li></ul></div>
  </div>
  <div class="wrap foot-note"><p><strong>Aggression or serious fear?</strong> If your dog has bitten, or you're worried they might, work with a veterinarian and a qualified behavior professional rather than training alone.</p>
  <p>© {YEAR} Dog Trainer Toolz. Guides are general information, not a substitute for your veterinarian. As an Amazon Associate we earn from qualifying purchases.</p></div>
</footer>
</body>
</html>"""


def guide_card(g, show_pillar=True):
    p = P_BY_SLUG[g["pillar"]]
    kicker = f'<p class="kicker">{icon(p["icon"], "ico sm")}{esc(p["name"])}</p>' if show_pillar else ""
    thumb = f'<a class="thumb" href="/{g["slug"]}/" tabindex="-1" aria-hidden="true"><img src="/img/{g["slug"]}-sm.jpg" alt="" width="720" height="480" loading="lazy"></a>' if g["img"] else ""
    return f"""<article class="card{' has-img' if g['img'] else ''}">
  {thumb}<div class="card-body">{kicker}<h3><a href="/{g['slug']}/">{esc(g['title'])}</a></h3>
  <p class="dek">{esc(g.get('dek', ''))}</p>
  <p class="meta">{g['minutes']} min read</p></div>
</article>"""


def pillar_img(p):
    return next((g["slug"] for g in by_pillar[p["slug"]] if g["img"]), None)


def pillar_tile(p, i):
    n = len(by_pillar[p["slug"]])
    pi = pillar_img(p)
    ph = f'<span class="pimg"><img src="/img/{pi}-sm.jpg" alt="" width="720" height="480" loading="lazy"></span>' if pi else ""
    return f"""<a class="pillar{' has-img' if pi else ''}" href="/topics/{p['slug']}/">{ph}
  <span class="pnum">{i:02d}</span>{icon(p['icon'], 'ico lg')}
  <span class="pname">{esc(p['name'])}</span>
  <span class="pblurb">{esc(p['blurb'])}</span>
  <span class="pcount">{n} guide{'s' if n != 1 else ''} →</span></a>"""


def write(path, content):
    target = OUT / path.strip("/") / "index.html" if not path.endswith((".html", ".xml", ".txt", ".json")) else OUT / path.strip("/")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def simple(path, title, inner, *, active="", description=None):
    write(path, page(title, f'<div class="wrap narrow"><article class="article"><h1>{esc(title)}</h1><div class="prose">{inner}</div></article></div>',
                     path=path, active=active, description=description))


# ---------------------------------------------------------------- pages -----
def build():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    for f in (ROOT / "static").iterdir():
        shutil.copy(f, OUT / f.name)
    if IMG_DIR.exists():
        (OUT / "img").mkdir()
        for f in IMG_DIR.glob("*.jpg"):
            shutil.copy(f, OUT / "img" / f.name)

    featured = [guide_by_slug[s] for s in SITE["featured_guides"] if s in guide_by_slug]
    tools = sorted([parse_tool(t) for t in (ROOT / "content/tools").glob("*.html")], key=lambda t: int(t.get("order", 50)))
    tool_cards = "".join(f"""<a class="tool-card" href="/tools/{t['slug']}/">{icon(t.get('icon','tools'), 'ico lg')}<span class="pname">{esc(t['title'])}</span><span class="pblurb">{esc(t['dek'])}</span><span class="pcount">Open the tool →</span></a>""" for t in tools)
    # ---- Home
    home = f"""<section class="hero">
  <div class="wrap hero-grid">
    <div>
      <p class="eyebrow">Free tools + step-by-step training plans</p>
      <h1>Train your dog at home,<br>one small win at a time.</h1>
      <p class="lede">Clear, reward-based plans for the things every owner deals with: potty training, puppy biting, pulling on the leash, barking, jumping and coming when called. Plus free tools that do the planning for you.</p>
      <p class="ctas"><a class="btn" href="/tools/">Try the free tools</a> <a class="btn ghost" href="/topics/">Find a training plan</a></p>
    </div>
    <div class="hero-side">{'<img class="hero-photo" src="/img/home.jpg" alt="' + alt('home') + '" width="1600" height="1067">' if has_img('home') else ''}
    <aside class="stat-card">
      <p class="stat"><span>5</span> minutes</p>
      <p>That's all a training session needs. Short, frequent, fun sessions beat long ones every time. <a href="/dog-training-101-how-to-teach-the-basics/">Start with the basics →</a></p>
    </aside></div>
  </div>
</section>
<div class="wrap">
<section class="block">
  <div class="block-head"><h2>Free training tools</h2><a class="more" href="/tools/">All tools →</a></div>
  <div class="tools-grid">{tool_cards}</div>
</section>
<section class="block">
  <div class="block-head"><h2>Start here</h2><a class="more" href="/guides/">All {len(guides)} guides →</a></div>
  <div class="grid three">{''.join(guide_card(g) for g in featured)}</div>
</section>
<section class="block">
  <div class="block-head"><h2>Training topics</h2><a class="more" href="/topics/">All topics →</a></div>
  <div class="pillars">{''.join(pillar_tile(p, i + 1) for i, p in enumerate(PILLARS))}</div>
</section>
<section class="band">
  <div>
    <p class="eyebrow">The golden rules</p>
    <h2>Five habits behind every well-trained dog</h2>
    <p>Whatever you're teaching, these make it work faster.</p>
    <a class="btn light" href="/positive-reinforcement-training-with-dogs/">Why reward-based training works</a>
  </div>
  <ol class="mini-breeds checks">
    <li><span>Reward the behavior you want, the moment it happens.</span></li>
    <li><span>Keep sessions short: 3 to 5 minutes, a few times a day.</span></li>
    <li><span>Make it easy first, then add distance, duration and distractions.</span></li>
    <li><span>Manage the environment so mistakes can't become habits.</span></li>
    <li><span>Meet your dog's needs: exercise, sniffing, chewing and rest.</span></li>
  </ol>
</section>
<section class="promise">
  <h2>How we train</h2>
  <div class="grid three">
    <div><h3>Reward-based</h3><p>We use treats, toys, play and praise, the methods backed by research and recommended by veterinary behavior organizations. No shock, prong or pain.</p></div>
    <div><h3>Small steps</h3><p>Every plan breaks a skill into steps your dog can win at, so you both stay motivated.</p></div>
    <div><h3>Honest about limits</h3><p>Aggression, serious fear and separation panic need professional help. We tell you when.</p></div>
  </div>
</section>
</div>"""
    write("/", page(SITE["name"], home, path="/", jsonld={
        "@context": "https://schema.org", "@type": "WebSite", "name": SITE["name"], "url": DOMAIN + "/",
        "description": SITE["description"]}))

    # ---- Tools
    write("/tools/", page("Free Dog Training Tools", f"""<div class="wrap">
<header class="page-head narrow"><p class="eyebrow">Free tools</p><h1>Free dog training tools</h1>
<p class="lede">Planners, calculators and checklists that take the guesswork out of training. No sign-up, nothing to install, and they work on your phone.</p></header>
<div class="tools-grid">{tool_cards}</div></div>""", path="/tools/", active="tools",
        description="Free dog training tools: puppy potty schedule generator, treat calorie calculator, socialization checklist and printable training log."))
    for t in tools:
        rel = [guide_by_slug[x] for x in t.get("related", "").split() if x in guide_by_slug]
        relhtml = f'<section class="block"><h2 class="label">Related guides</h2><div class="grid two">{"".join(guide_card(r) for r in rel)}</div></section>' if rel else ""
        body = f"""<div class="wrap narrow"><article class="article tool">
<p class="kicker">{icon('tools', 'ico sm')}<a href="/tools/">Free tools</a></p>
<h1>{esc(t['title'])}</h1><p class="lede">{esc(t['dek'])}</p>
<div class="tool-body">{amzn_links(t['html'])}</div>
<p class="note">This tool gives general guidance. Every dog is different. Ask your vet about your dog's health, diet and vaccination timing.</p>
</article>{relhtml}</div>"""
        write(f"/tools/{t['slug']}/", page(t["title"], body, path=f"/tools/{t['slug']}/", active="tools", description=t["dek"],
              jsonld={"@context": "https://schema.org", "@type": "WebApplication", "name": t["title"], "applicationCategory": "LifestyleApplication",
                      "operatingSystem": "Any", "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"}, "description": t["dek"]}))

    # ---- Topics overview
    pv = f"""<div class="wrap">
<header class="page-head narrow"><p class="eyebrow">Topics</p><h1>Training topics</h1>
<p class="lede">Step-by-step plans grouped by what you're working on, from a brand-new puppy to an adult dog with habits to unlearn.</p></header>
<div class="pillars">{''.join(pillar_tile(p, i + 1) for i, p in enumerate(PILLARS))}</div>
</div>"""
    write("/topics/", page("Training Topics", pv, path="/topics/", active="pillars",
                           description="Dog training topics: puppy training, basic commands, leash walking, problem behaviors, methods and gear, and tricks."))
    for i, p in enumerate(PILLARS):
        items = by_pillar[p["slug"]]
        nxt = PILLARS[(i + 1) % len(PILLARS)]
        body = f"""<div class="wrap">
<header class="page-head narrow"><p class="eyebrow"><a href="/topics/">Training topics</a></p>{icon(p['icon'], 'ico xl')}<h1>{esc(p['name'])}</h1>
<p class="lede">{esc(p['blurb'])}</p></header>
<div class="grid two">{''.join(guide_card(g, False) for g in items)}</div>
<p class="next-pillar">Next topic: <a href="/topics/{nxt['slug']}/">{esc(nxt['name'])} →</a></p>
</div>"""
        write(f"/topics/{p['slug']}/", page(p["name"], body, path=f"/topics/{p['slug']}/", active="pillars",
                                             description=f"{p['name']}: {p['blurb']}"))

    # ---- Guides library
    sections = ""
    for p in PILLARS:
        lis = "".join(f'<li data-t="{esc((g["title"] + " " + g.get("dek", "")).lower())}"><a href="/{g["slug"]}/">{esc(g["title"])}</a></li>'
                      for g in by_pillar[p["slug"]])
        sections += f"""<section class="cat-list"><h2>{icon(p['icon'], 'ico sm')}<a href="/topics/{p['slug']}/">{esc(p['name'])}</a></h2><ul>{lis}</ul></section>"""
    gidx = f"""<div class="wrap narrow">
<header class="page-head"><p class="eyebrow">Library</p><h1>All guides</h1>
<p class="lede">{len(guides)} practical guides, grouped by topic.</p>
<input id="filter" class="filter" type="search" placeholder="Search, e.g. biting, recall, barking" aria-label="Search guides"></header>
{sections}<p id="none" class="muted" hidden>No guides match that search.</p></div>
<script>
const f=document.getElementById('filter');f.addEventListener('input',()=>{{const q=f.value.trim().toLowerCase();let any=false;
document.querySelectorAll('.cat-list').forEach(s=>{{let n=0;s.querySelectorAll('li').forEach(li=>{{const ok=!q||li.dataset.t.includes(q);li.hidden=!ok;if(ok)n++;}});s.hidden=n===0;if(n)any=true;}});
document.getElementById('none').hidden=any;}});
</script>"""
    write("/guides/", page("All Guides", gidx, path="/guides/", active="guides",
                           description="Every Dog Trainer Toolz guide: puppy training, basic commands, leash walking, problem behaviors, training methods and tricks."))

    # ---- Guide pages
    for g in guides:
        p = P_BY_SLUG[g["pillar"]]
        related = [x for x in by_pillar[g["pillar"]] if x is not g][:4]
        rel = f"""<section class="block"><h2 class="label">More on {esc(p['name'].lower())}</h2>
<div class="grid two">{''.join(guide_card(r, False) for r in related)}</div></section>""" if related else ""
        aff = '<p class="aff">This guide contains affiliate links. If you buy through them we may earn a small commission at no cost to you. <a href="/affiliate-disclaimer/">Details</a>.</p>' if g["has_aff"] else ""
        body = f"""<div class="wrap narrow">
<article class="article">
  <p class="kicker">{icon(p['icon'], 'ico sm')}<a href="/topics/{p['slug']}/">{esc(p['name'])}</a></p>
  <h1>{esc(g['title'])}</h1>
  <p class="lede">{esc(g.get('dek', ''))}</p>
  <p class="meta">{g['minutes']} min read · Updated {g['date'].strftime('%B %Y')}</p>
  {aff}
  {f'<figure class="hero-img"><img src="/img/{g["slug"]}.jpg" alt="{alt(g["slug"])}" width="1600" height="1067"><figcaption>Photo: <a href="https://unsplash.com/photos/{IMGS[g["slug"]]["id"]}" rel="nofollow noopener" target="_blank">Unsplash</a></figcaption></figure>' if g['img'] else ''}
  <div class="prose">{g['html']}</div>
  <p class="note">This guide is general information, not veterinary advice. If your dog is sick, hurt or acting unusually, call your veterinarian.</p>
</article>
{rel}
</div>"""
        write(f"/{g['slug']}/", page(g["title"], body, path=f"/{g['slug']}/", description=g.get("dek"), og_type="article",
                                     active="guides", jsonld={"@context": "https://schema.org", "@type": "Article", "headline": g["title"],
                                                              "description": g.get("dek", ""), "dateModified": g["date"].isoformat(),
                                                              "publisher": {"@type": "Organization", "name": SITE["name"]}}))

    # ---- Picks
    groups = ""
    for grp in PICKS["groups"]:
        p = P_BY_SLUG.get(grp["pillar"])
        items = "".join(f"""<li class="pick"><div><h3>{esc(it['name'])}</h3><p>{esc(it['why'])}</p></div>
<a class="btn small" href="{esc(amazon(it['query']))}" rel="sponsored nofollow noopener" target="_blank">See options on Amazon</a></li>""" for it in grp["items"])
        groups += f"""<section class="pick-group" id="{grp['id']}"><h2>{icon(p['icon'], 'ico sm') if p else ''}{esc(grp['title'])}</h2>
<p class="muted">{esc(grp['blurb'])}</p><ul class="picks">{items}</ul></section>"""
    toc = " · ".join(f'<a href="#{g["id"]}">{esc(g["title"])}</a>' for g in PICKS["groups"])
    pk = f"""<div class="wrap narrow">
<header class="page-head"><p class="eyebrow">Gear</p><h1>Dog training gear</h1>
<p class="lede">{esc(PICKS['intro'])}</p>
<p class="aff">As an Amazon Associate we earn from qualifying purchases. It costs you nothing extra. <a href="/affiliate-disclaimer/">Details</a>.</p>
<p class="toc">{toc}</p></header>
{groups}</div>"""
    write("/gear/", page("Dog Training Gear", pk, path="/gear/", active="picks",
                         description="The harnesses, leashes, treat pouches, clickers, crates and enrichment toys we recommend for reward-based dog training."))

    # ---- Static pages
    email = SITE["contact_email"]
    simple("/about/", "About Dog Trainer Toolz", f"""<p>Most dog owners don't need a dog trainer for every problem. They need a clear plan, broken into steps small enough to succeed at, and a few tools that take the guesswork out of it.</p>
<p>That's what Dog Trainer Toolz is for: <a href="/tools/">free tools</a> like a potty schedule generator and a treat calorie calculator, and <a href="/topics/">step-by-step training plans</a> for puppies, basic commands, leash walking and common problem behaviors.</p>
<h2>How we train</h2>
<p>Every plan on this site uses reward-based methods: treats, toys, play and praise. That's the approach supported by research and recommended by veterinary behavior organizations, and it's the one that keeps training fun for both of you. We don't recommend shock, prong or choke collars.</p>
<p>We're also honest about limits. Aggression, serious fear and separation panic need a veterinarian and a qualified behavior professional, and our guides say so.</p>
<h2>How we make money</h2>
<p>Some links on this site are affiliate links. If you buy through them, we may earn a small commission. That never changes what we recommend. See our <a href="/affiliate-disclaimer/">affiliate disclosure</a>.</p>
<p>Questions or corrections: <a href="mailto:{email}">{email}</a>.</p>""", active="about",
           description="Dog Trainer Toolz: free dog training tools and step-by-step, reward-based training plans for owners.")
    simple("/contact/", "Contact & Advertising", f"""<p>Questions, corrections and suggestions: <a href="mailto:{email}">{email}</a>.</p>
<h2>Advertising and partnerships</h2>
<p>We work with brands and services that support reward-based training: training gear, treats, enrichment toys, online courses and certified trainers. Options include sponsored guides, sponsored tools and featured placements, always clearly labeled.</p>
<p>Email <a href="mailto:{email}">{email}</a> with what you have in mind.</p>
<p><em>We can't give advice about individual dogs by email. For aggression or serious fear, please contact your veterinarian or a qualified behavior professional.</em></p>""")
    simple("/privacy-policy/", "Privacy Policy", f"""<p>Last updated {TODAY.strftime('%B %-d, %Y')}.</p>
<p>Dog Trainer Toolz does not require an account and does not sell personal information. Tools that remember your progress, like the socialization checklist, store it only in your own browser. Our hosting provider may keep standard server logs (such as IP address and browser type) for security and performance.</p>
<p>When you click an affiliate link, the retailer (for example Amazon) may set its own cookies to credit the referral. Their privacy policies apply on their sites.</p>
<p>If you email us, we use your address only to reply. Questions: <a href="mailto:{email}">{email}</a>.</p>""")
    simple("/affiliate-disclaimer/", "Affiliate Disclosure", """<p>Dog Trainer Toolz is a participant in the Amazon Services LLC Associates Program, an affiliate advertising program designed to provide a means for sites to earn advertising fees by advertising and linking to Amazon.com. As an Amazon Associate we earn from qualifying purchases.</p>
<p>We may also earn commissions from other retailers we link to. Affiliate links are marked, cost you nothing extra and never decide what we recommend.</p>""")
    simple("/terms/", "Terms", """<p>Content and tools on Dog Trainer Toolz are general information only and are not veterinary or behavioral advice. If your dog shows aggression, serious fear or a sudden change in behavior, contact your veterinarian and a qualified behavior professional.</p>
<p>Product prices and availability are set by the retailer and may change. You may link to any page on this site freely.</p>""")
    cred = "".join(f'<li><a href="https://unsplash.com/photos/{v["id"]}" rel="nofollow noopener" target="_blank">{esc(v["alt"])}</a></li>'
                   for k, v in IMGS.items() if has_img(k))
    simple("/photo-credits/", "Photo Credits", f"""<p>Photos on this site come from <a href="https://unsplash.com" rel="nofollow noopener" target="_blank">Unsplash</a> and are used under the <a href="https://unsplash.com/license" rel="nofollow noopener" target="_blank">Unsplash License</a>, which allows free commercial use. Thank you to the photographers.</p>
<ul>{cred}</ul>""")
    (OUT / "404.html").write_text(page("Page not found", """<div class="wrap narrow"><article class="article"><h1>This page wandered off.</h1>
<p class="lede">We rebuilt the site and some old pages moved. Try one of these:</p>
<p class="ctas"><a class="btn" href="/guides/">Search the guides</a> <a class="btn ghost" href="/topics/">Browse topics</a></p></article></div>""", path="/404"), encoding="utf-8")

    # ---- sitemap, robots, redirects
    urls = ["/", "/tools/", "/topics/", "/guides/", "/gear/", "/about/", "/contact/"] + [f"/tools/{t['slug']}/" for t in tools] + [f"/topics/{p['slug']}/" for p in PILLARS] \
        + [f"/{g['slug']}/" for g in guides]
    write("/sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
          + "".join(f"<url><loc>{DOMAIN}{u}</loc></url>" for u in urls) + "</urlset>")
    write("/robots.txt", f"User-agent: *\nAllow: /\nSitemap: {DOMAIN}/sitemap.xml\n")
    shutil.copy(ROOT / "redirects.txt", OUT / "_redirects")
    print(f"Built {len(guides)} guides, {sum(len(g['items']) for g in PICKS['groups'])} gear picks -> {OUT}")


if __name__ == "__main__":
    build()
