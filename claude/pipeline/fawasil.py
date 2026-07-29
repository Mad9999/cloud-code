"""Fawasil Observatory — the researcher wing's first live experiment.

For all 6236 verses of the Qur'an, extract the fasila (verse-ending letter) and
build a per-surah "ending fingerprint": the distribution of the tajwid
attributes of that final letter (ghunna, madd, shidda, hams, istiala ...).

Deliberate scope limit: this works at the level of the FINAL LETTER only, not a
full phonetic decomposition — the decomposition rules are validated for
Al-Fatiha alone. The UI states this limit explicitly.
"""

import json
import re
from collections import Counter
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DATA_DIR = BASE / "data"

DIACRITICS = re.compile(r"[ؐ-ًؚ-ٰٟۖ-ۭـ]")
NON_LETTER = re.compile(r"[^ء-ي]")

# Normalize orthographic variants to a base tajwid letter present in letters.json.
NORMALIZE = {
	"أ": "ء", "إ": "ء", "آ": "ء", "ؤ": "ء", "ئ": "ء", "ٱ": "ا",
	"ى": "ي", "ة": "ه",  # ta marbuta at waqf is pronounced as ha
}


def load_letters():
	with open(DATA_DIR / "letters.json", encoding="utf-8") as f:
		return json.load(f)["letters"]


def load_meta():
	with open(DATA_DIR / "surah_meta.json", encoding="utf-8") as f:
		return json.load(f)


def final_letter(text):
	"""Last pronounced consonant of a verse read with waqf."""
	bare = NON_LETTER.sub("", DIACRITICS.sub("", text))
	if not bare:
		return None
	ch = bare[-1]
	return NORMALIZE.get(ch, ch)


def attr_tags(letter, letters):
	"""Salient tajwid tags of a single letter for fingerprinting."""
	a = letters.get(letter)
	if not a:
		return []
	tags = [a["voicing"], a["strength"], a["elevation"]]
	if a["itbaq"]:
		tags.append("itbaq")
	if a["qalqala"]:
		tags.append("qalqala")
	tags.extend(a["extras"])  # ghunna, madd, safir, lin ...
	return tags


def build():
	letters = load_letters()
	meta = load_meta()
	verses_by_surah = {}
	with open(DATA_DIR / "quran-simple.txt", encoding="utf-8") as f:
		for line in f:
			line = line.strip()
			if not line or line.startswith("#"):
				continue
			s, a, text = line.split("|", 2)
			verses_by_surah.setdefault(int(s), []).append(text)

	surahs = []
	global_final = Counter()
	for s in range(1, 115):
		verses = verses_by_surah[s]
		finals = [final_letter(t) for t in verses]
		finals = [f for f in finals if f]
		letter_counts = Counter(finals)
		global_final.update(finals)

		tag_counts = Counter()
		for f in finals:
			tag_counts.update(attr_tags(f, letters))
		total = len(finals) or 1
		fingerprint = {t: round(100 * c / total, 1) for t, c in tag_counts.items()}

		m = meta[str(s)]
		top_letter, top_n = letter_counts.most_common(1)[0]
		surahs.append({
			"n": s,
			"name": m["name"],
			"revelation": "مكية" if m["revelationType"] == "Meccan" else "مدنية",
			"ayah_count": len(verses),
			"dominant_fasila": top_letter,
			"dominant_pct": round(100 * top_n / total, 1),
			"top_letters": letter_counts.most_common(4),
			"fingerprint": fingerprint,
		})

	return {
		"total_ayahs": sum(len(v) for v in verses_by_surah.values()),
		"surah_count": len(surahs),
		"global_top_fasila": global_final.most_common(8),
		"surahs": surahs,
		"scope_note": "التحليل على مستوى حرف الفاصلة الأخير فقط (لا التفكيك الصوتي الكامل)؛ قواعد التفكيك الكامل مدقّقة لسورة الفاتحة وحدها.",
		"source": "نص Tanzil (رواية حفص) عبر api.alquran.cloud، صفات الحروف من المقدمة الجزرية",
	}


if __name__ == "__main__":
	r = build()
	print("total ayahs:", r["total_ayahs"], "| surahs:", r["surah_count"])
	print("global top fasila letters:", r["global_top_fasila"])
	for s in r["surahs"][:8]:
		print(
			f"  {s['n']:3} {s['name']:14} {s['revelation']:5} "
			f"فاصلة غالبة: {s['dominant_fasila']} ({s['dominant_pct']}%)"
		)
