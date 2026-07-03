"""Build orchestrator: runs all analyses, validates invariants, and emits
app/generated/data.js (a single embeddable payload so the app works over
file:// without fetch) plus the spectrogram PNGs.
"""

import json
import sys
from pathlib import Path

import audio_fft
import phonetic_profile
import semantic_graph

BASE = Path(__file__).resolve().parent.parent
GEN_DIR = BASE / "app" / "generated"

# Hand-verified phoneme counts per verse (waqf reading, Hafs). The decomposed
# sequences were reviewed letter-by-letter against the mushaf; any drift in
# the rules must fail the build rather than silently ship wrong data.
EXPECTED_PHONEMES = {1: 18, 2: 20, 3: 12, 4: 11, 5: 21, 6: 16, 7: 42}


def fail(msg):
	print(f"VALIDATION FAILED: {msg}", file=sys.stderr)
	sys.exit(1)


def validate(surah, phonetics):
	if surah["verse_count"] != 7 or len(surah["verses"]) != 7:
		fail("Al-Fatiha must have exactly 7 verses")
	word_total = sum(len(v["words"]) for v in surah["verses"])
	if word_total != surah["word_count"] or word_total != 29:
		fail(f"word count {word_total} != 29")
	ids = [w["i"] for v in surah["verses"] for w in v["words"]]
	if ids != list(range(1, 30)):
		fail("word ids must be contiguous 1..29")
	for v in surah["verses"]:
		if len(v["simple"].split()) != len(v["words"]):
			fail(f"verse {v['n']}: simple text tokens != words entries")
	for pv in phonetics["verses"]:
		expected = EXPECTED_PHONEMES[pv["n"]]
		if pv["stats"]["phoneme_count"] != expected:
			fail(
				f"verse {pv['n']}: phoneme count {pv['stats']['phoneme_count']} "
				f"!= verified {expected}"
			)
	print(f"validation OK: 7 verses, {word_total} words, phoneme counts match")


def main():
	with open(BASE / "data" / "surah_001.json", encoding="utf-8") as f:
		surah = json.load(f)
	with open(BASE / "data" / "letters.json", encoding="utf-8") as f:
		letters = json.load(f)

	print("building phonetic profile ...")
	phonetics = phonetic_profile.build()
	validate(surah, phonetics)

	print("building semantic graph ...")
	graph = semantic_graph.build()
	print(f"  {len(graph['nodes'])} nodes, {len(graph['edges'])} edges")

	print("analyzing recitation audio ...")
	acoustics = audio_fft.build()

	payload = {
		"surah": surah,
		"letters": letters,
		"phonetics": phonetics,
		"graph": graph,
		"acoustics": acoustics,
	}
	GEN_DIR.mkdir(parents=True, exist_ok=True)
	out = GEN_DIR / "data.js"
	with open(out, "w", encoding="utf-8") as f:
		f.write("window.QURAN_DATA = ")
		json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))
		f.write(";\n")
	print(f"wrote {out} ({out.stat().st_size // 1024} KiB)")


if __name__ == "__main__":
	main()
