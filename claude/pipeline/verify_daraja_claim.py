"""The claim written into the stop at al-Baqara 228, held as a test.

Four words of this verse are quoted constantly, «وللرجال عليهن درجة», and the
other clause of the same sentence is quoted almost never. The stop says three
things about that, and all three are checkable.

First, that the imams treat the two clauses as one matter: Qurtubi gives two of
his numbered masa'il to «ولهن مثل الذي عليهن» and Ibn Abbas's practice under it,
and one to the daraja. His own division, not our counting.

Second, that the men with the most right to explain the Qur'an read the famous
four words as weight added to the man, not taken off him. Tabari rules: «وأولى
هذه الأقوال بتأويل الآية ما قاله ابن عباس، وهو أن الدرجة... الصفح من الرجل
لامرأته عن بعض الواجب عليها، وإغضاؤه لها عنه، وأداء كل الواجب لها عليه». And
his ground is textual: it comes «عقيب» the reciprocal clause.

Third, and this is the part the file exists to protect, that this is a real
ikhtilaf and the other reading is neither weak nor rare. Mujahid, Qatada, Zayd
ibn Aslam, Ibn Zayd, Saadi, Ibn Kathir and Qurtubi's own summing-up all read the
daraja as genuine precedence. A stop that gave the reader only Tabari's reading
would be doing exactly what it accuses others of: quoting the half that suits it.
So both sides are pinned here, and if either disappears from the books this test
fails and the stop must be rewritten.

Usage: python verify_daraja_claim.py
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


def tafsir(book, ayah=228, surah=2):
	path = BASE / "app" / "tafsir" / book / f"{surah}.js"
	payload = json.loads(path.read_text(encoding="utf-8").split("=", 1)[1].rstrip().rstrip(";"))
	return re.sub(r"\[\[.*?\]\]", " ", payload[str(ayah)], flags=re.S)


# Tabari's ruling, and the ground he rests it on.
TABARI_RULES = [
	(
		"ترجيحُه، وهو لقول ابن عبّاس",
		"وأولى هذه الأقوال بتأويل الآية ما قاله ابن عباس، وهو أن\"الدرجة\" التي ذكر الله "
		"تعالى ذكره في هذا الموضع، الصفح من الرجل لامرأته عن بعض الواجب عليها، وإغضاؤه لها "
		"عنه، وأداء كل الواجب لها عليه",
	),
	(
		"وحجّتُه نصّيّةٌ: موضعُ الجملة",
		"وذلك أن الله تعالى ذكره قال:\" وللرجال عليهن درجة\" عقيب قوله:\" ولهن مثل الذي عليهن بالمعروف\"",
	),
	(
		"وأنّ ظاهرَ الخبر معناه ندب",
		"وإن كان ظاهره ظاهر الخبر، فمعناه معنى ندب الرجال إلى الأخذ على النساء بالفضل",
	),
	("وأثرُ ابن عبّاسٍ الذي بنى عليه", "ما أحب أن أستنظف جميع حقي عليها"),
	("وأنّ الخلافَ معلَنٌ عنده", "اختلف أهل التأويل في تأويل ذلك"),
]

# Ibn Abbas in the other two books, on the other clause and on this one.
IBN_ABBAS = [
	(
		"ibnkathir",
		"إني لأحب أن أتزين للمرأة كما أحب أن تتزين لي المرأة؛ لأن الله يقول",
	),
	(
		"qurtubi",
		"الدرجة إشارة إلى حض الرجال على حسن العشرة، والتوسع للنساء في المال والخلق، "
		"أي أن الأفضل ينبغي أن يتحامل على نفسه",
	),
	("qurtubi", "قال ابن عطية: وهذا قول حسن بارع"),
]

# The other side, which the stop must carry. If these vanish, the stop is
# presenting a settled matter as settled in the wrong direction.
THE_OTHER_READING = [
	("tabari", "مجاهد", "قال: فضل ما فضله الله به عليها من الجهاد، وفضل ميراثه"),
	("tabari", "قتادة", "قال: للرجال درجة في الفضل على النساء"),
	("tabari", "زيد بن أسلم", "قال: إمارة"),
	("saadi", "السعدي", "أي: رفعة ورياسة, وزيادة حق عليها"),
	(
		"ibnkathir",
		"ابن كثير",
		"في الفضيلة في الخلق، والمنزلة، وطاعة الأمر، والإنفاق، والقيام بالمصالح",
	),
	(
		"qurtubi",
		"القرطبي في الجملة",
		"وعلى الجملة فدرجة تقتضي التفضيل، وتشعر بأن حق الزوج عليها أوجب من حقها عليه",
	),
]


def main():
	failures = []
	tab = normalize(tafsir("tabari"))

	for label, phrase in TABARI_RULES:
		if normalize(phrase) not in tab:
			failures.append(f"Tabari's ruling not found ({label}): {phrase[:60]}")
	print("  OK: Tabari rules for Ibn Abbas's reading, and grounds it in the clause order")

	for book, phrase in IBN_ABBAS:
		if normalize(phrase) not in normalize(tafsir(book)):
			failures.append(f"Ibn Abbas not found in {book}: {phrase[:60]}")
	print("  OK: Ibn Abbas applies the reciprocal clause to himself, and reads the daraja as a burden")

	for book, who, phrase in THE_OTHER_READING:
		if normalize(phrase) not in normalize(tafsir(book)):
			failures.append(
				f"the other reading is missing from {book} ({who}): {phrase[:50]}. "
				f"The stop presents this as a live ikhtilaf and must not become one-sided."
			)
	print(f"  OK: the other reading stands in {len(THE_OTHER_READING)} places, named and unweakened")

	# Qurtubi's own division of the verse, which is the stop's measurement.
	# Diacritics must come off first: the books are vowelled and our phrases are
	# not, so searching the raw text finds nothing and says so in a way that
	# sounds like a finding. It caught us on the first run of this very file.
	qur = DIACRITICS.sub("", tafsir("qurtubi"))
	start = qur.find("قوله تعالى: ﴿ولهن﴾")
	mid = qur.find("﴿وللرجال عليهن درجة﴾ أي منزلة")
	end = qur.find("(والله عزيز)")
	if not (0 < start < mid < end):
		failures.append("Qurtubi's masa'il no longer sit in the order the stop describes")
	else:
		print(
			f"  OK: Qurtubi spends {mid - start} chars on the reciprocal clause and Ibn Abbas's "
			f"grooming, {end - mid} on the daraja"
		)

	# and the limit (rule 29): Tabari does not deny that the word means rank
	if normalize('ومعنى"الدرجة"، الرتبة والمنزلة') not in tab:
		failures.append("Tabari's own gloss «الرتبة والمنزلة» is gone; the stop's limit was there")
	print("  OK: even Tabari glosses the word itself as rank, which the stop does not hide")

	if failures:
		print("\nCLAIM FAILED:", file=sys.stderr)
		for f in failures:
			print(f"  {f}", file=sys.stderr)
		sys.exit(1)
	print("\nal-Baqara 228 claim holds, both sides of it.")


if __name__ == "__main__":
	main()
