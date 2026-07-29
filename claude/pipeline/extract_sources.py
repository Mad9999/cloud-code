"""Source-library extractor for the Qur'anic Engineering project.

Reads the reference catalog (data/sources_catalog.json — a web-verified list of
the project's 50 reference books, each with author, era, a copyright *tier* and,
where lawful, a fetch URL), then:

  * downloads the PDF of every PUBLIC-DOMAIN work (classical heritage) and every
    FREE-OFFICIAL work (modern/academic with an author/publisher-authorized free
    copy) into sources/pdf/ ;
  * NEVER downloads COPYRIGHTED works that have no authorized free copy — it only
    records where to obtain them legally, so we can cite them later ;
  * writes docs/sources-library.md — a human-readable attribution catalog ;
  * writes data/sources_manifest.json — a machine record of what was fetched and
    the exact attribution for each book.

Copyright honesty is by design: piracy mirrors are never used (the resolver
workflow rejects them), and copyrighted works are cited, not copied.

Usage:
  python3 extract_sources.py            # report + write catalog docs, no download
  python3 extract_sources.py --fetch    # also download public-domain + free-official PDFs
"""

import argparse
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
CATALOG = BASE / "data" / "sources_catalog.json"
PDF_DIR = BASE / "sources" / "pdf"
MANIFEST = BASE / "data" / "sources_manifest.json"
DOC = BASE / "docs" / "sources-library.md"

UA = "Mozilla/5.0 (compatible; QuranEngineeringSourceBot/1.0)"
FETCHABLE_TIERS = {"public_domain", "free_official"}
TIER_LABEL = {
	"public_domain": "تراث (ملكية عامة)",
	"free_official": "نسخة مجانية رسمية",
	"copyrighted": "محميّ (لا يُحمَّل، إسناد فقط)",
	"uncertain": "غير مؤكّد",
}


def load_catalog():
	if not CATALOG.exists():
		sys.exit(
			f"catalog not found: {CATALOG}\n"
			"Run the source-resolver workflow first, then write its verified "
			"output to data/sources_catalog.json."
		)
	with open(CATALOG, encoding="utf-8") as f:
		return json.load(f)


def safe_name(entry):
	title = entry["title"].replace("/", "-").replace(" ", "_")[:60]
	return f"{entry['i']:02d}-{title}.pdf"


def fetch_url_of(entry):
	return (entry.get("fetch_url") or "").strip()


def is_fetchable(entry):
	"""Lawful to fetch: heritage public-domain, or an authorized free copy."""
	return entry.get("tier") in FETCHABLE_TIERS and bool(candidate_urls(entry))


def candidate_urls(entry):
	"""All http(s) URLs for this book: the verified fetch_url first, then every
	digital source. Landing pages are resolved to a direct PDF later."""
	urls = []
	fu = fetch_url_of(entry)
	if fu.startswith("http"):
		urls.append(fu)
	for s in entry.get("digital_sources", []):
		ref = (s.get("ref") or "").strip()
		if ref.startswith("http") and ref not in urls:
			urls.append(ref)
	return urls


def _http_get(url, timeout):
	req = urllib.request.Request(url, headers={"User-Agent": UA})
	with urllib.request.urlopen(req, timeout=timeout) as resp:
		return resp.read()


def archive_pdf_url(url):
	"""archive.org details/download page -> a direct .pdf download URL via the
	metadata API (picks the largest real PDF, skipping OCR/text sidecars)."""
	m = re.search(r"archive\.org/(?:details|download|metadata)/([^/?#]+)", url)
	if not m:
		return None
	ident = m.group(1)
	try:
		meta = json.loads(_http_get(f"https://archive.org/metadata/{ident}", 45))
	except Exception:  # noqa: BLE001
		return None
	pdfs = [f for f in meta.get("files", []) if str(f.get("name", "")).lower().endswith(".pdf")]
	if not pdfs:
		return None
	pdfs.sort(key=lambda f: int(f.get("size", 0) or 0), reverse=True)
	name = urllib.parse.quote(pdfs[0]["name"])
	return f"https://archive.org/download/{ident}/{name}"


def resolve_direct(entry):
	"""Return a directly-downloadable PDF URL, resolving landing pages."""
	cands = candidate_urls(entry)
	for u in cands:
		if u.lower().split("?")[0].endswith(".pdf"):
			return u
	for u in cands:
		if "archive.org" in u:
			direct = archive_pdf_url(u)
			if direct:
				return direct
	# last resort: a raw URL we can try and then PDF-validate
	return cands[0] if cands else None


def fetch_pdf(entry):
	PDF_DIR.mkdir(parents=True, exist_ok=True)
	dest = PDF_DIR / safe_name(entry)
	if dest.exists() and dest.stat().st_size > 0:
		return {"status": "already_present", "path": str(dest.relative_to(BASE))}
	url = resolve_direct(entry)
	if not url:
		return {"status": "failed", "reason": "no resolvable direct URL"}
	try:
		data = _http_get(url, 120)
	except Exception as e:  # noqa: BLE001 - report any network/HTTP failure, keep going
		return {"status": "failed", "reason": str(e), "url": url}
	if not data:
		return {"status": "failed", "reason": "empty response", "url": url}
	if data[:5] != b"%PDF-":
		# never keep an HTML landing/error page masquerading as a book
		return {"status": "failed", "reason": "not a PDF (landing/error page)", "url": url}
	dest.write_bytes(data)
	return {"status": "fetched", "path": str(dest.relative_to(BASE)), "bytes": len(data), "url": url}


def attribution(entry):
	"""Human citation string, e.g. «الكشاف» للزمخشري (ت 538هـ)."""
	parts = [f"«{entry['title']}»"]
	if entry.get("author"):
		parts.append(f"لـ{entry['author']}")
	death = entry.get("author_death_hijri") or entry.get("author_death_gregorian")
	if death:
		parts.append(f"(ت {death})")
	return " ".join(parts)


def source_link(entry):
	url = fetch_url_of(entry)
	if not url and entry.get("digital_sources"):
		url = entry["digital_sources"][0].get("ref", "")
	return url


VERIF_LABEL = {
	"verified": "✅ مؤكَّد (طُوبق العنوان داخل الملف)",
	"unreadable_text": "⚠️ نصّ معطوب، تحقّق بشريّ",
	"scanned_no_text": "⚠️ مسح ضوئي، تحقّق بشريّ",
	"link_ok": "🔗 رابط حيّ (غير مفحوص المحتوى)",
	"needs_review": "❗ يُراجَع (قد يكون كتابًا آخر)",
}
REVIEW_LEVELS = {"unreadable_text", "scanned_no_text", "needs_review"}


def write_doc(catalog, records):
	by_cat = {}
	for e in catalog["books"]:
		by_cat.setdefault(e.get("category", "أخرى"), []).append(e)
	rec_by_i = {r["i"]: r for r in records}

	lines = [
		"# مكتبة المصادر: الإسناد والتحقّق",
		"",
		"> تُولَّد آليًّا من `pipeline/extract_sources.py` + `pipeline/verify_sources.py` فوق `data/sources_catalog.json`.",
		"> **أمانة الحقوق**: يُجلب التراث العام والنسخ المجانية الرسمية فقط؛ والمحميّ يُذكر للاستشهاد ولا يُحمَّل (مواقع القرصنة مرفوضة).",
		"> **أمانة الدقّة**: عمود «التحقّق» آليّ حتميّ؛ «مؤكَّد» يعني أن عنوان الكتاب طُوبق داخل نصّه المستخرَج. ما وُسم بتحقّقٍ بشريّ **لا يُعتمد دون فحص**. والميتاداتا (المؤلف/سنة الوفاة) **مصرَّح بها من مصدر آليّ، غير متحقَّقة مستقلًّا** بعد.",
		"",
	]
	for cat, items in by_cat.items():
		lines.append(f"## {cat}")
		lines.append("")
		lines.append("| # | الكتاب | الدرجة | المصدر | الحالة | التحقّق |")
		lines.append("|---|---|---|---|---|---|")
		for e in sorted(items, key=lambda x: x["i"]):
			rec = rec_by_i.get(e["i"], {})
			status = rec.get("result", {}).get("status", "—")
			url = source_link(e)
			src_cell = f"[رابط]({url})" if url.startswith("http") else (url or "—")
			verif = VERIF_LABEL.get(e.get("verification"), "—")
			lines.append(
				f"| {e['i']} | {attribution(e)} | {TIER_LABEL.get(e.get('tier'), '—')} "
				f"| {src_cell} | {status} | {verif} |"
			)
		lines.append("")

	review = [e for e in catalog["books"] if e.get("verification") in REVIEW_LEVELS]
	if review:
		lines.append("## بحاجة إلى فحص بشريّ (لم يتأكّد آليًّا)")
		lines.append("")
		lines.append("> هذه ملفات نُزّلت لكن تعذّر تأكيد محتواها آليًّا (مسح ضوئي أو ترميز نصّ معطوب). **ليست خاطئة بالضرورة**، لكن لا تُعتمد حتى تُفتَح وتُراجَع.")
		lines.append("")
		for e in sorted(review, key=lambda x: x["i"]):
			lines.append(f"- **#{e['i']}** {attribution(e)} — {VERIF_LABEL.get(e.get('verification'))}")
		lines.append("")

	DOC.parent.mkdir(parents=True, exist_ok=True)
	DOC.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
	ap = argparse.ArgumentParser()
	ap.add_argument("--fetch", action="store_true", help="download public-domain + free-official PDFs")
	args = ap.parse_args()

	catalog = load_catalog()
	books = catalog["books"]
	records = []
	counts = {}

	def bump(k):
		counts[k] = counts.get(k, 0) + 1

	for e in books:
		rec = {"i": e["i"], "title": e["title"], "attribution": attribution(e),
			"tier": e.get("tier"), "sources": e.get("digital_sources", [])}
		if e.get("tier") == "copyrighted":
			rec["result"] = {"status": "cite_only", "note": "محميّ، يُذكر للاستشهاد ولا يُحمَّل",
				"where": source_link(e) or e.get("notes", "")}
			bump("cite_only")
		elif not is_fetchable(e):
			rec["result"] = {"status": "no_source", "note": "لا رابط مشروع متحقَّق"}
			bump("no_source")
		elif args.fetch:
			res = fetch_pdf(e)
			rec["result"] = res
			bump(res["status"])
		else:
			rec["result"] = {"status": "ready", "tier": e.get("tier"), "url": fetch_url_of(e)}
			bump("ready")
		records.append(rec)

	MANIFEST.parent.mkdir(parents=True, exist_ok=True)
	with open(MANIFEST, "w", encoding="utf-8") as f:
		json.dump({"total": len(books), "counts": counts, "records": records},
			f, ensure_ascii=False, indent="\t")
	write_doc(catalog, records)

	print(f"catalog: {len(books)} books")
	for k, v in sorted(counts.items()):
		print(f"  {k}: {v}")
	print(f"wrote {MANIFEST.relative_to(BASE)} and {DOC.relative_to(BASE)}")
	if not args.fetch:
		print("(run with --fetch to download the public-domain + free-official PDFs)")


if __name__ == "__main__":
	main()
