#!/usr/bin/env python3
"""Fetch verbatim tafsir text (copy-paste) from the quran.com API and store it
keyed by ayah, so any ayah can be looked up against the actual books.

Sources (trusted classical/【contemporary】 tafsirs, fetched verbatim):
  16 muyassar   التفسير الميسّر (مجمع الملك فهد)
  14 ibnkathir  تفسير ابن كثير
  94 baghawi    تفسير البغوي
  91 saadi      تفسير السعدي
  90 qurtubi    تفسير القرطبي
  15 tabari     تفسير الطبري

The text is fetched verbatim (only HTML tags stripped, entities unescaped,
whitespace collapsed) — NOT paraphrased. Output: one JS file per (tafsir,surah)
under app/tafsir/<slug>/<surah>.js assigning window.TAFSIR_<SLUG>_<surah>,
loaded on demand by the browser (keeps file:// working, avoids a huge bundle).
"""
import subprocess, json, re, html, sys, time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

WORKERS = 4  # be gentle with the API (503s appear above this)

BASE = Path(__file__).resolve().parent.parent
QURAN = BASE / "data" / "quran-simple.txt"
OUT = BASE / "app" / "tafsir"

TAFSIRS = [
    (16, "muyassar",  "التفسير الميسّر"),
    (14, "ibnkathir", "تفسير ابن كثير"),
    (94, "baghawi",   "تفسير البغوي"),
    (91, "saadi",     "تفسير السعدي"),
    (90, "qurtubi",   "تفسير القرطبي"),
    (15, "tabari",    "تفسير الطبري"),
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
    if not t:
        return ""
    t = re.sub(r"<[^>]+>", " ", t)
    t = html.unescape(t)
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\s*\n\s*", "\n", t)
    return t.strip()

def fetch_ayah(tid, s, a):
    """Return (a, text) on success, (a, None) if all retries fail.
    Retries with backoff on transient errors (503, non-JSON)."""
    url = f"https://api.quran.com/api/v4/tafsirs/{tid}/by_ayah/{s}:{a}"
    delay = 0.6
    for attempt in range(7):
        try:
            out = subprocess.run(["curl", "-s", "--max-time", "45", url],
                                 capture_output=True, text=True, timeout=55).stdout
            d = json.loads(out)  # error pages (503/404 HTML) raise here -> retry
            return a, clean(d.get("tafsir", {}).get("text") or "")
        except Exception:
            if attempt < 6:
                time.sleep(delay)
                delay = min(delay * 1.8, 12)
    return a, None

def build_surah(tid, slug, s, n, entries=None, targets=None):
    """Fetch `targets` ayat (default 1..n) into `entries`; return list of failures."""
    if entries is None:
        entries = {}
    if targets is None:
        targets = list(range(1, n + 1))
    fails = []
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = [ex.submit(fetch_ayah, tid, s, a) for a in targets]
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
        for tid, slug, name in TAFSIRS:
            if only and slug not in only:
                continue
            entries, fails = build_surah(tid, slug, s, n)
            # up to 3 extra passes over the failures (transient 503s)
            for _ in range(3):
                if not fails:
                    break
                time.sleep(2.0)
                entries, fails = build_surah(tid, slug, s, n, entries, fails)
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
