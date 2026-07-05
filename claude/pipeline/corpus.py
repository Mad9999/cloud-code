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


def parse_all():
	"""Yield every morphological token: (s, a, w, seg, form, root|None)."""
	with open(MORPH, encoding="utf-8") as f:
		for line in f:
			line = line.rstrip("\n")
			if not line or "\t" not in line:
				continue
			parts = line.split("\t")
			if len(parts) < 4:
				continue
			loc, form, _tag, feats = parts[:4]
			s, a, w, seg = loc.split(":")
			m = ROOT_RE.search(feats)
			yield int(s), int(a), int(w), int(seg), form, (m.group(1) if m else None)


def build_explorer():
	"""Whole-Qur'an payload for the Root Explorer (all 114 surahs). Single pass:
	reconstruct each verse's words (segment forms concatenated, with the stem's
	root) + a full root concordance. Each word of the whole Qur'an becomes a
	gate to everywhere its root appears. Computed facts — never generated."""
	words = defaultdict(lambda: defaultdict(lambda: {"text": "", "root": None}))
	roots = defaultdict(lambda: {"count": 0, "lemmas": Counter(), "ayahs": set(), "surahs": set()})
	surah_root_counts = defaultdict(Counter)
	for s, a, w, _seg, form, root in parse_all():
		e = words[(s, a)][w]
		e["text"] += form
		if root:
			e["root"] = root
			r = roots[root]
			r["count"] += 1
			r["ayahs"].add((s, a))
			r["surahs"].add(s)
			surah_root_counts[s][root] += 1

	verse_words = {}
	for (s, a), wd in words.items():
		verse_words[f"{s}:{a}"] = [[wd[w]["text"], wd[w]["root"]] for w in sorted(wd)]

	root_spread = {r: len(d["surahs"]) for r, d in roots.items()}
	roots_out = {}
	for r, d in roots.items():
		roots_out[r] = {
			"count": d["count"], "ayah_count": len(d["ayahs"]),
			"surah_count": len(d["surahs"]),
			"ayahs": sorted([[s, a] for s, a in d["ayahs"]]),
		}
	surah_profile = {}
	for s, cnt in surah_root_counts.items():
		surah_profile[s] = {
			"top_roots": cnt.most_common(6),
			"unique_roots": sum(1 for r in cnt if root_spread[r] == 1),
		}

	with open(BASE / "data" / "surah_meta.json", encoding="utf-8") as f:
		meta = json.load(f)
	surah_names = {n: m["name"] for n, m in meta.items()}
	surah_ayahs = {n: m["ayahs"] for n, m in meta.items()}
	surah_type = {n: ("مكية" if m["revelationType"] == "Meccan" else "مدنية") for n, m in meta.items()}

	return {
		"verse_words": verse_words, "roots": roots_out,
		"surah_names": surah_names, "surah_ayahs": surah_ayahs,
		"surah_type": surah_type, "surah_profile": surah_profile,
		"distinct_roots_total": len(roots_out),
	}


def build_surah_map(top_k=6):
	"""Inter-surah connection map: link each surah to the others that 'speak the
	same language' — highest cosine similarity over their root vectors, weighted
	so RARE shared roots count more than ubiquitous ones (أله/قول are everywhere).
	Also records the distinctive roots that bind each pair. Computed facts."""
	import math
	surah_roots = defaultdict(Counter)
	for s, _a, _w, _seg, _form, root in parse_all():
		if root:
			surah_roots[s][root] += 1
	surahs = sorted(surah_roots)
	n = len(surahs)
	df = Counter()
	for s in surahs:
		for r in surah_roots[s]:
			df[r] += 1
	idf = {r: math.log(n / df[r]) for r in df}

	def vec(s):
		return {r: (1 + math.log(c)) * idf[r] for r, c in surah_roots[s].items()}

	vecs = {s: vec(s) for s in surahs}
	norms = {s: math.sqrt(sum(x * x for x in v.values())) or 1 for s, v in vecs.items()}

	def sim(a, b):
		va, vb = vecs[a], vecs[b]
		common = set(va) & set(vb)
		return sum(va[r] * vb[r] for r in common) / (norms[a] * norms[b]) if common else 0.0

	def shared(a, b):
		common = set(surah_roots[a]) & set(surah_roots[b])
		return [r for r in sorted(common, key=lambda r: -idf[r])[:4]]

	with open(BASE / "data" / "surah_meta.json", encoding="utf-8") as f:
		meta = json.load(f)
	out = {}
	for a in surahs:
		sims = sorted(((sim(a, b), b) for b in surahs if b != a), reverse=True)[:top_k]
		m = meta[str(a)]
		out[a] = {
			"name": m["name"], "type": "مكية" if m["revelationType"] == "Meccan" else "مدنية",
			"ayahs": m["ayahs"], "size": sum(surah_roots[a].values()),
			"neighbors": [[b, round(sc, 3), shared(a, b)] for sc, b in sims],
		}
	return {"surahs": out}


if __name__ == "__main__":
	import sys
	if "--map" in sys.argv:
		payload = build_surah_map()
		out = BASE / "app" / "generated" / "surah_map.js"
		out.parent.mkdir(parents=True, exist_ok=True)
		with open(out, "w", encoding="utf-8") as f:
			f.write("window.SURAH_MAP = ")
			json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))
			f.write(";\n")
		print(f"wrote surah_map.js ({out.stat().st_size // 1024} KiB) — {len(payload['surahs'])} surahs")
		sys.exit(0)
	if "--explorer" in sys.argv:
		payload = build_explorer()
		out = BASE / "app" / "generated" / "explorer.js"
		out.parent.mkdir(parents=True, exist_ok=True)
		with open(out, "w", encoding="utf-8") as f:
			f.write("window.EXPLORER_DATA = ")
			json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))
			f.write(";\n")
		print(f"wrote explorer.js ({out.stat().st_size // 1024} KiB) — "
			f"{len(payload['roots'])} roots, {len(payload['verse_words'])} verses, "
			f"{len(payload['surah_names'])} surahs")
		sys.exit(0)
	c = build()
	print("distinct roots:", c["distinct_roots"], "| root-bearing tokens:", c["total_tokens_with_root"])
	top = sorted(c["roots"].items(), key=lambda kv: -kv[1]["count"])[:10]
	print("top roots:", [(r, d["count"]) for r, d in top])
	# a couple of discoveries
	single = [r for r, d in c["roots"].items() if len(d["surahs"]) == 1]
	print("roots appearing in only ONE surah:", len(single))
	most_unique = max(c["surah_profile"].items(), key=lambda kv: len(kv[1]["unique_roots"]))
	print("surah with most unique roots:", most_unique[0], "->", len(most_unique[1]["unique_roots"]))
