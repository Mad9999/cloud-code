"""The claim written into the stop at al-Baqara 285, held as a test.

The stop says the order in the closing verses runs one way and not the other:
the Companions said they could not bear 2:284, the Prophet (peace be upon him)
did not soften it but told them to say «سمعنا وأطعنا» rather than what the
people before them said, and only after «فلما أقر بها القوم وذلت بها ألسنتهم»
did the relief come. Submission first, then the easing.

It also says the connection to Bani Israel is not our reading but his: he named
«سمعنا وعصينا» himself, which is what al-Baqara records of them at 2:93, and
what the Qur'an sets against «سمعنا وأطعنا» explicitly at 4:46.

And it carries the disagreement over whether 2:284 was abrogated, which must not
be flattened either way: Muslim's hadith says «فلما فعلوا ذلك نسخها الله», while
Ibn Abbas says «فإنها لم تنسخ» and al-Hasan «هي محكمة لم تنسخ», and Ibn Jarir
chose that, on the ground that «لا يلزم من المحاسبة المعاقبة». That is the same
threshold he used at 2:256, applied 28 verses later against a report in Muslim,
so the stop pairs them; the test checks both ends of the pair, since if either
wording is not there the pairing is ours and not his.

Usage: python verify_khawatim_claim.py
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


# The story, from Muslim, as Ibn Kathir relays it under 2:284.
STORY = [
	("ثقلُها عليهم", "اشتد ذلك على أصحاب رسول الله ﷺ"),
	("وهيئتُهم", "ثم جثوا على الركب"),
	(
		"وصدقُهم في الشكوى",
		"كلفنا من الأعمال ما نطيق: الصلاة والصيام والجهاد والصدقة، وقد أنزل عليك هذه الآية ولا نطيقها",
	),
	(
		"وجوابُه ﷺ، وهو موضع القضيّة",
		"أتريدون أن تقولوا كما قال أهل الكتابين من قبلكم: سمعنا وعصينا؟ بل قولوا: سمعنا وأطعنا، غفرانك ربنا وإليك المصير",
	),
	("والتسليمُ قبل التخفيف", "فلما أقر بها القوم وذلت بها ألسنتهم"),
	("ثمّ التخفيف", "فلما فعلوا ذلك نسخها الله"),
	("ومخرجُه", "ورواه مسلم منفردا به"),
]

# The disagreement, both sides, in Ibn Kathir's report.
IKHTILAF = [
	("قولُ ابن عبّاس", "فإنها لم تنسخ"),
	("وقولُ الحسن", "وعن الحسن البصري أنه قال: هي محكمة لم تنسخ"),
	("واختيارُ ابن جرير وحجّتُه", "واختار ابن جرير ذلك، واحتج على أنه لا يلزم من المحاسبة المعاقبة"),
	("وشاهدُه من الصحيحين", "فإني قد سترتها عليك في الدنيا وأنا أغفرها لك اليوم"),
	("وتخريجُه", "وهذا الحديث مخرج في الصحيحين"),
]

# The same threshold at 2:256, so the pair is his and not ours.
TABARI_256 = "أن الناسخ غير كائن ناسخا إلا ما نفى حكم المنسوخ، فلم يجز اجتماعهما"

SAADI_285 = [
	"ثبت عنه -صلى الله عليه وسلم- أن من قرأ هاتين الآيتين في ليلته كفتاه",
	"ويؤخذ من هنا قاعدة التيسير ونفي الحرج في أمور الدين كلها",
]


def main():
	failures = []
	q = quran()
	k284 = tafsir("ibnkathir", 284)

	for label, phrase in STORY:
		if normalize(phrase) not in k284:
			failures.append(f"the story is not as we tell it ({label}): {phrase}")
	print("  OK: the story runs submission first and easing after, verbatim from Muslim")

	# the contrast is his, not ours: he named their word, and the Qur'an has it
	if "سمعنا وعصينا" not in q["2:93"]:
		failures.append("2:93 does not carry «سمعنا وعصينا», so the arc we draw is not there")
	if "سمعنا وأطعنا" not in q["2:285"]:
		failures.append("2:285 does not carry «سمعنا وأطعنا»")
	if not ("سمعنا وعصينا" in q["4:46"] and "سمعنا وأطعنا" in q["4:46"]):
		failures.append("4:46 no longer sets the two sayings against each other")
	# sort by number, not as text: '24:51' sorts before '2:285' as a string, and
	# our first pass wrote the expected list the way a reader would order it and
	# then failed on its own ordering rather than on anything in the Qur'an
	def by_place(k):
		return [int(x) for x in k.split(":")]

	said_disobey = sorted((k for k, v in q.items() if "سمعنا وعصينا" in v), key=by_place)
	said_obey = sorted((k for k, v in q.items() if "سمعنا وأطعنا" in v), key=by_place)
	if said_disobey != ["2:93", "4:46"] or said_obey != ["2:285", "4:46", "5:7", "24:51"]:
		failures.append(f"the two sayings moved: {said_disobey} / {said_obey}")
	print("  OK: he named their word, al-Baqara records it at 2:93, and 4:46 sets the two side by side")

	for label, phrase in IKHTILAF:
		if normalize(phrase) not in k284:
			failures.append(f"the disagreement is not carried ({label}): {phrase}")
	print("  OK: both sides of the abrogation dispute are in Ibn Kathir, with Ibn Jarir's ground")

	if normalize(TABARI_256) not in tafsir("tabari", 256):
		failures.append("Tabari's threshold at 2:256 is gone, so the pairing has no second end")
	print("  OK: it is the same threshold he set at 2:256, so the pair is his")

	saadi = tafsir("saadi", 285)
	for phrase in SAADI_285:
		if normalize(phrase) not in saadi:
			failures.append(f"Saadi's words not found: {phrase}")
	# 286 is empty and 285 speaks for it; if that ever changes, the citation must
	path = BASE / "app" / "tafsir" / "saadi" / "2.js"
	entries = json.loads(path.read_text(encoding="utf-8").split("=", 1)[1].rstrip().rstrip(";"))
	if entries["286"].strip():
		failures.append("Saadi's 286 is no longer empty: cite him there, not at 285")
	print("  OK: Saadi's words are cited at 285, which is where his prose for both verses sits")

	if failures:
		print("\nCLAIM FAILED:", file=sys.stderr)
		for f in failures:
			print(f"  {f}", file=sys.stderr)
		sys.exit(1)
	print("\nal-Baqara 285 claim holds.")


if __name__ == "__main__":
	main()
