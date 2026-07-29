"""The claim written into the stop at Ya-Sin 42.

A man writing a commentary on the whole Qur'an says of one verse that it is
among the hardest places for him. He then lays out the readings, rejects each
with a stated reason, declines to settle it, and writes «والله أعلم بحقيقة
الحال». Then something happens that he did not have to record and recorded
anyway: «فلما وصلت في الكتابة إلى هذا الموضع، ظهر لي معنى ليس ببعيد من مراد الله
تعالى». A meaning came to him in the act of writing, and he added it without
going back to delete the admission that had preceded it.

The stop rests on that being rare, so the rarity is measured here rather than
asserted: this is the only place in his commentary on the mushaf where he says a
place is difficult for himself. The two other hits for «أشكل» are about other
people, a student's difficulty at 75:19 and the deviants' at 3:7, and the test
holds that distinction so nobody later reads three where there is one.

It also holds the grade of his own suggestion, «ليس ببعيد», because the whole
value of the passage is that he marked his answer at its true strength instead
of promoting it once he had one.

Usage: python verify_ishkal_claim.py
"""

import json
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DIACRITICS = re.compile(r"[ً-ْٰـۖ-ۭٓ-ٟ]")


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


def tafsir(surah, ayah, book="saadi"):
	path = BASE / "app" / "tafsir" / book / f"{surah}.js"
	payload = json.loads(path.read_text(encoding="utf-8").split("=", 1)[1].rstrip().rstrip(";"))
	return strip_marks(re.sub(r"\[\[.*?\]\]", " ", payload[str(ayah)], flags=re.S))


THE_ADMISSION = "وهذا الموضع من أشكل المواضع علي في التفسير"

# He rejects each reading and says why, which is the part that makes the
# admission useful rather than merely humble.
THE_REASONS = [
	(
		"ردُّ قول من فسّر الذرّيّة بالآباء",
		"مما لا يعهد في القرآن إطلاق الذرية على الآباء، بل فيها من الإيهام، وإخراج الكلام "
		"عن موضوعه، ما يأباه كلام رب العالمين",
	),
	(
		"وردُّ الاحتمال الذي استحسنه هو",
		"ولكن ينقض هذا المعنى قوله: { وخلقنا لهم من مثله ما يركبون }",
	),
	("وعلّةُ الردّ", "فيكون ذلك تكريرا للمعنى، تأباه فصاحة القرآن"),
	("ووقوفُه", "والله أعلم بحقيقة الحال"),
]

# And then the thing that arrived while he was writing, graded as he graded it.
WHILE_WRITING = "فلما وصلت في الكتابة إلى هذا الموضع، ظهر لي معنى ليس ببعيد من مراد الله تعالى"

# The rarity. «أشكل» appears elsewhere in his tafsir but not about himself.
ELSEWHERE_NOT_HIS = [(3, 7, "وأشكل عليهم"), (75, 19, "عما أشكل عليه")]


def main():
	failures = []
	text = tafsir(36, 42)

	if normalize(THE_ADMISSION) not in normalize(text):
		failures.append("his admission of difficulty is not where we cite it")
	print("  OK: he says this is among the hardest places for him, in his own words")

	for label, phrase in THE_REASONS:
		if normalize(phrase) not in normalize(text):
			failures.append(f"his reasoning is incomplete ({label}): {phrase[:50]}")
	print(f"  OK: {len(THE_REASONS)} steps of rejecting each reading with a stated reason, and stopping")

	if normalize(WHILE_WRITING) not in normalize(text):
		failures.append(
			"the sentence about a meaning arriving while writing is gone, and it is the "
			"reason the stop exists"
		)
	if "ليس ببعيد" not in text:
		failures.append(
			"he graded his own suggestion «ليس ببعيد» and that grade has vanished. The stop's "
			"point is that he did not promote it once he had an answer."
		)
	print("  OK: the meaning that came while writing, kept at the strength he gave it")

	# the rarity, measured
	mine = []
	for path in sorted((BASE / "app" / "tafsir" / "saadi").glob("*.js")):
		surah = int(path.stem)
		payload = json.loads(path.read_text(encoding="utf-8").split("=", 1)[1].rstrip().rstrip(";"))
		for ayah, v in payload.items():
			flat = strip_marks(re.sub(r"\[\[.*?\]\]", " ", v, flags=re.S))
			if "أشكل المواضع علي" in flat or "من المشكل علي" in flat:
				mine.append((surah, int(ayah)))
	if mine != [(36, 42)]:
		failures.append(
			f"the stop says this is the only place he calls a verse hard for himself, and "
			f"the sweep now finds {mine}"
		)
	print(f"  OK: swept all 114 surahs; he says it of himself in exactly {len(mine)} place")

	# and that the other «أشكل» hits are about other people, not him
	for surah, ayah, phrase in ELSEWHERE_NOT_HIS:
		if phrase not in tafsir(surah, ayah):
			failures.append(
				f"the other «أشكل» at {surah}:{ayah} no longer reads «{phrase}», so the stop's "
				f"claim that those are about other people needs rechecking"
			)
	print("  OK: the other two «أشكل» in his tafsir are other people's difficulty, not his")

	if failures:
		print("\nCLAIM FAILED:", file=sys.stderr)
		for f in failures:
			print(f"  {f}", file=sys.stderr)
		sys.exit(1)
	print("\nYa-Sin 42 claim holds.")


if __name__ == "__main__":
	main()
