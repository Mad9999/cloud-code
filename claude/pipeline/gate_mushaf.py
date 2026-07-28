"""The need-gate, run across the whole mushaf instead of one surah at a time.

Rule 33 says the verse asks and the template is not imposed, and that the
question is settled by measurement. Measuring one surah at a time was fine while
we worked one surah at a time. Finishing the Book means knowing, before starting
any surah, where in it the imams stopped and where they walked on.

The signal is Saadi's share, per the third tanbih under rule 33: Qurtubi is the
imam of rulings and Saadi the imam of meanings, and our reader wants the light
rather than the branches, so Saadi's ratio is the truer pointer for us. Qurtubi
and Ibn Kathir and Tabari are printed alongside because the shape of the four
together names the kind of verse before you read a word of it:

  meaning stops, rulings walk on      -> a verse that teaches a way (2:177)
  meanings and rulings both stop      -> asked from both sides, and rare (2:282)
  narration stops, the rest walk on   -> reports to be weighed (2:255)

The gate only points. It never decides. What it opens still has to be read, and
most of what it opens will still be «لا شيء», which is the expected answer and
not a failure of the pass.

Usage:
  python gate_mushaf.py            summary for every surah
  python gate_mushaf.py 18         the open verses of one surah
  python gate_mushaf.py --top 40   the strongest calls in the whole mushaf
"""

import json
import re
import sys
from pathlib import Path

from measure_attention import measure, load

DIACRITICS = re.compile(r"[ً-ْٰـۖ-ۭٓ-ٟ]")
FASL = re.compile(r"فصل\s*(في|فيما)")
FAIDA = re.compile(r"ومنها:")


def strip_marks(s):
	return DIACRITICS.sub("", s)

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "data"

# A verse is "open" when the imam of meanings dwells on it well past his own
# average for that surah. The rank cut keeps long surahs from flooding the list
# purely because they have more verses to be above average in.
RATIO_CUT = 2.0
RANK_CUT = 12


def surah_names():
	raw = (BASE / "app" / "generated" / "quran_text.js").read_text(encoding="utf-8")
	payload = json.loads(raw.split("=", 1)[1].rstrip().rstrip(";"))
	counts = {}
	for key in payload:
		s = int(key.split(":")[0])
		counts[s] = counts.get(s, 0) + 1
	return counts


def already_has(surah):
	"""Verses in this surah that already carry something above their stop."""
	out = set()
	for f in DATA.glob("*.json"):
		try:
			doc = json.loads(f.read_text(encoding="utf-8"))
		except ValueError:
			continue
		if doc.get("n") != surah:
			continue
		for passage in doc.get("passages", []):
			for v in passage.get("verses", []):
				extra = set(v) - {"n", "reflection", "names", "heart_state", "action"}
				if extra:
					out.add(v["n"])
	return out


def open_verses(surah, counts):
	entries = load("saadi", surah)
	if not entries:
		return []
	done = already_has(surah)
	rows = []
	for ayah in range(1, counts[surah] + 1):
		if ayah in done:
			continue
		try:
			s = measure("saadi", surah, ayah)
		except (KeyError, StopIteration):
			continue
		if s["ratio"] < RATIO_CUT or s["rank"] > RANK_CUT:
			continue
		try:
			q = measure("qurtubi", surah, ayah)
			k = measure("ibnkathir", surah, ayah)
			t = measure("tabari", surah, ayah)
		except (KeyError, StopIteration):
			continue
		shape = "مختلط"
		# Sixteen entries in the whole mushaf, 0.3%, are where Saadi appends his
		# own synthesis of a passage to its last verse: a «فصل في...» or a run of
		# «ومنها». Reading those as a heavy verse is the wrong reading; they are
		# a heavy passage, and this is where the imam says what it came for. The
		# Khidr story ends in thirty-seven of them, more than the debt verse.
		body = strip_marks(entries.get(ayah, "") or entries.get(s.get("covered_by") or ayah, ""))
		if FASL.search(body) or len(FAIDA.findall(body)) >= 6:
			shape = "خلاصةُ الإمام للمقطع"
		elif s["ratio"] >= 2.0 and q["ratio"] < 1.5 and k["ratio"] < 1.5:
			shape = "معنًى خالص"
		elif s["rank"] <= 5 and q["rank"] <= 12:
			shape = "من الجهتين"
		elif k["rank"] <= 6 and s["rank"] > 8:
			shape = "رواية"
		elif q["rank"] <= 8 and s["ratio"] < 1.6:
			shape = "أحكام"
		rows.append((surah, ayah, s, q, k, t, shape))
	return rows


def main():
	counts = surah_names()
	args = sys.argv[1:]

	if args and args[0] == "--top":
		limit = int(args[1]) if len(args) > 1 else 40
		everything = []
		for surah in range(1, 115):
			everything.extend(open_verses(surah, counts))
		everything.sort(key=lambda r: -r[2]["ratio"])
		print(f"the {limit} loudest calls in the mushaf, by Saadi's share")
		print(f"{'ref':>9} {'saadi':>16} {'qurtubi':>8} {'ibnk':>8} {'tabari':>8}  shape")
		for surah, ayah, s, q, k, t, shape in everything[:limit]:
			rank = f"{s['rank']}/{s['of']}"
			print(
				f"{surah:>4}:{ayah:<4} {s['ratio']:>6.2f}x {rank:>8} {q['ratio']:>7.2f}x "
				f"{k['ratio']:>7.2f}x {t['ratio']:>7.2f}x  {shape}"
			)
		print(f"\n{len(everything)} open verses across the mushaf")
		return

	if args:
		surah = int(args[0])
		rows = open_verses(surah, counts)
		print(f"surah {surah}: {len(rows)} open of {counts[surah]}")
		for _, ayah, s, q, k, t, shape in rows:
			print(
				f"  {ayah:>3} saadi {s['ratio']:>5.2f}x ({s['rank']}/{s['of']})  "
				f"qurtubi {q['ratio']:>5.2f}x  ibnk {k['ratio']:>5.2f}x  "
				f"tabari {t['ratio']:>5.2f}x  {shape}"
			)
		return

	print(f"{'surah':>6} {'ayat':>5} {'open':>5}  loudest")
	total = 0
	for surah in range(1, 115):
		rows = open_verses(surah, counts)
		total += len(rows)
		if not rows:
			continue
		best = max(rows, key=lambda r: r[2]["ratio"])
		print(
			f"{surah:>6} {counts[surah]:>5} {len(rows):>5}  "
			f"{surah}:{best[1]} at {best[2]['ratio']:.2f}x ({best[6]})"
		)
	print(f"\n{total} open verses across the mushaf")


if __name__ == "__main__":
	main()
