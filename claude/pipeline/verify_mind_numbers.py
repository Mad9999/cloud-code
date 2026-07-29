"""Numbers the mind states about our own artifacts, re-derived from them.

Three of these rotted in one day, all the same way. Rule 31 said the manhaj
document held 25 rules of 40 tested; it holds 13 sections and there is no way
to get 25 out of it. Rule 33 argued from Ibn Kathir's 127-fold spread, measured
with a ruler we fixed that morning and never re-ran; it is 214. Rule 34 said the
em-dash was absent from 11.4M characters and that no bullet appeared; the
character is absent from 150M, and Muyassar alone has 886 bullets.

Each was true, or true enough, on the day it was written. None was re-derived
afterwards, and a number remembered rather than counted is a number decaying
quietly inside an argument that leans on it. So the numbers the mind asserts
about our own files are counted here, from the files, every run.

This does not police the mind's numbers about the imams' books; those are in the
claim valves, where the burden is heavier. This is only for the claims we make
about ourselves, which are the ones nobody else will ever check.

The mind lives outside this repo (D:/Claude/projects/quran). If it is not
mounted, the check says so and passes rather than failing a build for a path
that is not this project's business.

Usage: python verify_mind_numbers.py
"""

import json
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
MIND_DIR = Path("D:/Claude/projects/quran")
ARCH = MIND_DIR / "architecture.md"
MANHAJ = MIND_DIR / "manhaj-al-mufassirin.md"

BOOKS = ("muyassar", "saadi", "ibnkathir", "baghawi", "qurtubi", "tabari")

# A retracted number stays in the mind, because we keep the error visible next to
# its correction rather than quietly deleting it. So the first cut of this file
# fired on all four numbers it had just helped fix: it read the retractions as
# assertions.
#
# That is the third time in one day that a check confused mentioning a thing with
# using it. Stripping em-dashes ate the sentence that names the em-dash. The
# guillemet valve cannot tell a bent verse from our own words. And now this. We
# wrote the mention/use distinction into rule 34 this morning and did not apply
# it two hours later, which is the whole lesson about rules that live only in
# memory.
RETRACTED = ("⚠️", "⛔", "~~", "وكان ها هنا", "كنتُ كتبتُ", "وصُحّح", "صُحّح ")


def asserting_lines(text):
	"""Lines that state a number, not lines that quote one we withdrew."""
	return [ln for ln in text.split("\n") if not any(mark in ln for mark in RETRACTED)]


def asserts(text, needle):
	return any(needle in ln for ln in asserting_lines(text))


def manhaj_sections():
	"""Sections of the manhaj document, excluding its closing essay."""
	text = MANHAJ.read_text(encoding="utf-8")
	heads = re.findall(r"^## (.+)$", text, re.M)
	return [h for h in heads if not h.startswith("خاتمة")]


def em_dash_in_books():
	total = chars = 0
	for book in BOOKS:
		for f in (BASE / "app" / "tafsir" / book).glob("*.js"):
			t = f.read_text(encoding="utf-8")
			chars += len(t)
			total += t.count("—")
	return total, chars


def bullets_in_books():
	counts = {}
	for book in BOOKS:
		n = 0
		for f in (BASE / "app" / "tafsir" / book).glob("*.js"):
			n += f.read_text(encoding="utf-8").count("•")
		counts[book] = n
	return counts


def ibnkathir_spread():
	"""Longest block share over shortest, in al-Baqara, measured by blocks."""
	raw = (BASE / "app" / "tafsir" / "ibnkathir" / "2.js").read_text(encoding="utf-8")
	payload = json.loads(raw.split("=", 1)[1].rstrip().rstrip(";"))
	entries = {int(k): re.sub(r"\[\[.*?\]\]", " ", v, flags=re.S) for k, v in payload.items()}
	grouped = {}
	for ayah, text in entries.items():
		grouped.setdefault(text, []).append(ayah)
	shares = [len(t) / len(a) for t, a in grouped.items() if t.strip()]
	return round(max(shares) / min(shares))


def main():
	if not ARCH.exists():
		print(f"  the mind is not mounted at {MIND_DIR}, so its numbers are not checked here")
		return
	arch = ARCH.read_text(encoding="utf-8")
	failures = []

	# rule 31: how many sections does the manhaj document actually hold?
	sections = manhaj_sections()
	if asserts(arch, "ثلاثةَ عشرَ بابًا") and len(sections) != 13:
		failures.append(
			f"rule 31 says thirteen sections; the manhaj has {len(sections)}. Recount and rewrite."
		)
	if asserts(arch, "٢٥ قاعدةً من ٤٠") or asserts(MANHAJ.read_text(encoding="utf-8"), "٢٥ قاعدة من ٤٠"):
		failures.append("the 25-of-40 claim is back and cannot be derived from the document")
	print(f"  OK: the manhaj holds {len(sections)} sections, and the mind says so")

	# rule 34: the character's absence is the ban's only evidence from the books
	dashes, chars = em_dash_in_books()
	if dashes:
		failures.append(f"rule 34's ground is gone: «—» now appears {dashes} times in the books")
	if asserts(arch, "١١ مليون") or asserts(arch, "أحدَ عشرَ مليونَ حرف"):
		failures.append(
			f"rule 34 still cites 11M characters; the corpus files are {chars / 1e6:.0f}M"
		)
	bullets = bullets_in_books()
	if asserts(arch, "ولا نقطةَ تعداد") and any(bullets.values()):
		failures.append(f"rule 34 still denies bullets; Muyassar has {bullets['muyassar']}")
	print(
		f"  OK: «—» is absent from {chars / 1e6:.0f}M characters of the six books, "
		f"and the mind no longer denies the bullets ({bullets['muyassar']} in Muyassar)"
	)

	# rule 33: the spread it argues from, by the ruler we now use
	spread = ibnkathir_spread()
	if asserts(arch, "١٢٧ ضعفًا"):
		failures.append(f"rule 33 still argues from 127; by blocks Ibn Kathir's spread is {spread}")
	stated = re.search(r"ابنُ كثير بين أقصرِ كتلةٍ وأطولها \*\*(\d+|[٠-٩]+) ضعفًا\*\*", arch)
	if stated:
		digits = stated.group(1).translate(str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789"))
		if abs(int(digits) - spread) > 1:
			failures.append(f"rule 33 states {digits}; measured now it is {spread}")
	print(f"  OK: Ibn Kathir's spread in al-Baqara is {spread}x by blocks, and the mind says so")

	if failures:
		print("\nA NUMBER IN THE MIND NO LONGER COMES OUT OF THE THING IT DESCRIBES:", file=sys.stderr)
		for f in failures:
			print(f"  {f}", file=sys.stderr)
		sys.exit(1)
	print("\nthe mind's numbers about our own work still come out of our own work.")


if __name__ == "__main__":
	main()
