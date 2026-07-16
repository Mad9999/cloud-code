"""The claim written into the stop at al-Baqara 258, held as a test.

The stop is about how Ibrahim argued with a man who was equivocating, and it
leans on three things: that «يحيي ويميت» is said of God everywhere it occurs in
the Qur'an, so the king was reaching for a description the Book reserves; that
Ibrahim answered the equivocation by extending the man's own claim rather than
by disputing it, in Saadi's words «اطرد معه في الدليل»; and that Saadi read the
king's missing «الذي» as the tell.

It also pins a finding we dropped, which matters more than the ones we kept.
«أحيي وأميت» in the first person occurs exactly once in the whole Qur'an, in
this tyrant's mouth. That is a striking sentence and it is worthless: the story
of Ibrahim and the king occurs exactly once too, so the count of the phrase is
an artifact of the count of the story, not a fact about the wording. The test
holds both counts precisely so that nobody, us included, can revive the number
later without meeting the reason it was dropped.

Usage: python verify_hijaj_claim.py
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


def quran():
	raw = (BASE / "app" / "generated" / "quran_text.js").read_text(encoding="utf-8")
	return {k: strip_marks(v) for k, v in json.loads(raw.split("=", 1)[1].rstrip().rstrip(";")).items()}


def saadi(ayah, surah=2):
	path = BASE / "app" / "tafsir" / "saadi" / f"{surah}.js"
	payload = json.loads(path.read_text(encoding="utf-8").split("=", 1)[1].rstrip().rstrip(";"))
	return normalize(re.sub(r"\[\[.*?\]\]", " ", payload[str(ayah)], flags=re.S))


# Every place the Qur'an says «يحيي ويميت». All nine were read by eye and the
# subject is God in every one; that reading is ours, so what is written here is
# the list itself plus the one thing a machine can honestly check, which is that
# a divine referent governs. The referent is not always in the verse: 57:2 says
# «له ملك السماوات والأرض يحيي ويميت» and the «له» reaches back to «سبح لله» in
# 57:1. Our first test demanded God adjacent to the verb and so failed on 9:116
# and 57:2, where the fault was the test's and not the claim's.
OF_GOD = ["2:258", "3:156", "7:158", "9:116", "10:56", "23:80", "40:68", "44:8", "57:2"]
DIVINE = re.compile(r"(الله|لا إله إلا هو|هو الذي|وهو|ربي الذي|له ملك)")

SAADI_WORDS = [
	("التلُّ في تركِ «الذي»", "ولم يقل أنا الذي أحيي وأميت، لأنه لم يدع الاستقلال بالتصرف"),
	("وأنّه إنّما زعم المحاكاة", "وإنما زعم أنه يفعل كفعل الله ويصنع صنعه"),
	("وأنّ الرجل كان يغالط", "فلما رآه إبراهيم يغالط في مجادلته"),
	("وأنّ كلامه لا يبلغ رتبة الشبهة", "ويتكلم بشيء لا يصلح أن يكون شبهة فضلا عن كونه حجة"),
	("وطريقةُ إبراهيم", "اطرد معه في الدليل"),
	("وأنّها إلزامٌ بطردِ دليلِ الخصم", "وهذا إلزام له بطرد دليله إن كان صادقا في دعواه"),
	("وثمرتُها", "تحير فلم يرجع إليه جوابا وانقطعت حجته وسقطت شبهته"),
]

# Ibn al-Qayyim's point, which Saadi relays from Miftah Dar as-Sa'ada. It is his
# and not Saadi's, and not ours.
IBN_QAYYIM = [
	"قال ابن القيم رحمه الله: وفي هذه المناظرة نكتة لطيفة جدا",
	"وهي أن شرك العالم إنما هو مستند إلى عبادة الكواكب والقبور",
	"من مفتاح دار السعادة",
]


def main():
	failures = []
	q = quran()

	# 1) the description is God's, everywhere it is said
	found = sorted((k for k, v in q.items() if "يحيي ويميت" in v), key=lambda k: [int(x) for x in k.split(":")])
	if found != OF_GOD:
		failures.append(f"the places changed: {found}")
	for key in found:
		surah, ayah = (int(x) for x in key.split(":"))
		# the referent may sit in the verse before, so read that too
		scope = q.get(f"{surah}:{ayah - 1}", "") + " " + q[key][: q[key].find("يحيي ويميت")]
		if not DIVINE.search(scope):
			failures.append(f"{key}: no divine referent governs «يحيي ويميت»: ...{scope[-60:]}")
	print(f"  OK: «يحيي ويميت» occurs in {len(found)} places, a divine referent governing each")

	# 2) the dropped finding, held with its reason
	first_person = [k for k, v in q.items() if "أحيي وأميت" in v]
	if first_person != ["2:258"]:
		failures.append(f"«أحيي وأميت» is no longer unique to 2:258: {first_person}")
	story = [k for k, v in q.items() if "حاج إبراهيم" in v]
	if story != ["2:258"]:
		failures.append(f"the story is no longer unique to 2:258: {story}")
	if len(first_person) != len(story):
		failures.append(
			"the phrase count and the story count have come apart: the dropped finding "
			"may be worth re-examining, since its whole defect was that they matched"
		)
	print(
		"  OK: «أحيي وأميت» occurs once, and so does the story, which is why the count "
		"was dropped and not written"
	)

	# 3) Saadi's reading
	text = saadi(258)
	for label, phrase in SAADI_WORDS:
		if normalize(phrase) not in text:
			failures.append(f"Saadi's words not found ({label}): {phrase}")
	print("  OK: Saadi's reading of the tell, the equivocation, and the method, verbatim")

	# 4) the wording the tell rests on, in the verse itself
	verse = q["2:258"]
	if "ربي الذي يحيي ويميت" not in verse:
		failures.append("Ibrahim's wording is not what the stop says it is")
	if "أنا أحيي وأميت" not in verse:
		failures.append("the king's wording is not what the stop says it is")
	if "أنا الذي أحيي وأميت" in verse:
		failures.append("the king does say «الذي»: Saadi's tell, and our stop, are wrong")
	print("  OK: Ibrahim says «الذي» and the king does not, in the verse itself")

	# 5) Ibn al-Qayyim's, attributed where Saadi puts it
	for phrase in IBN_QAYYIM:
		if normalize(phrase) not in text:
			failures.append(f"Ibn al-Qayyim's point not found as Saadi relays it: {phrase}")
	print("  OK: the point about the stars and the graves is Ibn al-Qayyim's, via Saadi")

	if failures:
		print("\nCLAIM FAILED:", file=sys.stderr)
		for f in failures:
			print(f"  {f}", file=sys.stderr)
		sys.exit(1)
	print("\nal-Baqara 258 claim holds.")


if __name__ == "__main__":
	main()
