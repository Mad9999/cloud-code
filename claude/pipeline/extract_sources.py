"""Source-library extractor for the Qur'anic Engineering project.

Reads the reference catalog (data/sources_catalog.json — a web-verified list of
the project's reference books with author, era, copyright status and a digital
source), then:

  * downloads the PDF of every PUBLIC-DOMAIN work into sources/pdf/ ;
  * NEVER downloads copyrighted works (modern/academic) — it only records where
    to obtain them legally, so we can cite them later ;
  * writes docs/sources-library.md — a human-readable attribution catalog ;
  * writes data/sources_manifest.json — a machine record of what was fetched
    and the exact attribution for each book.

Usage:
  python3 extract_sources.py            # report + write catalog docs, no download
  python3 extract_sources.py --fetch    # also download public-domain PDFs
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
GRADE_LABEL = {
	"public_domain": "ملكية عامة",
	"copyrighted": "محميّ (لا يُحمَّل)",
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


def is_pdf_source(entry):
	"""A fetchable public-domain PDF: public-domain + a usable direct URL."""
	if entry.get("copyright_status") != "public_domain":
		return False
	url = (entry.get("best_fetch") or "").strip()
	return url.startswith("http")


def fetch_pdf(entry):
	url = entry["best_fetch"].strip()
	PDF_DIR.mkdir(parents=True, exist_ok=True)
	dest = PDF_DIR / safe_name(entry)
	if dest.exists() and dest.stat().st_size > 0:
		return {"status": "already_present", "path": str(dest.relative_to(BASE)), "url": url}
	try:
		req = urllib.request.Request(url, headers={"User-Agent": UA})
		with urllib.request.urlopen(req, timeout=60) as resp:
			data = resp.read()
		if not data:
			return {"status": "failed", "reason": "empty response", "url": url}
		dest.write_bytes(data)
		return {
			"status": "fetched",
			"path": str(dest.relative_to(BASE)),
			"bytes": len(data),
			"url": url,
		}
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


def write_doc(catalog, records):
	by_cat = {}
	for e in catalog["books"]:
		by_cat.setdefault(e.get("category", "أخرى"), []).append(e)
	rec_by_i = {r["i"]: r for r in records}

	lines = [
		"# مكتبة المصادر — الإسناد الكامل",
		"",
		"> تُولَّد آليًّا من `pipeline/extract_sources.py` فوق `data/sources_catalog.json` (روابط متحقَّقة عبر ورشة).",
		"> **أمانة الحقوق**: الكتب المحمية (الحديثة/الأكاديمية) لا تُحمَّل؛ يُذكر مصدرها للاستشهاد والاقتناء المشروع فقط.",
		"",
	]
	for cat, items in by_cat.items():
		lines.append(f"## {cat}")
		lines.append("")
		lines.append("| # | الكتاب | الحقوق | المصدر الرقمي | الحالة |")
		lines.append("|---|---|---|---|---|")
		for e in sorted(items, key=lambda x: x["i"]):
			rec = rec_by_i.get(e["i"], {})
			status = rec.get("result", {}).get("status", "—")
			src = e.get("best_fetch") or ""
			if not src and e.get("digital_sources"):
				src = e["digital_sources"][0].get("ref", "")
			src_cell = f"[رابط]({src})" if src.startswith("http") else (src or "—")
			lines.append(
				f"| {e['i']} | {attribution(e)} | {GRADE_LABEL.get(e.get('copyright_status'), '—')} "
				f"| {src_cell} | {status} |"
			)
		lines.append("")
	DOC.parent.mkdir(parents=True, exist_ok=True)
	DOC.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
	ap = argparse.ArgumentParser()
	ap.add_argument("--fetch", action="store_true", help="download public-domain PDFs")
	args = ap.parse_args()

	catalog = load_catalog()
	books = catalog["books"]
	records = []
	counts = {"fetched": 0, "already_present": 0, "skipped_copyright": 0, "no_source": 0, "failed": 0}

	for e in books:
		rec = {"i": e["i"], "title": e["title"], "attribution": attribution(e),
			"copyright_status": e.get("copyright_status"), "sources": e.get("digital_sources", [])}
		if e.get("copyright_status") == "copyrighted":
			rec["result"] = {"status": "skipped_copyright",
				"note": "محميّ — يُذكر للاستشهاد ولا يُحمَّل", "where": e.get("best_fetch") or e.get("notes", "")}
			counts["skipped_copyright"] += 1
		elif not is_pdf_source(e):
			rec["result"] = {"status": "no_source", "note": "لا رابط عام متحقَّق"}
			counts["no_source"] += 1
		elif args.fetch:
			res = fetch_pdf(e)
			rec["result"] = res
			counts[res["status"]] = counts.get(res["status"], 0) + 1
		else:
			rec["result"] = {"status": "ready", "url": e["best_fetch"]}
		records.append(rec)

	MANIFEST.parent.mkdir(parents=True, exist_ok=True)
	with open(MANIFEST, "w", encoding="utf-8") as f:
		json.dump({"total": len(books), "counts": counts, "records": records},
			f, ensure_ascii=False, indent="\t")
	write_doc(catalog, records)

	print(f"catalog: {len(books)} books")
	for k, v in counts.items():
		if v:
			print(f"  {k}: {v}")
	print(f"wrote {MANIFEST.relative_to(BASE)} and {DOC.relative_to(BASE)}")
	if not args.fetch:
		print("(run with --fetch to download the public-domain PDFs)")


if __name__ == "__main__":
	main()
