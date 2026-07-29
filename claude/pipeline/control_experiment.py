"""Control-sample experiment payload (السؤال ٤: غربلة الاطّرادات).

Recomputes the Qur'an fasila numbers fresh from fawasil.build() (so the
Qur'an side is never trusted to hand-entered values), loads the adversarially
verified control corpora + verdicts from data/control_corpora.json, checks
they agree, and emits the comparison for the UI.
"""

import json
from pathlib import Path

import fawasil

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def quran_side():
	fw = fawasil.build()
	total = fw["total_ayahs"]
	top = dict(fw["global_top_fasila"])
	pct = {l: round(100 * c / total, 1) for l, c in top.items()}
	doms = sorted(s["dominant_pct"] for s in fw["surahs"])
	mid = doms[len(doms) // 2]
	return {
		"total_ayahs": total,
		"nun_pct": pct.get("ن", 0),
		"nun_alif_pct": round(pct.get("ن", 0) + pct.get("ا", 0), 1),
		"soft_naml_pct": round(pct.get("ن", 0) + pct.get("ا", 0) + pct.get("م", 0), 1),
		"per_surah_dominant_median": mid,
		"monorhyme_like_surahs": sum(1 for s in fw["surahs"] if s["dominant_pct"] >= 80),
		"top8_coverage_pct": round(100 * sum(top.values()) / total, 1),
	}


def build():
	with open(DATA_DIR / "control_corpora.json", encoding="utf-8") as f:
		control = json.load(f)
	fresh = quran_side()
	stated = control["quran_baseline"]
	# The stored Qur'an baseline must match the freshly computed one within
	# rounding, or the experiment is out of sync with the data.
	for key in ("nun_pct", "nun_alif_pct", "soft_naml_pct"):
		if abs(fresh[key] - stated[key]) > 0.2:
			raise ValueError(f"control baseline {key} {stated[key]} != fresh {fresh[key]}")
	control["quran_baseline"] = fresh  # ship the freshly computed side
	return control


if __name__ == "__main__":
	c = build()
	print("Qur'an side (fresh):", c["quran_baseline"])
	for v in c["verdicts"]:
		print(f"  [{v['verdict']:17}] {v['dimension']} (ثقة {v['confidence']})")
	print("survived:", len(c["synthesis"]["survived"]), "| killed:", len(c["synthesis"]["killed"]))
