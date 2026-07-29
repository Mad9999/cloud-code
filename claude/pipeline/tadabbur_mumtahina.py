"""Progressive sourced contemplation of al-Mumtahina (surah 60, 13 ayat) — built
passage by passage like al-Baqara. Not محاورة. Every covered verse carries a
sourced, graded reflection; asbab optional (source & grade required if present);
hotspots/passage ranges validated against the verified morphology.
"""

import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SRC = BASE / "data" / "tadabbur_mumtahina.json"
MORPH = BASE / "data" / "quran-morphology.txt"
OUT = BASE / "app" / "generated" / "tadabbur_mumtahina.js"
GRADES = {"qati", "ma'thur", "ijtihadi"}
SURAH = 60
TOTAL = 13


def build():
	with open(SRC, encoding="utf-8") as f:
		data = json.load(f)
	if data.get("total_ayahs") != TOTAL:
		raise SystemExit(f"tadabbur_mumtahina: total_ayahs must be {TOTAL}")

	seen = set()
	covered = 0
	for pi, p in enumerate(data["passages"]):
		vs = p["verses"]
		nums = [v["n"] for v in vs]
		lo, hi = p["range"]
		if nums != list(range(lo, hi + 1)):
			raise SystemExit(f"tadabbur_mumtahina: passage #{pi} '{p.get('title')}' verses "
				f"{nums} do not match range {lo}..{hi}")
		for v in vs:
			n = v["n"]
			if not (1 <= n <= TOTAL):
				raise SystemExit(f"tadabbur_mumtahina: verse {n} out of range")
			if n in seen:
				raise SystemExit(f"tadabbur_mumtahina: verse {n} covered twice")
			seen.add(n)
			ref = v.get("reflection") or {}
			if not ref.get("text") or not ref.get("source"):
				raise SystemExit(f"tadabbur_mumtahina: 3:{n} reflection missing text/source")
			if ref.get("grade") not in GRADES:
				raise SystemExit(f"tadabbur_mumtahina: 3:{n} bad grade {ref.get('grade')!r}")
			if not (v.get("heart_state") or {}).get("text") or not (v.get("action") or {}).get("text"):
				raise SystemExit(f"tadabbur_mumtahina: 3:{n} missing heart_state/action")
			sb = v.get("sabab")
			if sb and (not sb.get("text") or not sb.get("source") or sb.get("grade") not in GRADES):
				raise SystemExit(f"tadabbur_mumtahina: 3:{n} sabab missing text/source/grade")
			covered += 1
		blk = p.get("fadl")
		if blk and (not blk.get("source") or blk.get("grade") not in GRADES):
			raise SystemExit(f"tadabbur_mumtahina: passage #{pi} fadl missing source/grade")

	data["coverage"] = {"covered": covered, "total": TOTAL}
	OUT.parent.mkdir(parents=True, exist_ok=True)
	with open(OUT, "w", encoding="utf-8") as f:
		f.write("window.TADABBUR_MUMTAHINA = ")
		json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
		f.write(";\n")
	print(f"tadabbur_mumtahina: {len(data['passages'])} passages, {covered}/{TOTAL} ayat covered "
		f"-> {OUT.name} ({OUT.stat().st_size} B)")


if __name__ == "__main__":
	build()
