"""Harun valve: machine-check the claim we make in the tadabbur of al-Baqara 51 —
that the Qur'an never lays the making of the calf on Harun, names as-Samiri as
its maker, and casts Harun as the one who forbade it.

This is a claim ABOUT THE QURANIC TEXT (qat'i). It defends a prophet against an
accusation carried in another scripture, so it must fail loudly if it ever
stops being true of the mushaf we ship.

Usage: PYTHONUTF8=1 python verify_harun_claim.py
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
	print(f"HARUN-CLAIM FAILED: {msg}", file=sys.stderr)
	sys.exit(1)


def main():
	q = load_quran()

	# 1. "Harun" and "the calf" never meet in a single verse.
	together = [k for k, v in q.items() if "هارون" in v and "عجل" in v]
	if together:
		fail(f"Harun and the calf share verse(s) {together} — retract the claim")
	print("  OK: Harun and the calf never occur in the same verse (0)")

	# 2. The calf's maker is named, and the name is as-Samiri.
	if "السامري" not in q["20:85"]:
		fail("20:85: expected as-Samiri named as the one who misled them")
	if "السامري" not in q["20:87"]:
		fail("20:87: expected as-Samiri named as the one who cast it")
	print("  OK: the maker is named — as-Samiri (20:85, 20:87)")

	# 3. Harun is the one who forbade it, in the Qur'an's own words.
	v = q["20:90"]
	for phrase in ["ولقد قال لهم هارون من قبل", "يا قوم انما فتنتم به", "فاتبعوني واطيعوا امري"]:
		if normalize(phrase) not in v:
			fail(f"20:90: expected Harun's rebuke '{phrase}'")
	print("  OK: 20:90 has Harun forbidding them before Musa's return")

	# 4. Harun's own plea: he was overpowered, not complicit.
	if "ان القوم استضعفوني" not in q["7:150"]:
		fail("7:150: expected Harun's plea that the people overpowered him")
	if "اني خشيت ان تقول فرقت بين بني اسرائيل" not in q["20:94"]:
		fail("20:94: expected Harun's reason for not fighting them")
	print("  OK: Harun's plea is preserved (7:150, 20:94)")

	print("\nالخلاصة المتحقَّقة: صانعُ العجل في القرآن هو السامريُّ باسمه،")
	print("وهارونُ هو الذي نهى عنه وقال «يا قوم إنما فتنتم به» — واسمُه لا يجتمع")
	print("مع العجل في آيةٍ واحدةٍ قط.")


if __name__ == "__main__":
	main()
