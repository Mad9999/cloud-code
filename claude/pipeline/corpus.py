"""Whole-Qur'an factual depth backbone (رقم القاعدة ١٢: كشفيّ لا مولَّد).

Ingests the word-by-word morphology of the entire Qur'an (6236 verses) and
builds computed, non-interpretive depth that reveals what is ALREADY there —
never invents meaning:

  * a root concordance: every triliteral root -> where it occurs across the
    whole Qur'an (this is the basis of ترابط السور — each word becomes a gate
    to everywhere its root appears);
  * per-verse roots and per-surah root profiles;
  * inter-surah links by shared distinctive roots.

Source: word-by-word morphology of the Quranic Arabic Corpus (Kais Dukes),
via the `mustafa0x/quran-morphology` mirror. Attribution kept; factual data.
"""

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
MORPH = BASE / "data" / "quran-morphology.txt"

ROOT_RE = re.compile(r"ROOT:([^|]+)")
LEM_RE = re.compile(r"LEM:([^|]+)")


def parse():
	"""Yield (surah, ayah, word, root, lemma) for every root-bearing token."""
	with open(MORPH, encoding="utf-8") as f:
		for line in f:
			line = line.rstrip("\n")
			if not line or "\t" not in line:
				continue
			parts = line.split("\t")
			if len(parts) < 4:
				continue
			loc, _form, _tag, feats = parts[:4]
			m = ROOT_RE.search(feats)
			if not m:
				continue
			s, a, w, _seg = loc.split(":")
			lem = LEM_RE.search(feats)
			yield int(s), int(a), int(w), m.group(1), (lem.group(1) if lem else "")


def build():
	roots = defaultdict(lambda: {"count": 0, "lemmas": Counter(), "ayahs": set()})
	verse_roots = defaultdict(list)      # (s,a) -> [root, ...] in word order
	surah_roots = defaultdict(Counter)   # s -> Counter(root)

	for s, a, w, root, lem in parse():
		r = roots[root]
		r["count"] += 1
		if lem:
			r["lemmas"][lem] += 1
		r["ayahs"].add((s, a))
		verse_roots[(s, a)].append((w, root))
		surah_roots[s][root] += 1

	# finalize roots: sorted unique ayah list + top lemma
	roots_out = {}
	for root, d in roots.items():
		ayahs = sorted(d["ayahs"])
		roots_out[root] = {
			"count": d["count"],
			"ayah_count": len(ayahs),
			"lemma": d["lemmas"].most_common(1)[0][0] if d["lemmas"] else "",
			"surahs": sorted({s for s, _ in ayahs}),
			"ayahs": [[s, a] for s, a in ayahs],
		}

	# per-surah profile: distinctive roots (appear only in this surah)
	root_surah_spread = {r: len(v["surahs"]) for r, v in roots_out.items()}
	surah_profile = {}
	for s, cnt in surah_roots.items():
		unique = sorted([r for r in cnt if root_surah_spread[r] == 1])
		surah_profile[s] = {
			"distinct_roots": len(cnt),
			"total_roots": sum(cnt.values()),
			"unique_roots": unique,          # roots found in NO other surah
			"top_roots": cnt.most_common(8),
		}

	return {
		"total_tokens_with_root": sum(v["count"] for v in roots_out.values()),
		"distinct_roots": len(roots_out),
		"roots": roots_out,
		"verse_roots": {f"{s}:{a}": [r for _w, r in sorted(v)] for (s, a), v in verse_roots.items()},
		"surah_profile": surah_profile,
	}


if __name__ == "__main__":
	c = build()
	print("distinct roots:", c["distinct_roots"], "| root-bearing tokens:", c["total_tokens_with_root"])
	top = sorted(c["roots"].items(), key=lambda kv: -kv[1]["count"])[:10]
	print("top roots:", [(r, d["count"]) for r, d in top])
	# a couple of discoveries
	single = [r for r, d in c["roots"].items() if len(d["surahs"]) == 1]
	print("roots appearing in only ONE surah:", len(single))
	most_unique = max(c["surah_profile"].items(), key=lambda kv: len(kv[1]["unique_roots"]))
	print("surah with most unique roots:", most_unique[0], "->", len(most_unique[1]["unique_roots"]))
