"""Sourced contemplation (تدبّر) for the short worship surahs — al-Ikhlas,
al-Falaq, al-Nas, al-'Asr, al-Kawthar. This is deliberately NOT «محاورة»: the
per-verse divine response belongs to al-Fatiha alone (Muslim 395), so we never
manufacture one for these surahs. Each verse carries a sourced, graded
reflection; the Quranic text itself is taken at runtime from the verified
morphology data, not re-transcribed here (no chance of a copy error).

Validation FAILS the build if any verse lacks a reflection with a source and a
grade, if a surah's verse count disagrees with the verified text, or if a grade
is outside the allowed set — nothing worship-facing ships unsourced.
"""

import json
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SRC = BASE / "data" / "tadabbur_short.json"
MORPH = BASE / "data" / "quran-morphology.txt"
OUT = BASE / "app" / "generated" / "tadabbur_short.js"
GRADES = {"qati", "ma'thur", "ijtihadi"}


def verse_counts():
	"""Authoritative ayah count per surah from the verified morphology file."""
	counts = {}
	with open(MORPH, encoding="utf-8") as f:
		for line in f:
			if not line.strip() or "\t" not in line:
				continue
			loc = line.split("\t", 1)[0]
			s, a = loc.split(":")[:2]
			counts[int(s)] = max(counts.get(int(s), 0), int(a))
	return counts


def build():
	with open(SRC, encoding="utf-8") as f:
		data = json.load(f)
	counts = verse_counts()

	for su in data["surahs"]:
		n = su["n"]
		vs = su["verses"]
		if n not in counts:
			raise SystemExit(f"tadabbur_short: surah {n} not found in morphology")
		if len(vs) != counts[n]:
			raise SystemExit(f"tadabbur_short: surah {n} has {len(vs)} verses, "
				f"verified text has {counts[n]}")
		seen = set()
		for v in vs:
			seen.add(v["n"])
			ref = v.get("reflection") or {}
			if not ref.get("text") or not ref.get("source"):
				raise SystemExit(f"tadabbur_short: {n}:{v['n']} reflection missing text/source")
			if ref.get("grade") not in GRADES:
				raise SystemExit(f"tadabbur_short: {n}:{v['n']} bad grade {ref.get('grade')!r}")
			if not (v.get("heart_state") or {}).get("text") or not (v.get("action") or {}).get("text"):
				raise SystemExit(f"tadabbur_short: {n}:{v['n']} missing heart_state/action")
		if seen != set(range(1, counts[n] + 1)):
			raise SystemExit(f"tadabbur_short: surah {n} verse numbers not 1..{counts[n]}")
		# surah-level sourced blocks, if present, must carry source + grade
		for key in ("fadl", "sabab"):
			blk = su.get(key)
			if blk and (not blk.get("source") or blk.get("grade") not in GRADES):
				raise SystemExit(f"tadabbur_short: surah {n} {key} missing source/grade")

	OUT.parent.mkdir(parents=True, exist_ok=True)
	with open(OUT, "w", encoding="utf-8") as f:
		f.write("window.TADABBUR_SHORT = ")
		json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
		f.write(";\n")
	total = sum(len(su["verses"]) for su in data["surahs"])
	print(f"tadabbur_short: {len(data['surahs'])} surahs, {total} verses (all sourced & graded) "
		f"-> {OUT.name} ({OUT.stat().st_size} B)")


if __name__ == "__main__":
	build()
