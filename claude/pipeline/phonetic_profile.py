"""Phonetic profile builder for Surah Al-Fatiha.

Decomposes each verse (Tanzil "simple" orthography) into a phoneme sequence,
applying tajwid-grounded reading rules (hamzat wasl, shadda doubling, shamsi
assimilation, madd detection, waqf at verse end), then aggregates sifat
statistics per verse using data/letters.json.

Scope note: the rule set is validated for Al-Fatiha's orthography. Extending to
other surahs requires covering tanwin, ta marbuta, and more wasl cases.
"""

import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

HARAKAT = {"َ": "fatha", "ُ": "damma", "ِ": "kasra"}
SUKUN = "ْ"
SHADDA = "ّ"
DAGGER_ALIF = "ٰ"
MARKS = set(HARAKAT) | {SUKUN, SHADDA, DAGGER_ALIF}

# Hamza orthographic variants normalized to bare hamza.
HAMZA_FORMS = {"أ": "fatha", "إ": "kasra"}  # أ / إ carry their own seat

# Ijtihadi intensity heuristic (documented in docs/methodology.md):
# jahr +1 / hams -1; shidda +2 / rakhawa -1; istiala +2; itbaq +2; qalqala +1.
INTENSITY_WEIGHTS = {
	"jahr": 1,
	"hams": -1,
	"shidda": 2,
	"tawassut": 0,
	"rakhawa": -1,
	"istiala": 2,
	"istifal": 0,
}


def load_json(name):
	with open(DATA_DIR / name, encoding="utf-8") as f:
		return json.load(f)


def tokenize(word):
	"""Split a word into (base letter, [marks]) units."""
	units = []
	for ch in word:
		if ch in MARKS:
			if not units:
				raise ValueError(f"mark before any letter in {word!r}")
			units[-1][1].append(ch)
		else:
			units.append([ch, []])
	return units


def letter_intensity(attrs):
	score = INTENSITY_WEIGHTS[attrs["voicing"]] + INTENSITY_WEIGHTS[attrs["strength"]]
	score += INTENSITY_WEIGHTS[attrs["elevation"]]
	if attrs["itbaq"]:
		score += 2
	if attrs["qalqala"]:
		score += 1
	return score


def intensity_bin(score, is_madd):
	"""Map raw score to one of 5 polarity bins (soft2 .. hard2)."""
	if is_madd:
		return "soft2"
	if score >= 5:
		return "hard2"
	if score >= 2:
		return "hard1"
	if score == 1:
		return "neutral"
	if score >= -1:
		return "soft1"
	return "soft2"


def starts_with_wasl(word):
	units = tokenize(word)
	return bool(units) and units[0][0] == "ا" and not units[0][1]


def decompose_verse(verse_words):
	"""Return the phoneme event list for one verse read in isolation
	(continuous within the verse, waqf on the last word)."""
	phonemes = []

	def emit(char, state, word_i, flags=None, weight=1.0):
		phonemes.append({
			"char": char,
			"state": state,
			"word": word_i,
			"flags": flags or [],
			"weight": weight,
		})

	n_words = len(verse_words)
	for w_idx, word in enumerate(verse_words):
		units = tokenize(word)
		next_word = verse_words[w_idx + 1] if w_idx + 1 < n_words else None
		bare = "".join(ch for ch in word if ch not in MARKS)
		is_allah = bare in ("الله", "لله")  # implied dagger alif after doubled lam

		for u_idx, (base, marks) in enumerate(units):
			is_word_final = u_idx == len(units) - 1
			nxt = units[u_idx + 1] if u_idx + 1 < len(units) else None

			# Normalize seated hamza (أ / إ) to bare hamza with its vowel.
			if base in HAMZA_FORMS:
				vowel = next((HARAKAT[m] for m in marks if m in HARAKAT), HAMZA_FORMS[base])
				emit("ء", vowel, w_idx)
				continue

			if base == "ا" and not marks:
				if u_idx == 0:
					# Hamzat wasl: pronounced only when the verse starts here.
					if w_idx == 0:
						vowel = "kasra" if word.startswith("اه") else "fatha"
						emit("ء", vowel, w_idx, ["wasl_start"])
					continue
				# Bare alif inside/at end of word = madd alif.
				if is_word_final and next_word and starts_with_wasl(next_word):
					continue  # dropped: two sakins meet across the wasl
				if nxt and SHADDA in nxt[1]:
					emit("ا", "madd", w_idx, ["madd_lazim"], 6.0)
				else:
					emit("ا", "madd", w_idx, [], 2.0)
				continue

			# Silent assimilated letter (shamsi lam, and first lam of الله):
			# bare letter directly followed by a shadda letter.
			if not marks and nxt and SHADDA in nxt[1]:
				continue

			vowel = next((HARAKAT[m] for m in marks if m in HARAKAT), None)
			has_sukun = SUKUN in marks
			has_shadda = SHADDA in marks
			has_dagger = DAGGER_ALIF in marks

			if has_shadda:
				emit(base, "sakin", w_idx, ["shadda"])
				emit(base, vowel or "sakin", w_idx, ["shadda"])
			elif has_sukun:
				flags = []
				prev = phonemes[-1] if phonemes else None
				if base in "وي" and prev and prev["state"] == "fatha":
					flags.append("lin")
				emit(base, "sakin", w_idx, flags)
			elif vowel:
				emit(base, vowel, w_idx)
			elif base == "و" and phonemes and phonemes[-1]["state"] == "damma":
				emit("و", "madd", w_idx, [], 2.0)
				continue
			elif base == "ي" and phonemes and phonemes[-1]["state"] == "kasra":
				emit("ي", "madd", w_idx, [], 2.0)
				continue
			else:
				raise ValueError(f"unhandled unit {base!r} {marks!r} in {word!r}")

			if has_dagger:
				emit("ا", "madd", w_idx, ["dagger"], 2.0)
			if is_allah and base == "ل" and has_shadda:
				emit("ا", "madd", w_idx, ["implied_alif"], 2.0)

	# Waqf: the final voweled consonant becomes sakin; a preceding madd
	# becomes madd 'arid (still counted as madd).
	if phonemes and phonemes[-1]["state"] in ("fatha", "damma", "kasra"):
		phonemes[-1]["state"] = "sakin"
		phonemes[-1]["flags"].append("waqf")
	return phonemes


def annotate(phonemes, letters):
	for p in phonemes:
		attrs = letters[p["char"]]
		p["attrs"] = {
			"name": attrs["name"],
			"voicing": attrs["voicing"],
			"strength": attrs["strength"],
			"elevation": attrs["elevation"],
			"itbaq": attrs["itbaq"],
			"makhraj": attrs["makhraj"],
			"extras": attrs["extras"],
		}
		is_madd = p["state"] == "madd"
		# Qalqala is realized only on a truly sakin letter; the first half of a
		# mushaddad pair in continuous reading does not qalqala.
		p["qalqala_realized"] = (
			attrs["qalqala"] and p["state"] == "sakin" and "shadda" not in p["flags"]
		)
		score = letter_intensity(attrs)
		p["intensity"] = score
		p["bin"] = intensity_bin(score, is_madd)
	return phonemes


def verse_stats(phonemes):
	total_w = sum(p["weight"] for p in phonemes)
	def wsum(pred):
		return sum(p["weight"] for p in phonemes if pred(p))

	madd_w = wsum(lambda p: p["state"] == "madd")
	stats = {
		"phoneme_count": len(phonemes),
		"duration_weight": round(total_w, 2),
		"pct_hams": round(100 * wsum(lambda p: p["attrs"]["voicing"] == "hams") / total_w, 1),
		"pct_jahr": round(100 * wsum(lambda p: p["attrs"]["voicing"] == "jahr") / total_w, 1),
		"pct_shidda": round(100 * wsum(lambda p: p["attrs"]["strength"] == "shidda") / total_w, 1),
		"pct_rakhawa": round(100 * wsum(lambda p: p["attrs"]["strength"] == "rakhawa") / total_w, 1),
		"pct_istiala": round(100 * wsum(lambda p: p["attrs"]["elevation"] == "istiala") / total_w, 1),
		"pct_madd": round(100 * madd_w / total_w, 1),
		"pct_ghunna": round(100 * wsum(lambda p: "ghunna" in p["attrs"]["extras"]) / total_w, 1),
		"qalqala_count": sum(1 for p in phonemes if p["qalqala_realized"]),
		"mean_intensity": round(
			sum(p["intensity"] * p["weight"] for p in phonemes) / total_w, 2
		),
		"makhraj_dist": {},
	}
	for p in phonemes:
		m = p["attrs"]["makhraj"]
		stats["makhraj_dist"][m] = stats["makhraj_dist"].get(m, 0) + 1
	return stats


def build():
	surah = load_json("surah_001.json")
	letters = load_json("letters.json")["letters"]
	out = {"surah": surah["surah"], "verses": []}
	for verse in surah["verses"]:
		words = verse["simple"].split()
		phonemes = annotate(decompose_verse(words), letters)
		out["verses"].append({
			"n": verse["n"],
			"words": words,
			"phonemes": phonemes,
			"stats": verse_stats(phonemes),
		})
	return out


if __name__ == "__main__":
	result = build()
	for v in result["verses"]:
		seq = " ".join(
			p["char"] + ("ـ" if p["state"] == "madd" else "") for p in v["phonemes"]
		)
		print(f"ayah {v['n']} ({v['stats']['phoneme_count']} phonemes): {seq}")
		print("   ", {k: v["stats"][k] for k in ("pct_hams", "pct_madd", "mean_intensity", "qalqala_count")})
