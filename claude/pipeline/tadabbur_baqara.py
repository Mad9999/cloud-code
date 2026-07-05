"""Progressive sourced contemplation of al-Baqara (286 ayat) — built passage by
passage, greatest first. Unlike the short surahs we do NOT cover every verse;
coverage is partial and HONESTLY declared (how many of 286). Every covered verse
must still carry a sourced, graded reflection. Not محاورة (that is al-Fatiha's).

Validation FAILS the build if a covered verse lacks a sourced graded reflection,
if a verse number falls outside 1..286, if passages overlap/duplicate a verse,
or if a passage's declared range disagrees with its verses.
"""

import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SRC = BASE / "data" / "tadabbur_baqara.json"
OUT = BASE / "app" / "generated" / "tadabbur_baqara.js"
GRADES = {"qati", "ma'thur", "ijtihadi"}
TOTAL = 286


def build():
	with open(SRC, encoding="utf-8") as f:
		data = json.load(f)
	if data.get("total_ayahs") != TOTAL:
		raise SystemExit(f"tadabbur_baqara: total_ayahs must be {TOTAL}")

	seen = set()
	covered = 0
	for pi, p in enumerate(data["passages"]):
		vs = p["verses"]
		nums = [v["n"] for v in vs]
		lo, hi = p["range"]
		if nums != list(range(lo, hi + 1)):
			raise SystemExit(f"tadabbur_baqara: passage #{pi} '{p.get('title')}' verses "
				f"{nums} do not match range {lo}..{hi}")
		for v in vs:
			n = v["n"]
			if not (1 <= n <= TOTAL):
				raise SystemExit(f"tadabbur_baqara: verse {n} out of range 1..{TOTAL}")
			if n in seen:
				raise SystemExit(f"tadabbur_baqara: verse {n} covered twice")
			seen.add(n)
			ref = v.get("reflection") or {}
			if not ref.get("text") or not ref.get("source"):
				raise SystemExit(f"tadabbur_baqara: 2:{n} reflection missing text/source")
			if ref.get("grade") not in GRADES:
				raise SystemExit(f"tadabbur_baqara: 2:{n} bad grade {ref.get('grade')!r}")
			if not (v.get("heart_state") or {}).get("text") or not (v.get("action") or {}).get("text"):
				raise SystemExit(f"tadabbur_baqara: 2:{n} missing heart_state/action")
			covered += 1
		blk = p.get("fadl")
		if blk and (not blk.get("source") or blk.get("grade") not in GRADES):
			raise SystemExit(f"tadabbur_baqara: passage #{pi} fadl missing source/grade")

	data["coverage"] = {"covered": covered, "total": TOTAL}
	OUT.parent.mkdir(parents=True, exist_ok=True)
	with open(OUT, "w", encoding="utf-8") as f:
		f.write("window.TADABBUR_BAQARA = ")
		json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
		f.write(";\n")
	print(f"tadabbur_baqara: {len(data['passages'])} passages, {covered}/{TOTAL} ayat covered "
		f"(all sourced & graded) -> {OUT.name} ({OUT.stat().st_size} B)")


if __name__ == "__main__":
	build()
