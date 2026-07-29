"""Semantic knowledge-graph builder for Surah Al-Fatiha.

Transforms the golden dataset (data/surah_001.json) into a node/edge graph:
verses, words, roots and thematic axes as nodes; root membership, theme
membership and the sourced semantic links as typed edges.
"""

import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def build():
	with open(DATA_DIR / "surah_001.json", encoding="utf-8") as f:
		surah = json.load(f)

	nodes = []
	edges = []
	word_node = {}

	for verse in surah["verses"]:
		nodes.append({
			"id": f"v{verse['n']}",
			"kind": "verse",
			"label": f"آية {verse['n']}",
			"text": verse["uthmani"],
			"theme": verse["theme"],
		})
		for w in verse["words"]:
			wid = f"w{w['i']}"
			word_node[w["i"]] = wid
			nodes.append({
				"id": wid,
				"kind": "word",
				"label": w["text"],
				"verse": verse["n"],
				"root": w["root"],
				"pos": w["pos"],
				"gloss": w["gloss"],
			})
			edges.append({"from": f"v{verse['n']}", "to": wid, "type": "membership"})

	# Root nodes: one per distinct root, linked to every word sharing it.
	roots = {}
	for verse in surah["verses"]:
		for w in verse["words"]:
			if w["root"]:
				roots.setdefault(w["root"], []).append(w["i"])
	for root, word_ids in sorted(roots.items()):
		rid = f"r_{root}"
		nodes.append({
			"id": rid,
			"kind": "root",
			"label": root,
			"count": len(word_ids),
		})
		for i in word_ids:
			edges.append({"from": rid, "to": word_node[i], "type": "jidhri"})

	for theme in surah["themes"]:
		tid = f"t_{theme['id']}"
		nodes.append({
			"id": tid,
			"kind": "theme",
			"label": theme["label"],
			"grade": theme["grade"],
		})
		for i in theme["words"]:
			edges.append({"from": tid, "to": word_node[i], "type": "mawdui"})

	# Sourced semantic links become edges between word groups (first word of
	# each side is the representative endpoint to keep the graph readable).
	for link in surah["semantic_links"]:
		src = link.get("from_words", [])
		dst = link.get("to_words", [])
		if src and dst:
			edges.append({
				"from": word_node[src[0]],
				"to": word_node[dst[0]],
				"type": link["type"],
				"link_id": link["id"],
				"label": link["label"],
			})
		nodes.append({
			"id": f"l_{link['id']}",
			"kind": "link_card",
			"label": link["label"],
			"type": link["type"],
			"note": link["note"],
			"source": link["source"],
			"grade": link["grade"],
			"from_words": src,
			"to_words": dst,
			"external": link.get("to"),
			"at_verse": link.get("at_verse"),
		})

	return {"nodes": nodes, "edges": edges}


if __name__ == "__main__":
	g = build()
	kinds = {}
	for n in g["nodes"]:
		kinds[n["kind"]] = kinds.get(n["kind"], 0) + 1
	print("nodes:", kinds)
	types = {}
	for e in g["edges"]:
		types[e["type"]] = types.get(e["type"], 0) + 1
	print("edges:", types)
