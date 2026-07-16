"""The claim written into the stop at al-Baqara 256, held as a test.

The stop says: Tabari refuses the claim that «لا إكراه في الدين» is abrogated,
and refuses it by a stated threshold rather than by preference, a threshold he
takes from another book of his own; that he raises his opponent's evidence
himself and grants it is sound before answering it; and that the imams differ
here in six recorded positions, so neither of the two confident readings the
verse is pulled toward today is what they landed on.

Every piece of that is checked here against the six books, because a stop that
tells a reader how to weigh an abrogation claim had better be weighable itself.

One thing this file also pins is a defect in our copy. Tabari's second clause
reads «فهو من الناس والمنسوخ بمعزل» where the word plainly wants to be
«الناسخ». We nearly quoted it corrected, which would have put into his mouth a
word our copy does not have, so the test holds the typo in place: if a later
edition of the corpus fixes it, this fails and we look again rather than
discovering years on that our quotation drifted.

Usage: python verify_naskh_claim.py
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


def tafsir(book, ayah, surah=2):
	path = BASE / "app" / "tafsir" / book / f"{surah}.js"
	payload = json.loads(path.read_text(encoding="utf-8").split("=", 1)[1].rstrip().rstrip(";"))
	return normalize(re.sub(r"\[\[.*?\]\]", " ", payload[str(ayah)], flags=re.S))


# The threshold, in Tabari's words, and his verdict by it.
THRESHOLD = [
	(
		"الأصلُ الذي يحيل فيه على كتابه الآخر",
		"أن الناسخ غير كائن ناسخا إلا ما نفى حكم المنسوخ، فلم يجز اجتماعهما",
	),
	("حكمُه بذلك الأصل", "ولا معنى لقول من زعم أن الآية منسوخة الحكم، بالإذن بالمحاربة"),
	("ونسبةُ الإنكار إلى أصحاب القول الذي رجّحه", "وأنكروا أن يكون شيء منها منسوخا"),
]

# He raises the objection against himself and grants it before answering.
OBJECTION = [
	("إيرادُ حجّة المخالف", "فإن قال قائل"),
	("الإقرارُ بصحّتها", "ذلك غير مدفوعة صحته"),
	(
		"الجوابُ بأصلٍ لا بردٍّ",
		"ولكن الآية قد تنزل في خاص من الأمر، ثم يكون حكمها عاما في كل ما جانس المعنى الذي أنزلت فيه",
	),
]

# The disagreement is real and recorded, so no single reading may be sold as
# settled. Qurtubi counts them; Ibn Kathir carries both sides.
IKHTILAF = [
	("qurtubi", "اختلف العلماء في معنى هذه الآية على ستة أقوال"),
	("qurtubi", "قيل إنها منسوخة، لأن النبي ﷺ قد أكره العرب على دين الإسلام"),
	("ibnkathir", "وقال آخرون: بل هي منسوخة بآية القتال"),
	("ibnkathir", "وقد ذهب طائفة كثيرة من العلماء أن هذه محمولة على أهل الكتاب"),
]

# Saadi's brevity is the point of rule 33's refinement: he is short here (1.27x,
# 73rd of 272) and spends the shortness on exactly the confusion of our day.
SAADI = [
	"لا تدل الآية الكريمة على ترك قتال الكفار المحاربين",
	"وأما القتال وعدمه فلم تتعرض له، وإنما يؤخذ فرض القتال من نصوص أخر",
]

# What the stop must not be read as saying (rule 29). Tabari's own reading is a
# narrowing, not a blanket: he states that the Prophet (peace be upon him) did
# compel some, and that is why the verse cannot mean what the easy reading
# wants it to mean. A stop that hid this would be selling the flattering half.
NOT_DENIED = [
	"وكان المسلمون جميعا قد نقلوا عن نبيهم ﷺ أنه أكره على الإسلام قوما فأبى أن يقبل منهم إلا الإسلام",
	"لا إكراه في الدين لأحد ممن حل قبول الجزية منه بأدائه الجزية",
]

# Our copy's typo, pinned so our quotation cannot silently drift with it.
TYPO_IN_OUR_COPY = "فهو من الناس والمنسوخ بمعزل"
TYPO_CORRECTED = "فهو من الناسخ والمنسوخ بمعزل"


def main():
	failures = []
	tab = tafsir("tabari", 256)

	for label, phrase in THRESHOLD:
		if normalize(phrase) not in tab:
			failures.append(f"threshold not found ({label}): {phrase}")
	print("  OK: Tabari states the threshold for naskh, and rules by it, verbatim")

	for label, phrase in OBJECTION:
		if normalize(phrase) not in tab:
			failures.append(f"objection handling not found ({label}): {phrase}")
	print("  OK: he raises the counter-evidence himself and grants it before answering")

	for book, phrase in IKHTILAF:
		if normalize(phrase) not in tafsir(book, 256):
			failures.append(f"ikhtilaf not found in {book}: {phrase}")
	print("  OK: the disagreement is recorded, in six positions, with both sides carried")

	for phrase in SAADI:
		if normalize(phrase) not in tafsir("saadi", 256):
			failures.append(f"Saadi's words not found: {phrase}")
	print("  OK: Saadi's brief text says the verse does not address fighting at all")

	for phrase in NOT_DENIED:
		if normalize(phrase) not in tab:
			failures.append(f"the claim's limit is not where we said it is: {phrase}")
	print("  OK: Tabari's reading narrows the verse rather than emptying the matter")

	if normalize(TYPO_IN_OUR_COPY) not in tab:
		failures.append("our copy's typo is gone: re-read Tabari and re-check the quotation")
	if normalize(TYPO_CORRECTED) in tab:
		failures.append("our copy now reads «الناسخ»: the stop may quote the full clause")
	print("  OK: our copy still reads «الناس» for «الناسخ», so we still do not quote that clause")

	if failures:
		print("\nCLAIM FAILED:", file=sys.stderr)
		for f in failures:
			print(f"  {f}", file=sys.stderr)
		sys.exit(1)
	print("\nal-Baqara 256 claim holds.")


if __name__ == "__main__":
	main()
