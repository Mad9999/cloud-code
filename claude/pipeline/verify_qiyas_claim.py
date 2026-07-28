"""The claim written into the stop at az-Zumar 3.

At 2:165 we wrote a note on Saadi's word that the mushrik does not dispute who
creates and provides, and only levels others with God in worship. That was one
imam in one place, and the note said so.

Here the Qur'an says it in their own mouths: «ما نعبدهم إلا ليقربونا إلى الله
زلفى». They are not claiming their gods make or sustain anything. They are
claiming access. So the note at 2:165 now has the verse behind it, and this stop
records that.

What Saadi adds is the diagnosis. Shirk is not a failure to notice God. It is an
analogy: «وقاسوا الذي ليس كمثله شيء، الملك العظيم، بالملوك». And he does not
leave the analogy to be felt, he breaks it in four places, naming for each why a
king needs an intermediary and God does not. This file holds all four, because
an argument summarised loses exactly the thing that made it an argument.

And the conclusion that follows, which is the answer to a question people ask
without expecting an answer, why shirk alone is unforgiven: «لأنه يتضمن القدح في
الله تعالى».

Usage: python verify_qiyas_claim.py
"""

import json
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DIACRITICS = re.compile(r"[ً-ْٰـۖ-ۭٓ-ٟ]")


def normalize(s):
	s = DIACRITICS.sub("", s)
	s = re.sub(r"[آأإٱ]", "ا", s)
	s = s.replace("ى", "ي")
	s = re.sub(r"[ءؤئ]", "", s)
	s = s.replace("ة", "ت")
	s = re.sub(r"[^ء-ي ]", " ", s)
	s = re.sub(r"وا\b", "و", s)
	return re.sub(r" +", " ", s).strip().replace(" ", "")


def tafsir(book, surah, ayah):
	path = BASE / "app" / "tafsir" / book / f"{surah}.js"
	payload = json.loads(path.read_text(encoding="utf-8").split("=", 1)[1].rstrip().rstrip(";"))
	return normalize(re.sub(r"\[\[.*?\]\]", " ", payload[str(ayah)], flags=re.S))


def quran():
	raw = (BASE / "app" / "generated" / "quran_text.js").read_text(encoding="utf-8")
	return json.loads(raw.split("=", 1)[1].rstrip().rstrip(";"))


# What they say for themselves, and Saadi's reading of what it concedes.
THEIR_PLEA = "ما نعبدهم إلا ليقربونا إلى الله زلفى"
WHAT_IT_CONCEDES = (
	"أي: لترفع حوائجنا لله، وتشفع لنا عنده، وإلا، فنحن نعلم أنها، لا تخلق، ولا ترزق، "
	"ولا تملك من الأمر شيئا"
)

# The analogy, and its verdict.
THE_ANALOGY = "وقاسوا الذي ليس كمثله شيء، الملك العظيم، بالملوك"
THE_VERDICT = "وهذا القياس من أفسد الأقيسة، وهو يتضمن التسوية بين الخالق والمخلوق"

# Four reasons a king needs a broker, each paired with why God does not. The
# pairing is the argument; a stop that kept only the conclusion would be
# reporting that Saadi disagreed, not why.
THE_FOUR = [
	(
		"العلم",
		"فإن الملوك، إنما احتاجوا للوساطة بينهم وبين رعاياهم، لأنهم لا يعلمون أحوالهم",
		"الذي لا يحتاج من يخبره بأحوال رعيته وعباده",
	),
	(
		"الرحمة",
		"وربما لا يكون في قلوبهم رحمة لصاحب الحاجة",
		"بل هو أرحم بهم من أنفسهم ووالديهم",
	),
	(
		"الخوف",
		"ويحتاجون إلى الشفعاء والوزراء، ويخافون منهم",
		"وجميع الشفعاء يخافونه، فلا يشفع منهم أحد إلا بإذنه، وله الشفاعة كلها",
	),
	(
		"الغنى",
		"وهم أيضا فقراء، قد يمنعون لما يخشون من الفقر",
		"لم ينقصوا من غناه شيئا، ولم ينقصوا مما عنده، إلا كما ينقص البحر إذا غمس فيه المخيط",
	),
]

WHY_UNFORGIVEN = (
	"ويعلم أيضا الحكمة في كون الشرك لا يغفره الله تعالى، لأنه يتضمن القدح في الله تعالى"
)

# The note at 2:165 that this verse now stands behind.
NOTE_AT_2_165 = "لا يسوونهم بالله في الخلق والرزق والتدبير, وإنما يسوونهم به في العبادة"


def main():
	failures = []
	sa = tafsir("saadi", 39, 3)

	if normalize(THEIR_PLEA) not in normalize(quran()["39:3"]):
		failures.append("the verse no longer quotes them saying it, which is the stop's spine")
	if normalize(WHAT_IT_CONCEDES) not in sa:
		failures.append("Saadi's reading of what their plea concedes is missing")
	print("  OK: the Qur'an quotes their own plea, and Saadi reads what it concedes")

	for phrase in (THE_ANALOGY, THE_VERDICT):
		if normalize(phrase) not in sa:
			failures.append(f"the analogy or its verdict is missing: {phrase[:50]}")
	print("  OK: shirk is named as an analogy between God and kings, and the analogy condemned")

	for label, king, god in THE_FOUR:
		if normalize(king) not in sa or normalize(god) not in sa:
			failures.append(
				f"one half of the {label} pairing is gone. Keeping the conclusion without "
				f"these four is reporting that he disagreed, not why."
			)
	print(f"  OK: all {len(THE_FOUR)} pairings intact, each naming a king's need and God's freedom from it")

	if normalize(WHY_UNFORGIVEN) not in sa:
		failures.append("his answer for why shirk alone is unforgiven is missing")
	print("  OK: and why shirk alone goes unforgiven, in his words")

	# the 2:165 note this verse backs
	if normalize(NOTE_AT_2_165) not in tafsir("saadi", 2, 165):
		failures.append(
			"the 2:165 note's quote is gone, so this stop's cross-reference to it is stale"
		)
	print("  OK: the note at 2:165 still stands, and this verse is its evidence")

	if failures:
		print("\nCLAIM FAILED:", file=sys.stderr)
		for f in failures:
			print(f"  {f}", file=sys.stderr)
		sys.exit(1)
	print("\naz-Zumar 3 claim holds.")


if __name__ == "__main__":
	main()
