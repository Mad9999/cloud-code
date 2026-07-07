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
import subprocess, json, re, html, sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

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
    key = f"{s}:{a}"
    url = f"https://api.quran.com/api/v4/tafsirs/{tid}/by_ayah/{key}"
    for attempt in range(4):
        try:
            out = subprocess.run(["curl", "-s", "--max-time", "40", url],
                                 capture_output=True, text=True, timeout=50).stdout
            d = json.loads(out)
            return a, clean(d.get("tafsir", {}).get("text") or "")
        except Exception:
            if attempt == 3:
                return a, None
    return a, None

def build_surah(tid, slug, s, n):
    entries = {}
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = [ex.submit(fetch_ayah, tid, s, a) for a in range(1, n + 1)]
        for fu in as_completed(futs):
            a, txt = fu.result()
            if txt is None:
                raise SystemExit(f"fetch_tafsir: FAILED {slug} {s}:{a}")
            entries[a] = txt
    d = OUT / slug
    d.mkdir(parents=True, exist_ok=True)
    var = f"TAFSIR_{slug.upper()}_{s}"
    payload = {str(a): entries[a] for a in range(1, n + 1)}
    with open(d / f"{s}.js", "w", encoding="utf-8") as f:
        f.write(f"window.{var} = ")
        json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))
        f.write(";\n")
    filled = sum(1 for a in entries.values() if a)
    return filled

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
    for s in surahs:
        n = counts[s]
        for tid, slug, name in TAFSIRS:
            if only and slug not in only:
                continue
            filled = build_surah(tid, slug, s, n)
            print(f"  {slug:10} surah {s:3} : {filled}/{n} ayat", flush=True)
    print("done.")

if __name__ == "__main__":
    main()
