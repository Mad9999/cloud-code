"""Ibn Kathir counted the mushaf by memory and got it right. We did not.

On «الم» at the head of al-Baqara he makes a claim, and he does not leave it as
taste. He grounds it: «وهذا معلوم بالاستقراء، وهو الواقع في تسع وعشرين سورة».
Survey, count, number, then the enumerated examples.

We checked his 29 with a machine and got it wrong twice before we got it right.
The first question was too tight (the verse must BE the letters) and returned 19,
missing «الر تلك آيات الكتاب». The second was too loose (the verse begins with
them) and returned 40, catching «يسألونك» and «قل» and «الرحمن». Only the third
question, the letters standing as their own word in the rasm, returns 29.

So the tool answered every question correctly and the questions were wrong, which
is today's error a sixth time and its worst face: the wrong question never shows
up in the output. It returns a clean number, and the number is a lie about a
different question than the one you meant.

All three counts are kept here, because the two failures are the point of the
file, and a later reader who sees only 29 learns nothing.

Usage: python verify_istiqra_claim.py
"""

import json
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DIACRITICS = re.compile(r"[ً-ْٰـۖ-ۭٓ-ٟ]")

# The disconnected letters as they stand at the head of a surah.
SETS = {"الم", "المص", "المر", "الر", "كهيعص", "طه", "طسم", "طس", "يس", "ص", "حم", "عسق", "ق", "ن"}

IBN_KATHIR_SAID = 29
HIS_WORDS = "وهذا معلوم بالاستقراء، وهو الواقع في تسع وعشرين سورة"
HIS_CLAIM = (
	"ولهذا كل سورة افتتحت بالحروف فلا بد أن يذكر فيها الانتصار للقرآن وبيان إعجازه وعظمته"
)


def strip_marks(s):
	return DIACRITICS.sub("", s)


def normalize(s):
	s = DIACRITICS.sub("", s)
	s = re.sub(r"[آأإٱ]", "ا", s)
	s = s.replace("ى", "ي")
	s = re.sub(r"[ءؤئ]", "", s)
	s = s.replace("ة", "ت")
	s = re.sub(r"[^ء-ي ]", " ", s)
	s = re.sub(r"وا\b", "و", s)
	return re.sub(r" +", " ", s).strip().replace(" ", "")


def quran():
	raw = (BASE / "app" / "generated" / "quran_text.js").read_text(encoding="utf-8")
	return json.loads(raw.split("=", 1)[1].rstrip().rstrip(";"))


def openers(q):
	return {s: strip_marks(q[f"{s}:1"]).strip() for s in range(1, 115)}


def count_too_tight(q):
	"""The verse must be the letters and nothing else. Loses «الر تلك آيات»."""
	return [s for s, v in openers(q).items() if v.replace(" ", "") in {x for x in SETS}]


def count_too_loose(q):
	"""The verse begins with the letters. Catches «يسألونك», «قل», «الرحمن»."""
	hits = []
	for s, v in openers(q).items():
		flat = v.replace(" ", "")
		if any(flat.startswith(x) for x in SETS):
			hits.append(s)
	return hits


def count_right(q):
	"""The letters stand as their own word in the rasm."""
	return [s for s, v in openers(q).items() if v.split() and v.split()[0] in SETS]


def main():
	q = quran()
	failures = []

	right = count_right(q)
	if len(right) != IBN_KATHIR_SAID:
		failures.append(
			f"we now count {len(right)} surahs opening with the letters; Ibn Kathir said "
			f"{IBN_KATHIR_SAID}. One of us has changed, and it is not him."
		)
	print(f"  OK: {len(right)} surahs open with the disconnected letters, which is his number")

	tight, loose = len(count_too_tight(q)), len(count_too_loose(q))
	if tight >= len(right) or loose <= len(right):
		failures.append(
			f"the two wrong questions no longer bracket the right one ({tight}, {loose} vs "
			f"{len(right)}), so this file has stopped teaching what it was written to teach"
		)
	print(f"  OK: the tight question still gives {tight}, the loose one {loose}, the right one {len(right)}")

	raw = (BASE / "app" / "tafsir" / "ibnkathir" / "2.js").read_text(encoding="utf-8")
	payload = json.loads(raw.split("=", 1)[1].rstrip().rstrip(";"))
	text = normalize(re.sub(r"\[\[.*?\]\]", " ", payload["1"], flags=re.S))
	for phrase in (HIS_WORDS, HIS_CLAIM):
		if normalize(phrase) not in text:
			failures.append(f"Ibn Kathir's words are not where we cite them: {phrase}")
	print("  OK: he states the claim and grounds it in istiqra' with the count, verbatim")

	if failures:
		print("\nCLAIM FAILED:", file=sys.stderr)
		for f in failures:
			print(f"  {f}", file=sys.stderr)
		sys.exit(1)
	print("\nIbn Kathir's istiqra' holds, and it took us three questions to see it.")


if __name__ == "__main__":
	main()
