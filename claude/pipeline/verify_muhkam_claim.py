"""The claim written into the stop at Al Imran 7, the verse that governs reading.

This is the rule the whole Book is read by, so the stop has to be exact and the
valve has to hold it exactly.

Saadi states the obligation in one clause: «فالواجب في هذا أن يرد المتشابه إلى
المحكم والخفي إلى الجلي». And he names the disease as an inversion rather than a
lack: «يتركون المحكم الواضح ويذهبون إلى المتشابه، ويعكسون الأمر فيحملون المحكم
على المتشابه». With the consequence that follows from it: «وإلا فالمحكم الصريح
ليس محلا للفتنة».

Ibn Kathir supplies the practical test, and a worked example so the reader is not
left with an abstraction: which verses does a man cite and which does he leave.
And he relays Aisha's report, in which the Prophet (peace be upon him) recited
this verse and then said what to do about the people in it.

The stop also keeps the waqf disagreement over «إلا الله» instead of quietly
choosing, because Saadi does not choose: he shows that the answer follows from
what «تأويل» is taken to mean, and that both are sound on their own reading.
Flattening that would be doing to this verse exactly what the verse warns about.

Usage: python verify_muhkam_claim.py
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


def tafsir(book, ayah=7, surah=3):
	path = BASE / "app" / "tafsir" / book / f"{surah}.js"
	payload = json.loads(path.read_text(encoding="utf-8").split("=", 1)[1].rstrip().rstrip(";"))
	return normalize(re.sub(r"\[\[.*?\]\]", " ", payload[str(ayah)], flags=re.S))


SAADI = [
	("حدُّ المحكم", "منه آيات محكمات أي: واضحات الدلالة، ليس فيها شبهة ولا إشكال"),
	("وأنّه الأكثر", "أي: أصله الذي يرجع إليه كل متشابه، وهي معظمه وأكثره"),
	("وحدُّ المتشابه", "أي: يلتبس معناها على كثير من الأذهان"),
	("والواجبُ", "فالواجب في هذا أن يرد المتشابه إلى المحكم والخفي إلى الجلي"),
	(
		"والداءُ عكسٌ لا نقص",
		"أي: يتركون المحكم الواضح ويذهبون إلى المتشابه، ويعكسون الأمر فيحملون المحكم على المتشابه",
	),
	(
		"ولازمُه",
		"وإلا فالمحكم الصريح ليس محلا للفتنة، لوضوح الحق فيه لمن قصده اتباعه",
	),
	(
		"وجوابُ مالك",
		"فقال مالك: الاستواء معلوم، والكيف مجهول، والإيمان به واجب، والسؤال عنه بدعة",
	),
	("وموقفُ الراسخين", "فيؤمنون بها ويكلون المعنى إلى الله فيسلمون ويسلمون"),
]

# The waqf disagreement, which the stop carries rather than settles.
THE_WAQF = "جمهورهم يقفون عندها، وبعضهم يعطف عليها"

IBN_KATHIR = [
	(
		"وصفُ الداء",
		"إنما يأخذون منه بالمتشابه الذي يمكنهم أن يحرفوه إلى مقاصدهم الفاسدة",
	),
	("ولمَ يتركون المحكم", "فأما المحكم فلا نصيب لهم فيه؛ لأنه دامغ لهم وحجة عليهم"),
	(
		"والمثالُ المضروب",
		"كما لو احتج النصارى بأن القرآن قد نطق بأن عيسى هو روح الله وكلمته ألقاها إلى مريم",
	),
]
AISHA = "فإذا رأيتم الذين يجادلون فيه فهم الذين عنى الله فاحذروهم"


def main():
	failures = []
	sa, ik = tafsir("saadi"), tafsir("ibnkathir")

	for label, phrase in SAADI:
		if normalize(phrase) not in sa:
			failures.append(f"Saadi not found ({label}): {phrase[:55]}")
	print(f"  OK: Saadi's {len(SAADI)} statements, including the obligation and the inversion")

	if normalize(THE_WAQF) not in sa:
		failures.append(
			"the waqf disagreement over «إلا الله» is gone. The stop carries it rather than "
			"settling it, because Saadi does not settle it, and flattening it here would be "
			"the exact fault this verse describes."
		)
	print("  OK: the waqf disagreement stands, jumhur stopping and some continuing")

	for label, phrase in IBN_KATHIR:
		if normalize(phrase) not in ik:
			failures.append(f"Ibn Kathir not found ({label}): {phrase[:55]}")
	if normalize(AISHA) not in ik:
		failures.append("Aisha's report and the Prophet's instruction on it are missing")
	print("  OK: Ibn Kathir's test, his worked example, and Aisha's report")

	# the verse's own wording, which the stop leans on twice
	raw = (BASE / "app" / "generated" / "quran_text.js").read_text(encoding="utf-8")
	verse = normalize(json.loads(raw.split("=", 1)[1].rstrip().rstrip(";"))["3:7"])
	for phrase in ("هن أم الكتاب", "فأما الذين في قلوبهم زيغ", "ابتغاء الفتنة وابتغاء تأويله"):
		if normalize(phrase) not in verse:
			failures.append(f"the verse no longer says «{phrase}»")
	print("  OK: the verse itself calls the clear ones the mother of the Book")

	if failures:
		print("\nCLAIM FAILED:", file=sys.stderr)
		for f in failures:
			print(f"  {f}", file=sys.stderr)
		sys.exit(1)
	print("\nAl Imran 7 claim holds.")


if __name__ == "__main__":
	main()
