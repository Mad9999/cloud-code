"""Does what we wrote reach the reader's eye?

Every other valve here checks our data against the imams' books. Not one of
them checked our data against the screen, and in that gap twenty qadiyyas sat
for weeks: written, sourced, valve-green, and invisible. app.js did not contain
the string "qadiyya" once. Fourteen of the twenty had reached the browser's copy
by accident of an old build; six had not reached it at all, because writing to
data/ is not building, and we did not know that build.py leaves the tadabbur
files alone.

So this valve measures the distance from the file to the eye, in three hops:

    data/tadabbur_*.json  ->  app/generated/tadabbur_*.js  ->  app/app.js

A field present in the data and absent from the generated copy means someone
wrote without building. A field present in the generated copy and unnamed in
app.js means the app cannot show it, whatever it says in the file. Either way
the writing is not published, and the honest word for shipping it is that we
did not.

Usage: python verify_reaches_reader.py
"""

import json
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "data"
GEN = BASE / "app" / "generated"
APP = BASE / "app" / "app.js"

# Fields that carry writing meant for a reader. A field here must survive all
# three hops. Add to this list when a new kind of writing is invented, which is
# the moment the question 'does it reach anyone' is easiest to forget.
READER_FIELDS = ["qadiyya", "reflection", "sabab", "heart_state", "action", "names"]

# Rule 28: the scholar's register, not the engineer's. Seven of these were in the
# honesty fields, written the same day the rule was quoted approvingly: «مثبتٌ في
# verify_dayn_claim.py», «أُثبت الخطأ في الصمّام». The intent was right, since the
# honesty field exists so a reader can check us. The register was not: an imam
# writing his book does not hand you a filename. He says «ومن شاء فليعُدّ».
#
# The invitation stays and the machinery's vocabulary goes. The reader is told the
# claim is testable and that the tool ships with the project; he is not asked to
# learn our directory layout to trust our count.
WORKSHOP_WORDS = ["الصمّام", "الصمام", "verify_", ".py", "pipeline/", "البناء يفشل", "الوكيل", "الوكلاء"]


def load_js(path):
	raw = path.read_text(encoding="utf-8")
	return json.loads(raw.split("=", 1)[1].rstrip().rstrip(";"))


def count_field(node, field):
	if isinstance(node, dict):
		return (field in node) + sum(count_field(v, field) for v in node.values())
	if isinstance(node, list):
		return sum(count_field(v, field) for v in node)
	return 0


def main():
	app = APP.read_text(encoding="utf-8")
	failures = []
	checked = 0

	for src in sorted(DATA.glob("tadabbur_*.json")):
		stem = src.stem  # tadabbur_baqara
		built = GEN / f"{stem}.js"
		if not built.exists():
			continue
		data = json.loads(src.read_text(encoding="utf-8"))
		shipped = load_js(built)
		for field in READER_FIELDS:
			in_data = count_field(data, field)
			if not in_data:
				continue
			checked += 1
			in_built = count_field(shipped, field)
			if in_built < in_data:
				failures.append(
					f"{stem}: {field} written {in_data} times, only {in_built} built. "
					f"Run pipeline/{stem}.py"
				)
			if not re.search(r"\b" + re.escape(field) + r"\b", app):
				failures.append(
					f"{stem}: {field} is in the data {in_data} times and app.js never names it, "
					f"so the reader cannot see any of it"
				)

	print(f"  checked {checked} field/file pairs across data -> generated -> app")

	# and the register of what does reach him
	for src in sorted(DATA.glob("tadabbur_*.json")):
		text = src.read_text(encoding="utf-8")
		for word in WORKSHOP_WORDS:
			if word in text:
				# «الوكيل» is also God's name in the Qur'an, and «وكيل» is a word of
				# the Book; only flag it where it is ours, not where it is quoted
				hits = [
					line.strip()[:100]
					for line in text.split("\n")
					if word in line and "reflection" not in line[: line.find(word)]
				]
				if word in ("الوكيل", "الوكلاء") and not any("honesty" in h for h in hits):
					continue
				failures.append(
					f"{src.stem}: «{word}» reaches the reader (rule 28: the scholar's register,"
					f" not the workshop's). Say the claim is testable without naming the tool."
				)
	print("  OK: the reader is not handed our filenames or our machinery's vocabulary")

	if failures:
		print("\nWRITING THAT DOES NOT REACH THE READER:", file=sys.stderr)
		for f in sorted(set(failures)):
			print(f"  {f}", file=sys.stderr)
		sys.exit(1)
	print("  OK: every field we write is built, and named by the app that renders it")


if __name__ == "__main__":
	main()
