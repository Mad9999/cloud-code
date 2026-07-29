# -*- coding: utf-8 -*-
"""Print the verified-quote count, so a commit message never carries a remembered number.

Rule 26z. Twice in one session I typed the count from memory into a commit
message and twice it was wrong, because I wrote the message in the same breath
as the run that would have measured it. A number that can be measured must
never be recalled.
"""
import io
import subprocess
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
out = subprocess.run([sys.executable, 'pipeline/verify_quotes.py'],
                     capture_output=True, text=True, encoding='utf-8').stdout
for line in out.splitlines():
	if 'verbatim tafsir quotes' in line:
		print(line.split(':')[1].strip())
		break
else:
	sys.exit('verify_quotes.py did not report a count')
