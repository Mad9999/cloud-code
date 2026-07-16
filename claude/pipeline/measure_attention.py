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


def covered_by(entries, ayah):
	"""An empty entry is not silence: find the verse whose text speaks for it.

	Saadi has 60 empty entries across the mushaf and Qurtubi two. They are not
	gaps in the corpus. Saadi comments on a run of verses under one heading and
	the extraction keys the prose to the first of them, so 2:286 is empty while
	2:285 carries 1,917 characters that run through both and close with «تم
	تفسير سورة البقرة». Left alone, this tool would have reported Saadi at
	0.00x, last of 272, on the final verse of al-Baqara, and rule 33 would have
	read that as 'he passes over it, so write nothing'. He does not pass over
	it. He ends the surah there.
	"""
	for n in range(ayah - 1, 0, -1):
		if entries.get(n, "").strip():
			return n
	return None


def measure(book, surah, ayah):
	"""Two readings, because they answer two questions.

	'ratio' and 'rank' divide a block by the verses it covers, which is what
	'does this verse ask for something' means. 'bulk' is the block whole, which
	is what 'does this subject weigh' means, and the two come apart: Qurtubi's
	riba block at 2:275-279 is 58,131 characters, his second largest in the
	surah, and yet only 1.17x per verse because it is spread over five. Reading
	only the share would have said the subject is ordinary. It is not.
	"""
	entries = load(book, surah)
	speaks_for = None
	if not entries.get(ayah, "").strip():
		speaks_for = covered_by(entries, ayah)
		if speaks_for is None:
			return {"span": str(ayah), "chars": 0, "ratio": 0.0, "rank": 0, "bulk_rank": 0,
				"of": 0, "grouped": 0, "entries": len(entries), "covered_by": None}
		ayah = speaks_for
	bl = [(a, s) for a, s in blocks(entries) if s > 0]
	shares = sorted(((size / len(ayat), min(ayat)) for ayat, size in bl), reverse=True)
	average = sum(s for s, _ in shares) / len(shares)
	bulks = sorted(((size, min(ayat)) for ayat, size in bl), reverse=True)
	span, size = next((a, s) for a, s in bl if ayah in a)
	share = size / len(span)
	return {
		"span": f"{min(span)}-{max(span)}" if len(span) > 1 else str(ayah),
		"chars": size,
		"ratio": share / average,
		"rank": [start for _, start in shares].index(min(span)) + 1,
		"bulk_rank": [start for _, start in bulks].index(min(span)) + 1,
		"of": len(shares),
		"grouped": sum(len(a) for a, _ in bl if len(a) > 1),
		"entries": len(entries),
		"covered_by": speaks_for,
	}


def main():
	surah = int(sys.argv[1]) if len(sys.argv) > 1 else 2
	if len(sys.argv) > 2:
		ayah = int(sys.argv[2])
		print(f"surah {surah}, ayah {ayah}")
		print(
			f"{'book':10} {'span':>9} {'chars':>7} {'ratio':>7} {'rank':>10} {'bulk':>10} {'grouped':>9}"
		)
		for book in BOOKS:
			m = measure(book, surah, ayah)
			note = f"  (empty here; spoken for by {m['covered_by']})" if m["covered_by"] else ""
			print(
				f"{book:10} {m['span']:>9} {m['chars']:>7} {m['ratio']:>6.2f}x "
				f"{str(m['rank']) + '/' + str(m['of']):>10} "
				f"{str(m['bulk_rank']) + '/' + str(m['of']):>10} "
				f"{str(m['grouped']) + '/' + str(m['entries']):>9}{note}"
			)
		print("  ratio/rank: does this verse ask.  bulk: does this subject weigh.")
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
