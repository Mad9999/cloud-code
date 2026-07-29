"""Bespoke «الآية تُضيء» scenes for Aal 'Imran's greatest verses. Each scene is an
AID: the design (graded ijtihadi) serves the fixed verse text; the meaning it
renders is sourced. Validation fails the build if a scene lacks a scene_key,
title, a sourced graded rationale, or hotspots with word/label/note, or if a
hotspot points outside the verse's word count (checked against the verified
morphology). Mirrors scenes_baqara.py for surah 3.
"""

import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SRC = BASE / "data" / "scenes_alimran.json"
MORPH = BASE / "data" / "quran-morphology.txt"
OUT = BASE / "app" / "generated" / "scenes_alimran.js"
GRADES = {"qati", "ma'thur", "ijtihadi"}


def word_counts(surah):
	"""Number of word-positions per verse of a surah, from the verified text."""
	counts = {}
	with open(MORPH, encoding="utf-8") as f:
		for line in f:
			if not line.strip() or "\t" not in line:
				continue
			loc = line.split("\t", 1)[0]
			parts = loc.split(":")
			if int(parts[0]) != surah:
				continue
			a, w = int(parts[1]), int(parts[2])
			counts[a] = max(counts.get(a, 0), w)
	return counts


def build():
	with open(SRC, encoding="utf-8") as f:
		data = json.load(f)
	surah = data["surah"]
	counts = word_counts(surah)

	for sc in data["verses"]:
		n = sc["n"]
		if n not in counts:
			raise SystemExit(f"scenes_alimran: verse {surah}:{n} not in morphology")
		for k in ("scene_key", "title", "design_rationale", "sources"):
			if not sc.get(k):
				raise SystemExit(f"scenes_alimran: {surah}:{n} missing '{k}'")
		if sc.get("grade") not in GRADES:
			raise SystemExit(f"scenes_alimran: {surah}:{n} bad grade {sc.get('grade')!r}")
		hs = sc.get("hotspots") or []
		if not hs:
			raise SystemExit(f"scenes_alimran: {surah}:{n} has no hotspots")
		for h in hs:
			if not h.get("label") or not h.get("note") or "word" not in h:
				raise SystemExit(f"scenes_alimran: {surah}:{n} hotspot missing word/label/note")
			if not (1 <= h["word"] <= counts[n]):
				raise SystemExit(f"scenes_alimran: {surah}:{n} hotspot word {h['word']} "
					f"out of range 1..{counts[n]}")

	OUT.parent.mkdir(parents=True, exist_ok=True)
	with open(OUT, "w", encoding="utf-8") as f:
		f.write("window.SCENES_ALIMRAN = ")
		json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
		f.write(";\n")
	print(f"scenes_alimran: {len(data['verses'])} scenes for surah {surah} "
		f"(all sourced & graded, hotspots in range) -> {OUT.name} ({OUT.stat().st_size} B)")


if __name__ == "__main__":
	build()
