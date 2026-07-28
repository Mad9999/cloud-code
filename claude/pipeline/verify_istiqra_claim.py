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

# He counts al-Baqara itself at the head of his commentary, and attributes the
# count rather than floating it: «في عدد الكوفي وعدد علي بن أبي طالب». So it is
# checkable, and it is checked here, with the margins stated rather than hidden.
HIS_TALLY = (
	"خمسة وعشرون ألفا وخمسمائة حرف، وستة آلاف ومائة وعشرون كلمة، ومائتان وستة "
	"وثمانون آية في عدد الكوفي وعدد علي بن أبي طالب رضي الله عنه"
)
HIS_NUMBERS = {"ayat": 286, "words": 6120, "letters": 25500}
# Word and letter tallies depend on rasm conventions that vary between counting
# schools, so an exact match would be the surprising result, not a near one.
TOLERANCE = {"ayat": 0.0, "words": 0.01, "letters": 0.05}

# The entry keyed to 2:1 in our corpus opens with the tail of al-Fatiha's
# commentary and only reaches al-Baqara a third of the way in. It is the only
# such leak we found in ten surah-openings, and it inflates Ibn Kathir's block
# for 2:1 into the largest in the surah. Pinned so nobody reads that rank as a
# fact about his attention.
FATIHA_LEAK_MARKER = "غير صراط المغضوب عليهم"
BAQARA_STARTS_AT = "تفسير سورة البقرة"


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

	# his tally of al-Baqara, against ours
	if normalize(HIS_TALLY) not in text:
		failures.append("his tally of al-Baqara, with its attribution, is not where we cite it")
	verses = [strip_marks(q[f"2:{n}"]) for n in range(1, 287)]
	joined = " ".join(verses)
	ours = {
		"ayat": len(verses),
		"words": len(joined.split()),
		"letters": len(re.sub(r"[^ء-ي]", "", joined)),
	}
	for key, his in HIS_NUMBERS.items():
		gap = abs(ours[key] - his) / his
		if gap > TOLERANCE[key]:
			failures.append(
				f"his {key} count {his} vs ours {ours[key]}, off by {gap:.1%}, past the "
				f"{TOLERANCE[key]:.0%} the stop tells the reader to expect"
			)
	print(
		f"  OK: his tally holds: {ours['ayat']} ayat exactly, {ours['words']} words to his "
		f"{HIS_NUMBERS['words']}, {ours['letters']} letters to his {HIS_NUMBERS['letters']}"
	)

	# and the corpus defect that inflates his 2:1 block
	entry = re.sub(r"\[\[.*?\]\]", " ", payload["1"], flags=re.S)
	flat = DIACRITICS.sub("", entry)
	head = flat.find(BAQARA_STARTS_AT)
	if FATIHA_LEAK_MARKER not in flat[:5000] or head <= 0:
		failures.append(
			"the al-Fatiha tail no longer opens our 2:1 entry. If the corpus was fixed, "
			"good, and the stop's caveat about the inflated block must be rewritten."
		)
	else:
		print(
			f"  OK: our 2:1 entry still opens with al-Fatiha's tail, {head / len(flat):.0%} of "
			f"it, so his rank there is a corpus artifact and the stop says so"
		)

	if failures:
		print("\nCLAIM FAILED:", file=sys.stderr)
		for f in failures:
			print(f"  {f}", file=sys.stderr)
		sys.exit(1)
	print("\nIbn Kathir's istiqra' holds, and it took us three questions to see it.")


if __name__ == "__main__":
	main()
