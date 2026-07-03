"""Spiritual arc derivation for Al-Fatiha.

Fuses existing, honest signals into one per-verse "heart movement" profile that
downstream visuals (pulse, balance) consume:
  - section (praise / covenant / petition) from the prophetic division
  - speech_mode (ghayba -> khitab) from the golden dataset
  - mean_intensity from the phonetic engine (tajwid-grounded)
  - presence of a divine response from the qudsi hadith

No new religious claim is invented here: this module only re-projects data that
is already sourced and graded elsewhere into a shape the UI can render.
"""

import json
from pathlib import Path

import phonetic_profile

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

SECTION_AR = {"praise": "ثناء", "covenant": "عهد", "petition": "طلب"}


def load(name):
	with open(DATA_DIR / name, encoding="utf-8") as f:
		return json.load(f)


def build():
	surah = load("surah_001.json")
	tadabbur = load("tadabbur_001.json")
	phon = phonetic_profile.build()

	div = surah["ring_structure"]["prophetic_division"]
	intensity = {v["n"]: v["stats"]["mean_intensity"] for v in phon["verses"]}
	responses = {v["n"]: v.get("divine_response") for v in tadabbur["verses"]}

	imin = min(intensity.values())
	imax = max(intensity.values())
	span = (imax - imin) or 1.0

	arc = []
	for verse in surah["verses"]:
		n = verse["n"]
		if n in div["first_half"]:
			section = "praise"
		elif n == div["pivot_verse"]:
			section = "covenant"
		else:
			section = "petition"

		# warmth 0..1: cool during praise, warming into the petition, driven by
		# the physically-grounded intensity so the color never lies about the data.
		warmth = round((intensity[n] - imin) / span, 3)

		arc.append({
			"n": n,
			"section": section,
			"section_ar": SECTION_AR[section],
			"speech_mode": verse["speech_mode"],
			"intensity": intensity[n],
			"warmth": warmth,
			"has_divine_response": responses[n] is not None,
			"is_pivot": n == div["pivot_verse"],
			"is_iltifat": n == surah["ring_structure"]["iltifat_at"],
		})
	return {
		"pivot_verse": div["pivot_verse"],
		"iltifat_at": surah["ring_structure"]["iltifat_at"],
		"sections": {
			"praise": div["first_half"],
			"covenant": [div["pivot_verse"]],
			"petition": div["second_half"],
		},
		"verses": arc,
	}


if __name__ == "__main__":
	a = build()
	for v in a["verses"]:
		flags = []
		if v["is_pivot"]:
			flags.append("PIVOT")
		if v["is_iltifat"]:
			flags.append("ILTIFAT")
		print(
			f"ayah {v['n']}: {v['section_ar']:5} | {v['speech_mode']:5} | "
			f"intensity {v['intensity']:+.2f} | warmth {v['warmth']:.2f} "
			f"{'| ' + ' '.join(flags) if flags else ''}"
		)
