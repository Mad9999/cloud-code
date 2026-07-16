"""The claim written into the stop at al-Baqara 255, held as a test.

The stop says: in his commentary on this one verse Ibn Kathir turns away three
reports, and one of them is a proof of the very position he himself adopts. A
statement like that must be checkable by anyone, not taken on our word, so it
is written here as a test that fails the build if it is false.

Three reports, not six. Our first count came to six because we counted the
phrases of rejection rather than the reports rejected: two of the phrases fall
on two routes to one text, and two more fall on one hadith doubted twice. That
is the error rule 27 was written against, made this time against ourselves, so
the honest count is fixed here where it cannot drift: three texts, four routes.

It also holds the smaller claims the stop leans on: that the wording of the
thief's hadith is Bukhari's as Ibn Kathir relays it, and that 'his Kursi is
his knowledge' is Tabari's wording and not Ibn Kathir's, since we nearly
attributed it to the wrong book.

Usage: python verify_kursi_claim.py
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


# The three texts Ibn Kathir turns away inside 2:255, each with the routes he
# names and the words he turns it away with. Routes are nested under their
# text so the count cannot be inflated by counting them twice.
REJECTED = [
	(
		"رفعُ «كرسيه موضع قدميه» إلى النبي ﷺ",
		["وهو غلط", "وهو متروك", "ولا يصح أيضا"],
	),
	(
		"حديثُ القارورتين عن أبي هريرة مرفوعًا",
		["وهذا حديث غريب جدا والأظهر أنه إسرائيلي لا مرفوع"],
	),
	(
		"حديثُ الأطيط عن عمر، من طريق عبد الله بن خليفة",
		["وليس بذاك المشهور", "وفي سماعه من عمر نظر", "وعندي في صحته نظر"],
	),
]

# The position he adopts, whose evidence he then doubts. This is the hinge of
# the claim: without it he is merely strict with others.
ADOPTED = "والصحيح أن الكرسي غير العرش والعرش أكبر منه"
ADOPTED_EVIDENCE = "وقد اعتمد ابن جرير على حديث عبد الله بن خليفة، عن عمر في ذلك وعندي في صحته نظر"

# What the stop does NOT say, held here so a later hand cannot quietly widen
# it (rule 29). He did not drop the position: he keeps it on other athar. And
# he did not reject the saying itself, only its being raised to the Prophet ﷺ:
# as Ibn Abbas's own word al-Hakim graded it on the two shaykhs' condition.
NOT_DENIED = [
	"كما دلت على ذلك الآثار والأخبار",
	"عن ابن عباس موقوفا مثله وقال: صحيح على شرط الشيخين ولم يخرجاه",
]

# The thief's hadith, which Ibn Kathir relays from Bukhari.
BUKHARI = [
	"وقد ذكر البخاري هذه القصة عن أبي هريرة",
	"أما إنه قد كذبك وسيعود",
	"صدقك وهو كذوب",
	"وكانوا أحرص شيء على الخير",
]

# 'his Kursi is his knowledge' with this wording is Tabari's; Ibn Kathir's is
# the bare 'his knowledge'. We nearly cited the wrong imam.
WORDING = [
	("tabari", "كرسيه علمه", True),
	("ibnkathir", "كرسيه علمه", False),
	("ibnkathir", "قال: علمه", True),
]


def main():
	failures = []
	text = tafsir("ibnkathir", 2, 255)

	routes = 0
	for label, phrases in REJECTED:
		routes += len(phrases)
		for phrase in phrases:
			if normalize(phrase) not in text:
				failures.append(f"rejection not found ({label}): {phrase}")
	print(f"  OK: {len(REJECTED)} reports turned away verbatim in Ibn Kathir on 2:255")

	for phrase in (ADOPTED, ADOPTED_EVIDENCE):
		if normalize(phrase) not in text:
			failures.append(f"hinge phrase not found: {phrase}")
	print("  OK: he states the position he holds, and doubts its evidence, in the same passage")

	for phrase in NOT_DENIED:
		if normalize(phrase) not in text:
			failures.append(f"the claim's limit is not where we said it is: {phrase}")
	print("  OK: he keeps the position on other athar, and keeps the saying as Ibn Abbas's own")

	for phrase in BUKHARI:
		if normalize(phrase) not in text:
			failures.append(f"Bukhari hadith wording not found: {phrase}")
	print("  OK: the thief's hadith is relayed from Bukhari with the wording we quote")

	for book, phrase, expected in WORDING:
		found = normalize(phrase) in tafsir(book, 2, 255)
		if found is not expected:
			failures.append(
				f"wording check failed: «{phrase}» {'missing from' if expected else 'present in'} {book}"
			)
	print("  OK: «كرسيه علمه» is Tabari's wording, not Ibn Kathir's")

	# The stop says he does not do this only where it costs him nothing. Guard
	# the narrow form of the claim: the doubted report is the one Ibn Jarir
	# rested the adopted position on, so the two must sit in one sentence.
	if normalize(ADOPTED_EVIDENCE) not in text:
		failures.append("the doubt and the adopted position are not in one sentence")

	if failures:
		print("\nCLAIM FAILED:", file=sys.stderr)
		for f in failures:
			print(f"  {f}", file=sys.stderr)
		sys.exit(1)
	print("\nal-Baqara 255 claim holds.")


if __name__ == "__main__":
	main()
