"""The claim written into the stop at al-Kahf 82.

The Khidr story is read every Friday and remembered for one thing: that God's
wisdom runs under events we cannot see. That is true and Saadi says it. But at
the story's close he appends thirty-eight benefits, the largest such run in the
whole mushaf, seven more than the debt verse, and most of them are not about
hidden wisdom at all. They are about how to learn.

The stop says so, and the counting is checked here rather than asserted. The
count is 38, not 37: one «فمنها» opens the run and thirty-seven «ومنها» follow,
and taking only the second form gives the prettier round number and the wrong
one.

It also holds three things the run contains that a reader will not expect, each
verbatim, because each corrects something commonly said:

That Musa is definitively the superior of the two, «فإن موسى بلا شك أفضل من
الخضر», in a story usually told the other way around.

That Khidr was not a prophet but a righteous servant, with Saadi's reason: the
Qur'an describes him by servanthood and by mercy and knowledge given him, and
never by messengership.

And that patience is not a virtue decorating knowledge but the condition of
getting any: «فمن لا صبر له لا يدرك العلم».

Usage: python verify_khidr_claim.py
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


def tafsir(book, surah, ayah):
	path = BASE / "app" / "tafsir" / book / f"{surah}.js"
	payload = json.loads(path.read_text(encoding="utf-8").split("=", 1)[1].rstrip().rstrip(";"))
	return strip_marks(re.sub(r"\[\[.*?\]\]", " ", payload[str(ayah)], flags=re.S))


TOTAL = 38
RUNNER_UP = ("2:282", 31)

OPENING = "وفي هذه القصة العجيبة الجليلة من الفوائد والأحكام والقواعد شيء كثير، ننبه على بعضه بعون الله"

# The benefits the stop quotes, all about learning rather than hidden wisdom.
ON_LEARNING = [
	("فضلُ العلم والرحلة فيه", "فضيلة العلم، والرحلة في طلبه، وأنه أهم الأمور"),
	("والأدبُ مع المعلّم", "التأدب مع المعلم، وخطاب المتعلم إياه ألطف خطاب"),
	("وتواضعُ الأفضل", "تواضع الفاضل للتعلم ممن دونه، فإن موسى -بلا شك- أفضل من الخضر"),
	(
		"والصبرُ شرطٌ لا زينة",
		"فمن لا صبر له لا يدرك العلم، ومن استعمل الصبر ولازمه أدرك به كل أمر سعى فيه",
	),
	(
		"والتأنّي قبل الحكم",
		"الأمر بالتأني والتثبت وعدم المبادرة إلى الحكم على الشيء حتى يعرف ما يراد منه",
	),
	("والعزمُ ليس فعلًا", "أن العزم على فعل الشيء ليس بمنزلة فعله"),
	("ونوعا العلم", "علم مكتسب يدركه العبد بجده واجتهاده، ونوع: علم لدني"),
]

# The correction about Khidr himself.
NOT_A_PROPHET = "أن ذلك العبد الذي لقياه، ليس نبيا، بل عبدا صالحا"

# And what the stop must not be read as denying: the hidden-wisdom reading is
# Saadi's own, stated in the same run, and the stop keeps it.
STILL_HIDDEN_WISDOM = (
	"أن هذه القضايا التي أجراها الخضر هي قدر محض أجراها الله وجعلها على يد هذا العبد الصالح"
)


def main():
	failures = []
	text = tafsir("saadi", 18, 82)
	body = text[text.find("ننبه على بعضه بعون الله") :]

	count = len(re.findall(r"فمنها:", body)) + len(re.findall(r"ومنها:", body))
	if count != TOTAL:
		failures.append(f"the run is {count} benefits, not the {TOTAL} the stop states")
	if len(re.findall(r"ومنها:", body)) == TOTAL:
		failures.append("the «فمنها» opener has vanished, so the stop's note about it is stale")
	print(f"  OK: {count} benefits, counting the «فمنها» that opens the run and not only the «ومنها»")

	# and that it is the largest such run in the mushaf
	biggest = []
	for surah in range(1, 115):
		path = BASE / "app" / "tafsir" / "saadi" / f"{surah}.js"
		if not path.exists():
			continue
		payload = json.loads(path.read_text(encoding="utf-8").split("=", 1)[1].rstrip().rstrip(";"))
		for ayah, v in payload.items():
			t = strip_marks(re.sub(r"\[\[.*?\]\]", " ", v, flags=re.S))
			n = len(re.findall(r"ومنها:", t)) + len(re.findall(r"فمنها:", t))
			if n >= 10:
				biggest.append((n, f"{surah}:{ayah}"))
	biggest.sort(reverse=True)
	if not biggest or biggest[0][1] != "18:82":
		failures.append(f"18:82 is no longer the largest run in the mushaf: {biggest[:2]}")
	if len(biggest) > 1 and biggest[1] != (RUNNER_UP[1], RUNNER_UP[0]):
		failures.append(f"the runner-up changed: {biggest[1]} vs the stated {RUNNER_UP}")
	print(f"  OK: largest run in the mushaf, {biggest[0][0]} here against {biggest[1][0]} at {biggest[1][1]}")

	if normalize(OPENING) not in normalize(text):
		failures.append("Saadi's own framing of the run is missing")
	for label, phrase in ON_LEARNING:
		if normalize(phrase) not in normalize(text):
			failures.append(f"benefit not found ({label}): {phrase[:55]}")
	print(f"  OK: {len(ON_LEARNING)} benefits about learning, each verbatim")

	if normalize(NOT_A_PROPHET) not in normalize(text):
		failures.append("Saadi's ruling that Khidr was not a prophet is missing")
	print("  OK: he states Khidr was a righteous servant and not a prophet, and Musa the superior")

	if normalize(STILL_HIDDEN_WISDOM) not in normalize(text):
		failures.append(
			"the hidden-wisdom benefit is gone. The stop keeps it deliberately: the famous "
			"reading is Saadi's too, and a stop that dropped it would be trading one "
			"one-sidedness for another."
		)
	print("  OK: the hidden-wisdom reading is in the same run, so the stop does not displace it")

	if failures:
		print("\nCLAIM FAILED:", file=sys.stderr)
		for f in failures:
			print(f"  {f}", file=sys.stderr)
		sys.exit(1)
	print("\nal-Kahf 82 claim holds.")


if __name__ == "__main__":
	main()
