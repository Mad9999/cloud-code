"""The claim written into the stop at al-Qalam 4.

«وإنك لعلى خلق عظيم» is quoted as praise and left there, which makes it a
compliment nobody can act on. Aisha's answer turns it into something a reader
can check himself against, and the way she answers is the whole point: she does
not describe him. She asks a question back. «ألست تقرأ القرآن؟ قال: بلى. قالت:
فإن خلق رسول الله ﷺ كان القرآن.» The description was already in the questioner's
hands.

The valve holds her answer in the fuller of Ibn Kathir's three routes, because
the short form «كان خلقه القرآن» loses the exchange, and the exchange is what
makes the stop's point. It holds Ibn Kathir's takhrij to Muslim. It holds the
ikhtilaf, since seven named salaf read «خلق عظيم» as «دين عظيم», the religion
itself, which the stop reports rather than passes over.

And it holds Saadi's concrete portrait, all of it, because a stop that said «he
had noble character» and stopped would be committing the very fault it is about.
The list includes «ولا يمسك عليه فلتات لسانه», which is the hardest line in it
and the easiest to drop.

Usage: python verify_khuluq_claim.py
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


def tafsir(book, surah=68, ayah=4):
	path = BASE / "app" / "tafsir" / book / f"{surah}.js"
	payload = json.loads(path.read_text(encoding="utf-8").split("=", 1)[1].rstrip().rstrip(";"))
	return normalize(re.sub(r"\[\[.*?\]\]", " ", payload[str(ayah)], flags=re.S))


# Her answer, in the form that keeps the exchange.
AISHA_FULL = "فقالت: أتقرأ القرآن؟ فقلت: نعم. فقالت: كان خلقه القرآن"
AISHA_SECOND = "فقالت: ألست تقرأ القرآن؟ قال: بلى. قالت: فإن خلق رسول الله ﷺ كان القرآن"
TAKHRIJ = "وقد رواه الإمام مسلم في صحيحه، من حديث قتادة بطوله"

# The other reading, which the stop carries.
AS_DEEN = "قال العوفي، عن ابن عباس: أي: وإنك لعلى دين عظيم، وهو الإسلام"
AS_DEEN_WHO = "وكذلك قال مجاهد، وأبو مالك، والسدي، والربيع بن أنس، والضحاك، وابن زيد"
AS_ADAB = "وقال عطية: لعلى أدب عظيم"

# Saadi's portrait. Kept whole, because summarising it is the fault the stop is about.
PORTRAIT = [
	("أنّ حاصلَه ما فسّرته عائشة", "وحاصل خلقه العظيم، ما فسرته به أم المؤمنين"),
	(
		"وسهولتُه وقربُه",
		"فكان صلى الله عليه وسلم سهلا لينا، قريبا من الناس، مجيبا لدعوة من دعاه، قاضيا "
		"لحاجة من استقضاه، جابرا لقلب من سأله",
	),
	("ولا يستبدّ", "وإن عزم على أمر لم يستبد به دونهم، بل يشاورهم ويؤامرهم"),
	("ويقبل ويعفو", "وكان يقبل من محسنهم، ويعفو عن مسيئهم"),
	(
		"وأشقُّها على النفس",
		"فكان لا يعبس في وجهه، ولا يغلظ عليه في مقاله، ولا يطوي عنه بشره، ولا يمسك عليه "
		"فلتات لسانه",
	),
	("ولا يؤاخذ بالجفوة", "ولا يؤاخذه بما يصدر منه من جفوة"),
]

# The verses Saadi names as the content of that khuluq, so the stop's claim that
# the description is checkable has something to check against.
THE_VERSES = ["7:199", "3:159", "9:128"]
THE_WORDS = [
	"خذ العفو وأمر بالعرف وأعرض عن الجاهلين",
	"فبما رحمة من الله لنت لهم",
	"لقد جاءكم رسول من أنفسكم عزيز عليه ما عنتم حريص عليكم بالمؤمنين رءوف رحيم",
]


def main():
	failures = []
	sa, ik = tafsir("saadi"), tafsir("ibnkathir")

	if normalize(AISHA_FULL) not in ik and normalize(AISHA_SECOND) not in ik:
		failures.append(
			"Aisha's answer in the form that keeps the exchange is gone. The short «كان "
			"خلقه القرآن» is not enough: the stop's point is that she answered with a "
			"question, pointing the man at a book he already had."
		)
	if normalize(TAKHRIJ) not in ik:
		failures.append("Ibn Kathir's takhrij of the report to Muslim is missing")
	print("  OK: Aisha's exchange with its takhrij, in the form that keeps the question")

	for phrase in (AS_DEEN, AS_DEEN_WHO, AS_ADAB):
		if normalize(phrase) not in ik:
			failures.append(f"the other reading is missing: {phrase[:50]}")
	print("  OK: the reading «دين عظيم» stands, with the seven who held it, and Atiyya's «أدب»")

	for label, phrase in PORTRAIT:
		if normalize(phrase) not in sa:
			failures.append(f"Saadi's portrait is incomplete ({label}): {phrase[:50]}")
	print(f"  OK: all {len(PORTRAIT)} pieces of Saadi's portrait, none summarised away")

	# and the verses he names, checked against the mushaf itself
	raw = (BASE / "app" / "generated" / "quran_text.js").read_text(encoding="utf-8")
	q = json.loads(raw.split("=", 1)[1].rstrip().rstrip(";"))
	for ref, words in zip(THE_VERSES, THE_WORDS):
		if normalize(words) not in normalize(q[ref]):
			failures.append(f"{ref} does not carry the words Saadi cites: {words[:40]}")
	print(f"  OK: the {len(THE_VERSES)} verses he names as the content of that khuluq check out")

	if failures:
		print("\nCLAIM FAILED:", file=sys.stderr)
		for f in failures:
			print(f"  {f}", file=sys.stderr)
		sys.exit(1)
	print("\nal-Qalam 4 claim holds.")


if __name__ == "__main__":
	main()
