"""Adam-narrative valve: machine-check the claim we make in the tadabbur of
al-Baqara 36 — that the Qur'an never names Hawwa and never casts her as the
tempter; the tempter is always ash-Shaytan, and the two are addressed as a
pair throughout.

This is a claim ABOUT THE QUR'ANIC TEXT (qat'i), not about the tafsir
literature (some of which relays isra'iliyyat). It is stated in the product,
so it must fail loudly if it ever stops being true of the text we ship.

Usage: PYTHONUTF8=1 python verify_adam_claim.py
"""

import json
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
GEN = BASE / "app" / "generated"

DIACRITICS = re.compile(r"[ً-ْٰۖ-ۭ]")


def normalize(s):
	s = DIACRITICS.sub("", s)
	return re.sub(r"[آأإٱ]", "ا", s)


def load_quran():
	raw = (GEN / "quran_text.js").read_text(encoding="utf-8")
	payload = json.loads(raw.split("=", 1)[1].rstrip().rstrip(";"))
	return {k: normalize(v) for k, v in payload.items()}


def fail(msg):
	print(f"ADAM-CLAIM FAILED: {msg}", file=sys.stderr)
	sys.exit(1)


def main():
	q = load_quran()

	# 1. Hawwa is never named anywhere in the Qur'an.
	named = [k for k, v in q.items() if re.search(r"(^| )حواء( |$)|(^| )حوا( |$)", v)]
	if named:
		fail(f"Hawwa is named after all, at {named} — the claim must be retracted")
	print("  OK: Hawwa is never named in the Qur'an (0 occurrences)")

	# 2. Every 'waswasa' in the Adam narrative has ash-Shaytan as its subject.
	adam_waswasa = {"7:20": "لهما", "20:120": "إليه"}
	for ref, particle in adam_waswasa.items():
		v = q[ref]
		if "وسوس" not in v:
			fail(f"{ref}: expected a waswasa verb")
		if "الشيطان" not in v:
			fail(f"{ref}: the tempter is not named ash-Shaytan")
		if normalize(particle) not in v:
			fail(f"{ref}: expected the address particle {particle}")
	# and no other verse in the whole Qur'an puts the temptation on her
	for ref, v in q.items():
		if "وسوس" in v and ref not in adam_waswasa:
			# 50:16 (one's own soul) and 114:5 (the whisperer) — never Hawwa
			if "زوج" in v or "امراة" in v:
				fail(f"{ref}: a waswasa verse involves the wife — re-examine")
	print("  OK: in every Adam-story waswasa verse the subject is ash-Shaytan")

	# 3. The pair is addressed as a pair: dual forms carry the whole episode.
	duals = {
		"2:35": ["اسكن انت وزوجك", "وكلا منها", "ولا تقربا", "فتكونا"],
		"2:36": ["فازلهما الشيطان", "فاخرجهما"],
		"7:20": ["فوسوس لهما الشيطان"],
		"7:21": ["وقاسمهما"],
		"7:22": ["فدلاهما بغرور", "فلما ذاقا الشجرة", "الم انهكما", "واقل لكما"],
		"7:23": ["قالا ربنا ظلمنا انفسنا"],
		"20:121": ["فاكلا منها"],
	}
	for ref, phrases in duals.items():
		for p in phrases:
			if normalize(p) not in q[ref]:
				fail(f"{ref}: expected the dual phrase '{p}'")
	print(f"  OK: dual address verified across {len(duals)} verses")

	# 4. Where the singular appears, it points at Adam — not at her.
	if "فوسوس اليه الشيطان" not in q["20:120"] or "يا ادم" not in q["20:120"]:
		fail("20:120: expected Satan to approach Adam directly, by name")
	if "وعصى ادم ربه" not in q["20:121"]:
		fail("20:121: expected Adam to be the one named as disobeying")
	print("  OK: the singular in Ta-Ha names Adam (approached, and disobeying)")

	print("\nالخلاصة المتحقَّقة: الموسوِس في القرآن هو الشيطان دائمًا، والخطاب مثنّى،")
	print("واسم حواء لا يُذكر البتة، والمفرد حين ورد فهو لآدم لا لها.")


if __name__ == "__main__":
	main()
