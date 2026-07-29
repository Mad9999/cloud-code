#!/usr/bin/env python3
"""Generate the browser-side index for the verbatim-tafsir browser:
  - app/generated/quran_text.js   window.QURAN_TEXT = {"s:a": "ayah text", ...}
  - app/generated/tafsir_manifest.js  window.TAFSIR_MANIFEST = {tafsirs, counts, names}
Ayah text is the simple (imlaa'i) Tanzil text already vendored in data/.
"""
import json, re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
QURAN = BASE / "data" / "quran-simple.txt"
GEN = BASE / "app" / "generated"
BISM = "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ "

TAFSIRS = [
    ("muyassar",  "التفسير الميسّر"),
    ("ibnkathir", "تفسير ابن كثير"),
    ("baghawi",   "تفسير البغوي"),
    ("saadi",     "تفسير السعدي"),
    ("qurtubi",   "تفسير القرطبي"),
    ("tabari",    "تفسير الطبري"),
]
# Arabic surah names (114) — from the mushaf order
NAMES = ["الفاتحة","البقرة","آل عمران","النساء","المائدة","الأنعام","الأعراف","الأنفال","التوبة","يونس","هود","يوسف","الرعد","إبراهيم","الحجر","النحل","الإسراء","الكهف","مريم","طه","الأنبياء","الحج","المؤمنون","النور","الفرقان","الشعراء","النمل","القصص","العنكبوت","الروم","لقمان","السجدة","الأحزاب","سبأ","فاطر","يس","الصافات","ص","الزمر","غافر","فصلت","الشورى","الزخرف","الدخان","الجاثية","الأحقاف","محمد","الفتح","الحجرات","ق","الذاريات","الطور","النجم","القمر","الرحمن","الواقعة","الحديد","المجادلة","الحشر","الممتحنة","الصف","الجمعة","المنافقون","التغابن","الطلاق","التحريم","الملك","القلم","الحاقة","المعارج","نوح","الجن","المزمل","المدثر","القيامة","الإنسان","المرسلات","النبأ","النازعات","عبس","التكوير","الانفطار","المطففين","الانشقاق","البروج","الطارق","الأعلى","الغاشية","الفجر","البلد","الشمس","الليل","الضحى","الشرح","التين","العلق","القدر","البينة","الزلزلة","العاديات","القارعة","التكاثر","العصر","الهمزة","الفيل","قريش","الماعون","الكوثر","الكافرون","النصر","المسد","الإخلاص","الفلق","الناس"]

def main():
    text = {}
    counts = {}
    with open(QURAN, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            s, a, t = line.split("|", 2)
            s, a = int(s), int(a)
            # ayah 1 of most surahs is prefixed with the basmala in this source;
            # strip it for display except al-Fatiha (1) and at-Tawba (9 has none).
            # word-based (robust to diacritic byte differences): the basmala is the
            # first 4 whitespace-separated words when un-diacritized matches "بسم الله الرحمن الرحيم".
            if a == 1 and s not in (1, 9):
                words = t.split(" ")
                if len(words) > 4:
                    bare = "".join(c for c in "".join(words[:4]) if c not in "ًٌٍَُِّْٰـ")
                    if bare == "بسماللهالرحمنالرحيم":
                        t = " ".join(words[4:])
            text[f"{s}:{a}"] = t
            counts[s] = max(counts.get(s, 0), a)
    GEN.mkdir(parents=True, exist_ok=True)
    with open(GEN / "quran_text.js", "w", encoding="utf-8") as f:
        f.write("window.QURAN_TEXT = ")
        json.dump(text, f, ensure_ascii=False, separators=(",", ":"))
        f.write(";\n")
    manifest = {
        "tafsirs": [{"slug": s, "name": n} for s, n in TAFSIRS],
        "counts": counts,
        "names": {str(i + 1): NAMES[i] for i in range(114)},
    }
    with open(GEN / "tafsir_manifest.js", "w", encoding="utf-8") as f:
        f.write("window.TAFSIR_MANIFEST = ")
        json.dump(manifest, f, ensure_ascii=False, separators=(",", ":"))
        f.write(";\n")
    print(f"quran_text.js: {len(text)} ayat")
    print(f"tafsir_manifest.js: {len(TAFSIRS)} tafsirs, {len(counts)} surahs, {len(NAMES)} names")

if __name__ == "__main__":
    main()
