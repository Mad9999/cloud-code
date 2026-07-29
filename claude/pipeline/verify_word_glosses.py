# -*- coding: utf-8 -*-
"""Every word gloss that reaches a reader must say where it came from.

Rule 26h, third occurrence. `verify_reaches_reader.py` discovers the fields it
guards by walking nodes that carry an integer `n`. Word entries key on `i`, so
their fields were never in the guarded set, and twenty-six glosses in al-Fatiha
sat on the most-read page of the app in our own words with no attribution --
several of them Saadi's sentences reworded, which turns a quotation into a claim
of our own. A guard that walks a shape we described is blind to every shape we
did not.

This walks the data for *any* node that looks like a word entry, and requires:
  - a non-empty `source`
  - and, if the gloss quotes inside guillemets, that the quote is verbatim in
    one of the six books for that surah.
"""
import io
import json
import re
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
ROOT = Path(__file__).resolve().parent.parent
DIA = re.compile(r"[ً-ْٰـۖ-ۭٓ-ٟ]")
BOOKS = ("muyassar", "saadi", "ibnkathir", "baghawi", "qurtubi", "tabari")
_corpus = {}


def norm(s):
	s = DIA.sub("", s); s = re.sub(r"[آأإٱ]", "ا", s); s = s.replace("ى", "ي")
	s = re.sub(r"[ءؤئ]", "", s); s = s.replace("ة", "ت"); s = re.sub(r"[^ء-ي ]", " ", s)
	s = re.sub(r"وا\b", "و", s)
	return re.sub(r" +", " ", s).strip().replace(" ", "")


def corpus(surah):
	if surah not in _corpus:
		blob = ""
		for b in BOOKS:
			f = ROOT / 'app' / 'tafsir' / b / f'{surah}.js'
			if not f.exists():
				continue
			d = json.loads(f.read_text(encoding='utf-8').split('=', 1)[1].rstrip().rstrip(';'))
			blob += " " + " ".join(re.sub(r'\[\[.*?\]\]', ' ', v, flags=re.S) for v in d.values())
		_corpus[surah] = norm(blob)
	return _corpus[surah]


def words(node, out=None):
	"""Any dict carrying a gloss is a word entry, whatever else it keys on."""
	if out is None:
		out = []
	if isinstance(node, dict):
		if 'gloss' in node:
			out.append(node)
		for v in node.values():
			words(v, out)
	elif isinstance(node, list):
		for v in node:
			words(v, out)
	return out


def surah_of(path, doc):
	if isinstance(doc, dict):
		for k in ('surah', 'n'):
			if isinstance(doc.get(k), int):
				return doc[k]
	m = re.search(r'(\d{1,3})', path.stem)
	return int(m.group(1)) if m else None


def main():
	problems, checked = [], 0
	for path in sorted((ROOT / 'data').glob('*.json')):
		try:
			doc = json.loads(path.read_text(encoding='utf-8'))
		except Exception:
			continue
		found = words(doc)
		if not found:
			continue
		surah = surah_of(path, doc)
		for w in found:
			checked += 1
			where = f"{path.name} {w.get('text', '?')}"
			src = (w.get('source') or '').strip()
			if not src:
				problems.append(f"{where}: شرحٌ بلا مصدر -- «{w['gloss'][:50]}»")
				continue
			if surah is None:
				continue
			hay = corpus(surah)
			for m in re.finditer(r'«([^»]+)»', w['gloss']):
				frag = m.group(1).replace('**', '').strip()
				if len(norm(frag)) >= 8 and norm(frag) not in hay:
					problems.append(f"{where}: اقتباسٌ لم يثبت في كتب السورة -- «{frag[:60]}»")

	print(f"  word glosses checked:   {checked}")
	if problems:
		print(f"  >>> {len(problems)} مأخذًا:")
		for p in problems:
			print(f"      {p}")
		sys.exit(1)
	print("  OK: every gloss names its source, and every quotation in one is verbatim")


if __name__ == '__main__':
	main()
