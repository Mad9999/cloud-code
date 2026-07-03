"""Build orchestrator: runs all analyses, validates invariants, and emits
app/generated/data.js (worshipper wing) and app/generated/fawasil.js
(researcher wing) as embeddable payloads so the app works over file://
without fetch, plus the spectrogram PNGs.
"""

import json
import sys
from pathlib import Path

import arc
import audio_fft
import control_experiment
import fawasil
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


def validate_fatiha(surah, phonetics):
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
	print(f"  OK: 7 verses, {word_total} words, phoneme counts match")


def validate_tadabbur(tadabbur):
	verses = tadabbur["verses"]
	if len(verses) != 7:
		fail("tadabbur must cover 7 verses")
	for v in verses:
		n = v["n"]
		if not v.get("reflection", {}).get("source"):
			fail(f"verse {n}: reflection missing a source")
		if v["reflection"].get("grade") != "ma'thur":
			fail(f"verse {n}: reflection must be graded ma'thur")
		# Only verse 1 (Basmala) is allowed to lack a divine response.
		if v.get("divine_response") is None and n != 1:
			fail(f"verse {n}: missing divine_response without documented reason")
		if v.get("divine_response") is None and not v.get("divine_response_note"):
			fail(f"verse {n}: null divine_response must carry an explanatory note")
		for field in ("heart_state", "action"):
			if v[field].get("grade") != "ijtihadi":
				fail(f"verse {n}: {field} must be graded ijtihadi")
	print("  OK: tadabbur graded and sourced; only verse 1 lacks divine response")


def validate_fawasil(fw):
	if fw["total_ayahs"] != 6236:
		fail(f"Quran ayah total {fw['total_ayahs']} != 6236")
	if fw["surah_count"] != 114:
		fail(f"surah count {fw['surah_count']} != 114")
	for s in fw["surahs"]:
		if not s["fingerprint"]:
			fail(f"surah {s['n']}: empty fasila fingerprint")
	print("  OK: 6236 ayahs, 114 surahs, every surah has a fasila fingerprint")


def write_payload(name, var, payload):
	GEN_DIR.mkdir(parents=True, exist_ok=True)
	out = GEN_DIR / name
	with open(out, "w", encoding="utf-8") as f:
		f.write(f"window.{var} = ")
		json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))
		f.write(";\n")
	print(f"wrote {out} ({out.stat().st_size // 1024} KiB)")


def main():
	with open(BASE / "data" / "surah_001.json", encoding="utf-8") as f:
		surah = json.load(f)
	with open(BASE / "data" / "letters.json", encoding="utf-8") as f:
		letters = json.load(f)
	with open(BASE / "data" / "tadabbur_001.json", encoding="utf-8") as f:
		tadabbur = json.load(f)

	print("phonetic profile ...")
	phonetics = phonetic_profile.build()
	validate_fatiha(surah, phonetics)

	print("tadabbur & dialogue layer ...")
	validate_tadabbur(tadabbur)

	print("spiritual arc ...")
	spiritual_arc = arc.build()

	print("semantic graph ...")
	graph = semantic_graph.build()
	print(f"  {len(graph['nodes'])} nodes, {len(graph['edges'])} edges")

	print("recitation audio (FFT + envelope) ...")
	acoustics = audio_fft.build()

	print("fawasil observatory (full Qur'an) ...")
	fw = fawasil.build()
	validate_fawasil(fw)

	print("control-sample experiment (sieve) ...")
	control = control_experiment.build()
	print(f"  survived {len(control['synthesis']['survived'])}, "
		f"killed {len(control['synthesis']['killed'])} claims")

	write_payload("data.js", "QURAN_DATA", {
		"surah": surah,
		"letters": letters,
		"phonetics": phonetics,
		"graph": graph,
		"acoustics": acoustics,
		"tadabbur": tadabbur,
		"arc": spiritual_arc,
	})
	write_payload("fawasil.js", "FAWASIL_DATA", fw)
	write_payload("control.js", "CONTROL_DATA", control)


if __name__ == "__main__":
	main()
