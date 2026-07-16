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

	if failures:
		print("\nWRITING THAT DOES NOT REACH THE READER:", file=sys.stderr)
		for f in sorted(set(failures)):
			print(f"  {f}", file=sys.stderr)
		sys.exit(1)
	print("  OK: every field we write is built, and named by the app that renders it")


if __name__ == "__main__":
	main()
