"""Acoustic analysis of a real verse-by-verse recitation of Al-Fatiha.

Reads the mp3 files in ../audio (Shaykh Mahmoud Khalil al-Husary, murattal,
from everyayah.com), computes physical descriptors per verse (duration, RMS
energy, spectral centroid, frequency-band energy distribution) via scipy FFT,
and renders a spectrogram PNG per verse for the UI.
"""

import json
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy import signal

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

BASE = Path(__file__).resolve().parent.parent
AUDIO_DIR = BASE / "audio"
OUT_DIR = BASE / "app" / "generated" / "spectrograms"

# Single-hue sequential ramp anchored on the app's dark surface (#1a1a19):
# low energy recedes into the surface, high energy steps up through blue.
SPECTRO_CMAP = LinearSegmentedColormap.from_list(
	"surface_blue",
	["#1a1a19", "#0d366b", "#1c5cab", "#3987e5", "#86b6ef", "#cde2fb"],
)

BANDS = [(0, 200), (200, 500), (500, 1000), (1000, 2000), (2000, 4000), (4000, 8000)]


def load_mono(path):
	data, sr = sf.read(path)
	if data.ndim > 1:
		data = data.mean(axis=1)
	return data.astype(np.float64), sr


def trim_silence(x, sr, threshold_db=-45.0):
	"""Trim leading/trailing silence using a short-window RMS gate."""
	win = int(sr * 0.02)
	if len(x) < win * 4:
		return x
	frames = np.lib.stride_tricks.sliding_window_view(x, win)[::win]
	rms = np.sqrt((frames**2).mean(axis=1) + 1e-12)
	db = 20 * np.log10(rms + 1e-12)
	active = np.nonzero(db > threshold_db)[0]
	if active.size == 0:
		return x
	start = active[0] * win
	end = min(len(x), (active[-1] + 1) * win)
	return x[start:end]


def analyze_verse(n, path):
	x, sr = load_mono(path)
	x = trim_silence(x, sr)
	duration = len(x) / sr

	freqs, times, sxx = signal.spectrogram(
		x, fs=sr, nperseg=2048, noverlap=1536, scaling="spectrum"
	)
	power = sxx.mean(axis=1)

	centroid = float((freqs * power).sum() / (power.sum() + 1e-12))
	cumulative = np.cumsum(power)
	rolloff = float(freqs[np.searchsorted(cumulative, 0.85 * cumulative[-1])])

	total = power.sum() + 1e-12
	band_energy = {}
	for lo, hi in BANDS:
		mask = (freqs >= lo) & (freqs < hi)
		band_energy[f"{lo}-{hi}"] = round(float(power[mask].sum() / total) * 100, 2)

	rms = float(np.sqrt((x**2).mean()))

	render_spectrogram(n, freqs, times, sxx)

	return {
		"n": n,
		"file": path.name,
		"sample_rate": sr,
		"duration_s": round(duration, 2),
		"rms": round(rms, 4),
		"spectral_centroid_hz": round(centroid, 1),
		"rolloff85_hz": round(rolloff, 1),
		"band_energy_pct": band_energy,
	}


def render_spectrogram(n, freqs, times, sxx):
	OUT_DIR.mkdir(parents=True, exist_ok=True)
	fmask = freqs <= 5000
	db = 10 * np.log10(sxx[fmask] + 1e-12)
	vmax = db.max()

	fig, ax = plt.subplots(figsize=(7.2, 2.4), dpi=110)
	fig.patch.set_facecolor("#1a1a19")
	ax.set_facecolor("#1a1a19")
	ax.pcolormesh(
		times, freqs[fmask], db, cmap=SPECTRO_CMAP, vmin=vmax - 70, vmax=vmax,
		shading="gouraud",
	)
	ax.set_ylim(0, 5000)
	ax.tick_params(colors="#898781", labelsize=7)
	for spine in ax.spines.values():
		spine.set_color("#383835")
	ax.set_xlabel("s", color="#898781", fontsize=7)
	ax.set_ylabel("Hz", color="#898781", fontsize=7)
	fig.tight_layout(pad=0.4)
	fig.savefig(OUT_DIR / f"ayah_{n}.png", facecolor="#1a1a19")
	plt.close(fig)


def build():
	verses = []
	for n in range(1, 8):
		path = AUDIO_DIR / f"00100{n}.mp3"
		if not path.exists():
			verses.append({"n": n, "missing": True})
			continue
		verses.append(analyze_verse(n, path))
	return {
		"reciter": "الشيخ محمود خليل الحصري (مرتل)",
		"source": "everyayah.com — Husary_128kbps",
		"verses": verses,
	}


if __name__ == "__main__":
	result = build()
	for v in result["verses"]:
		if v.get("missing"):
			print(f"ayah {v['n']}: audio missing")
		else:
			print(
				f"ayah {v['n']}: {v['duration_s']}s, centroid {v['spectral_centroid_hz']} Hz, "
				f"bands {v['band_energy_pct']}"
			)
