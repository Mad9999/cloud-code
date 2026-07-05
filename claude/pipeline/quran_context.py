"""Sourced context library (مكتبة المصادر المُسنَدة) — the trusted classical
references for the Qur'an's stories, occasions of revelation, history, and
tafsir-by-narration. We do NOT summarise these works (that would be putting our
words in their mouths); we catalogue and cite them, so the reader goes to the
source. Every entry is a heritage work in the public domain, graded and
honestly attributed (disputed death-years flagged, not hidden).

Validation FAILS the build on any entry missing an author, death year, a known
category, coverage text, a tier, or a reading pointer — nothing ships unsourced.
"""

import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SRC = BASE / "data" / "quran_context_sources.json"
OUT = BASE / "app" / "generated" / "quran_context.js"

REQUIRED = ("title", "author", "death_h", "death_g", "category", "coverage", "tier", "read_at")


def build():
	with open(SRC, encoding="utf-8") as f:
		data = json.load(f)

	cats = {c[0] for c in data["categories"]}
	if not cats:
		raise SystemExit("quran_context: no categories defined")

	books = data["books"]
	if not books:
		raise SystemExit("quran_context: no books")

	for i, b in enumerate(books):
		for k in REQUIRED:
			if not b.get(k):
				raise SystemExit(f"quran_context: book #{i} '{b.get('title', '?')}' missing '{k}'")
		if b["category"] not in cats:
			raise SystemExit(f"quran_context: book '{b['title']}' has unknown category '{b['category']}'")
		if not isinstance(b["read_at"], list) or not b["read_at"]:
			raise SystemExit(f"quran_context: book '{b['title']}' has empty read_at")
		if b["tier"] != "public_domain":
			# this curated library is heritage-only by design; guard the invariant
			raise SystemExit(f"quran_context: book '{b['title']}' tier '{b['tier']}' — expected public_domain")

	# per-category counts (for display) and integrity summary
	counts = {}
	for b in books:
		counts[b["category"]] = counts.get(b["category"], 0) + 1
	linked = sum(1 for b in books if b.get("link"))

	payload = {
		"meta": data["_meta"],
		"categories": data["categories"],
		"books": books,
		"counts": counts,
	}
	OUT.parent.mkdir(parents=True, exist_ok=True)
	with open(OUT, "w", encoding="utf-8") as f:
		f.write("window.QURAN_CONTEXT = ")
		json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))
		f.write(";\n")
	print(f"quran_context: {len(books)} sourced works across {len(cats)} categories "
		f"({linked} with verified direct links) -> {OUT.name} ({OUT.stat().st_size} B)")
	return payload


if __name__ == "__main__":
	build()
