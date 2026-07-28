"""The claim written into the stop at al-Baqara 177.

Saadi spends more of himself on this verse than on any other in the surah but
one: 4.57x his average share, second of 271 blocks, behind only the debt verse.
Qurtubi passes over it at 1.41x. That split, the imam of meanings stopping where
the imam of rulings walks on, is the signature the fifth tanbih under rule 33
describes, and it says: this verse teaches a way, not a ruling.

The stop says four things and each is checked here.

That the verse answers «what is birr» by first denying something, and that the
something is what the surah had just spent ten verses on. Ibn Kathir supplies
the connection in his own words rather than us inferring it.

That Saadi calls the arguing itself «العناء الذي ليس تحته إلا الشقاق والخلاف».

That the answer is a structure and not a heap: seventeen items in five groups,
counted off the wording of the verse itself and not off any imam's brackets or
our own arrangement.

And that Ibn Kathir relays the athar of Abu Dharr, in which a man asks the
Prophet (peace be upon him) about iman and is answered with this verse, and then
grades it broken twice. That pairing is the point: he neither buries the report
nor sells it. A stop that used the athar without his grading would be taking the
half that helps.

Usage: python verify_birr_claim.py
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


def tafsir(book, ayah=177, surah=2):
	path = BASE / "app" / "tafsir" / book / f"{surah}.js"
	payload = json.loads(path.read_text(encoding="utf-8").split("=", 1)[1].rstrip().rstrip(";"))
	return re.sub(r"\[\[.*?\]\]", " ", payload[str(ayah)], flags=re.S)


def quran():
	raw = (BASE / "app" / "generated" / "quran_text.js").read_text(encoding="utf-8")
	return json.loads(raw.split("=", 1)[1].rstrip().rstrip(";"))


# The verse's own structure. Counted off the revelation, not off a commentator's
# brackets and not off an arrangement of ours. Saadi brackets 21 segments here,
# which includes a witness verse from al-Imran and his closing; that number would
# have been ours dressed as his.
GROUPS = {
	"المؤمنُ به": ["بالله", "واليوم الآخر", "والملائكة", "والكتاب", "والنبيين"],
	"المُعطَون": [
		"ذوي القربى", "واليتامى", "والمساكين", "وابن السبيل", "والسائلين", "وفي الرقاب",
	],
	"العملُ المفروض": ["وأقام الصلاة", "وآتى الزكاة"],
	"العهد": ["والموفون بعهدهم إذا عاهدوا"],
	"مواطنُ الصبر": ["في البأساء", "والضراء", "وحين البأس"],
}
TOTAL = 17

# Ibn Kathir gives the occasion, so the link to the qibla is his and not ours.
IBN_KATHIR = [
	(
		"وصفُه للآية",
		"اشتملت هذه الآية الكريمة، على جمل عظيمة، وقواعد عميمة، وعقيدة مستقيمة",
	),
	(
		"وربطُها بالقبلة، وهو ربطُه لا ربطُنا",
		"فإن الله تعالى لما أمر المؤمنين أولا بالتوجه إلى بيت المقدس، ثم حولهم إلى الكعبة، "
		"شق ذلك على نفوس طائفة من أهل الكتاب وبعض المسلمين",
	),
	(
		"وتحريرُه لموضع البرّ",
		"وليس في لزوم التوجه إلى جهة من المشرق إلى المغرب بر ولا طاعة، إن لم يكن عن أمر الله وشرعه",
	),
]

# The athar and its grading, which must travel together.
ATHAR = "أنه سأل رسول الله ﷺ: ما الإيمان؟ فتلا عليه"
GRADINGS = ["وهذا منقطع؛ فإن مجاهدا لم يدرك أبا ذر", "رواه ابن مردويه، وهذا أيضا منقطع"]

SAADI = [
	("الجدالُ في الجهة عناء", "فيكون كثرة البحث فيه والجدال من العناء الذي ليس تحته إلا الشقاق والخلاف"),
	("ولمَ قيل «على حبه»", "بين به أن المال محبوب للنفوس, فلا يكاد يخرجه العبد"),
	("والإخراجُ مع الحبّ برهان", "فمن أخرجه مع حبه له تقربا إلى الله تعالى, كان هذا برهانا لإيمانه"),
	("وأشقُّ صوره", "أن يتصدق وهو صحيح شحيح, يأمل الغنى, ويخشى الفقر"),
	("ولمَ سُمّوا صادقين", "لأن أعمالهم صدقت إيمانهم"),
	("والعهدُ يجمع الدين", "لأن الوفاء بالعهد, يدخل فيه الدين كله"),
]


def main():
	failures = []
	verse = DIACRITICS.sub("", quran()["2:177"])
	flat = normalize(verse)

	counted = 0
	for group, items in GROUPS.items():
		missing = [x for x in items if normalize(x) not in flat]
		if missing:
			failures.append(f"the verse no longer carries {missing} under «{group}»")
		counted += len(items) - len(missing)
	if counted != TOTAL:
		failures.append(f"the count is {counted}, not the {TOTAL} the stop tells the reader")
	print(f"  OK: {counted} items in {len(GROUPS)} groups, all read off the verse's own wording")

	ik = normalize(tafsir("ibnkathir"))
	for label, phrase in IBN_KATHIR:
		if normalize(phrase) not in ik:
			failures.append(f"Ibn Kathir's words not found ({label}): {phrase[:60]}")
	print("  OK: the link to the qibla is Ibn Kathir's own, stated in his own words")

	if normalize(ATHAR) not in ik:
		failures.append("the Abu Dharr athar is gone from Ibn Kathir")
	for g in GRADINGS:
		if normalize(g) not in ik:
			failures.append(
				f"Ibn Kathir's grading of the athar is missing: {g}. The stop must never "
				f"carry the report without the grading that travels with it."
			)
	print("  OK: the athar and both of Ibn Kathir's «منقطع» rulings on it are present")

	sa = normalize(tafsir("saadi"))
	for label, phrase in SAADI:
		if normalize(phrase) not in sa:
			failures.append(f"Saadi's words not found ({label}): {phrase[:60]}")
	print("  OK: Saadi's reading of the arguing, of «على حبه», and of «صدقوا» is verbatim")

	# and the measurement the stop rests its existence on
	sys.path.insert(0, str(BASE / "pipeline"))
	from measure_attention import measure

	s, q = measure("saadi", 2, 177), measure("qurtubi", 2, 177)
	if s["rank"] > 3:
		failures.append(f"Saadi no longer peaks here: rank {s['rank']}/{s['of']}")
	if q["ratio"] > 2.0:
		failures.append(
			f"Qurtubi is no longer passing over it at {q['ratio']:.2f}x, so the stop's "
			f"reading of the split between the two imams needs redoing"
		)
	print(
		f"  OK: Saadi {s['ratio']:.2f}x rank {s['rank']}/{s['of']}, Qurtubi {q['ratio']:.2f}x: "
		f"meaning stops where rulings walk on"
	)

	if failures:
		print("\nCLAIM FAILED:", file=sys.stderr)
		for f in failures:
			print(f"  {f}", file=sys.stderr)
		sys.exit(1)
	print("\nal-Baqara 177 claim holds.")


if __name__ == "__main__":
	main()
