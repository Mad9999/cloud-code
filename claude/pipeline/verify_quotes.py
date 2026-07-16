"""Quote valve (deep-pass round 2, rule 23 tooling): verify that every
guillemet-quoted fragment in the tadabbur stops that claims to be Qur'anic
actually matches the Qur'an text letter-for-letter (after normalization).

A fragment that matches nothing is either a tafsir/hadith quote (fine, needs
eyes) or a misquoted ayah (an honesty bug) — both go to the review list.

Usage: python verify_quotes.py            (summary + review file)
"""

import json
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "data"
GEN = BASE / "app" / "generated"
OUT = BASE / "pipeline" / "quote_review.json"

DIACRITICS = re.compile(r"[ً-ْٰـۖ-ۭٓ-ٟ]")
MIN_LEN = 12  # shorter fragments are too generic to classify


def normalize(s):
	s = DIACRITICS.sub("", s)
	s = re.sub(r"[آأإٱ]", "ا", s)  # alef variants -> alef
	s = s.replace("ى", "ي")  # alef maqsura -> yaa
	s = re.sub(r"[ءؤئ]", "", s)  # hamza seats vary between editions (باؤوا/باءوا)
	s = s.replace("ة", "ت")  # rasm variants (مرضات/مرضاة, رحمت/رحمة)
	s = re.sub(r"[^ء-ي ]", " ", s)  # drop punctuation/digits
	s = re.sub(r"وا\b", "و", s)  # silent alef after waw (تتلوا/تتلو)
	return re.sub(r" +", " ", s).strip()


def squash(s):
	return s.replace(" ", "")  # rasm word-spacing varies (أين ما/أينما)


def load_quran():
	raw = (GEN / "quran_text.js").read_text(encoding="utf-8")
	payload = json.loads(raw.split("=", 1)[1].rstrip().rstrip(";"))
	# payload: flat {"surah:ayah": text}
	surahs = {}
	for key, text in payload.items():
		s, a = key.split(":")
		surahs.setdefault(int(s), {})[int(a)] = normalize(text)
	return {
		s: [ayat[n] for n in sorted(ayat)] for s, ayat in surahs.items()
	}


def iter_strings(node):
	if isinstance(node, str):
		yield node
	elif isinstance(node, dict):
		for v in node.values():
			yield from iter_strings(v)
	elif isinstance(node, list):
		for v in node:
			yield from iter_strings(v)


def fragments(text):
	for m in re.finditer(r"«([^»]+)»", text):
		# elisions inside a quote are checked piecewise
		for part in re.split(r"\.\.\.|…|\*", m.group(1)):
			part = part.strip()
			if len(normalize(part)) >= MIN_LEN:
				yield part


BOOKS = ("muyassar", "saadi", "ibnkathir", "baghawi", "qurtubi", "tabari")
_tafsir_cache = {}

# Surah names as our stops cite them, so a cross-surah quote can be checked
# against the right file rather than landing in the review list unexamined.
SURAH_NAMES = {
	"الفاتحة": 1, "البقرة": 2, "آل عمران": 3, "النساء": 4, "المائدة": 5,
	"الأنعام": 6, "الأعراف": 7, "الأنفال": 8, "التوبة": 9, "يونس": 10,
	"هود": 11, "يوسف": 12, "الرعد": 13, "إبراهيم": 14, "الحجر": 15,
	"النحل": 16, "الإسراء": 17, "الكهف": 18, "مريم": 19, "طه": 20,
	"الأنبياء": 21, "الحج": 22, "المؤمنون": 23, "النور": 24, "الفرقان": 25,
	"الشعراء": 26, "النمل": 27, "القصص": 28, "العنكبوت": 29, "الروم": 30,
	"لقمان": 31, "السجدة": 32, "الأحزاب": 33, "سبأ": 34, "فاطر": 35,
	"يس": 36, "الصافات": 37, "ص": 38, "الزمر": 39, "غافر": 40,
	"فصلت": 41, "الشورى": 42, "الزخرف": 43, "الدخان": 44, "الجاثية": 45,
	"الأحقاف": 46, "محمد": 47, "الفتح": 48, "الحجرات": 49, "ق": 50,
	"الذاريات": 51, "الطور": 52, "النجم": 53, "القمر": 54, "الرحمن": 55,
	"الواقعة": 56, "الحديد": 57, "المجادلة": 58, "الحشر": 59, "الممتحنة": 60,
	"الصف": 61, "الجمعة": 62, "المنافقون": 63, "التغابن": 64, "الطلاق": 65,
	"التحريم": 66, "الملك": 67, "القلم": 68, "الحاقة": 69, "المعارج": 70,
	"نوح": 71, "الجن": 72, "المزمل": 73, "المدثر": 74, "القيامة": 75,
	"الإنسان": 76, "المرسلات": 77, "النبأ": 78, "النازعات": 79, "عبس": 80,
	"التكوير": 81, "الانفطار": 82, "المطففين": 83, "الانشقاق": 84, "البروج": 85,
	"الطارق": 86, "الأعلى": 87, "الغاشية": 88, "الفجر": 89, "البلد": 90,
	"الشمس": 91, "الليل": 92, "الضحى": 93, "الشرح": 94, "التين": 95,
	"العلق": 96, "القدر": 97, "البينة": 98, "الزلزلة": 99, "العاديات": 100,
	"القارعة": 101, "التكاثر": 102, "العصر": 103, "الهمزة": 104, "الفيل": 105,
	"قريش": 106, "الماعون": 107, "الكوثر": 108, "الكافرون": 109, "النصر": 110,
	"المسد": 111, "الإخلاص": 112, "الفلق": 113, "الناس": 114,
}


def cited_surahs(doc):
	"""Surah numbers this document names, so cross-surah quotes are checked."""
	blob = json.dumps(doc, ensure_ascii=False)
	return sorted({n for name, n in SURAH_NAMES.items() if name in blob})


def tafsir_text(book, surah):
	key = (book, surah)
	if key not in _tafsir_cache:
		path = BASE / "app" / "tafsir" / book / f"{surah}.js"
		try:
			raw = path.read_text(encoding="utf-8")
			payload = json.loads(raw.split("=", 1)[1].rstrip().rstrip(";"))
			joined = " ".join(payload.values())
			# strip critical-apparatus footnotes ([[...]]) so quotes can
			# match across them; single [...] additions keep their word
			joined = re.sub(r"\[\[.*?\]\]", " ", joined, flags=re.S)
			_tafsir_cache[key] = squash(normalize(joined))
		except (OSError, ValueError):
			_tafsir_cache[key] = ""
	return _tafsir_cache[key]


def closest_ayah(norm, surahs, own):
	"""Best-overlap ayah in the stop's own surah, to expose near-miss
	misquotes (a real ayah with one word off) vs hadith/tafsir text."""
	if own not in surahs:
		return None
	words = set(norm.split())
	best, score = None, 0.0
	for i, ayah in enumerate(surahs[own], 1):
		aw = set(ayah.split())
		if not aw:
			continue
		s = len(words & aw) / max(len(words), 1)
		if s > score:
			best, score = i, s
	if best and score >= 0.6:
		return {"ayah": best, "overlap": round(score, 2), "text": surahs[own][best - 1]}
	return None


ARABIC = re.compile(r"[ء-ي]")
LINE_COMMENT = re.compile(r"^\s*(//|#)")


def code_lines(text):
	"""Yield (number, line) for lines that are not English prose about code.

	Docstrings and block comments are where we explain ourselves, in English,
	and English takes the em-dash. Skipping them is not a loophole: nothing in
	a comment reaches a reader of the app. The first cut of this guard skipped
	only `//` and `#` lines and so flagged its own docstring, which quotes the
	very dash it forbids.
	"""
	in_block = False
	for i, line in enumerate(text.split("\n"), 1):
		fences = line.count('"""') + line.count("'''")
		opens_block = "/*" in line and "*/" not in line
		if in_block:
			if "*/" in line or fences:
				in_block = False
			continue
		if fences == 1 or opens_block:
			in_block = True
			continue
		if LINE_COMMENT.match(line):
			continue
		yield i, line


def arabic_prose(line):
	"""Does an em-dash on this line sit in Arabic the reader will see?

	Counting letters to decide gets it backwards inside a template literal:
	`<b>${s.name} - ${s.revelation}</b>` is mostly Latin, and renders to the
	reader as pure Arabic. So the code around each dash is cleared away first
	and we judge what is actually left beside it.
	"""
	stripped = re.sub(r"\$\{[^{}]*\}", "ـ", line)  # a rendered value
	stripped = re.sub(r"<[^>]+>", " ", stripped)  # markup, not prose
	for m in re.finditer("—", stripped):
		window = stripped[max(0, m.start() - 30) : m.start() + 30]
		if ARABIC.search(window) or "ـ" in window:
			return True
	return False


def check_no_em_dash():
	"""The em-dash is not Arabic punctuation: it appears zero times across
	all six tafsirs (11.4M characters). It kept creeping back into our own
	Arabic by habit, so the valve guards the rule rather than the memory.

	The guard first watched data/ only, while the rule was about every Arabic
	text we write. It was the narrower thing that got obeyed: the app was
	rendering «البقرة — مدنية» to the reader's eye the whole time, and the
	scripts printed Arabic with dashes in it. A guard narrower than its rule
	teaches the rule's narrowness, so this one now walks everything we author.
	The imams' own books are not ours to police, and hold none anyway.
	"""
	offenders = []
	for pattern in ("data/*.json", "app/*.js", "app/*.html", "pipeline/*.py"):
		for f in sorted(BASE.glob(pattern)):
			bad = [
				(i, line.strip())
				for i, line in code_lines(f.read_text(encoding="utf-8"))
				if "—" in line and arabic_prose(line)
			]
			if bad:
				offenders.append((f.relative_to(BASE).as_posix(), bad))
	if offenders:
		print("EM-DASH FOUND in Arabic prose (rule 34):", file=sys.stderr)
		for name, bad in offenders:
			for i, line in bad:
				print(f"  {name}:{i}  {line[:90]}", file=sys.stderr)
		sys.exit(1)
	print("  OK: no em-dash in any Arabic prose we author (rule 34)")


def main():
	check_no_em_dash()
	surahs = load_quran()
	if not surahs:
		print("could not parse quran_text.js", file=sys.stderr)
		sys.exit(1)
	whole = {n: squash(" ".join(ayat)) for n, ayat in surahs.items()}
	total = matched_own = matched_other = tafsir_hits = unmatched = 0
	review = []
	for f in sorted(DATA.glob("tadabbur_*.json")):
		doc = json.loads(f.read_text(encoding="utf-8"))
		own = doc.get("n")
		if own is None and f.stem.split("_")[1].isdigit():
			own = int(f.stem.split("_")[1])  # legacy files (tadabbur_001)
		seen = set()
		for text in iter_strings(doc):
			for frag in fragments(text):
				spaced = normalize(frag)
				norm = squash(spaced)
				if norm in seen:
					continue
				seen.add(norm)
				total += 1
				if own in whole and norm in whole[own]:
					matched_own += 1
				elif any(norm in w for w in whole.values()):
					matched_other += 1
				else:
					# A stop may legitimately quote a mufassir on ANOTHER
					# surah's verse (Ibn Kathir on an-Nahl 101 inside a
					# Baqara stop, say). Search the surahs this file
					# actually cites, not just its own.
					book_hit = next(
						(
							b
							for s in [own, *cited_surahs(doc)]
							for b in BOOKS
							if norm in tafsir_text(b, s)
						),
						None,
					)
					if book_hit:
						tafsir_hits += 1
					else:
						unmatched += 1
						review.append(
							{
								"file": f.name,
								"surah": own,
								"fragment": frag,
								"closest": closest_ayah(spaced, surahs, own),
							}
						)
	OUT.write_text(
		json.dumps(review, ensure_ascii=False, indent=1), encoding="utf-8"
	)
	print(f"fragments checked: {total}")
	print(f"  matched in own surah:   {matched_own}")
	print(f"  matched elsewhere:      {matched_other} (cross-surah witness quotes)")
	print(f"  verbatim tafsir quotes: {tafsir_hits}")
	print(f"  unmatched (review):     {unmatched}  -> {OUT.name}")


if __name__ == "__main__":
	main()
