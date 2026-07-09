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


def main():
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
					book_hit = next(
						(b for b in BOOKS if norm in tafsir_text(b, own)), None
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
