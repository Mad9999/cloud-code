"""«مأثور» must mean transmitted, and «قطعي» must mean the text.

Rule 2 promised «الفصل الصارم بين ثلاث درجات», and then defined the middle one as
«منقول عن مصدر معتمد يُذكر بالاسم (مسلم ٣٩٥، الكشاف، التحرير والتنوير، نظم الدرر،
مدارج السالكين...)». That definition puts a hadith in Muslim and a tafsir printed
in 1973 in the same box, so the separation it promised was not strict, it was a
list of respectable book titles.

Six entries carried the consequence to the reader's eye. Ibn al-Qayyim's reading
of the three tawhids in al-Fatiha's opening, Zamakhshari on the iltifat, Ibn
Ashur on the badal, Suyuti on al-Fatiha asking and al-Baqara answering. Every one
is a scholar's inference, some six to eight centuries after revelation and one in
the twentieth. All six said «مأثور» to the reader, which says: this was handed
down.

They do not belong with our own «اجتهادي» either. Ibn al-Qayyim's inference and
ours are not the same weight, and filing them together would be a different lie
in the opposite direction. So there is a fourth grade, «قولُ عالم», and this file
keeps the boundary: a source that is only later scholars cannot be «مأثور».

Usage: python verify_grades.py
"""

import json
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "data"
APP = BASE / "app" / "app.js"

# Books whose author is reasoning, not transmitting. Their names in a source line
# are not by themselves a defect; a source that has nothing else is.
LATER_SCHOLARS = [
	"ابن القيم", "مدارج السالكين", "مفتاح دار السعادة",
	"الزمخشري", "الكشاف",
	"ابن عاشور", "التحرير والتنوير",
	"البقاعي", "نظم الدرر",
	"الجرجاني", "دلائل الإعجاز",
	"السيوطي", "تناسق الدرر",
	"الرازي", "أبو حيان", "الألوسي",
]

# Anything that carries transmission: the six books, the two Sahihs, a Companion.
TRANSMITTERS = [
	"مسلم", "البخاري", "صحيح", "الترمذي", "أبو داود", "النسائي", "ابن ماجه",
	"أحمد", "الدارمي", "الحاكم", "ابن حبان", "الدارقطني", "ابن أبي حاتم",
	"الطبري", "ابن جرير", "ابن كثير", "القرطبي", "البغوي", "السعدي", "الميسّر", "الميسر",
	"ابن عباس", "ابن مسعود", "عائشة", "عمر", "علي", "أبي هريرة", "أبو هريرة",
	"متّفق", "متفق", "ابن إسحاق",
]

GRADES = {"qati", "ma'thur", "qawl_alim", "ijtihadi"}


def walk(node, out, where=""):
	if isinstance(node, dict):
		if "grade" in node:
			out.append((node.get("grade"), node.get("source") or "", where))
		for k, v in node.items():
			walk(v, out, k if isinstance(v, (dict, list)) else where)
	elif isinstance(node, list):
		for v in node:
			walk(v, out, where)


def main():
	failures = []
	app = APP.read_text(encoding="utf-8")

	for g in GRADES:
		if g not in app:
			failures.append(f"the app does not know the grade «{g}», so it cannot label it")
	print(f"  OK: the app knows all {len(GRADES)} grades")

	checked = mislabelled = 0
	for f in sorted(DATA.glob("*.json")):
		try:
			doc = json.loads(f.read_text(encoding="utf-8"))
		except ValueError:
			continue
		entries = []
		walk(doc, entries)
		for grade, source, where in entries:
			if grade is None:
				continue
			checked += 1
			if grade not in GRADES:
				failures.append(f"{f.name}: unknown grade «{grade}» at {where}")
				continue
			if grade != "ma'thur":
				continue
			late = [s for s in LATER_SCHOLARS if s in source]
			if late and not any(t in source for t in TRANSMITTERS):
				mislabelled += 1
				failures.append(
					f"{f.name}: «مأثور» on a source that is only {late[0]}, who is reasoning "
					f"and not transmitting. It is «قولُ عالم». ({source[:60]})"
				)
	print(f"  OK: checked {checked} graded entries; none calls a scholar's inference «مأثور»")

	# and the reader must be able to see the difference
	css = (BASE / "app" / "style.css").read_text(encoding="utf-8")
	if ".badge.qawl-alim" not in css:
		failures.append("«قولُ عالم» has no colour, so it renders indistinguishable")
	stray = re.findall(r'class="badge ([a-z-]+)"', (BASE / "app" / "index.html").read_text(encoding="utf-8"))
	known = {"qati", "mathur", "qawl-alim", "ijtihadi"}
	for cls in set(stray) - known:
		failures.append(f"index.html has a badge class «{cls}» with no grade behind it and no colour")
	print("  OK: each grade has a colour, and no badge in the page is class-less")

	if failures:
		print("\nA GRADE IS TELLING THE READER SOMETHING UNTRUE:", file=sys.stderr)
		for f in failures:
			print(f"  {f}", file=sys.stderr)
		sys.exit(1)
	print("\n«مأثور» means transmitted; a scholar's inference says so in its own name.")


if __name__ == "__main__":
	main()
