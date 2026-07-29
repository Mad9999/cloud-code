"""The claim written into the stop at al-Baqara 143, on «أمة وسطا».

Two words that get quoted as a compliment the ummah pays itself. The stop says
they are not a description at all, they are a qualification for a job, and the
job is named in the same breath: «لتكونوا شهداء على الناس».

The evidence is unusually strong for a matter of meaning, because the Prophet
(peace be upon him) glossed the word himself. Ibn Kathir relays from Abu Sa'id,
in Bukhari and three others, the scene of Nuh being asked who will testify for
him and answering «محمد وأمته», with the gloss attached: «الوسط: العدل، فتدعون،
فتشهدون له بالبلاغ، ثم أشهد عليكم». Tabari carries the same by several isnads,
marfu', with the single word «عدولا».

And the stop keeps the disagreement that sits underneath, because it is real and
because flattening it would hand the reader a false certainty. Ibn Kathir reads
the word as «الخيار والأجود», best. Tabari's own linguistic view is the other
one, the part between two extremes, and he spells out which extremes: the ghuluw
of the Christians and the taqsir of the Jews. Then he does not leave the two
readings at war. He joins them: «وذلك معنى الخيار، لأن الخيار من الناس عدولهم».

That reconciliation is the load-bearing wall. If it disappears the stop is
picking a side in a dispute the imams did not treat as a dispute, so it is
tested here along with both readings it reconciles.

Usage: python verify_wasat_claim.py
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


def tafsir(book, ayah=143, surah=2):
	path = BASE / "app" / "tafsir" / book / f"{surah}.js"
	payload = json.loads(path.read_text(encoding="utf-8").split("=", 1)[1].rstrip().rstrip(";"))
	return normalize(re.sub(r"\[\[.*?\]\]", " ", payload[str(ayah)], flags=re.S))


# The Prophet's own gloss, and the scene it was given in.
MARFU = [
	("مشهدُ نوحٍ يوم القيامة", "يدعى نوح يوم القيامة فيقال له: هل بلغت؟ فيقول: نعم"),
	("ومن يشهد له", "فيقال لنوح: من يشهد لك؟ فيقول: محمد وأمته"),
	("والتفسيرُ ملحقٌ بالمشهد", "قال: الوسط : العدل، فتدعون، فتشهدون له بالبلاغ، ثم أشهد عليكم"),
	("وتخريجُه", "رواه البخاري والترمذي والنسائي وابن ماجه من طرق عن الأعمش"),
]
TABARI_MARFU = 'عن أبي سعيد، عن النبي ﷺ في قوله:"وكذلك جعلناكم أمة وسطا" قال، عدولا'

# The two readings, and the sentence that joins them.
READING_KHIYAR = [
	("ibnkathir", "والوسط هاهنا: الخيار والأجود"),
	("ibnkathir", "لنجعلكم خيار الأمم، لتكونوا يوم القيامة شهداء على الأمم"),
]
READING_BAYN = [
	(
		"ترجيحُ الطبريِّ اللغويّ",
		'وأنا أرى أن"الوسط" في هذا الموضع، هو"الوسط" الذي بمعنى: الجزء الذي هو بين الطرفين',
	),
	(
		"وتعيينُه الطرفين",
		"لتوسطهم في الدين، فلا هم أهل غلو فيه، غلو النصارى الذين غلوا بالترهب",
	),
	(
		"والطرفُ الآخر",
		"ولا هم أهل تقصير فيه، تقصير اليهود الذين بدلوا كتاب الله، وقتلوا أنبياءهم",
	),
]
THE_JOIN = 'وأما التأويل، فإنه جاء بأن"الوسط" العدل. وذلك معنى الخيار، لأن الخيار من الناس عدولهم'


def main():
	failures = []
	ik, tab = tafsir("ibnkathir"), tafsir("tabari")

	for label, phrase in MARFU:
		if normalize(phrase) not in ik:
			failures.append(f"the marfu' gloss is not where we cite it ({label}): {phrase[:55]}")
	if normalize(TABARI_MARFU) not in tab:
		failures.append("Tabari's marfu' «عدولا» is gone, so the gloss rests on one book only")
	print("  OK: the Prophet's own gloss «العدل» stands in two books, with its takhrij")

	for book, phrase in READING_KHIYAR:
		if normalize(phrase) not in tafsir(book):
			failures.append(f"the «الخيار» reading is missing from {book}: {phrase[:55]}")
	for label, phrase in READING_BAYN:
		if normalize(phrase) not in tab:
			failures.append(f"the «بين الطرفين» reading is missing ({label}): {phrase[:55]}")
	print("  OK: both readings stand, named, with Tabari's two extremes spelled out")

	if normalize(THE_JOIN) not in tab:
		failures.append(
			"Tabari's reconciliation is gone. Without it the stop would be taking a side in "
			"something the imams did not treat as a quarrel, which is the opposite of its point."
		)
	print("  OK: Tabari joins the two readings rather than setting them against each other")

	# the verse itself supplies the purpose, so the stop is not importing it
	raw = (BASE / "app" / "generated" / "quran_text.js").read_text(encoding="utf-8")
	verse = normalize(json.loads(raw.split("=", 1)[1].rstrip().rstrip(";"))["2:143"])
	for phrase in ("لتكونوا شهداء على الناس", "ويكون الرسول عليكم شهيدا"):
		if normalize(phrase) not in verse:
			failures.append(f"the verse no longer says «{phrase}», which the stop leans on")
	print("  OK: the verse names the purpose itself, and names it in both directions")

	if failures:
		print("\nCLAIM FAILED:", file=sys.stderr)
		for f in failures:
			print(f"  {f}", file=sys.stderr)
		sys.exit(1)
	print("\nal-Baqara 143 claim holds.")


if __name__ == "__main__":
	main()
