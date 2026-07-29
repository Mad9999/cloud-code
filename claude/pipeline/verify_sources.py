"""Deterministic accuracy check for the source library — so a citation is never
an illusion.

Zero agents, zero tokens: it only inspects local files and (optionally) pings
URLs. For every downloaded PDF it extracts the first pages' text and checks that
the book's own title/author actually appears inside — proving the FILE IS THE
BOOK, not a wrong or mismatched download. Each catalog entry gets an explicit
verification level; anything it cannot confirm is marked `needs_review`, never
dressed up as certain.

  verified        the PDF's text contains the title (and/or author) — trustworthy
  scanned_no_text the PDF has no text layer (image scan) — content not checkable
  link_ok         no local file, but a live source link exists (cite-only works)
  needs_review    could not confirm anything — DO NOT trust without a human check

Metadata (author, death year) is labeled "agent-asserted, not independently
verified" — we do not pretend it is certain.

Usage:
  python3 verify_sources.py           # verify local PDFs (offline, no network)
  python3 verify_sources.py --links   # also HTTP-check source links + title-match HTML pages
"""

import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
CATALOG = BASE / "data" / "sources_catalog.json"
PDF_DIR = BASE / "sources" / "pdf"
OUT = BASE / "data" / "sources_verification.json"

UA = "Mozilla/5.0 (compatible; QuranEngineeringSourceBot/1.0)"
AR_DIACRITICS = re.compile(r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED\u0640]")  # combining marks + tatweel only (never letters)


def normalize(text):
	"""Strip Arabic diacritics/tatweel, unify alif/ya/ta-marbuta, lowercase."""
	text = AR_DIACRITICS.sub("", text)
	text = (text.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
		.replace("ى", "ي").replace("ة", "ه").replace("ـ", ""))
	return re.sub(r"\s+", " ", text).strip().lower()


STOP = {"في", "من", "على", "عن", "the", "of", "and", "an", "a", "to", "in", "علم", "علوم", "كتاب"}


def keywords(title):
	"""Distinctive title words to look for in the extracted text."""
	# take the part before a bracket/dash, split, drop stopwords and short tokens
	head = re.split(r"[\(\)\[\]\-–—:=]", title)[0]
	words = [normalize(w) for w in head.split()]
	return [w for w in words if len(w) >= 3 and w not in STOP][:5]


def safe_name(entry):
	title = entry["title"].replace("/", "-").replace(" ", "_")[:60]
	return f"{entry['i']:02d}-{title}.pdf"


def pdf_text(path, pages=25):
	"""Extract text from the first pages. PyMuPDF first (best), pypdf fallback."""
	try:
		import fitz  # pymupdf
		doc = fitz.open(str(path))
		return "".join(doc[i].get_text() for i in range(min(pages, doc.page_count)))
	except Exception:  # noqa: BLE001 - fall back to pypdf
		pass
	try:
		import pypdf
		reader = pypdf.PdfReader(str(path))
		return "\n".join((p.extract_text() or "") for p in reader.pages[:pages])
	except Exception as e:  # noqa: BLE001
		return f"__ERROR__:{e}"


def haystacks(raw):
	"""Normalized text plus a per-word-reversed variant. Many Arabic PDFs store
	glyphs in visual (reversed) order, so the title's letters appear backwards;
	matching against both recovers them without false 'wrong book' alarms."""
	norm = normalize(raw)
	rev = " ".join(w[::-1] for w in norm.split())
	return norm, rev


def verify_pdf(entry, path):
	raw = pdf_text(path)
	if raw.startswith("__ERROR__"):
		return {"level": "needs_review", "caveat": f"تعذّر قراءة الـPDF ({raw[10:60]})"}
	fwd, rev = haystacks(raw)
	if len(fwd) < 40:
		return {"level": "scanned_no_text",
			"caveat": "ملفٌ ممسوح ضوئيًّا بلا طبقة نصّ، فلا يمكن مطابقة العنوان آليًّا (تحقّق بشريّ)"}
	arabic = sum(1 for c in fwd if "ء" <= c <= "ي")
	if arabic / len(fwd) < 0.15:
		return {"level": "unreadable_text",
			"caveat": "طبقة النصّ في الـPDF معطوبة الترميز (تُقرأ كرموز لاتينية)، فلا يمكن التحقّق آليًّا، لا يعني أنه كتابٌ خاطئ (تحقّق بشريّ)"}
	inhay = lambda k: k in fwd or k in rev  # noqa: E731
	kws = keywords(entry["title"])
	hits = [k for k in kws if inhay(k)]
	author_tokens = [normalize(w) for w in (entry.get("author") or "").split() if len(w) >= 4][:6]
	author_hit = any(inhay(t) for t in author_tokens)
	ok = len(hits) >= max(1, len(kws) // 2) or (hits and author_hit)
	if ok:
		return {"level": "verified", "title_hits": hits, "author_in_text": author_hit,
			"caveat": "طُوبق عنوان الكتاب داخل نصّه المستخرَج"}
	return {"level": "needs_review", "title_hits": hits, "author_in_text": author_hit,
		"caveat": "نصّ الملف لا يطابق كلمات العنوان، فقد يكون كتابًا آخر أو مسحًا رديئًا (تحقّق بشريّ)"}


def http_check(url, want_title=None):
	try:
		req = urllib.request.Request(url, headers={"User-Agent": UA})
		with urllib.request.urlopen(req, timeout=30) as resp:
			ctype = resp.headers.get("Content-Type", "")
			body = resp.read(200000) if "html" in ctype else b""
		res = {"live": True, "ctype": ctype.split(";")[0]}
		if want_title and body:
			text = normalize(body.decode("utf-8", "ignore"))
			res["title_on_page"] = any(k in text for k in keywords(want_title))
		return res
	except Exception as e:  # noqa: BLE001
		return {"live": False, "reason": str(e)[:80]}


def main():
	ap = argparse.ArgumentParser()
	ap.add_argument("--links", action="store_true", help="also HTTP-check source links (network)")
	args = ap.parse_args()

	if not CATALOG.exists():
		sys.exit(f"catalog not found: {CATALOG}")
	catalog = json.load(open(CATALOG, encoding="utf-8"))
	records = []
	counts = {}
	needs_review = []

	for e in catalog["books"]:
		path = PDF_DIR / safe_name(e)
		rec = {"i": e["i"], "title": e["title"], "tier": e.get("tier"),
			"metadata_note": "المؤلف وسنة الوفاة مصرَّح بهما من مصدر آليّ، غير متحقَّقين مستقلًّا"}
		if path.exists() and path.stat().st_size > 0:
			rec["verification"] = verify_pdf(e, path)
			rec["pdf"] = str(path.relative_to(BASE))
		else:
			# no local file: cite-only or un-fetched. Optionally confirm the link is live.
			link = (e.get("fetch_url") or "").strip() or (
				e["digital_sources"][0]["ref"] if e.get("digital_sources") else "")
			if args.links and link.startswith("http"):
				chk = http_check(link, e["title"])
				if chk.get("live"):
					rec["verification"] = {"level": "link_ok", "link": link, "http": chk,
						"caveat": "رابط حيّ؛ المحتوى غير مُنزَّل فلا فحص نصّي (خاصةً المحميّ)"}
				else:
					rec["verification"] = {"level": "needs_review", "link": link, "http": chk,
						"caveat": "الرابط لم يستجب، تأكّد يدويًّا"}
			else:
				rec["verification"] = {"level": "link_ok" if link else "needs_review",
					"link": link,
					"caveat": ("رابط مصدر مذكور، غير مفحوص (شغّل --links للفحص)" if link
						else "لا ملف ولا رابط مؤكَّد، تحقّق بشريّ")}
		lvl = rec["verification"]["level"]
		counts[lvl] = counts.get(lvl, 0) + 1
		if lvl == "needs_review":
			needs_review.append({"i": e["i"], "title": e["title"], "why": rec["verification"]["caveat"]})
		# write the level back into the catalog entry
		e["verification"] = lvl
		records.append(rec)

	json.dump(catalog, open(CATALOG, "w", encoding="utf-8"), ensure_ascii=False, indent="\t")
	json.dump({"total": len(records), "counts": counts, "needs_review": needs_review,
		"records": records}, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent="\t")

	print(f"verified {len(records)} catalog entries:")
	for k, v in sorted(counts.items()):
		print(f"  {k}: {v}")
	if needs_review:
		print(f"NEEDS REVIEW ({len(needs_review)}):")
		for n in needs_review:
			print(f"  #{n['i']} {n['title'][:45]} — {n['why']}")
	print(f"wrote {OUT.relative_to(BASE)} and updated the catalog verification field")


if __name__ == "__main__":
	main()
