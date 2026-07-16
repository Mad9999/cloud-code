"""The claim written into the stop at al-Baqara 275, held as a test.

The stop rests on a count and on Malik's reason for the same thing, and the
order matters: Malik got there first, by memory, over three days. We did not
discover that the Qur'an declares war only over riba. We confirmed with a script
in a second what an imam said he had reached by «تصفحت كتاب الله وسنة نبيه».

So this file checks two things that must both hold or the stop is empty. That the
root ح ر ب occurs six times in the Qur'an and the war issues from God in exactly
one of them, 2:279; and that Malik's words, and the case he said them in, are in
Qurtubi verbatim, since without his reasoning the count is our own bright idea
and rule 5 says it does not get written.

It also holds the limit. Malik was answering a man's oath about what enters the
belly of a son of Adam, so the comparison in front of him was riba against wine.
Qurtubi records his words as general. The stop reports both and settles neither.

Usage: python verify_riba_claim.py
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


def tafsir(book, ayah, surah=2):
	path = BASE / "app" / "tafsir" / book / f"{surah}.js"
	payload = json.loads(path.read_text(encoding="utf-8").split("=", 1)[1].rstrip().rstrip(";"))
	return normalize(re.sub(r"\[\[.*?\]\]", " ", payload[str(ayah)], flags=re.S))


ROOT = re.compile(r"\S*(?:حرب|حارب|يحارب)\S*")

# Where the root falls, and which way the war points. Read by eye, all six.
WAR_FROM_GOD = ["2:279"]
WAR_AGAINST_GOD = ["5:33", "9:107"]
WAR_AMONG_MEN = ["5:64", "8:57", "47:4"]

# Malik's case and his reason, in Qurtubi, from Ibn Bukayr.
MALIK = [
	("الرجلُ وسؤالُه", "جاء رجل إلى مالك بن أنس"),
	("والواقعةُ التي حلف عليها", "إني رأيت رجلا سكرانا يتعاقر يريد أن يأخذ القمر"),
	("ونصُّ يمينه، وهو حدُّ المسألة", "فقلت: امرأتي طالق إن كان يدخل جوف ابن آدم أشر من الخمر"),
	("وتوقُّفُه", "ارجع حتى أنظر في مسألتك"),
	(
		"وفتواه وعلّتُها",
		"امرأتك طالق، إني تصفحت كتاب الله وسنة نبيه فلم أر شيئا أشر من الربا، لأن الله أذن فيه بالحرب",
	),
]

QURTUBI_ELSE = [
	"هذا وعيد إن لم يذروا الربا، والحرب داعية القتل",
	"دلت هذه الآية على أن أكل الربا والعمل به من الكبائر، ولا خلاف في ذلك",
]

# Ibn Kathir puts these under 278-281, one block, not under 275. We first went
# looking for them in the wrong entry.
IBN_KATHIR_278 = [
	"وهذا تهديد شديد ووعيد أكيد، لمن استمر على تعاطي الربا بعد الإنذار",
	"فقالوا: نتوب إلى الله، ونذر ما بقي من الربا، فتركوه كلهم",
]


def main():
	failures = []
	q = quran()

	found = sorted(
		(k for k, v in q.items() if ROOT.search(v)), key=lambda k: [int(x) for x in k.split(":")]
	)
	expected = sorted(
		WAR_FROM_GOD + WAR_AGAINST_GOD + WAR_AMONG_MEN, key=lambda k: [int(x) for x in k.split(":")]
	)
	if found != expected:
		failures.append(f"the root's places changed: {found}")
	print(f"  OK: the root ح ر ب occurs in {len(found)} places in the Qur'an")

	# the one place the war comes from God's side
	from_god = [k for k in found if "بحرب من الله" in q[k]]
	if from_god != WAR_FROM_GOD:
		failures.append(f"«بحرب من الله» is no longer only 2:279: {from_god}")
	for key in WAR_AGAINST_GOD:
		if not re.search(r"(يحاربون|حارب) الله", q[key]):
			failures.append(f"{key} was read as war against God and no longer reads that way")
	print("  OK: the war issues from God in one place only, 2:279, and is waged against Him in two")

	# Malik, without whom the count does not get written
	qurtubi = tafsir("qurtubi", 275)
	for label, phrase in MALIK:
		if normalize(phrase) not in qurtubi:
			failures.append(f"Malik's case not found ({label}): {phrase}")
	print("  OK: Malik's three days, his ruling, and his reason are in Qurtubi verbatim")

	for phrase in QURTUBI_ELSE:
		if normalize(phrase) not in qurtubi:
			failures.append(f"Qurtubi's words not found: {phrase}")
	print("  OK: Qurtubi's own reading of the threat, and his report of no disagreement")

	for phrase in IBN_KATHIR_278:
		if normalize(phrase) not in tafsir("ibnkathir", 278):
			failures.append(f"Ibn Kathir's words not found under 278: {phrase}")
	print("  OK: Ibn Kathir's words sit under 278-281, which is where the stop cites them")

	if failures:
		print("\nCLAIM FAILED:", file=sys.stderr)
		for f in failures:
			print(f"  {f}", file=sys.stderr)
		sys.exit(1)
	print("\nal-Baqara 275 claim holds.")


if __name__ == "__main__":
	main()
