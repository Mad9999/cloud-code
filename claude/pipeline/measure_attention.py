"""Rule 33's instrument: how much attention did each imam give this verse?

Rule 33 says the verse asks and the template is not imposed, and that the
question is settled by measurement rather than by taste. The measurement was
being taken wrongly.

An imam often comments on a run of verses in one stretch of prose. Our tafsir
files are keyed by ayah, so every ayah in such a run carries a copy of the
whole run's text. Measuring per key therefore credits each of those verses
with the length of all of them together. The distortion is not small and it is
not even: of Baghawi's 286 entries in al-Baqara, 223 are copies of a shared
block; of Ibn Kathir's, 186; of Tabari's, 12.

So we measure blocks, not keys, and we compare a verse's share of its block
against the average share. Usage: python measure_attention.py <surah> [ayah]
"""

import json
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
BOOKS = ("muyassar", "saadi", "ibnkathir", "baghawi", "qurtubi", "tabari")


def load(book, surah):
	path = BASE / "app" / "tafsir" / book / f"{surah}.js"
	raw = path.read_text(encoding="utf-8")
	payload = json.loads(raw.split("=", 1)[1].rstrip().rstrip(";"))
	# critical-apparatus footnotes are the editor's, not the imam's
	return {int(k): re.sub(r"\[\[.*?\]\]", " ", v, flags=re.S) for k, v in payload.items()}


def blocks(entries):
	"""Group ayat whose commentary is one and the same stretch of prose."""
	grouped = {}
	for ayah, text in entries.items():
		grouped.setdefault(text, []).append(ayah)
	return [(sorted(ayat), len(text)) for text, ayat in grouped.items()]


def measure(book, surah, ayah):
	entries = load(book, surah)
	bl = blocks(entries)
	shares = sorted(((size / len(ayat), min(ayat)) for ayat, size in bl), reverse=True)
	average = sum(s for s, _ in shares) / len(shares)
	span, size = next((a, s) for a, s in bl if ayah in a)
	share = size / len(span)
	rank = [start for _, start in shares].index(min(span)) + 1
	return {
		"span": f"{min(span)}-{max(span)}" if len(span) > 1 else str(ayah),
		"chars": size,
		"ratio": share / average,
		"rank": rank,
		"of": len(shares),
		"grouped": sum(len(a) for a, _ in bl if len(a) > 1),
		"entries": len(entries),
	}


def main():
	surah = int(sys.argv[1]) if len(sys.argv) > 1 else 2
	if len(sys.argv) > 2:
		ayah = int(sys.argv[2])
		print(f"surah {surah}, ayah {ayah}")
		print(f"{'book':10} {'span':>9} {'chars':>7} {'ratio':>7} {'rank':>12} {'grouped':>9}")
		for book in BOOKS:
			m = measure(book, surah, ayah)
			print(
				f"{book:10} {m['span']:>9} {m['chars']:>7} {m['ratio']:>6.2f}x "
				f"{str(m['rank']) + '/' + str(m['of']):>12} {str(m['grouped']) + '/' + str(m['entries']):>9}"
			)
		return
	# no ayah given: list the verses this surah's imams dwell on most
	entries = load("saadi", surah)
	print(f"surah {surah}: where Saadi dwells (meaning, the reader's signal)")
	rows = []
	for ayah in sorted(entries):
		m = measure("saadi", surah, ayah)
		if m["ratio"] >= 1.6:
			rows.append((m["ratio"], ayah, m))
	for ratio, ayah, m in sorted(rows, reverse=True)[:25]:
		ik = measure("ibnkathir", surah, ayah)
		print(f"  {ayah:3}  saadi {ratio:5.2f}x ({m['rank']}/{m['of']})   ibnkathir {ik['ratio']:5.2f}x ({ik['rank']}/{ik['of']})")


if __name__ == "__main__":
	main()
