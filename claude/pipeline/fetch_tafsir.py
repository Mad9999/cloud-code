#!/usr/bin/env python3
"""Fetch verbatim tafsir text (copy-paste) and store it keyed by ayah, so any
ayah can be looked up against the actual books.

Source: spa5k/tafsir_api via the jsDelivr CDN (mirrors the quran.com tafsir
data; CDN-cached so it is fast and not origin-rate-limited). Trusted tafsirs:
  muyassar   التفسير الميسّر (مجمع الملك فهد)
  ibnkathir  تفسير ابن كثير
  baghawi    تفسير البغوي
  saadi      تفسير السعدي
  qurtubi    تفسير القرطبي
  tabari     تفسير الطبري

Text is fetched verbatim (only stray HTML stripped, entities unescaped,
whitespace normalised, paragraph breaks kept) — NOT paraphrased. Output: one
JS file per (tafsir,surah) under app/tafsir/<slug>/<surah>.js assigning
window.TAFSIR_<SLUG>_<surah>, loaded on demand by the browser (keeps file://
working, avoids a huge up-front bundle). Files are deterministically
re-fetchable, so a container restart loses no hand-authored work.
"""
import subprocess, json, re, html, sys, time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# Source: spa5k/tafsir_api served via jsDelivr CDN — mirrors the quran.com
# tafsir data but is CDN-cached, so it is fast and not origin-rate-limited.
CDN = "https://cdn.jsdelivr.net/gh/spa5k/tafsir_api@main/tafsir"
WORKERS = 16

BASE = Path(__file__).resolve().parent.parent
QURAN = BASE / "data" / "quran-simple.txt"
OUT = BASE / "app" / "tafsir"

# (cdn_slug, out_slug, display_name)
TAFSIRS = [
    ("ar-tafsir-muyassar",   "muyassar",  "التفسير الميسّر"),
    ("ar-tafsir-ibn-kathir", "ibnkathir", "تفسير ابن كثير"),
    ("ar-tafsir-al-baghawi", "baghawi",   "تفسير البغوي"),
    ("ar-tafseer-al-saddi",  "saadi",     "تفسير السعدي"),
    ("ar-tafseer-al-qurtubi","qurtubi",   "تفسير القرطبي"),
    ("ar-tafsir-al-tabari",  "tabari",    "تفسير الطبري"),
]

def ayah_counts():
    counts = {}
    with open(QURAN, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            s, a, _ = line.split("|", 2)
            s, a = int(s), int(a)
            counts[s] = max(counts.get(s, 0), a)
    return counts

def clean(t):
    """Normalise the verbatim tafsir text: strip stray HTML, unescape entities,
    keep paragraph breaks (blank lines) but collapse runs of spaces."""
    if not t:
        return ""
    t = re.sub(r"<[^>]+>", " ", t)
    t = html.unescape(t)
    t = t.replace("\r", "\n")
    # drop markdown separator artifacts (lines that are only * and spaces)
    t = re.sub(r"(?m)^[ \t]*\*[ \t*]*$", "", t)
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"[ \t]*\n[ \t]*", "\n", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()

def fetch_ayah(cdn_slug, s, a):
    """Return (a, text) on success, (a, None) if all retries fail."""
    url = f"{CDN}/{cdn_slug}/{s}/{a}.json"
    delay = 0.5
    for attempt in range(6):
        try:
            out = subprocess.run(["curl", "-s", "--max-time", "40", url],
                                 capture_output=True, text=True, timeout=50).stdout
            d = json.loads(out)
            return a, clean(d.get("text") or "")
        except Exception:
            if attempt < 5:
                time.sleep(delay)
                delay = min(delay * 1.7, 8)
    return a, None

def build_surah(cdn_slug, slug, s, n, entries=None, targets=None):
    """Fetch `targets` ayat (default 1..n) into `entries`; return list of failures."""
    if entries is None:
        entries = {}
    if targets is None:
        targets = list(range(1, n + 1))
    fails = []
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = [ex.submit(fetch_ayah, cdn_slug, s, a) for a in targets]
        for fu in as_completed(futs):
            a, txt = fu.result()
            if txt is None:
                fails.append(a)
            else:
                entries[a] = txt
    return entries, fails

def write_surah(slug, s, n, entries):
    d = OUT / slug
    d.mkdir(parents=True, exist_ok=True)
    var = f"TAFSIR_{slug.upper()}_{s}"
    payload = {str(a): entries.get(a, "") for a in range(1, n + 1)}
    with open(d / f"{s}.js", "w", encoding="utf-8") as f:
        f.write(f"window.{var} = ")
        json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))
        f.write(";\n")
    return sum(1 for a in range(1, n + 1) if payload[str(a)])

def main():
    counts = ayah_counts()
    # args: surah numbers (space or comma sep) or "1-114"; default 1-114
    if len(sys.argv) > 1:
        spec = sys.argv[1]
        if "-" in spec:
            lo, hi = spec.split("-"); surahs = list(range(int(lo), int(hi) + 1))
        else:
            surahs = [int(x) for x in spec.replace(",", " ").split()]
    else:
        surahs = list(range(1, 115))
    only = sys.argv[2].split(",") if len(sys.argv) > 2 else None  # slugs filter
    persistent = []
    for s in surahs:
        n = counts[s]
        for cdn_slug, slug, name in TAFSIRS:
            if only and slug not in only:
                continue
            entries, fails = build_surah(cdn_slug, slug, s, n)
            # up to 3 extra passes over the failures (transient 503s)
            for _ in range(3):
                if not fails:
                    break
                time.sleep(2.0)
                entries, fails = build_surah(cdn_slug, slug, s, n, entries, fails)
            filled = write_surah(slug, s, n, entries)
            flag = "" if not fails else f"  !! {len(fails)} gaps: {sorted(fails)}"
            print(f"  {slug:10} surah {s:3} : {filled}/{n} ayat{flag}", flush=True)
            for a in fails:
                persistent.append(f"{slug} {s}:{a}")
    if persistent:
        print("PERSISTENT GAPS (" + str(len(persistent)) + "): " + ", ".join(persistent))
    print("done.")

if __name__ == "__main__":
    main()
