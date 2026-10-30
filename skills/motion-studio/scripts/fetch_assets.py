#!/usr/bin/env python3
"""fetch_assets: search + download FREE, no-API-key stock images/video with license info recorded.

Only fetch what code cannot draw (photo cutouts of a camera, car, laptop, a texture, a B-roll clip).
No people unless the user asked for people.

Usage
  python3 fetch_assets.py "vintage camera" [--n 3] [--media image|video] [--source auto|openverse|commons]
                          [--outdir assets] [--width 1600] [--cutout]
  python3 fetch_assets.py --credits assets                  # print the credits file
Sources (no keys needed)
  openverse  api.openverse.org (images). Only commercial-use licenses are kept: cc0, pdm, by, by-sa.
             (Anonymous access is rate-limited and sometimes slow; we time out after 25 s and fall back.)
  commons    Wikimedia Commons API (images AND video). Only CC0 / Public domain / CC BY / CC BY-SA kept.
  Optional upgrade (NOT set up, needs the user's OK + a free API key they create): Pexels, Pixabay.
Every download is logged to <outdir>/credits.json and <outdir>/CREDITS.md (title, creator, license, license URL,
source page). BY / BY-SA need on-screen or description credit: paste CREDITS.md into the video description.
--cutout  removes the background into <name>_cutout.png with rembg (local, free; model isnet-general-use, Apache-2.0),
          installed in ~/.local/share/rembg-venv. Check the cutout on the contact sheet; hair/glass edges can be rough.
"""
import argparse, html, json, os, re, subprocess, sys, time, urllib.parse, urllib.request

UA = "motion-studio/1.0 (Codex skill; personal video project)"
OV_OK = {"cc0", "pdm", "by", "by-sa"}
REMBG = os.path.expanduser("~/.local/share/rembg-venv/bin/rembg")
REMBG_MODEL = "isnet-general-use"   # Apache-2.0 (IS-Net/DIS). Do NOT use rembg's default bria-rmbg: it is non-commercial (CC BY-NC).

def get(url, timeout=25):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()

def strip(s): return html.unescape(re.sub(r"<[^>]+>", "", s or "")).strip()

def commons_ok(lic):
    l = (lic or "").lower()
    if any(b in l for b in ("nc", "nd", "fair use", "non-free")): return False
    return l.startswith("cc0") or "public domain" in l or l.startswith("pd") or re.match(r"cc[ -]by(-sa)?[ -]\d", l) is not None or l in ("cc by", "cc by-sa")

def search_openverse(q, n):
    url = "https://api.openverse.org/v1/images/?" + urllib.parse.urlencode({"q": q, "page_size": 20})
    data = json.loads(get(url))
    out = []
    for r in data.get("results", []):
        if r.get("license") not in OV_OK or not r.get("url"): continue
        out.append({"provider": "openverse/" + (r.get("source") or r.get("provider") or "?"), "title": r.get("title") or q,
                    "creator": r.get("creator") or "unknown", "creator_url": r.get("creator_url"),
                    "license": (r["license"].upper() if r["license"] not in ("cc0", "pdm") else r["license"].upper()) + (" " + r["license_version"] if r.get("license_version") else ""),
                    "license_url": r.get("license_url"), "source_page": r.get("foreign_landing_url"), "download": r["url"], "media": "image"})
        if len(out) >= n: break
    return out

def search_commons(q, n, media, width):
    ft = "filetype:video" if media == "video" else "filetype:bitmap"
    params = {"action": "query", "format": "json", "generator": "search", "gsrsearch": f"{q} {ft}", "gsrnamespace": 6, "gsrlimit": 40,
              "prop": "imageinfo", "iiprop": "url|extmetadata|mime|size", "iiurlwidth": width}
    data = json.loads(get("https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(params)))
    pages = sorted(data.get("query", {}).get("pages", {}).values(), key=lambda p: p.get("index", 0))
    out = []
    for p in pages:
        ii = (p.get("imageinfo") or [{}])[0]; md = ii.get("extmetadata", {})
        lic = strip(md.get("LicenseShortName", {}).get("value"))
        if not commons_ok(lic): continue
        if media == "video":
            if not ii.get("mime", "").startswith("video"): continue
            dl = ii.get("url")
            if ii.get("size", 0) > 80e6: continue
        else:
            if not ii.get("mime", "").startswith("image"): continue
            dl = ii.get("thumburl") or ii.get("url")
        out.append({"provider": "wikimedia-commons", "title": p["title"].replace("File:", ""), "creator": strip(md.get("Artist", {}).get("value")) or "unknown",
                    "license": lic, "license_url": strip(md.get("LicenseUrl", {}).get("value")) or None, "source_page": ii.get("descriptionurl"),
                    "download": dl, "media": media})
        if len(out) >= n: break
    return out

def slug(s): return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:50] or "asset"

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("query", nargs="?"); ap.add_argument("--n", type=int, default=3); ap.add_argument("--media", default="image", choices=["image", "video"])
    ap.add_argument("--source", default="auto", choices=["auto", "openverse", "commons"]); ap.add_argument("--outdir", default="assets")
    ap.add_argument("--width", type=int, default=1600); ap.add_argument("--cutout", action="store_true"); ap.add_argument("--credits")
    a = ap.parse_args()
    if a.credits:
        print(open(os.path.join(a.credits, "CREDITS.md")).read()); return
    if not a.query: ap.error("query required")
    os.makedirs(a.outdir, exist_ok=True)
    hits, used, errors = [], None, []
    order = ["commons"] if a.media == "video" else (["openverse", "commons"] if a.source == "auto" else [a.source])
    if a.source == "commons": order = ["commons"]
    for src in order:
        try:
            hits = search_openverse(a.query, a.n) if src == "openverse" else search_commons(a.query, a.n, a.media, a.width)
            used = src
            if hits: break
        except Exception as e:
            errors.append(f"{src}: {e}")
    if not hits: sys.exit(json.dumps({"error": "no free-licensed results", "tried": order, "errors": errors}))
    cj = os.path.join(a.outdir, "credits.json")
    credits = json.load(open(cj)) if os.path.exists(cj) else []
    saved = []
    for h in hits:
        ext = os.path.splitext(urllib.parse.urlparse(h["download"]).path)[1].lower() or (".webm" if a.media == "video" else ".jpg")
        fn = os.path.join(a.outdir, f"{slug(a.query)}_{len(credits) + 1:02d}{ext}")
        try:
            data = get(h["download"], timeout=60)
        except Exception as e:
            errors.append(f"download {h['download']}: {e}"); continue
        open(fn, "wb").write(data)
        h.update({"file": fn, "query": a.query, "fetched": time.strftime("%Y-%m-%d")})
        if a.cutout and a.media == "image":
            if os.path.exists(REMBG):
                co = os.path.splitext(fn)[0] + "_cutout.png"
                r = subprocess.run([REMBG, "i", "-m", REMBG_MODEL, fn, co], capture_output=True, text=True,
                                   env={**os.environ, "NUMBA_CACHE_DIR": "/tmp/numba-cache"})  # Codex sandbox: site-packages is read-only
                h["cutout"] = co if r.returncode == 0 else None
                if r.returncode == 0:
                    try:   # crop to the object so it is easy to place in the canvas
                        from PIL import Image
                        im = Image.open(co); bb = im.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox()
                        if bb: im.crop(bb).save(co)
                    except Exception as e:
                        errors.append(f"autocrop: {e}")
                if r.returncode: errors.append("rembg: " + r.stderr[-300:])
            else:
                errors.append("rembg not installed; no cutout")
        credits.append(h); saved.append(h)
    json.dump(credits, open(cj, "w"), indent=2)
    with open(os.path.join(a.outdir, "CREDITS.md"), "w") as fh:
        fh.write("# Asset credits\n\n")
        for c in credits:
            fh.write(f"- **{c['title']}** by {c['creator']}, {c['license']}" + (f" ({c['license_url']})" if c.get("license_url") else "") +
                     f", via {c['provider']}: {c['source_page']} -> `{os.path.basename(c['file'])}`\n")
    print(json.dumps({"source": used, "saved": [{k: s.get(k) for k in ("file", "cutout", "license", "creator", "source_page")} for s in saved],
                      "errors": errors}, indent=1))

if __name__ == "__main__":
    main()
