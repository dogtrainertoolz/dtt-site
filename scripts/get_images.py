#!/usr/bin/env python3
"""Download the photos listed in content/images.json from Unsplash and save
web-sized copies: content/images/<key>.jpg (1600px wide) and <key>-sm.jpg (720px).
Skips photos already downloaded. Needs: pip install pillow
Run: python3 scripts/get_images.py   (add --force to re-download everything)
"""
import io
import json
import sys
import urllib.request
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
IMG = ROOT / "content/images"
IMG.mkdir(parents=True, exist_ok=True)
data = {k: v for k, v in json.loads((ROOT / "content/images.json").read_text()).items() if not k.startswith("_")}
force = "--force" in sys.argv
ok, failed = 0, []
for key, info in data.items():
    big, small = IMG / f"{key}.jpg", IMG / f"{key}-sm.jpg"
    if big.exists() and small.exists() and not force:
        ok += 1
        continue
    url = f"https://unsplash.com/photos/{info['id']}/download?force=true&w=2000"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        raw = urllib.request.urlopen(req, timeout=60).read()
        im = Image.open(io.BytesIO(raw)).convert("RGB")
        # crop to 3:2 landscape, centered
        w, h = im.size
        tw, th = (w, int(w * 2 / 3)) if h > w * 2 / 3 else (int(h * 3 / 2), h)
        left, top = (w - tw) // 2, (h - th) // 2
        im = im.crop((left, top, left + tw, top + th))
        im.resize((1600, 1067), Image.LANCZOS).save(big, "JPEG", quality=80, optimize=True, progressive=True)
        im.resize((720, 480), Image.LANCZOS).save(small, "JPEG", quality=78, optimize=True, progressive=True)
        ok += 1
        print("ok  ", key)
    except Exception as e:
        failed.append(key)
        print("FAIL", key, e)
print(f"{ok}/{len(data)} images ready" + (f"; failed: {failed}" if failed else ""))
