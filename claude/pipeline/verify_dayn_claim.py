"""The claim written into the stop at al-Baqara 282, held as a test.

The stop says: the longest verse in the Book of God is about writing down a
loan, and it is not long by a little; that both the imam of rulings and the
imam of meanings spend more on it than on any other verse in the surah, which
they rarely agree on; that Saadi draws from this one place as many benefits as
from all the rest of al-Baqara together; and that he says in his own words
that learning to write is a matter of religion.

Two honesties are pinned here because both were tempting to drop.

Saadi opens «احتوت هاتان الآيتان», so his benefits cover 282 and 283 together,
and his last of them are about the pledge, which is 283's subject. The stop
must not credit them to one verse.

And the count depends on how you count. With the colon it is 31 here against 31
in all the other 285 verses; by the bare word it is 31 against 34. The first is
the prettier number, so the test holds both: the claim has to survive either
way or it is not a claim, it is a choice of ruler.

Usage: python verify_dayn_claim.py
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
	return json.loads(raw.split("=", 1)[1].rstrip().rstrip(";"))


def tafsir(book, surah=2):
	path = BASE / "app" / "tafsir" / book / f"{surah}.js"
	payload = json.loads(path.read_text(encoding="utf-8").split("=", 1)[1].rstrip().rstrip(";"))
	return {k: re.sub(r"\[\[.*?\]\]", " ", v, flags=re.S) for k, v in payload.items()}


def blocks(entries):
	grouped = {}
	for ayah, text in entries.items():
		grouped.setdefault(text, []).append(int(ayah))
	return [(sorted(a), len(t)) for t, a in grouped.items()]


def rank_of(book, ayah):
	bl = blocks(tafsir(book))
	shares = sorted(((size / len(a), min(a)) for a, size in bl), reverse=True)
	average = sum(s for s, _ in shares) / len(shares)
	span, size = next((a, s) for a, s in bl if ayah in a)
	return (size / len(span)) / average, [s for _, s in shares].index(min(span)) + 1, len(shares)


# Saadi's own words, which are the stop's spine.
SAADI_WORDS = [
	("أنّ الفوائد للآيتين لا لآية", "احتوت هاتان الآيتان"),
	("لا يُقترح أكمل منها", "الإصلاحات التي لا يقترح العقلاء أعلى ولا أكمل منها"),
	("تعلّمُ الكتابة من الدين", "أن تعلم الكتابة من الأمور الدينية"),
	(
		"وتعليمُ الدنيا كتعليم العبادة",
		"فمنه أيضا تعليم الأمور الدنيوية المتعلقة بالمعاملات، فإن الله تعالى حفظ على العباد أمور دينهم ودنياهم",
	),
	("ودقّتُه في «فسوق بكم»", "لم يقل: \"فأنتم فساق\" أو \"فاسقون\"، بل قال: فإنه فسوق بكم"),
]


def main():
	failures = []

	# 1) the longest verse, and not by a little
	q = quran()
	by_char = sorted(((len(strip_marks(t).replace(" ", "")), k) for k, t in q.items()), reverse=True)
	by_word = sorted(((len(strip_marks(t).split()), k) for k, t in q.items()), reverse=True)
	if by_char[0][1] != "2:282" or by_word[0][1] != "2:282":
		failures.append(f"2:282 is not the longest: {by_char[0]}, {by_word[0]}")
	if by_char[0][0] < by_char[1][0] * 1.4 or by_word[0][0] < by_word[1][0] * 1.4:
		failures.append("the gap to the runner-up is smaller than the stop claims")
	print(
		f"  OK: 2:282 is the longest verse, {by_char[0][0]} chars to {by_char[1][0]} "
		f"({by_char[1][1]}), {by_word[0][0]} words to {by_word[1][0]}"
	)

	# 2) both imams peak here, which is the unusual part
	for book in ("saadi", "qurtubi"):
		ratio, rank, of = rank_of(book, 282)
		if rank != 1:
			failures.append(f"{book} does not peak at 282: rank {rank}/{of} at {ratio:.2f}x")
		print(f"  OK: {book} peaks at 282, {ratio:.2f}x, {rank} of {of} blocks")

	# 3) the count, either way of counting
	saadi = tafsir("saadi")
	for pattern, label in ((r"ومنها:", "with the colon"), (r"\bومنها\b", "by the bare word")):
		here = len(re.findall(pattern, saadi["282"]))
		rest = sum(len(re.findall(pattern, v)) for k, v in saadi.items() if k != "282")
		runner = max(len(re.findall(pattern, v)) for k, v in saadi.items() if k != "282")
		if here < rest * 0.9:
			failures.append(f"the count does not hold {label}: {here} here, {rest} in the rest")
		if here < runner * 4:
			failures.append(f"the gap to the runner-up verse is small {label}: {here} vs {runner}")
		print(f"  OK: {label}, {here} benefits here against {rest} in the other 285, runner-up {runner}")

	# 4) Saadi's words
	saadi_text = normalize(saadi["282"])
	for label, phrase in SAADI_WORDS:
		if normalize(phrase) not in saadi_text:
			failures.append(f"Saadi's words not found ({label}): {phrase}")
	print("  OK: Saadi says learning to write is a matter of religion, in his own words")

	# 5) the limit: his benefits cover 283 too, and 283 is a separate text
	if saadi["282"] == saadi["283"]:
		failures.append("282 and 283 are one text: the stop's framing of the count must change")
	if normalize("مشروعية الوثيقة بالحقوق، وهي الرهون والضمانات") not in saadi_text:
		failures.append("the pledge benefits are not under 282, so the 'two verses' caveat is wrong")
	print("  OK: his benefits reach into 283's subject, so the stop credits them to both")

	if failures:
		print("\nCLAIM FAILED:", file=sys.stderr)
		for f in failures:
			print(f"  {f}", file=sys.stderr)
		sys.exit(1)
	print("\nal-Baqara 282 claim holds.")


if __name__ == "__main__":
	main()
