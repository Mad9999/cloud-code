"""The claim written into the stop at al-Muddaththir 31, which judges this project.

The Qur'an states a number, nineteen, and then in the very next verse says what
the number is for: «وما جعلنا عدتهم إلا فتنة للذين كفروا». A test. Ibn Kathir
puts it plainly: «إنما ذكرنا عدتهم أنهم تسعة عشر اختبارا منا للناس».

And he records what actually happened when people first heard it. Abu Jahl did
arithmetic with it on the spot: «أما يستطيع كل عشرة منكم لواحد منهم فتغلبونهم؟»
And Abu al-Ashaddayn volunteered a division of labour: «اكفوني منهم اثنين وأنا
أكفيكم منهم سبعة عشر». The first human response to a revealed number was to
calculate with it, and that calculation was the calculation of disbelief.

This project counts. It counted twenty-nine surahs to check Ibn Kathir, and
al-Baqara's letters to check his tally, and «يحيي ويميت» across the mushaf. So
this verse is not a stop about other people. The test it names is one we are
standing inside, and the stop says so.

Held here: the sabab in Ibn Kathir's own words, the verse's own statement of
purpose, the four groups it says the number sorts people into, and Saadi's
instruction on what to do with a revealed number, «والواجب أن يتلقى ما أخبر الله
به ورسوله بالتسليم». If any of those leaves the books, the stop is making a claim
it can no longer support.

Usage: python verify_number_claim.py
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


def tafsir(book, ayah=31, surah=74):
	path = BASE / "app" / "tafsir" / book / f"{surah}.js"
	payload = json.loads(path.read_text(encoding="utf-8").split("=", 1)[1].rstrip().rstrip(";"))
	return normalize(re.sub(r"\[\[.*?\]\]", " ", payload[str(ayah)], flags=re.S))


def quran():
	raw = (BASE / "app" / "generated" / "quran_text.js").read_text(encoding="utf-8")
	return json.loads(raw.split("=", 1)[1].rstrip().rstrip(";"))


# What happened when people first heard a number from revelation.
THE_SABAB = [
	(
		"حسابُ أبي جهل",
		"وذلك رد على مشركي قريش حين ذكر عدد الخزنة، فقال أبو جهل: يا معشر قريش، أما يستطيع "
		"كل عشرة منكم لواحد منهم فتغلبونهم",
	),
	(
		"وقسمةُ أبي الأشدّين",
		"يا معشر قريش، اكفوني منهم اثنين وأنا أكفيكم منهم سبعة عشر، إعجابا منه بنفسه",
	),
	("وتصريحُ ابن كثيرٍ بالغرض", "إنما ذكرنا عدتهم أنهم تسعة عشر اختبارا منا للناس"),
]

# Saadi on what a revealed number is for, and what is owed to it.
SAADI = [
	(
		"مقاصدُ الآية",
		"وهذه مقاصد جليلة، يعتني بها أولو الألباب، وهي السعي في اليقين, وزيادة الإيمان في كل وقت",
	),
	("ودفعُ الشبهة", "ودفع الشكوك والأوهام التي تعرض في مقابلة الحق"),
	("والعددُ يفرز", "ومميزا للكاذبين من الصادقين"),
	("والواجبُ", "والواجب أن يتلقى ما أخبر الله به ورسوله بالتسليم"),
	(
		"وعلّتُه",
		"فإذا كنتم جاهلين بجنوده، وأخبركم بها العليم الخبير، فعليكم أن تصدقوا خبره، من غير "
		"شك ولا ارتياب",
	),
	(
		"والوجهُ الآخرُ للفتنة",
		"ومن أضله، جعل ما أنزله على رسوله زيادة شقاء عليه وحيرة، وظلمة في حقه",
	),
]

# The verse sorts hearers, and the stop counts the groups off the verse itself.
GROUPS = [
	"ليستيقن الذين أوتوا الكتاب",
	"ويزداد الذين آمنوا إيمانا",
	"ولا يرتاب الذين أوتوا الكتاب والمؤمنون",
	"وليقول الذين في قلوبهم مرض والكافرون ماذا أراد الله بهذا مثلا",
]


def main():
	failures = []
	q = quran()

	if normalize("عليها تسعة عشر") not in normalize(q["74:30"]):
		failures.append("74:30 no longer carries the number the stop is about")
	if normalize("وما جعلنا عدتهم إلا فتنة للذين كفروا") not in normalize(q["74:31"]):
		failures.append("the verse's own statement that the number is a fitna is gone")
	print("  OK: the number stands in 74:30 and the verse names it a fitna in 74:31")

	verse = normalize(q["74:31"])
	for g in GROUPS:
		if normalize(g) not in verse:
			failures.append(f"the verse no longer sorts hearers by «{g[:40]}»")
	print(f"  OK: the verse itself names {len(GROUPS)} responses to the number")

	ik = tafsir("ibnkathir")
	for label, phrase in THE_SABAB:
		if normalize(phrase) not in ik:
			failures.append(f"the sabab is not where we cite it ({label}): {phrase[:50]}")
	print("  OK: Abu Jahl's arithmetic and Ibn Kathir's statement of purpose, verbatim")

	sa = tafsir("saadi")
	for label, phrase in SAADI:
		if normalize(phrase) not in sa:
			failures.append(f"Saadi's words not found ({label}): {phrase[:50]}")
	print("  OK: Saadi on what a revealed number is for and what is owed to it, verbatim")

	# The stop turns this on us, so the turning has to be true: we do count.
	counted = [
		p.name
		for p in (BASE / "pipeline").glob("verify_*.py")
		if "re.findall" in p.read_text(encoding="utf-8")
		or "len(" in p.read_text(encoding="utf-8")
	]
	if len(counted) < 3:
		failures.append(
			"the stop tells the reader this project counts, and the project has stopped "
			"counting, so that sentence is now false about us"
		)
	print(f"  OK: {len(counted)} of our own valves count things, so the stop's turn on us is true")

	if failures:
		print("\nCLAIM FAILED:", file=sys.stderr)
		for f in failures:
			print(f"  {f}", file=sys.stderr)
		sys.exit(1)
	print("\nal-Muddaththir 31 claim holds, and it holds against us.")


if __name__ == "__main__":
	main()
