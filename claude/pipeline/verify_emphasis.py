# -*- coding: utf-8 -*-
"""Emphasis must mark where the eye stops, not style the paragraph.

Found by an adversary reading a subagent's imitation of my own writing, not by
reading my writing: it said that bolding every sentence means nothing is bolded,
and that this is the clearest tell of a machine author. Measured against the 139
stops written by hand, the charge held: 1.61 bold spans per line, and 77% of
lines carried bold across more than 60% of their length. The median bolded
fraction of a bolded line was 98%. So the marks were not emphasis at all; they
were a default paragraph style, and they steered the reader's eye nowhere.

This holds the corrected discipline:
  - a line longer than 70 characters may not be bolded across more than 60% of
    its length. Short lines are exempt on purpose: a one-line summary is itself
    the phrase the eye should stop at, and marking all of it is correct.
  - no single bold span may run past 120 characters. You cannot ask an eye to
    stop at a two-hundred-character run; that is a paragraph, not a phrase.
  - the whole corpus must stay under 0.6 bold spans per line
  - nothing inside « » or ﴿ ﴾ is bolded: a quotation is already marked by its
    own brackets, and bolding inside them competes with that signal
  - title and source carry no emphasis at all

The thresholds are not invented. They were read off the 55 stops written under
the corrected spec, which sit at 0.28 spans per line with nothing over-marked.
"""
import io
import json
import re
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
ROOT = Path(__file__).resolve().parent.parent
BOLD = re.compile(r'\*\*([^*]+)\*\*')
LINE_MAX = 0.60
SHORT_LINE = 70
SPAN_MAX = 120
CORPUS_MAX = 0.60
NO_EMPHASIS = ('title', 'source')
SKIP = {'grade'}


def stops(node, out=None, where=None):
	if out is None:
		out = []
	if isinstance(node, dict):
		if 'qadiyya' in node and isinstance(node['qadiyya'], dict):
			out.append((where, node.get('n'), node['qadiyya']))
		for v in node.values():
			stops(v, out, where)
	elif isinstance(node, list):
		for v in node:
			stops(v, out, where)
	return out


def bold_share(line):
	plain = BOLD.sub(r'\1', line)
	marked = sum(len(m) for m in BOLD.findall(line))
	return marked / max(len(plain), 1)


def main():
	problems = []
	spans = lines = total = 0
	for path in sorted((ROOT / 'data').glob('*.json')):
		try:
			doc = json.loads(path.read_text(encoding='utf-8'))
		except Exception:
			continue
		for _, ayah, q in stops(doc, where=path.name):
			total += 1
			for field, text in q.items():
				if field in SKIP or not isinstance(text, str):
					continue
				where = f"{path.name} {ayah} [{field}]"
				if field in NO_EMPHASIS and BOLD.search(text):
					problems.append(f"{where}: تغميقٌ في حقلٍ لا تغميقَ فيه")
				for quoted in re.findall(r'«([^»]*)»', text) + re.findall(r'﴿([^﴾]*)﴾', text):
					if '**' in quoted:
						problems.append(f"{where}: تغميقٌ داخل النقل -- «{BOLD.sub(r'\1', quoted)[:40]}»")
				for line in text.split('\n'):
					line = line.strip()
					if not line:
						continue
					lines += 1
					marks = BOLD.findall(line)
					spans += len(marks)
					plain = BOLD.sub(r'\1', line)
					for m in marks:
						if len(m) > SPAN_MAX:
							problems.append(f"{where}: مقطعٌ مغمَّقٌ طولُه {len(m)} حرفًا -- {m[:52]}")
					share = bold_share(line)
					if len(plain) > SHORT_LINE and share > LINE_MAX:
						problems.append(f"{where}: {share:.0%} من سطرٍ طولُه {len(plain)} مغمَّق -- {plain[:52]}")

	density = spans / max(lines, 1)
	print(f"  stops:                {total}")
	print(f"  bold spans per line:  {density:.2f}  (ceiling {CORPUS_MAX})")
	if density > CORPUS_MAX:
		problems.append(f"الكثافةُ العامّة {density:.2f} فوق السقف {CORPUS_MAX}")
	if problems:
		print(f"  >>> {len(problems)} مأخذًا:")
		for p in problems[:40]:
			print(f"      {p}")
		if len(problems) > 40:
			print(f"      ... و{len(problems) - 40} غيرها")
		sys.exit(1)
	print("  OK: emphasis marks a phrase, never a paragraph, and never a quotation")


if __name__ == '__main__':
	main()
