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
import sys
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
	"copyrighted": "محميّ (لا يُحمَّل — إسناد فقط)",
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
	return entry.get("tier") in FETCHABLE_TIERS and fetch_url_of(entry).startswith("http")


def fetch_pdf(entry):
	url = fetch_url_of(entry)
	PDF_DIR.mkdir(parents=True, exist_ok=True)
	dest = PDF_DIR / safe_name(entry)
	if dest.exists() and dest.stat().st_size > 0:
		return {"status": "already_present", "path": str(dest.relative_to(BASE)), "url": url}
	try:
		req = urllib.request.Request(url, headers={"User-Agent": UA})
		with urllib.request.urlopen(req, timeout=90) as resp:
			data = resp.read()
		if not data:
			return {"status": "failed", "reason": "empty response", "url": url}
		dest.write_bytes(data)
		return {"status": "fetched", "path": str(dest.relative_to(BASE)), "bytes": len(data), "url": url}
	except Exception as e:  # noqa: BLE001 - report any network/HTTP failure, keep going
		return {"status": "failed", "reason": str(e), "url": url}


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


def write_doc(catalog, records):
	by_cat = {}
	for e in catalog["books"]:
		by_cat.setdefault(e.get("category", "أخرى"), []).append(e)
	rec_by_i = {r["i"]: r for r in records}

	lines = [
		"# مكتبة المصادر — الإسناد الكامل",
		"",
		"> تُولَّد آليًّا من `pipeline/extract_sources.py` فوق `data/sources_catalog.json` (روابط متحقَّقة عبر ورشة، ومواقع القرصنة مرفوضة).",
		"> **أمانة الحقوق**: يُجلب التراث العام والنسخ المجانية الرسمية فقط؛ والكتب المحميّة تُذكر للاستشهاد والاقتناء المشروع، ولا تُحمَّل.",
		"",
	]
	for cat, items in by_cat.items():
		lines.append(f"## {cat}")
		lines.append("")
		lines.append("| # | الكتاب | الدرجة | المصدر | الحالة |")
		lines.append("|---|---|---|---|---|")
		for e in sorted(items, key=lambda x: x["i"]):
			rec = rec_by_i.get(e["i"], {})
			status = rec.get("result", {}).get("status", "—")
			url = source_link(e)
			src_cell = f"[رابط]({url})" if url.startswith("http") else (url or "—")
			lines.append(
				f"| {e['i']} | {attribution(e)} | {TIER_LABEL.get(e.get('tier'), '—')} "
				f"| {src_cell} | {status} |"
			)
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
			rec["result"] = {"status": "cite_only", "note": "محميّ — يُذكر للاستشهاد ولا يُحمَّل",
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
