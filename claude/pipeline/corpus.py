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


def build_ayah_links(top_k=6, df_ceiling=300, min_shared_idf=2.4):
	"""Ayah-level echoes (السؤال البحثي السادس: شبكة الجواب) — for each of the
	6236 verses, the OTHER verses whose language echoes it, measured by the
	rare roots they share. idf-weighting means ubiquitous roots (أله/قول, in
	thousands of verses) create NO link; only distinctive shared vocabulary
	binds two verses. A verse that says صمد/كفأ finds its kin, not every verse
	that merely says «قال». Pure counting — the shared roots are shown as proof,
	the meaning is left to the reader.

	  * df_ceiling — a root present in more than this many verses is too common
	    to generate a candidate link (structural words, not distinctive echoes).
	  * min_shared_idf — a pair must share distinctive vocabulary worth at least
	    this combined idf, else no edge (kills one-weak-root coincidences)."""
	import math
	ayah_roots = defaultdict(set)          # (s,a) -> {root, ...}
	for s, a, _w, _seg, _form, root in parse_all():
		if root:
			ayah_roots[(s, a)].add(root)
	ayahs = sorted(ayah_roots)
	n = len(ayahs)
	inv = defaultdict(list)                # root -> [ayah_key, ...]
	for k in ayahs:
		for r in ayah_roots[k]:
			inv[r].append(k)
	idf = {r: math.log(n / len(v)) for r, v in inv.items()}

	def key(k):
		return f"{k[0]}:{k[1]}"

	out = {}
	for k in ayahs:
		roots = ayah_roots[k]
		distinctive = [r for r in roots if len(inv[r]) <= df_ceiling]
		scores = defaultdict(float)
		shared = defaultdict(list)
		for r in distinctive:
			w = idf[r]
			for other in inv[r]:
				if other != k:
					scores[other] += w
					shared[other].append(r)
		ranked = sorted(scores.items(), key=lambda kv: -kv[1])
		nbrs = []
		for other, sc in ranked:
			if sc < min_shared_idf:
				break
			roots_sorted = sorted(shared[other], key=lambda r: -idf[r])[:3]
			nbrs.append([key(other), round(sc, 2), roots_sorted])
			if len(nbrs) >= top_k:
				break
		if nbrs:
			out[key(k)] = nbrs
	linked = len(out)
	total_edges = sum(len(v) for v in out.values())
	return {"links": out, "stats": {"verses_with_echoes": linked, "total_verses": n, "edges": total_edges}}


def _surah_top_sim(surah_roots):
	"""Each surah's strongest neighbour similarity (idf-weighted tf-idf cosine).
	Shared by the real map and its null so scoring is identical."""
	import math
	surahs = sorted(surah_roots)
	n = len(surahs)
	df = Counter()
	for s in surahs:
		for r in surah_roots[s]:
			df[r] += 1
	idf = {r: math.log(n / df[r]) for r in df}
	vecs = {s: {r: (1 + math.log(c)) * idf[r] for r, c in surah_roots[s].items()} for s in surahs}
	norms = {s: math.sqrt(sum(x * x for x in v.values())) or 1 for s, v in vecs.items()}
	best = {}
	for a in surahs:
		va = vecs[a]
		top = 0.0
		for b in surahs:
			if b == a:
				continue
			vb = vecs[b]
			common = set(va) & set(vb)
			if common:
				sc = sum(va[r] * vb[r] for r in common) / (norms[a] * norms[b])
				if sc > top:
					top = sc
		best[a] = top
	return best


def build_surah_map_control(trials=20, seed=1234):
	"""Chance baseline for the surah connection map (رقم القاعدة ١٦): shuffle the
	Qur'an's root-tokens across surahs (preserving every surah's size and every
	root's frequency), recompute nearest-neighbour similarity, and see how much
	of the map is more than vocabulary statistics. Reported honestly whatever it
	shows — long legal Medinan surahs sharing words is ordinary, not a wonder."""
	import random
	surah_roots = defaultdict(Counter)
	edges = []
	for s, _a, _w, _seg, _form, root in parse_all():
		if root:
			surah_roots[s][root] += 1
			edges.append([s, root])
	real = _surah_top_sim(surah_roots)
	real_vals = sorted(real.values())
	real_median = real_vals[len(real_vals) // 2]

	rng = random.Random(seed)
	null_medians = []
	thresholds = [0.1, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5]
	null_counts = {t: 0 for t in thresholds}
	for _t in range(trials):
		col = [r for _s, r in edges]
		rng.shuffle(col)
		sr = defaultdict(Counter)
		for (s, _r), nr in zip(edges, col):
			sr[s][nr] += 1
		nb = _surah_top_sim(sr)
		nv = sorted(nb.values())
		null_medians.append(nv[len(nv) // 2])
		for t in thresholds:
			null_counts[t] += sum(1 for v in nv if v >= t)
	null_median = sum(null_medians) / len(null_medians)
	table = []
	for t in thresholds:
		real_c = sum(1 for v in real_vals if v >= t)
		null_c = null_counts[t] / trials
		table.append({"score": t, "real": real_c, "null": round(null_c, 1),
			"lift": round(real_c / null_c, 2) if null_c >= 1 else None})
	return {
		"trials": trials,
		"real_median_top_sim": round(real_median, 3),
		"null_median_top_sim": round(null_median, 3),
		"table": table,
		"surahs": len(surah_roots),
	}


def _top_echo_strength(ayah_roots, ayahs, df_ceiling, min_shared_idf):
	"""Per-ayah strongest echo score (sum of idf of shared distinctive roots).
	Shared with the null model so real & shuffled data use IDENTICAL scoring."""
	import math
	inv = defaultdict(list)
	for k in ayahs:
		for r in ayah_roots[k]:
			inv[r].append(k)
	n = len(ayahs)
	idf = {r: math.log(n / len(v)) for r, v in inv.items()}
	best = {}
	for k in ayahs:
		distinctive = [r for r in ayah_roots[k] if len(inv[r]) <= df_ceiling]
		scores = defaultdict(float)
		for r in distinctive:
			w = idf[r]
			for other in inv[r]:
				if other != k:
					scores[other] += w
		top = max(scores.values()) if scores else 0.0
		best[k] = top if top >= min_shared_idf else 0.0
	return best


def build_echo_control(trials=20, seed=1234, df_ceiling=300, min_shared_idf=2.4):
	"""Honesty guard against reading intention into coincidence (رقم القاعدة ٥:
	الانحياز ضدّ المبالغة). Before we let anyone — including ourselves — call an
	echo «تجاوبًا»، we must know how strong echoes are BY CHANCE.

	Null model: keep every verse's number of distinctive roots and every root's
	total frequency fixed, but randomly REWIRE which verse each root-occurrence
	lands in (a degree-preserving shuffle). This destroys any real topical
	co-location while preserving vocabulary statistics. If the real Qur'an's
	echoes are no stronger than this shuffle, then «صدى الآية» is a property of
	word-frequency alone and must NOT be dressed as meaning. We report the honest
	comparison whatever it says — including if it deflates the wonder."""
	import random
	ayah_roots = defaultdict(set)
	for s, a, _w, _seg, _form, root in parse_all():
		if root:
			ayah_roots[(s, a)].add(root)
	ayahs = sorted(ayah_roots)

	real = _top_echo_strength(ayah_roots, ayahs, df_ceiling, min_shared_idf)
	real_vals = sorted(real.values())
	real_median = real_vals[len(real_vals) // 2]
	real_strong = sum(1 for v in real_vals if v >= 8.0)   # "notable" echoes

	# edge list (verse, root); permute the root column -> degree-preserving null
	edges = [(k, r) for k in ayahs for r in ayah_roots[k]]
	rng = random.Random(seed)
	null_medians, null_strong_counts = [], []
	for _t in range(trials):
		roots_col = [r for _k, r in edges]
		rng.shuffle(roots_col)
		shuf = defaultdict(set)
		for (k, _r), nr in zip(edges, roots_col):
			shuf[k].add(nr)
		nb = _top_echo_strength(shuf, ayahs, df_ceiling, min_shared_idf)
		nv = sorted(nb.values())
		null_medians.append(nv[len(nv) // 2])
		null_strong_counts.append(sum(1 for v in nv if v >= 8.0))

	null_median = sum(null_medians) / len(null_medians)
	null_strong = sum(null_strong_counts) / len(null_strong_counts)

	# empirical lift table: how many verses reach each score threshold, real vs
	# the averaged null. Bands are DERIVED, not hand-drawn — so the product's
	# "above chance by X" labels are computed, not tuned to a wanted result.
	thresholds = [4, 6, 8, 10, 12, 14, 16, 18, 20, 25, 30]
	# re-run nulls accumulating per-threshold counts (reuse the same shuffle seed
	# path for reproducibility)
	rng2 = random.Random(seed)
	null_counts = {t: 0 for t in thresholds}
	for _t in range(trials):
		roots_col = [r for _k, r in edges]
		rng2.shuffle(roots_col)
		shuf = defaultdict(set)
		for (k, _r), nr in zip(edges, roots_col):
			shuf[k].add(nr)
		nb = _top_echo_strength(shuf, ayahs, df_ceiling, min_shared_idf)
		nv = list(nb.values())
		for t in thresholds:
			null_counts[t] += sum(1 for v in nv if v >= t)
	table = []
	for t in thresholds:
		real_c = sum(1 for v in real_vals if v >= t)
		null_c = null_counts[t] / trials
		table.append({"score": t, "real": real_c, "null": round(null_c, 1),
			"lift": round(real_c / null_c, 2) if null_c >= 1 else None})
	return {
		"trials": trials,
		"real_median_top_echo": round(real_median, 2),
		"null_median_top_echo": round(null_median, 2),
		"real_notable_echoes": real_strong,           # verses whose top echo >= 8.0
		"null_notable_echoes": round(null_strong, 1),
		"ratio_notable": round(real_strong / null_strong, 2) if null_strong else None,
		"table": table,
		"verses": len(ayahs),
	}


def build_discoveries_control(trials=20, seed=1234):
	"""Honesty guard for the كشوف (رقم القاعدة ١٦+١٧). A root that occurs ONCE is
	trivially 'confined to one surah' — that is expected, not a wonder, and any
	Zipfian text has hundreds of such hapaxes. The only statistically notable
	fact is a root that RECURS (freq >= 2) yet still never leaves one surah. We
	measure that against a shuffle: how many multi-occurrence roots stay confined
	by chance? Reported honestly — including that hapax uniqueness is ordinary."""
	import random
	root_count = Counter()
	root_surahs = defaultdict(set)
	edges = []
	for s, _a, _w, _seg, _form, root in parse_all():
		if root:
			root_count[root] += 1
			root_surahs[root].add(s)
			edges.append([s, root])
	hapax = sum(1 for r, c in root_count.items() if c == 1)
	real_confined = sum(1 for r, c in root_count.items() if c >= 2 and len(root_surahs[r]) == 1)

	rng = random.Random(seed)
	null_confined = []
	for _t in range(trials):
		col = [r for _s, r in edges]
		rng.shuffle(col)
		rs = defaultdict(set)
		for (s, _r), nr in zip(edges, col):
			rs[nr].add(s)
		null_confined.append(sum(1 for r, c in root_count.items() if c >= 2 and len(rs[r]) == 1))
	null_c = sum(null_confined) / len(null_confined)
	return {
		"trials": trials,
		"hapax": hapax,                                # trivially confined — expected
		"multi_occurrence_roots": sum(1 for c in root_count.values() if c >= 2),
		"real_confined_recurring": real_confined,      # freq>=2 yet in one surah
		"null_confined_recurring": round(null_c, 1),
		"lift": round(real_confined / null_c, 2) if null_c >= 1 else None,
	}


def build_discoveries(per_surah_cap=8, feed_cap=60):
	"""What the AI surfaces that a reader passes over (رقم القاعدة ١١+١٢): purely
	COMPUTED, verifiable facts — never generated meaning. Two honest categories:

	  * unique-to-surah roots — a root that occurs in NO other surah of the whole
	    Qur'an (e.g. صمد/كفأ only in al-Ikhlas). The reader never notices a word
	    is confined to one place until it is counted.
	  * hapax — a root that occurs exactly ONCE in the entire Qur'an.

	Each item carries its own proof (root, example word, location, counts) so the
	claim can be checked; nothing is interpreted, only counted."""
	words = defaultdict(lambda: defaultdict(lambda: {"text": "", "root": None}))
	root_count = Counter()
	root_surahs = defaultdict(set)
	root_first = {}                       # root -> (s, a) first occurrence
	for s, a, w, _seg, form, root in parse_all():
		e = words[(s, a)][w]
		e["text"] += form
		if root:
			e["root"] = root
			root_count[root] += 1
			root_surahs[root].add(s)
			if root not in root_first:
				root_first[root] = (s, a)

	# a readable example word (full reconstructed form) for each root
	example = {}
	for (s, a), wd in words.items():
		for w in wd:
			r = wd[w]["root"]
			if r and r not in example and root_first.get(r) == (s, a):
				example[r] = wd[w]["text"]

	with open(BASE / "data" / "surah_meta.json", encoding="utf-8") as f:
		meta = json.load(f)

	def sname(n):
		return meta[str(n)]["name"]

	surahs = {}
	feed = []
	for n in range(1, 115):
		confined = [r for r in root_surahs if len(root_surahs[r]) == 1 and n in root_surahs[r]]
		# unique: confined to this surah, ranked by how many times it recurs here
		uniq = sorted(confined, key=lambda r: -root_count[r])
		unique_items = [[r, example.get(r, ""), root_count[r], root_first[r][1]]
			for r in uniq[:per_surah_cap]]
		hapax_items = [[r, example.get(r, ""), root_first[r][1]]
			for r in sorted(confined) if root_count[r] == 1][:per_surah_cap]
		if unique_items or hapax_items:
			surahs[n] = {"name": sname(n), "unique": unique_items, "hapax": hapax_items}
		# feed: the striking ones — a word repeated yet still confined to one surah
		for r in uniq:
			if root_count[r] >= 2:
				feed.append({"type": "unique", "root": r, "form": example.get(r, ""),
					"surah": n, "name": sname(n), "ayah": root_first[r][1], "count": root_count[r]})

	feed.sort(key=lambda x: -x["count"])
	hapax_total = sum(1 for r in root_count if root_count[r] == 1)
	return {
		"surahs": surahs,
		"global": {
			"distinct_roots": len(root_count),
			"hapax_total": hapax_total,
			"feed": feed[:feed_cap],
		},
	}


if __name__ == "__main__":
	import sys
	if "--links" in sys.argv:
		payload = build_ayah_links()
		payload["control"] = build_echo_control()
		out = BASE / "app" / "generated" / "ayah_links.js"
		out.parent.mkdir(parents=True, exist_ok=True)
		with open(out, "w", encoding="utf-8") as f:
			f.write("window.AYAH_LINKS = ")
			json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))
			f.write(";\n")
		st = payload["stats"]
		c = payload["control"]
		print(f"wrote ayah_links.js ({out.stat().st_size // 1024} KiB) — "
			f"{st['verses_with_echoes']}/{st['total_verses']} verses linked, {st['edges']} edges")
		print(f"  echo control: real median {c['real_median_top_echo']} vs null {c['null_median_top_echo']}; "
			f"notable-echo lift {c['ratio_notable']}× (weak echoes ~ chance; only strong ones exceed it)")
		sys.exit(0)
	if "--discoveries" in sys.argv:
		payload = build_discoveries()
		payload["control"] = build_discoveries_control()
		out = BASE / "app" / "generated" / "discoveries.js"
		out.parent.mkdir(parents=True, exist_ok=True)
		with open(out, "w", encoding="utf-8") as f:
			f.write("window.DISCOVERIES = ")
			json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))
			f.write(";\n")
		g = payload["global"]
		print(f"wrote discoveries.js ({out.stat().st_size // 1024} KiB) — "
			f"{len(payload['surahs'])} surahs, {g['hapax_total']} hapax roots, "
			f"feed {len(g['feed'])}")
		sys.exit(0)
	if "--map" in sys.argv:
		payload = build_surah_map()
		payload["control"] = build_surah_map_control()
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
