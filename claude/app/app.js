/* Qur'anic Engineering MVP — interactive layers over the generated dataset.
   Plain vanilla JS, no external dependencies; works over file://. */

"use strict"

const D = window.QURAN_DATA
const $ = (sel) => document.querySelector(sel)

const COLORS = {
	page: "#0d0d0d", surface: "#1a1a19", ink: "#ffffff", ink2: "#c3c2b7",
	muted: "#898781", grid: "#2c2c2a", baseline: "#383835",
	blue: "#3987e5", aqua: "#199e70", yellow: "#c98500", violet: "#9085e9",
	red: "#e66767", magenta: "#d55181", orange: "#d95926",
}
const BIN_COLORS = {
	soft2: "#3987e5", soft1: "#86b6ef", neutral: "#6b6a64",
	hard1: "#e66767", hard2: "#d03b3b",
}
const BIN_LABELS = {
	soft2: "لينٌ ظاهر (همس/رخاوة/مد)", soft1: "مائل إلى اللين",
	neutral: "متوسط", hard1: "مائل إلى الشدة", hard2: "شدةٌ ظاهرة (استعلاء/قلقلة)",
}
const AR = {
	hams: "مهموس", jahr: "مجهور", shidda: "شديد", tawassut: "متوسط", rakhawa: "رخو",
	istiala: "مستعلٍ", istifal: "مستفل", safir: "صفير", ghunna: "غنة",
	tafashshi: "تفشٍّ", istitala: "استطالة", inhiraf: "انحراف", takrir: "تكرير",
	lin: "لين", madd: "مد",
	jawf: "الجوف", aqsa_halq: "أقصى الحلق", wasat_halq: "وسط الحلق",
	adna_halq: "أدنى الحلق", aqsa_lisan: "أقصى اللسان", wasat_lisan: "وسط اللسان",
	hafat_lisan: "حافة اللسان", tarf_lisan: "طرف اللسان", shafawi: "الشفتان",
}
const STATE_AR = { fatha: "فتحة", damma: "ضمة", kasra: "كسرة", sakin: "ساكن", madd: "مد" }
const GRADE_AR = { qati: "قطعي", "ma'thur": "مأثور", ijtihadi: "اجتهادي" }
const GRADE_CLASS = { qati: "qati", "ma'thur": "mathur", ijtihadi: "ijtihadi" }
const LINK_TYPE = {
	mawdui: { label: "موضوعي", color: COLORS.violet },
	munasaba: { label: "مناسبات", color: COLORS.yellow },
	balaghi: { label: "بلاغي", color: COLORS.magenta },
	nahwi: { label: "نحوي", color: COLORS.orange },
	tanazur: { label: "تناظر", color: COLORS.red },
	bayn_suwar: { label: "بين السور", color: COLORS.aqua },
	tafsiri: { label: "تفسيري", color: COLORS.blue },
}

const arNum = (n) => String(n).replace(/\d/g, (d) => "٠١٢٣٤٥٦٧٨٩"[d])
const gradeBadge = (g) => `<span class="badge ${GRADE_CLASS[g] || ""}">${GRADE_AR[g] || g}</span>`

/* ---------- tooltip ---------- */
const tip = $("#tooltip")
function showTip(html, x, y) {
	tip.innerHTML = html
	tip.style.display = "block"
	const w = tip.offsetWidth, h = tip.offsetHeight
	let px = x - w - 14
	if (px < 6) { px = x + 14 }
	let py = y - h / 2
	py = Math.max(6, Math.min(window.innerHeight - h - 6, py))
	tip.style.left = px + "px"
	tip.style.top = py + "px"
}
function hideTip() { tip.style.display = "none" }

/* ---------- tabs ---------- */
$("#tabs").addEventListener("click", (e) => {
	const btn = e.target.closest("button")
	if (!btn) { return }
	document.querySelectorAll("#tabs button").forEach((b) => b.classList.toggle("active", b === btn))
	document.querySelectorAll("section.layer").forEach((s) => s.classList.remove("visible"))
	$("#layer-" + btn.dataset.layer).classList.add("visible")
	if (btn.dataset.layer === "graph") { graphResize() }
	if (btn.dataset.layer === "phonetic") { drawRadar() }
	if (btn.dataset.layer === "acoustic") { drawBridge() }
	if (btn.dataset.layer === "observatory") { drawObsChart(); drawControlChart() }
	if (btn.dataset.layer === "scale") { drawScale() }
	if (btn.dataset.layer === "scenes") { sizeSceneCanvas(); if (!scenesRaf) { scenesLoop() } }
	if (btn.dataset.layer !== "dialogue") { stopDialogue() }
	if (btn.dataset.layer !== "tadabbur-short") { tsStop() }
	if (btn.dataset.layer === "suramap") { smResize() }
	const research = ["discover", "graph", "phonetic", "acoustic", "observatory", "explorer", "suramap"]
	$("#research-disclaimer").classList.toggle("show", research.includes(btn.dataset.layer))
})

/* ============================================================
   Layer 1 — Ring structure
   ============================================================ */
const RING = D.surah.ring_structure
const PAIR_COLORS = { "1-7": COLORS.red, "2-6": COLORS.aqua, "3-5": COLORS.violet }

function buildRing() {
	const W = 720, H = 560, cx = W / 2, cy = H / 2 - 10, R = 200
	const pos = {}
	for (let n = 1; n <= 7; n++) {
		// verse 4 (numeric axis) at the bottom; pairs mirror across the vertical
		const a = (90 + (n - 4) * (360 / 7)) * Math.PI / 180
		pos[n] = { x: cx + R * Math.cos(a), y: cy + R * Math.sin(a) }
	}
	let svg = `<svg viewBox="0 0 ${W} ${H}" style="width:100%">`
	svg += `<circle cx="${cx}" cy="${cy}" r="${R}" fill="none" stroke="${COLORS.grid}" stroke-width="1.5"/>`

	// mirror pair chords
	for (const p of RING.pairs) {
		const key = `${p.a}-${p.b}`, c = PAIR_COLORS[key]
		const A = pos[p.a], B = pos[p.b]
		svg += `<path d="M ${A.x} ${A.y} Q ${cx} ${cy} ${B.x} ${B.y}" fill="none" stroke="${c}" stroke-width="2" opacity="0.75" data-pair="${key}"/>`
	}
	// iltifat marker between v4 and v5
	const m1 = pos[4], m2 = pos[5]
	const mx = (m1.x + m2.x) / 2
	const my = (m1.y + m2.y) / 2
	svg += `<text x="${mx + (mx > cx ? 70 : -70)}" y="${my + 34}" fill="${COLORS.magenta}" font-size="15" text-anchor="middle">↯ الالتفات: من الغيبة إلى الخطاب</text>`

	// verse nodes: fill encodes the prophetic division
	for (let n = 1; n <= 7; n++) {
		const p = pos[n]
		const div = RING.prophetic_division
		const fill = n === div.pivot_verse ? COLORS.magenta : (div.first_half.includes(n) ? "#1c5cab" : "#0e7a56")
		const stroke = n === RING.numeric_axis ? COLORS.yellow : "rgba(255,255,255,0.25)"
		const verse = D.surah.verses[n - 1]
		svg += `<g class="ring-node" data-n="${n}" style="cursor:pointer">`
		svg += `<circle cx="${p.x}" cy="${p.y}" r="30" fill="${fill}" stroke="${stroke}" stroke-width="${n === RING.numeric_axis ? 3 : 1.5}"/>`
		svg += `<text x="${p.x}" y="${p.y + 7}" fill="#fff" font-size="20" text-anchor="middle">${arNum(n)}</text>`
		const lx = cx + (R + 66) * Math.cos((90 + (n - 4) * (360 / 7)) * Math.PI / 180)
		const ly = cy + (R + 66) * Math.sin((90 + (n - 4) * (360 / 7)) * Math.PI / 180)
		const short = verse.uthmani.split(" ").slice(0, 3).join(" ") + (verse.uthmani.split(" ").length > 3 ? "…" : "")
		svg += `<text x="${lx}" y="${ly}" fill="${COLORS.ink2}" font-size="15" text-anchor="middle">${short}</text>`
		svg += `</g>`
	}
	svg += `</svg>`
	$("#ring-svg-holder").innerHTML = svg

	document.querySelectorAll(".ring-node").forEach((g) => {
		g.addEventListener("click", () => selectRingVerse(Number(g.dataset.n)))
	})
	ringDefaultInfo()
}

function ringDefaultInfo() {
	const div = RING.prophetic_division
	$("#ring-info").innerHTML =
		`<b>${RING.axis_note}</b>` + gradeBadge("ijtihadi") +
		`<div style="margin-top:8px">${div.note} ${gradeBadge(div.grade)}</div>` +
		`<div class="src">المصدر: ${div.source} · منهجية التناظر: ${RING.methodology_source}</div>` +
		`<div class="legend" style="margin-top:10px">
			<span class="item"><span class="swatch" style="background:#1c5cab"></span> ثناءٌ لله (١–٤)</span>
			<span class="item"><span class="swatch" style="background:${COLORS.magenta}"></span> بين الله وعبده (٥)</span>
			<span class="item"><span class="swatch" style="background:#0e7a56"></span> عطاءٌ للعبد (٦–٧)</span>
			<span class="item"><span class="swatch" style="background:none;border:2px solid ${COLORS.yellow}"></span> المحور العددي (٤)</span>
		</div>`
}

function selectRingVerse(n) {
	const verse = D.surah.verses[n - 1]
	const pair = RING.pairs.find((p) => p.a === n || p.b === n)
	document.querySelectorAll("[data-pair]").forEach((el) => {
		const active = pair && el.dataset.pair === `${pair.a}-${pair.b}`
		el.setAttribute("stroke-width", active ? 4.5 : 2)
		el.setAttribute("opacity", active ? 1 : 0.25)
	})
	let html = `<b>﴿${verse.uthmani}﴾</b><div style="margin-top:6px">المحور الموضوعي: ${verse.theme}</div>`
	if (pair) {
		const other = pair.a === n ? pair.b : pair.a
		html += `<div style="margin-top:8px">↔ نظيرتها الآية ${arNum(other)}: ${pair.note} ${gradeBadge(pair.grade)}</div>`
	} else {
		html += `<div style="margin-top:8px">${RING.axis_note} ${gradeBadge("ijtihadi")}</div>`
	}
	if (n === RING.iltifat_at) {
		const l3 = D.surah.semantic_links.find((l) => l.id === "L3")
		html += `<div style="margin-top:8px">↯ ${l3.note} ${gradeBadge(l3.grade)}<div class="src">${l3.source}</div></div>`
	}
	$("#ring-info").innerHTML = html
}

/* ============================================================
   Layer 2 — Semantic force graph
   ============================================================ */
const KIND_STYLE = {
	verse: { color: COLORS.yellow, r: 15, label: "آية" },
	word: { color: COLORS.blue, r: 7, label: "كلمة" },
	root: { color: COLORS.aqua, r: 9, label: "جذر" },
	theme: { color: COLORS.violet, r: 12, label: "محور" },
}
let G = null

function mulberry32(seed) {
	return function () {
		seed |= 0; seed = (seed + 0x6d2b79f5) | 0
		let t = Math.imul(seed ^ (seed >>> 15), 1 | seed)
		t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
		return ((t ^ (t >>> 14)) >>> 0) / 4294967296
	}
}

function graphInit() {
	const canvas = $("#graph-canvas")
	const nodes = D.graph.nodes.filter((n) => n.kind !== "link_card")
		.map((n) => ({ ...n }))
	const idx = new Map(nodes.map((n, i) => [n.id, i]))
	const edges = D.graph.edges
		.filter((e) => idx.has(e.from) && idx.has(e.to))
		.map((e) => ({ ...e, a: idx.get(e.from), b: idx.get(e.to) }))
	const rand = mulberry32(7)
	nodes.forEach((n) => {
		const a = rand() * Math.PI * 2, r = 120 + rand() * 260
		n.x = Math.cos(a) * r; n.y = Math.sin(a) * r
		n.vx = 0; n.vy = 0
		n.r = KIND_STYLE[n.kind].r + (n.kind === "root" ? Math.min(4, n.count) : 0)
	})
	G = { canvas, ctx: canvas.getContext("2d"), nodes, edges, idx, alpha: 1, hover: null, drag: null, highlight: null }
	graphResize()
	requestAnimationFrame(graphTick)

	canvas.addEventListener("mousemove", (e) => {
		const p = graphMouse(e)
		if (G.drag) {
			G.drag.x = p.x; G.drag.y = p.y
			G.drag.vx = 0; G.drag.vy = 0
			G.alpha = Math.max(G.alpha, 0.35)
			return
		}
		G.hover = graphFind(p)
		canvas.style.cursor = G.hover ? "pointer" : "default"
		if (G.hover) {
			const n = G.hover
			let html = `<b>${n.label}</b> <span class="mut">(${KIND_STYLE[n.kind].label})</span>`
			if (n.kind === "word") {
				html += `<div class="mut">آية ${arNum(n.verse)} · ${n.pos}${n.root ? " · جذر: " + n.root : ""}</div><div>${n.gloss}</div>`
			}
			if (n.kind === "verse") { html += `<div>${n.theme}</div>` }
			if (n.kind === "root") { html += `<div class="mut">ورد ${arNum(n.count)} مرات في السورة</div>` }
			showTip(html, e.clientX, e.clientY)
		} else { hideTip() }
	})
	canvas.addEventListener("mousedown", (e) => {
		const n = graphFind(graphMouse(e))
		if (n) { G.drag = n; G.alpha = Math.max(G.alpha, 0.4) }
	})
	window.addEventListener("mouseup", () => { G.drag = null })
	canvas.addEventListener("mouseleave", () => { G.hover = null; hideTip() })

	// legend
	$("#graph-legend").innerHTML = Object.values(KIND_STYLE)
		.map((k) => `<span class="item"><span class="swatch" style="background:${k.color};border-radius:50%"></span> ${k.label}</span>`)
		.join("") +
		`<span class="item"><span class="line" style="background:${COLORS.magenta}"></span> رابط مُسند (انظر البطاقات)</span>`

	// sourced link cards
	const cards = D.graph.nodes.filter((n) => n.kind === "link_card")
	$("#links-list").innerHTML = cards.map((c) => {
		const t = LINK_TYPE[c.type] || { label: c.type, color: COLORS.muted }
		return `<div class="link-card" data-link="${c.id}">
			<div class="t"><span class="typechip" style="background:${t.color}"></span>${c.label} ${gradeBadge(c.grade)}</div>
			<div style="margin-top:4px">${c.note}</div>
			${c.external ? `<div style="margin-top:4px;color:${COLORS.ink2}">↗ ${c.external}</div>` : ""}
			<div class="src">النوع: ${t.label} · المصدر: ${c.source}</div>
		</div>`
	}).join("")
	document.querySelectorAll(".link-card").forEach((el) => {
		const card = cards.find((c) => c.id === el.dataset.link)
		el.addEventListener("mouseenter", () => {
			el.classList.add("hl")
			G.highlight = new Set([...(card.from_words || []), ...(card.to_words || [])].map((i) => "w" + i))
		})
		el.addEventListener("mouseleave", () => {
			el.classList.remove("hl")
			G.highlight = null
		})
	})
}

function graphResize() {
	const canvas = G.canvas
	const cssW = canvas.parentElement.clientWidth - 40
	const dpr = window.devicePixelRatio || 1
	canvas.style.height = "560px"
	canvas.width = cssW * dpr
	canvas.height = 560 * dpr
	G.dpr = dpr; G.w = cssW; G.h = 560
	G.alpha = Math.max(G.alpha, 0.3)
}

function graphMouse(e) {
	const rect = G.canvas.getBoundingClientRect()
	return { x: e.clientX - rect.left - G.w / 2, y: e.clientY - rect.top - G.h / 2 }
}

function graphFind(p) {
	let best = null, bd = 1e9
	for (const n of G.nodes) {
		const d = Math.hypot(n.x - p.x, n.y - p.y)
		if (d < n.r + 6 && d < bd) { best = n; bd = d }
	}
	return best
}

function graphTick() {
	const { nodes, edges, ctx } = G
	if (G.alpha > 0.005) {
		// pairwise repulsion
		for (let i = 0; i < nodes.length; i++) {
			for (let j = i + 1; j < nodes.length; j++) {
				const a = nodes[i], b = nodes[j]
				let dx = b.x - a.x, dy = b.y - a.y
				let d2 = dx * dx + dy * dy
				if (d2 < 1) { d2 = 1; dx = 1 }
				const f = (3200 * G.alpha) / d2
				const d = Math.sqrt(d2)
				const fx = (dx / d) * f, fy = (dy / d) * f
				a.vx -= fx; a.vy -= fy; b.vx += fx; b.vy += fy
			}
		}
		// springs
		for (const e of edges) {
			const a = nodes[e.a], b = nodes[e.b]
			const dx = b.x - a.x, dy = b.y - a.y
			const d = Math.max(1, Math.hypot(dx, dy))
			const target = e.type === "membership" ? 105 : e.type === "jidhri" ? 80 : 150
			const f = ((d - target) / d) * 0.028 * G.alpha * 8
			a.vx += dx * f; a.vy += dy * f
			b.vx -= dx * f; b.vy -= dy * f
		}
		// centering gravity + integration
		for (const n of nodes) {
			n.vx -= n.x * 0.0009 * G.alpha * 8
			n.vy -= n.y * 0.0015 * G.alpha * 8
			if (n !== G.drag) {
				n.x += n.vx; n.y += n.vy
			}
			n.vx *= 0.86; n.vy *= 0.86
		}
		G.alpha *= 0.995
	}
	graphDraw(ctx)
	requestAnimationFrame(graphTick)
}

function graphDraw(ctx) {
	const { nodes, edges } = G
	ctx.setTransform(G.dpr, 0, 0, G.dpr, (G.w / 2) * G.dpr, (G.h / 2) * G.dpr)
	ctx.clearRect(-G.w / 2, -G.h / 2, G.w, G.h)
	ctx.fillStyle = COLORS.surface
	ctx.fillRect(-G.w / 2, -G.h / 2, G.w, G.h)

	for (const e of edges) {
		const a = nodes[e.a], b = nodes[e.b]
		const semantic = !["membership", "jidhri", "mawdui"].includes(e.type)
		if (semantic) {
			ctx.strokeStyle = COLORS.magenta
			ctx.lineWidth = 1.8
			ctx.globalAlpha = 0.85
		} else {
			ctx.strokeStyle = e.type === "jidhri" ? COLORS.aqua : e.type === "mawdui" ? COLORS.violet : "#3a3a38"
			ctx.lineWidth = e.type === "membership" ? 0.7 : 1.1
			ctx.globalAlpha = e.type === "membership" ? 0.55 : 0.6
		}
		ctx.beginPath()
		ctx.moveTo(a.x, a.y)
		ctx.lineTo(b.x, b.y)
		ctx.stroke()
	}
	ctx.globalAlpha = 1

	for (const n of nodes) {
		const hl = G.highlight && G.highlight.has(n.id)
		const dim = G.highlight && !hl
		ctx.globalAlpha = dim ? 0.25 : 1
		ctx.beginPath()
		ctx.arc(n.x, n.y, n.r, 0, Math.PI * 2)
		ctx.fillStyle = KIND_STYLE[n.kind].color
		ctx.fill()
		// 2px surface ring separates overlapping marks
		ctx.lineWidth = hl ? 2.5 : 2
		ctx.strokeStyle = hl ? "#ffffff" : COLORS.surface
		ctx.stroke()
		if (n === G.hover) {
			ctx.beginPath()
			ctx.arc(n.x, n.y, n.r + 3.5, 0, Math.PI * 2)
			ctx.strokeStyle = "#fff"
			ctx.lineWidth = 1.5
			ctx.stroke()
		}
		ctx.fillStyle = dim ? "rgba(195,194,183,0.3)" : (n.kind === "word" ? COLORS.ink2 : COLORS.ink)
		ctx.font = (n.kind === "word" ? "13px " : "14px ") + '"Amiri","Noto Naskh Arabic",serif'
		ctx.textAlign = "center"
		ctx.fillText(arNum(n.label), n.x, n.y - n.r - 5)
	}
	ctx.globalAlpha = 1
}

/* ============================================================
   Layer 3 — Textual phonetic fingerprint
   ============================================================ */
function buildPhonetic() {
	$("#phonetic-legend").innerHTML = Object.keys(BIN_COLORS)
		.map((b) => `<span class="item"><span class="swatch" style="background:${BIN_COLORS[b]}"></span> ${BIN_LABELS[b]}</span>`)
		.join("")

	$("#phonetic-verses").innerHTML = D.phonetics.verses.map((pv) => {
		const verse = D.surah.verses[pv.n - 1]
		const chips = pv.phonemes.map((p, i) =>
			`<span class="chip ${p.state === "madd" ? "madd" : ""}" style="background:${BIN_COLORS[p.bin]}" data-v="${pv.n}" data-i="${i}">
				${p.char}${p.state === "madd" ? "ـ" : ""}<small>${STATE_AR[p.state]}</small>
			</span>`).join("")
		const s = pv.stats
		return `<div class="verse-block">
			<div class="vtitle"><span class="num">${arNum(pv.n)} ·</span> ﴿${verse.uthmani}﴾</div>
			<div class="chips">${chips}</div>
			<div class="stats-row">
				<span>${arNum(s.phoneme_count)} صوتاً</span>
				<span>همس ${s.pct_hams}٪</span>
				<span>مد ${s.pct_madd}٪</span>
				<span>استعلاء ${s.pct_istiala}٪</span>
				<span>مقياس الحدة ${s.mean_intensity}</span>
			</div>
		</div>`
	}).join("")

	$("#phonetic-verses").addEventListener("mousemove", (e) => {
		const chip = e.target.closest(".chip")
		if (!chip) { hideTip(); return }
		const p = D.phonetics.verses[chip.dataset.v - 1].phonemes[chip.dataset.i]
		const a = p.attrs
		const extras = a.extras.map((x) => AR[x]).join("، ")
		const flags = p.flags.filter((f) => ["lin", "madd_lazim", "waqf"].includes(f))
			.map((f) => ({ lin: "حرف لين", madd_lazim: "مد لازم (٦ حركات)", waqf: "سكون الوقف" })[f]).join("، ")
		showTip(
			`<b>${a.name}</b> — ${STATE_AR[p.state]}` +
			`<div>${AR[a.voicing]} · ${AR[a.strength]} · ${AR[a.elevation]}${a.itbaq ? " · مطبق" : ""}${extras ? " · " + extras : ""}</div>` +
			`<div class="mut">المخرج: ${AR[a.makhraj]} · درجة الحدة: ${p.intensity}${flags ? " · " + flags : ""}</div>`,
			e.clientX, e.clientY,
		)
	})
	$("#phonetic-verses").addEventListener("mouseleave", hideTip)

	// radar controls: pick up to two verses (series A blue, series B yellow)
	const ctrl = $("#radar-controls")
	ctrl.innerHTML = D.phonetics.verses
		.map((pv) => `<button data-n="${pv.n}">آية ${arNum(pv.n)}</button>`).join("")
	ctrl.addEventListener("click", (e) => {
		const b = e.target.closest("button")
		if (!b) { return }
		const n = Number(b.dataset.n)
		const i = radarSel.indexOf(n)
		if (i >= 0) { radarSel.splice(i, 1) }
		else { radarSel.push(n); if (radarSel.length > 2) { radarSel.shift() } }
		drawRadar()
	})
	buildStatsTable()
}

let radarSel = [5, 1]
const RADAR_AXES = [
	{ key: "pct_hams", label: "همس ٪" },
	{ key: "pct_shidda", label: "شدة ٪" },
	{ key: "pct_istiala", label: "استعلاء ٪" },
	{ key: "pct_madd", label: "مد ٪" },
	{ key: "pct_ghunna", label: "غنة ٪" },
	{ key: "intensity_norm", label: "مقياس الحدة" },
]

function radarValue(stats, key) {
	if (key === "intensity_norm") { return ((stats.mean_intensity + 3) / 11) * 100 }
	return stats[key]
}

function drawRadar() {
	const canvas = $("#radar-canvas")
	const cssW = canvas.parentElement.clientWidth - 40
	const dpr = window.devicePixelRatio || 1
	canvas.width = cssW * dpr
	canvas.height = 420 * dpr
	canvas.style.height = "420px"
	const ctx = canvas.getContext("2d")
	ctx.setTransform(dpr, 0, 0, dpr, cssW / 2, 215)
	ctx.clearRect(-cssW / 2, -215, cssW, 420)
	const R = 145
	// per-axis normalization to the max across all verses (values are small %)
	const maxes = RADAR_AXES.map((ax) =>
		Math.max(...D.phonetics.verses.map((v) => radarValue(v.stats, ax.key))) || 1)

	ctx.strokeStyle = COLORS.grid
	ctx.fillStyle = COLORS.muted
	ctx.font = '13px system-ui'
	for (let ring = 1; ring <= 4; ring++) {
		ctx.beginPath()
		for (let i = 0; i <= RADAR_AXES.length; i++) {
			const a = -Math.PI / 2 + (i * 2 * Math.PI) / RADAR_AXES.length
			const r = (R * ring) / 4
			const x = r * Math.cos(a), y = r * Math.sin(a)
			if (i === 0) { ctx.moveTo(x, y) } else { ctx.lineTo(x, y) }
		}
		ctx.stroke()
	}
	RADAR_AXES.forEach((ax, i) => {
		const a = -Math.PI / 2 + (i * 2 * Math.PI) / RADAR_AXES.length
		ctx.strokeStyle = COLORS.baseline
		ctx.beginPath()
		ctx.moveTo(0, 0)
		ctx.lineTo(R * Math.cos(a), R * Math.sin(a))
		ctx.stroke()
		ctx.fillStyle = COLORS.ink2
		ctx.textAlign = "center"
		ctx.fillText(ax.label, (R + 34) * Math.cos(a), (R + 26) * Math.sin(a) + 4)
	})

	const seriesColors = [COLORS.blue, COLORS.yellow]
	radarSel.forEach((n, si) => {
		const stats = D.phonetics.verses[n - 1].stats
		ctx.beginPath()
		RADAR_AXES.forEach((ax, i) => {
			const a = -Math.PI / 2 + (i * 2 * Math.PI) / RADAR_AXES.length
			const r = (radarValue(stats, ax.key) / maxes[i]) * R
			const x = r * Math.cos(a), y = r * Math.sin(a)
			if (i === 0) { ctx.moveTo(x, y) } else { ctx.lineTo(x, y) }
		})
		ctx.closePath()
		ctx.strokeStyle = seriesColors[si]
		ctx.lineWidth = 2
		ctx.stroke()
		ctx.globalAlpha = 0.14
		ctx.fillStyle = seriesColors[si]
		ctx.fill()
		ctx.globalAlpha = 1
		RADAR_AXES.forEach((ax, i) => {
			const a = -Math.PI / 2 + (i * 2 * Math.PI) / RADAR_AXES.length
			const r = (radarValue(stats, ax.key) / maxes[i]) * R
			ctx.beginPath()
			ctx.arc(r * Math.cos(a), r * Math.sin(a), 4, 0, Math.PI * 2)
			ctx.fillStyle = seriesColors[si]
			ctx.fill()
			ctx.strokeStyle = COLORS.surface
			ctx.lineWidth = 2
			ctx.stroke()
		})
	})

	$("#radar-legend").innerHTML = radarSel.map((n, si) =>
		`<span class="item"><span class="swatch" style="background:${seriesColors[si]}"></span> آية ${arNum(n)}: ﴿${D.surah.verses[n - 1].uthmani}﴾</span>`,
	).join("") + `<span class="item" style="color:${COLORS.muted}">كل بُعد منسوب إلى أعلى قيمته بين الآيات السبع</span>`

	document.querySelectorAll("#radar-controls button").forEach((b) => {
		const si = radarSel.indexOf(Number(b.dataset.n))
		b.className = si === 0 ? "sel-a" : si === 1 ? "sel-b" : ""
	})
}

function buildStatsTable() {
	const head = ["الآية", "الأصوات", "همس ٪", "جهر ٪", "شدة ٪", "استعلاء ٪", "مد ٪", "غنة ٪", "مقياس الحدة"]
	let html = "<tr>" + head.map((h) => `<th>${h}</th>`).join("") + "</tr>"
	for (const pv of D.phonetics.verses) {
		const s = pv.stats
		html += `<tr><td>آية ${arNum(pv.n)}</td><td>${s.phoneme_count}</td><td>${s.pct_hams}</td><td>${s.pct_jahr}</td><td>${s.pct_shidda}</td><td>${s.pct_istiala}</td><td>${s.pct_madd}</td><td>${s.pct_ghunna}</td><td>${s.mean_intensity}</td></tr>`
	}
	$("#stats-table").innerHTML = html
}

/* ============================================================
   Layer 4 — Physical acoustics of a real recitation
   ============================================================ */
function buildAcoustic() {
	$("#acoustic-src").textContent =
		`التلاوة: ${D.acoustics.reciter} — المصدر: ${D.acoustics.source}. ` +
		"الطيف محسوب بتحويل فورييه (نافذة ٢٠٤٨ عينة): الأفقي زمن، والعمودي تردد حتى ٥ كيلوهرتز، والإضاءة شدة الطاقة."
	$("#acoustic-cards").innerHTML = D.acoustics.verses.map((v) => {
		if (v.missing) {
			return `<div class="acoustic-card"><div class="vtitle">آية ${arNum(v.n)}</div>
				<div class="hint">الملف الصوتي غير متوفر — ضع ${"00100" + v.n}.mp3 في مجلد audio ثم أعد تشغيل build.py</div></div>`
		}
		const verse = D.surah.verses[v.n - 1]
		const bands = Object.entries(v.band_energy_pct)
			.map(([b, p]) => `<span>${b.replace("-", "–")} هرتز: <b>${p}٪</b></span>`).join("")
		return `<div class="acoustic-card verse-block">
			<div class="vtitle"><span class="num">${arNum(v.n)} ·</span> ﴿${verse.uthmani}﴾</div>
			<img src="generated/spectrograms/ayah_${v.n}.png" alt="طيف ترددي للآية ${v.n}" loading="lazy" />
			<audio controls preload="none" src="../audio/${v.file}"></audio>
			<div class="metric-row">
				<span>المدة: <b>${v.duration_s} ث</b></span>
				<span>مركز الثقل الطيفي: <b>${v.spectral_centroid_hz} هرتز</b></span>
				<span>حد ٨٥٪ من الطاقة: <b>${v.rolloff85_hz} هرتز</b></span>
			</div>
			<div class="metric-row">${bands}</div>
		</div>`
	}).join("")
}

function drawBridge() {
	const canvas = $("#bridge-canvas")
	const cssW = canvas.parentElement.clientWidth - 40
	const dpr = window.devicePixelRatio || 1
	canvas.width = cssW * dpr
	canvas.height = 340 * dpr
	canvas.style.height = "340px"
	const ctx = canvas.getContext("2d")
	ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
	ctx.clearRect(0, 0, cssW, 340)

	const verses = D.acoustics.verses.filter((v) => !v.missing)
	if (!verses.length) { return }
	const textVals = D.phonetics.verses.map((v) => (v.stats.mean_intensity + 3) / 11)
	const physVals = verses.map((v) => v.spectral_centroid_hz)
	const tMax = Math.max(...textVals), pMax = Math.max(...physVals)

	const padR = 60, padL = 16, padT = 24, padB = 44
	const plotW = cssW - padR - padL, plotH = 340 - padT - padB
	const groupW = plotW / 7

	// gridlines at 25/50/75/100 (% of max, indexed common base)
	ctx.strokeStyle = COLORS.grid
	ctx.fillStyle = COLORS.muted
	ctx.font = "11px system-ui"
	ctx.textAlign = "left"
	for (let g = 0; g <= 4; g++) {
		const y = padT + plotH - (plotH * g) / 4
		ctx.beginPath()
		ctx.moveTo(padL, y)
		ctx.lineTo(cssW - padR, y)
		ctx.stroke()
		ctx.fillText((g * 25) + "٪", cssW - padR + 8, y + 4)
	}

	verses.forEach((v, i) => {
		// RTL reading order: verse 1 on the right
		const gx = padL + plotW - (i + 1) * groupW
		const barW = 18, gap = 8
		const tH = (textVals[v.n - 1] / tMax) * plotH
		const pH = (physVals[i] / pMax) * plotH
		const cx = gx + groupW / 2

		const bar = (x, h, color) => {
			ctx.fillStyle = color
			ctx.beginPath()
			ctx.roundRect(x, padT + plotH - h, barW, h, [4, 4, 0, 0])
			ctx.fill()
		}
		bar(cx + gap / 2, tH, COLORS.blue)
		bar(cx - gap / 2 - barW, pH, COLORS.yellow)

		ctx.fillStyle = COLORS.ink2
		ctx.font = "11px system-ui"
		ctx.textAlign = "center"
		ctx.fillText(D.phonetics.verses[v.n - 1].stats.mean_intensity, cx + gap / 2 + barW / 2, padT + plotH - tH - 6)
		ctx.fillText(Math.round(physVals[i]) + "", cx - gap / 2 - barW / 2, padT + plotH - pH - 6)
		ctx.fillStyle = COLORS.ink
		ctx.font = "13px system-ui"
		ctx.fillText("آية " + arNum(v.n), cx, padT + plotH + 20)
	})

	ctx.strokeStyle = COLORS.baseline
	ctx.beginPath()
	ctx.moveTo(padL, padT + plotH)
	ctx.lineTo(cssW - padR, padT + plotH)
	ctx.stroke()

	$("#bridge-legend").innerHTML =
		`<span class="item"><span class="swatch" style="background:${COLORS.blue}"></span> مقياس الحدة النصي (القيمة فوق العمود بدرجته الخام)</span>` +
		`<span class="item"><span class="swatch" style="background:${COLORS.yellow}"></span> مركز الثقل الطيفي المقاس (هرتز)</span>` +
		`<span class="item" style="color:${COLORS.muted}">كل سلسلة منسوبة إلى أعلى قيمتها (أساس موحد ٪)</span>`
}

/* ============================================================
   Layer 5 — Practical framework
   ============================================================ */
function buildFramework() {
	const fw = D.surah.practical_framework
	$("#framework-title").innerHTML = fw.title + " " + gradeBadge(fw.grade)
	$("#framework-note").textContent = fw.note
	$("#framework-steps").innerHTML = fw.steps.map((s) => {
		const vs = s.verses.map((n) => `﴿${D.surah.verses[n - 1].uthmani}﴾`).join(" ")
		return `<div class="step">
			<div class="n">${arNum(s.n)}</div>
			<h4>${s.title}</h4>
			<div class="vs">${vs}</div>
			<p>${s.detail}</p>
		</div>`
	}).join("")
	const pd = D.surah.ring_structure.prophetic_division
	$("#prophetic-note").innerHTML = `${pd.note}<div class="src" style="margin-top:6px;color:${COLORS.muted}">المصدر: ${pd.source}</div>`
}

/* ============================================================
   Layer: خريطة السور (surah connection map) — 114 surahs linked by
   their shared distinctive roots. Force-directed. Computed facts.
   ============================================================ */
const SM = window.SURAH_MAP

// Grade a surah-similarity against the shuffled null (رقم القاعدة ١٦): most
// surah links are at chance level; only the strongest reflect real distinctive
// shared vocabulary. Computed band, not a hand-drawn one.
function simLift(sim) {
	const t = SM.control.table
	let row = null
	for (const r of t) { if (sim >= r.score) { row = r } }
	if (!row) { return { label: "قريبٌ من الصدفة", cls: "ec-chance" } }
	if (row.lift === null) { return { label: "نادرٌ في مقابل الصدفة", cls: "ec-strong" } }
	const x = row.lift
	if (x >= 3) { return { label: `أعلى من الصدفة بنحو ${arNum(Math.round(x))}×`, cls: "ec-above" } }
	if (x >= 1.5) { return { label: `أعلى من الصدفة قليلًا (${arNum(x)}×)`, cls: "ec-weak" } }
	return { label: "قريبٌ من الصدفة", cls: "ec-chance" }
}
let smG = null

function smName(n) {
	return (SM.surahs[n].name || ("سورة " + n)).replace(/^سُ?ورَةُ\s*/, "")
}

function buildSurahMap() {
	const canvas = $("#suramap-canvas")
	const nodes = Object.entries(SM.surahs).map(([n, d]) => ({ n: +n, ...d, vx: 0, vy: 0 }))
	const idx = new Map(nodes.map((nd, i) => [nd.n, i]))
	const seen = new Set(), edges = []
	nodes.forEach((nd) => {
		nd.neighbors.slice(0, 3).forEach(([m]) => {
			const key = nd.n < m ? nd.n + "-" + m : m + "-" + nd.n
			if (!seen.has(key) && idx.has(m)) { seen.add(key); edges.push({ a: idx.get(nd.n), b: idx.get(m) }) }
		})
	})
	const rand = mulberry32(9)
	const maxSize = Math.max(...nodes.map((n) => n.size))
	nodes.forEach((nd) => {
		const a = rand() * 6.2832, r = 120 + rand() * 260
		nd.x = Math.cos(a) * r; nd.y = Math.sin(a) * r
		nd.r = 4 + 13 * Math.sqrt(nd.size / maxSize)
	})
	smG = { canvas, ctx: canvas.getContext("2d"), nodes, edges, idx, alpha: 1, hover: null, sel: null, view: { scale: 1, cx: 0, cy: 0 } }
	smResize()
	requestAnimationFrame(smTick)

	canvas.addEventListener("mousemove", (e) => {
		const p = smMouse(e)
		smG.hover = smFind(p)
		canvas.style.cursor = smG.hover ? "pointer" : "default"
		if (smG.hover) {
			const d = smG.hover
			showTip(`<b>${smName(d.n)}</b> <span class="mut">(${d.type} · ${arNum(d.ayahs)} آية)</span>`, e.clientX, e.clientY)
		} else { hideTip() }
	})
	canvas.addEventListener("mousedown", (e) => {
		const nd = smFind(smMouse(e))
		if (nd) { smG.sel = nd; smG.alpha = Math.max(smG.alpha, 0.2); showSmPanel(nd) }
	})
	canvas.addEventListener("mouseleave", () => { smG.hover = null; hideTip() })

	$("#suramap-legend").innerHTML =
		`<span class="item"><span class="swatch" style="background:${COLORS.blue};border-radius:50%"></span> مكية</span>` +
		`<span class="item"><span class="swatch" style="background:${COLORS.aqua};border-radius:50%"></span> مدنية</span>` +
		`<span class="item" style="color:${COLORS.muted}">حجم الدائرة ~ طول السورة · الخيوط تصل المتشابهات</span>`
	$("#suramap-info").innerHTML = "اضغط أيّ سورة لترى أقرب السور إليها لغويًّا وما الجذور التي تجمعها."
}

function smResize() {
	const canvas = smG.canvas
	const cssW = canvas.parentElement.clientWidth - 40
	const dpr = window.devicePixelRatio || 1
	canvas.style.height = "560px"
	canvas.width = cssW * dpr; canvas.height = 560 * dpr
	smG.dpr = dpr; smG.w = cssW; smG.h = 560
	smG.alpha = Math.max(smG.alpha, 0.3)
}
function smMouse(e) {
	const rect = smG.canvas.getBoundingClientRect()
	const { scale, cx, cy } = smG.view
	return {
		x: (e.clientX - rect.left - smG.w / 2) / scale + cx,
		y: (e.clientY - rect.top - smG.h / 2) / scale + cy,
	}
}
function smFit() {
	const xs = smG.nodes.map((n) => n.x), ys = smG.nodes.map((n) => n.y)
	const minx = Math.min(...xs), maxx = Math.max(...xs), miny = Math.min(...ys), maxy = Math.max(...ys)
	const pad = 46
	const s = Math.min((smG.w - pad * 2) / Math.max(1, maxx - minx), (smG.h - pad * 2) / Math.max(1, maxy - miny), 1.3)
	smG.view = { scale: Math.max(0.45, s), cx: (minx + maxx) / 2, cy: (miny + maxy) / 2 }
}
function smFind(p) {
	let best = null, bd = 1e9
	for (const nd of smG.nodes) {
		const d = Math.hypot(nd.x - p.x, nd.y - p.y)
		if (d < nd.r + 6 && d < bd) { best = nd; bd = d }
	}
	return best
}

function smTick() {
	if (!$("#layer-suramap").classList.contains("visible")) { requestAnimationFrame(smTick); return }
	const { nodes, edges } = smG
	if (smG.alpha > 0.004) {
		const REP = 1600           // repulsion strength
		const MIND = 24            // distance floor: never let two nodes act closer than this
		const IDEAL = 96           // ideal edge length
		const MAXV = 30            // per-tick velocity cap — the guard against numerical blow-up
		for (const nd of nodes) { nd.vx *= 0.9; nd.vy *= 0.9 }
		for (let i = 0; i < nodes.length; i++) {
			const a = nodes[i]
			for (let j = i + 1; j < nodes.length; j++) {
				const b = nodes[j]
				let dx = b.x - a.x, dy = b.y - a.y
				let d = Math.hypot(dx, dy)
				if (d < 0.01) { dx = (i - j) || 1; dy = 1; d = Math.hypot(dx, dy) }
				const dd = Math.max(d, MIND)
				const f = (REP * smG.alpha) / (dd * dd)   // ~ inverse-square, bounded by the MIND floor
				const ux = dx / d, uy = dy / d
				a.vx -= ux * f; a.vy -= uy * f; b.vx += ux * f; b.vy += uy * f
			}
		}
		for (const e of edges) {
			const a = nodes[e.a], b = nodes[e.b]
			const dx = b.x - a.x, dy = b.y - a.y, d = Math.max(0.01, Math.hypot(dx, dy))
			const f = ((d - IDEAL) / d) * 0.05 * smG.alpha
			a.vx += dx * f; a.vy += dy * f; b.vx -= dx * f; b.vy -= dy * f
		}
		for (const nd of nodes) {
			nd.vx -= nd.x * 0.015 * smG.alpha      // gravity toward centre — keeps the cloud bounded
			nd.vy -= nd.y * 0.018 * smG.alpha
			const v = Math.hypot(nd.vx, nd.vy)
			if (v > MAXV) { nd.vx = (nd.vx / v) * MAXV; nd.vy = (nd.vy / v) * MAXV }
			nd.x += nd.vx; nd.y += nd.vy
		}
		smG.alpha *= 0.99
	}
	smFit()
	smDraw()
	requestAnimationFrame(smTick)
}

function smDraw() {
	const { ctx, nodes, edges } = smG
	const { scale, cx, cy } = smG.view
	ctx.setTransform(smG.dpr, 0, 0, smG.dpr, 0, 0)
	ctx.clearRect(0, 0, smG.w, smG.h)
	ctx.fillStyle = COLORS.surface
	ctx.fillRect(0, 0, smG.w, smG.h)
	ctx.setTransform(smG.dpr * scale, 0, 0, smG.dpr * scale,
		(smG.w / 2 - cx * scale) * smG.dpr, (smG.h / 2 - cy * scale) * smG.dpr)
	const selSet = smG.sel ? new Set(smG.sel.neighbors.slice(0, 3).map((x) => x[0]).concat(smG.sel.n)) : null
	for (const e of edges) {
		const a = nodes[e.a], b = nodes[e.b]
		const on = smG.sel && (a.n === smG.sel.n || b.n === smG.sel.n)
		ctx.strokeStyle = on ? hexA(COLORS.yellow, 0.8) : "#33322f"
		ctx.lineWidth = on ? 2 : 0.7
		ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke()
	}
	for (const nd of nodes) {
		const dim = selSet && !selSet.has(nd.n)
		ctx.globalAlpha = dim ? 0.25 : 1
		ctx.beginPath(); ctx.arc(nd.x, nd.y, nd.r, 0, Math.PI * 2)
		ctx.fillStyle = nd.type === "مكية" ? COLORS.blue : COLORS.aqua
		ctx.fill()
		ctx.lineWidth = (smG.sel && nd.n === smG.sel.n) ? 3 : 1.5
		ctx.strokeStyle = (smG.sel && nd.n === smG.sel.n) ? "#fff" : COLORS.surface
		ctx.stroke()
		if (nd.r > 9 || nd === smG.hover || (smG.sel && nd.n === smG.sel.n)) {
			ctx.fillStyle = dim ? "rgba(195,194,183,0.3)" : COLORS.ink
			ctx.font = "13px 'Amiri',serif"
			ctx.textAlign = "center"
			ctx.fillText(smName(nd.n), nd.x, nd.y - nd.r - 4)
		}
		ctx.globalAlpha = 1
	}
}

function smSelect(n) {
	const nd = smG.nodes.find((x) => x.n === n)
	if (nd) { smG.sel = nd; smG.alpha = Math.max(smG.alpha, 0.12); showSmPanel(nd) }
}

// The Surah Portrait: one place where a surah's whole picture comes together —
// what you expect (identity, its salient roots) plus what you may not notice
// (words confined to it) plus where it connects (its nearest surahs by shared
// rare roots, each clickable to walk the web). Unifies map + explorer + كشوف.
function showSmPanel(nd) {
	const prof = (window.EXPLORER_DATA.surah_profile || {})[nd.n] || {}
	const topR = (prof.top_roots || []).slice(0, 6).map(([r, c]) => `<b class="root">${r}</b> <span class="mut">${arNum(c)}</span>`).join("، ")
	const disc = DISC.surahs[nd.n]
	const uniq = (disc && disc.unique.length)
		? disc.unique.slice(0, 6).map((u) => `«${u[1]}»`).join("، ") : ""
	const rows = nd.neighbors.slice(0, 5).map(([m, sim, sh]) => {
		const lf = simLift(sim)
		return `<div class="rx-occ sm-nb" data-n="${m}"><span class="rx-ref">${smName(m)}</span> يجمعهما: ${sh.join("، ")} ` +
			`<span class="ec-band ${lf.cls}">${lf.label}</span></div>`
	}).join("")
	const c = SM.control
	$("#suramap-info").innerHTML =
		`<div class="rx-head"><b>${smName(nd.n)}</b> — ${nd.type} · ${arNum(nd.ayahs)} آية · ${arNum(nd.size)} كلمة</div>` +
		(topR ? `<div class="sm-sec"><span class="sm-lbl">أبرز جذورها:</span> ${topR}</div>` : "") +
		(uniq ? `<div class="sm-sec sm-uniq">✦ <span class="sm-lbl">كلماتٌ تفرّدت بها في القرآن كلّه:</span> ${uniq}</div>` : "") +
		`<div class="ec-control">⚖ <b>صمّام الأمانة:</b> قِسنا تشابُهَ السور على نموذجٍ عشوائيّ (خلطُ الجذور مع حفظ التكرارات). النتيجة الصادقة: <b>جِوارُ أكثر السور قريبٌ من الصدفة</b> (وسيطُ التشابه الحقيقيّ ${arNum(c.real_median_top_sim)} مقابل ${arNum(c.null_median_top_sim)} في العشوائيّ) — فطولُ السورة وكثرةُ ألفاظها الشائعة يكفيان لتشابهٍ ظاهر. لا يتجاوز الصدفةَ بوضوحٍ إلا القِلّةُ الأقوى. الوسمُ بجانب كلٍّ يبيّن ذلك؛ والجذورُ المشتركةُ حقٌّ في كلّ حال، والمعنى تتدبّره أنت.</div>` +
		`<div class="rx-stat" style="margin-top:6px">أقرب السور إليها لغويًّا — اضغط سورةً لتنتقل إليها في الشبكة:</div>` +
		`<div class="rx-list">${rows}</div>` +
		`<div class="sm-ctx">هذه أرقامٌ محسوبة تصف البنية، لا تفسّر المعنى. للقصّة وسببِ النزول والتفسير المُسنَد، ارجع إلى <button class="sm-ctx-link" data-go="sources">المصادر المُسنَدة</button>.</div>`
	$("#suramap-info").querySelectorAll(".sm-nb").forEach((el) =>
		el.addEventListener("click", () => smSelect(+el.dataset.n)))
	const go = $("#suramap-info").querySelector(".sm-ctx-link")
	if (go) { go.addEventListener("click", () => { const b = document.querySelector('#tabs button[data-layer="sources"]'); if (b) { b.click() } }) }
}

/* ============================================================
   Layer: مستكشف الجذر (root explorer) — every word is a gate to
   everywhere its root appears across the whole Qur'an. Computed facts.
   ============================================================ */
const EX = window.EXPLORER_DATA
const AL = window.AYAH_LINKS

// Grade an echo against the null model (رقم القاعدة ٥): most echoes are just
// vocabulary coincidence. Return the COMPUTED lift-over-chance and an honest
// band, so weak links can't masquerade as meaning — not even to us.
function echoLift(score) {
	const t = AL.control.table
	let row = null
	for (const r of t) { if (score >= r.score) { row = r } }
	if (!row) { return { label: "قريبٌ من الصدفة", cls: "ec-chance" } }
	if (row.lift === null) { return { label: "نادرٌ جدًّا في مقابل الصدفة", cls: "ec-strong" } }
	const x = row.lift
	if (x >= 8) { return { label: `أقوى من الصدفة بنحو ${arNum(Math.round(x))}×`, cls: "ec-strong" } }
	if (x >= 3) { return { label: `أعلى من الصدفة بنحو ${arNum(Math.round(x))}×`, cls: "ec-above" } }
	if (x >= 1.5) { return { label: `أعلى من الصدفة قليلًا (${arNum(x)}×)`, cls: "ec-weak" } }
	return { label: "قد يكون توارُدَ لفظٍ عاديّ — قريبٌ من الصدفة", cls: "ec-chance" }
}

function sname(s) {
	return (EX.surah_names[s] || ("سورة " + s)).replace(/^سُ?ورَةُ\s*/, "")
}
function ayahText(s, a) {
	const ws = EX.verse_words[s + ":" + a]
	return ws ? ws.map((w) => w[0]).join(" ") : ""
}

function buildExplorer() {
	const nums = Object.keys(EX.surah_names).map(Number).sort((a, b) => a - b)
	$("#explorer-controls").innerHTML =
		`<label class="ex-pick">السورة: <select id="ex-surah">` +
		nums.map((n) => `<option value="${n}">${arNum(n)} · ${sname(n)}</option>`).join("") +
		`</select></label>`
	$("#ex-surah").onchange = () => renderExplorerSurah(Number($("#ex-surah").value))
	// one delegated click handler for the whole (possibly large) verse list
	$("#explorer-verses").addEventListener("click", (e) => {
		const echo = e.target.closest(".rx-echo")
		if (echo) { showEchoes(echo.dataset.ref, echo); return }
		const el = e.target.closest(".rx-word")
		if (el) { showRootExplorer(el.dataset.root, el.textContent, el) }
	})
	renderExplorerSurah(1)
}

function renderExplorerSurah(n) {
	const cnt = EX.surah_ayahs[n]
	const prof = EX.surah_profile[n] || {}
	const topR = (prof.top_roots || []).map(([r, c]) => `${r} (${arNum(c)})`).join("، ")
	const disc = DISC.surahs[n]
	const uniqNote = (disc && disc.unique.length)
		? `<div class="ex-disc">✦ <b>ما قد لا تلاحظه:</b> ` +
			disc.unique.slice(0, 4).map((u) => `«${u[1]}»`).join("، ") +
			` — كلماتٌ لا يردُ جذرها في القرآن كلّه إلا في هذه السورة. <span class="mut">(كشفٌ محسوب)</span></div>`
		: ""
	$("#explorer-header").innerHTML =
		`<b>${sname(n)}</b> — ${EX.surah_type[n]} · ${arNum(cnt)} آية` +
		`${topR ? ` · أبرز جذورها: ${topR}` : ""}` +
		`${prof.unique_roots ? ` · جذورٌ تفرّدت بها: ${arNum(prof.unique_roots)}` : ""}` +
		uniqNote
	let html = ""
	for (let a = 1; a <= cnt; a++) {
		const ref = n + ":" + a
		const ws = EX.verse_words[ref] || []
		const words = ws.map((w) =>
			(w[1] && EX.roots[w[1]])
				? `<span class="rx-word" data-root="${w[1]}">${w[0]}</span>`
				: `<span>${w[0]}</span>`).join(" ")
		const echo = (AL.links[ref] && AL.links[ref].length)
			? ` <button class="rx-echo" data-ref="${ref}" title="مواضع يتردّد فيها صدى مفرداتها النادرة">⇄ صداها (${arNum(AL.links[ref].length)})</button>` : ""
		html += `<div class="rx-verse"><span class="rx-num">${arNum(a)}</span> ${words}${echo}</div>`
	}
	$("#explorer-verses").innerHTML = html
	$("#explorer-detail").innerHTML = "اضغط أيّ كلمة مُبرَزة لترى جذرها وأين ينتشر في القرآن كلّه — أو «⇄ صداها» لترى مواضعَ تُشبهها لغةً."
}

// The echo of a verse (السؤال السادس): where else across the whole Qur'an its
// DISTINCTIVE vocabulary reappears — pure root-sharing, the shared roots shown
// as proof. We surface the structure; the meaning is the reader's.
function showEchoes(ref, btn) {
	$("#explorer-verses").querySelectorAll(".rx-echo.sel").forEach((e) => e.classList.remove("sel"))
	if (btn) { btn.classList.add("sel") }
	const nbrs = AL.links[ref] || []
	const [s, a] = ref.split(":")
	const rows = nbrs.map(([o, sc, rs]) => {
		const [os, oa] = o.split(":")
		const chips = rs.map((r) => `<span class="ec-root">${r}</span>`).join("")
		const lf = echoLift(sc)
		return `<div class="rx-occ"><span class="rx-ref">${sname(os)} ${arNum(oa)}</span> ${chips} ` +
			`<span class="ec-band ${lf.cls}">${lf.label}</span>` +
			`<div class="ec-txt">${ayahText(os, oa)}</div></div>`
	}).join("")
	const c = AL.control
	$("#explorer-detail").innerHTML =
		`<div class="rx-head"><b>صدى الآية</b> — ${sname(s)} ${arNum(a)}</div>` +
		`<div class="rx-stat" style="font-family:var(--arabic);font-size:16px;color:var(--ink)">${ayahText(s, a)}</div>` +
		`<div class="ec-control">⚖ <b>صمّام الأمانة:</b> قِسنا هذه الروابط على نموذجٍ عشوائيّ (خلطنا جذور القرآن مع حفظ تكراراتها). النتيجة الصادقة: <b>أكثرُ الأصداء توارُدُ ألفاظٍ قريبٌ من الصدفة</b> (الوسيط الحقيقي ${arNum(c.real_median_top_echo)} مقابل ${arNum(c.null_median_top_echo)} في العشوائيّ)، ولا يتجاوز الصدفةَ بوضوحٍ إلا <b>الأقوى</b> منها. فلا تُقرأ ضعيفةُ الاشتراك «تجاوبًا»؛ الوسمُ بجانب كلٍّ يبيّن قوّته مقابل الصدفة. المعنى تتدبّره أنت.</div>` +
		`<div class="rx-list">${rows}</div>`
}

function showRootExplorer(root, wtext, el) {
	$("#explorer-verses").querySelectorAll(".rx-word.sel").forEach((e) => e.classList.remove("sel"))
	el.classList.add("sel")
	const r = EX.roots[root]
	if (!r) { return }
	const perSurah = {}
	r.ayahs.forEach(([s]) => { perSurah[s] = (perSurah[s] || 0) + 1 })
	const topS = Object.entries(perSurah).sort((a, b) => b[1] - a[1]).slice(0, 6)
		.map(([s, c]) => `${sname(s)} (${arNum(c)})`).join("، ")
	const cap = 80
	const rows = r.ayahs.slice(0, cap).map(([s, a]) =>
		`<div class="rx-occ"><span class="rx-ref">${sname(s)} ${arNum(a)}</span> ${ayahText(s, a)}</div>`).join("")
	const more = r.ayahs.length > cap
		? `<div class="rx-more">و ${arNum(r.ayahs.length - cap)} موضعًا آخر في المصحف…</div>` : ""
	$("#explorer-detail").innerHTML =
		`<div class="rx-head"><b>${wtext}</b> — الجذر <b class="root">${root}</b></div>` +
		`<div class="rx-stat">ظهر هذا الجذر في القرآن كلّه: <b>${arNum(r.count)}</b> مرة · في <b>${arNum(r.ayah_count)}</b> آية · عبر <b>${arNum(r.surah_count)}</b> سورة</div>` +
		`<div class="rx-surahs">أكثر السور حضورًا: ${topS}</div>` +
		`<h3>حيث يظهر عبر المصحف (عيّنة):</h3><div class="rx-list">${rows}${more}</div>`
}

/* ============================================================
   Layer: كشوف محسوبة (computed discoveries) — what the AI surfaces
   that a reader passes over. Pure counting facts, each with its proof.
   ============================================================ */
const DISC = window.DISCOVERIES

function stripSurah(name) {
	return (name || "").replace(/^سُ?ورَةُ\s*/, "")
}

function buildDiscoveries() {
	const g = DISC.global
	$("#disc-stats").innerHTML =
		`<span class="disc-stat"><b>${arNum(g.distinct_roots)}</b> جذرًا يُبنى منه القرآن كلّه</span>` +
		`<span class="disc-stat"><b>${arNum(g.hapax_total)}</b> جذرًا لا يردُ في المصحف إلا <b>مرّةً واحدة</b></span>` +
		`<span class="disc-stat"><b>${arNum(Object.keys(DISC.surahs).length)}</b> سورةً لها كلماتٌ تفرّدت بها</span>`
	const c = DISC.control
	$("#disc-feed").innerHTML =
		`<div class="ec-control">⚖ <b>صمّام الأمانة:</b> الكلمةُ التي ترد <b>مرّةً واحدة</b> تنحصرُ في سورةٍ بالبداهة (وفي القرآن ${arNum(c.hapax)} منها) — <b>لا لطيفةَ إحصائية في ذلك</b>، فأيُّ نصٍّ فيه مفرداتٌ نادرة. اللافتُ حقًّا: جذرٌ <b>يتكرّر</b> (مرّتين فأكثر) ومع ذلك لا يغادرُ سورةً واحدة — وهذا في القرآن <b>${arNum(c.real_confined_recurring)}</b> جذرًا مقابل <b>${arNum(c.null_confined_recurring)}</b> فقط في نموذجٍ عشوائيّ، أي <b>أعلى من الصدفة بنحو ${arNum(Math.round(c.lift))}×</b>. وهذه التغذيةُ تعرضُ هذه المتكرّرةَ المنحصرة وحدها:</div>` +
		g.feed.map((f, i) =>
		`<div class="disc-item" data-s="${f.surah}" data-a="${f.ayah}">` +
		`<div class="disc-line"><span class="disc-word">${f.form}</span>` +
		`<span class="disc-say">لا يردُ جذرُها <b class="root">${f.root}</b> في القرآن كلّه إلا في ` +
		`<b>${stripSurah(f.name)}</b> — ${arNum(f.count)} مرّات.</span></div>` +
		`<div class="disc-proof" id="disc-proof-${i}"><span class="disc-open">تحقّق: أظهِر الموضع الأول ↓</span></div></div>`).join("")
	$("#disc-feed").querySelectorAll(".disc-item").forEach((el, i) => {
		el.addEventListener("click", () => {
			const proof = $("#disc-proof-" + i)
			const s = +el.dataset.s, a = +el.dataset.a
			if (proof.dataset.open) {
				proof.dataset.open = ""; proof.innerHTML = `<span class="disc-open">تحقّق: أظهِر الموضع الأول ↓</span>`
			} else {
				proof.dataset.open = "1"
				proof.innerHTML = `<div class="disc-ayah"><span class="rx-ref">${stripSurah(DISC.surahs[s] ? DISC.surahs[s].name : sname(s))} ${arNum(a)}</span> ${ayahText(s, a)}</div>`
			}
		})
	})
}

/* ============================================================
   Layer: تدبّر السور القصار (contemplation of the short surahs) —
   sourced, graded reflection per verse. NOT محاورة: no manufactured
   divine response; that belongs to al-Fatiha alone (Muslim 395).
   ============================================================ */
const TS = window.TADABBUR_SHORT
let tsAudio = null
let tsSeq = null

// Reciters — all vendored locally (work offline), each recitation verified
// (loads & plays in the browser). الحصري lives at the audio root (shared with
// the Fatiha محاورة); per-ayah reciters under audio/<id>/SSSAAA.mp3, verified
// against everyayah's official list. محمد اللحيدان is not carried per-ayah on
// any per-ayah source (verified against everyayah AND quran.com), so his
// recitation is the WHOLE surah (audio/lhdan/SSS.mp3, from mp3quran) — honest,
// with the per-ayah step disabled and labelled for him.
const RECITERS = [
	{ id: "husary", name: "محمود خليل الحصري (مرتّل)", dir: "" },
	{ id: "ayyoub", name: "محمد أيوب", dir: "ayyoub/" },
	{ id: "minshawy", name: "محمد صديق المنشاوي (مرتّل)", dir: "minshawy/" },
	{ id: "abdulbasit", name: "عبد الباسط عبد الصمد (مرتّل)", dir: "abdulbasit/" },
	{ id: "alafasy", name: "مشاري العفاسي", dir: "alafasy/" },
	{ id: "sudais", name: "عبد الرحمن السديس", dir: "sudais/" },
	{ id: "lhdan", name: "محمد اللحيدان (السورة كاملةً)", dir: "lhdan/", whole: true },
]
let tsReciter = "husary"
let tsCurIdx = 0

// The tadabbur tab shows the short surahs (full coverage, verses[]) AND
// al-Baqara (progressive, passages[]). A unified entry list drives the picker.
const TB = window.TADABBUR_BAQARA
const LONG_SURAHS = [TB, window.TADABBUR_ALIMRAN, window.TADABBUR_NISA, window.TADABBUR_MAIDA, window.TADABBUR_ANAM, window.TADABBUR_ARAF, window.TADABBUR_ANFAL, window.TADABBUR_TAWBA, window.TADABBUR_YUNUS, window.TADABBUR_HUD, window.TADABBUR_YUSUF, window.TADABBUR_RAD, window.TADABBUR_IBRAHIM, window.TADABBUR_HIJR, window.TADABBUR_NAHL, window.TADABBUR_ISRA, window.TADABBUR_KAHF, window.TADABBUR_MARYAM, window.TADABBUR_TAHA, window.TADABBUR_ANBIYA, window.TADABBUR_HAJJ, window.TADABBUR_MUMINUN, window.TADABBUR_NUR, window.TADABBUR_FURQAN, window.TADABBUR_SHUARA, window.TADABBUR_NAML, window.TADABBUR_QASAS, window.TADABBUR_ANKABUT, window.TADABBUR_RUM, window.TADABBUR_LUQMAN, window.TADABBUR_SAJDA, window.TADABBUR_AHZAB, window.TADABBUR_SABA, window.TADABBUR_FATIR, window.TADABBUR_YASIN, window.TADABBUR_SAFFAT, window.TADABBUR_SAD, window.TADABBUR_ZUMAR, window.TADABBUR_GHAFIR, window.TADABBUR_FUSSILAT, window.TADABBUR_SHURA, window.TADABBUR_ZUKHRUF, window.TADABBUR_DUKHAN, window.TADABBUR_JATHIYA, window.TADABBUR_AHQAF, window.TADABBUR_MUHAMMAD, window.TADABBUR_FATH, window.TADABBUR_HUJURAT, window.TADABBUR_QAF, window.TADABBUR_DHARIYAT, window.TADABBUR_TUR, window.TADABBUR_NAJM, window.TADABBUR_QAMAR].filter(Boolean)
const TS_ENTRIES = TS.surahs.map((su) => ({
	kind: "short", n: su.n, name: stripSurah(EX.surah_names[su.n] || ("سورة " + su.n)),
	type: EX.surah_type[su.n], theme: su.theme, fadl: su.fadl, sabab: su.sabab, verses: su.verses,
})).concat(LONG_SURAHS.map((L) => ({
	kind: "long", n: L.n, name: L.name + (L.coverage && L.coverage.covered >= L.coverage.total ? "" : " (مختارات)"),
	type: EX.surah_type[L.n], passages: L.passages, coverage: L.coverage, audio: L.audio,
})))
let tsCurEntry = TS_ENTRIES[0]

function pad3(n) { return String(n).padStart(3, "0") }
function curReciter() { return RECITERS.find((x) => x.id === tsReciter) || RECITERS[0] }
// audio folder follows the reciter (al-Husary lives at the root). al-Baqara's
// great passages are vendored for the per-ayah reciters (not al-Luhaidan).
function audioDir() { return curReciter().dir }
function entryVerses(e) { return e.kind === "long" ? e.passages.flatMap((p) => p.verses) : e.verses }

function tsWholeMode() { return curReciter().whole && tsCurEntry && tsCurEntry.kind === "short" }

function tsStop() {
	if (tsAudio) { tsAudio.pause(); tsAudio = null }
	tsSeq = null
	document.querySelectorAll("#ts-body .ts-verse.playing").forEach((e) => e.classList.remove("playing"))
	const sb = $("#ts-listen")
	if (sb) { sb.textContent = tsWholeMode() ? "▶ استمع للسورة" : "▶ استمع للسورة متتابعةً" }
}

function tsPlayVerse(s, a, onEnd) {
	if (tsAudio) { tsAudio.pause() }
	document.querySelectorAll("#ts-body .ts-verse.playing").forEach((e) => e.classList.remove("playing"))
	const row = document.querySelector(`#ts-body .ts-verse[data-a="${a}"]`)
	if (row) { row.classList.add("playing"); row.scrollIntoView({ block: "nearest" }) }
	tsAudio = new Audio(`../audio/${audioDir()}${pad3(s)}${pad3(a)}.mp3`)
	tsAudio.onended = () => {
		if (row) { row.classList.remove("playing") }
		if (onEnd) { onEnd() }
	}
	tsAudio.play().catch(() => {})
}

// whole-surah playback (al-Luhaidan): one file per surah, no per-ayah step
function tsPlayWhole(e) {
	tsStop()
	const btn = $("#ts-listen")
	if (btn) { btn.textContent = "■ إيقاف" }
	tsSeq = { whole: true }
	tsAudio = new Audio(`../audio/${audioDir()}${pad3(e.n)}.mp3`)
	tsAudio.onended = () => tsStop()
	tsAudio.play().catch(() => {})
}

function tsPlaySurah(e) {
	if (tsWholeMode()) { tsPlayWhole(e); return }
	tsStop()
	const btn = $("#ts-listen")
	if (btn) { btn.textContent = "■ إيقاف" }
	const verses = entryVerses(e)
	tsSeq = { k: 0 }
	const step = () => {
		if (!tsSeq || tsSeq.k >= verses.length) { tsStop(); return }
		const v = verses[tsSeq.k]
		tsSeq.k += 1
		tsPlayVerse(e.n, v.n, step)
	}
	step()
}

function buildTadabburShort() {
	$("#ts-picker").innerHTML = TS_ENTRIES.map((e, i) =>
		`<button class="ts-tab${i === 0 ? " sel" : ""}" data-i="${i}">${e.name}</button>`).join("")
	$("#ts-picker").querySelectorAll(".ts-tab").forEach((b) =>
		b.addEventListener("click", () => renderTadabburShort(+b.dataset.i)))
	renderTadabburShort(0)
}

// the ayah's echoes across the whole Qur'an, brought into the worship view but
// graded against the chance baseline (رقم القاعدة ١٦): each link labelled by its
// computed lift, so a near-chance coincidence can't pose as «تجاوب». On demand.
function tsEchoHtml(ref) {
	const nbrs = (AL.links[ref] || []).slice(0, 4)
	if (!nbrs.length) { return "" }
	const rows = nbrs.map(([o, sc, rs]) => {
		const [os, oa] = o.split(":")
		const lf = echoLift(sc)
		const chips = rs.map((r) => `<span class="ec-root">${r}</span>`).join("")
		return `<div class="ts-echo-row"><span class="rx-ref">${sname(os)} ${arNum(oa)}</span> ${chips}` +
			`<span class="ec-band ${lf.cls}">${lf.label}</span><div class="ec-txt">${ayahText(os, oa)}</div></div>`
	}).join("")
	return `<div class="ts-echo-note">مواضعُ تشترك معها في لفظٍ مميّز — موزونةٌ على الصدفة، للتدبّر لا للاستدلال:</div>${rows}`
}

// one verse card, shared by short surahs and al-Baqara passages
function tsVerseCard(s, v, showPlay) {
	const names = (v.names && v.names.length) ? `<span class="ts-names">الأسماء الفاعلة: ${v.names.join(" · ")}</span>` : ""
	const playBtn = showPlay ? `<button class="ts-play" data-a="${v.n}" title="استمع لهذه الآية">▶</button> ` : ""
	const ref = s + ":" + v.n
	const echoBtn = (AL.links[ref] && AL.links[ref].length)
		? `<button class="ts-echo-btn" data-ref="${ref}">⇄ صداها في القرآن (${arNum(AL.links[ref].length)})</button>` : ""
	const sabab = v.sabab
		? `<div class="ts-vsabab">◆ <b>سببُ نزولها:</b> ${v.sabab.text} <span class="src">${v.sabab.source} ${gradeBadge(v.sabab.grade)}</span></div>` : ""
	return `<div class="ts-verse" data-a="${v.n}">` +
		`<div class="ts-ayah">${playBtn}﴿ ${ayahText(s, v.n)} <span class="vmark">${arNum(v.n)}</span> ﴾</div>` +
		sabab +
		`<div class="ts-reflect">${v.reflection.text}` +
		`<span class="src">${v.reflection.source} ${gradeBadge(v.reflection.grade)}</span></div>` +
		`<div class="ts-meta">${names}` +
		`<span class="ts-heart">القلب: ${v.heart_state.text} ${gradeBadge("ijtihadi")}</span></div>` +
		`<div class="ts-action">↦ ${v.action.text} ${gradeBadge("ijtihadi")}</div>` +
		(echoBtn ? `<div class="ts-echo-wrap">${echoBtn}<div class="ts-echo-body" hidden></div></div>` : "") +
		`</div>`
}

function renderTadabburShort(i) {
	tsCurIdx = i
	tsCurEntry = TS_ENTRIES[i]
	const e = tsCurEntry
	const long = e.kind === "long"
	tsStop()
	// reciter controls. al-Baqara's audio covers its great passages in the
	// per-ayah reciters (not al-Luhaidan, whose recitation is whole-surah).
	if (long) {
		const baqReciters = RECITERS.filter((r) => !r.whole)
		if (!baqReciters.some((r) => r.id === tsReciter)) { tsReciter = "husary" }
		$("#ts-reciter").innerHTML = `<label class="ts-rec-lbl">القارئ: <select id="ts-rec-sel">` +
			baqReciters.map((r) => `<option value="${r.id}"${r.id === tsReciter ? " selected" : ""}>${r.name}</option>`).join("") +
			`</select></label> <span class="ts-rec-note">الصوتُ للمقاطع الكبرى من البقرة (بصوت القارئ المختار)؛ والتدبّرُ لكلّ آية.</span>`
		$("#ts-rec-sel").addEventListener("change", (ev) => { tsReciter = ev.target.value; renderTadabburShort(tsCurIdx) })
	} else {
		$("#ts-reciter").innerHTML = `<label class="ts-rec-lbl">القارئ: <select id="ts-rec-sel">` +
			RECITERS.map((r) => `<option value="${r.id}"${r.id === tsReciter ? " selected" : ""}>${r.name}</option>`).join("") +
			`</select></label> <span class="ts-rec-note">${curReciter().whole
				? "اللحيدان: تلاوةُ السورةِ كاملةً (غير مقطّعةٍ آيةً-آية لديه)."
				: "تلاواتٌ محفوظةٌ تعمل بلا إنترنت."}</span>`
		$("#ts-rec-sel").addEventListener("change", (ev) => { tsReciter = ev.target.value; renderTadabburShort(tsCurIdx) })
	}
	$("#ts-picker").querySelectorAll(".ts-tab").forEach((b, k) => b.classList.toggle("sel", k === i))
	const whole = tsWholeMode()

	// for al-Baqara audio is vendored only for the great passages; show ▶ there
	const audioSet = long ? new Set(e.audio || []) : null
	const listenBtn = long ? "" : ` <button class="ts-listen" id="ts-listen">${whole ? "▶ استمع للسورة" : "▶ استمع للسورة متتابعةً"}</button>`
	let html = `<div class="ts-head"><b>${e.name}</b> <span class="mut">· ${e.type}${long ? "" : " · " + arNum(e.verses.length) + " آية"}${e.theme ? " · " + e.theme : ""}</span>${listenBtn}</div>`

	if (long) {
		const done = e.coverage.covered >= e.coverage.total
		html += done
			? `<div class="ts-coverage ts-done">اكتملت بحمد الله — <b>${arNum(e.coverage.total)}</b> آية كاملةً، كلُّها مُسنَدةٌ وموسومة (ابن كثير/السعدي). <span class="mut">(الصوتُ بصوت الحصري للمقاطع الكبرى؛ والتدبّرُ لكلّ آية.)</span></div>`
			: `<div class="ts-coverage">تُبنى هذه السورة تدرّجًا بإذن الله — <b>${arNum(e.coverage.covered)}</b> من <b>${arNum(e.coverage.total)}</b> آية، بادئين بأعظم مقاطعها وأكثرها تلاوةً. كلُّ ما هنا مُسنَدٌ وموسوم؛ ولا نُوهم أنّ التغطية كاملة. <span class="mut">(الصوتُ بصوت الحصري للمقاطع الكبرى؛ والتدبّرُ لكلِّ ما نُغطّيه.)</span></div>`
		html += e.passages.map((p) => {
			let ph = `<div class="ts-passage"><div class="ts-passage-head">${p.title} <span class="mut">(${arNum(p.range[0])}${p.range[1] !== p.range[0] ? "–" + arNum(p.range[1]) : ""})</span></div>`
			if (p.fadl) { ph += `<div class="ts-note ts-fadl">✦ <b>فضلها:</b> ${p.fadl.text} <span class="src">${p.fadl.source} ${gradeBadge(p.fadl.grade)}</span></div>` }
			ph += p.verses.map((v) => tsVerseCard(e.n, v, audioSet.has(v.n))).join("")
			return ph + `</div>`
		}).join("")
	} else {
		if (e.fadl) { html += `<div class="ts-note ts-fadl">✦ <b>فضلها:</b> ${e.fadl.text} <span class="src">${e.fadl.source} ${gradeBadge(e.fadl.grade)}</span></div>` }
		if (e.sabab) { html += `<div class="ts-note ts-sabab">◆ <b>سببُ نزولها:</b> ${e.sabab.text} <span class="src">${e.sabab.source} ${gradeBadge(e.sabab.grade)}</span></div>` }
		html += e.verses.map((v) => tsVerseCard(e.n, v, !whole)).join("")
	}

	// bridge to the sourced library — we point, we don't summarise
	const catLabel = (k) => ((window.QURAN_CONTEXT.categories.find((c) => c[0] === k) || [])[1] || k)
	const hasSabab = long ? e.passages.some((p) => p.sabab) : !!e.sabab
	const cats = ["tafsir_mathur"].concat(hasSabab ? ["asbab"] : [])
	const chips = cats.map((k) => `<span class="ts-src-chip">${catLabel(k)}</span>`).join(" ")
	html += `<div class="ts-srclink">للاستزادة المُسنَدة في ${e.name} — ارجع إلى ${chips} ` +
		`في <button class="ts-src-btn" type="button">المصادر المُسنَدة</button>. (نَدُلّ ولا نُلخّص؛ المعنى الكامل عند أهله.)</div>`

	$("#ts-body").innerHTML = html
	const listenEl = $("#ts-listen")
	if (listenEl) { listenEl.addEventListener("click", () => { if (tsSeq) { tsStop() } else { tsPlaySurah(e) } }) }
	const srcBtn = $("#ts-body").querySelector(".ts-src-btn")
	if (srcBtn) { srcBtn.addEventListener("click", () => { const t = document.querySelector('#tabs button[data-layer="sources"]'); if (t) { t.click() } }) }
	$("#ts-body").querySelectorAll(".ts-echo-btn").forEach((b) =>
		b.addEventListener("click", () => {
			const body = b.nextElementSibling
			if (body.hidden) {
				if (!body.dataset.filled) { body.innerHTML = tsEchoHtml(b.dataset.ref); body.dataset.filled = "1" }
				body.hidden = false; b.classList.add("open")
			} else { body.hidden = true; b.classList.remove("open") }
		}))
	$("#ts-body").querySelectorAll(".ts-play").forEach((b) =>
		b.addEventListener("click", () => {
			const a = +b.dataset.a
			const row = document.querySelector(`#ts-body .ts-verse[data-a="${a}"]`)
			if (row && row.classList.contains("playing")) { tsStop() } else { tsStop(); tsPlayVerse(e.n, a) }
		}))
}

/* ============================================================
   Layer: المصادر المُسنَدة (sourced context library) — the trusted
   classical references for stories, occasions of revelation, history,
   tafsir-by-narration. We catalogue and point; we do not summarise.
   ============================================================ */
const QC = window.QURAN_CONTEXT

function buildSources() {
	const byCat = {}
	QC.books.forEach((b) => { (byCat[b.category] = byCat[b.category] || []).push(b) })
	let html = ""
	for (const [key, label, blurb] of QC.categories) {
		const books = byCat[key] || []
		if (!books.length) { continue }
		html += `<div class="src-cat"><div class="src-cat-head"><h3>${label}</h3><span class="src-cat-blurb">${blurb}</span></div>`
		html += books.map((b) => {
			const where = b.link
				? `<a class="src-link" href="${b.link}" target="_blank" rel="noopener">اقرأ في ${b.read_at[0]} ↗</a>`
				: `<span class="src-where">متوفّر مجانًا في: ${b.read_at.join(" · ")}</span>`
			const caution = b.caution ? `<div class="src-caution">⚠ ${b.caution}</div>` : ""
			return `<div class="src-book">` +
				`<div class="src-title">${b.title}</div>` +
				`<div class="src-author">${b.author} <span class="src-death">(ت ${b.death_h} / ${b.death_g})</span></div>` +
				`<div class="src-cov">${b.coverage}</div>` +
				caution +
				`<div class="src-foot">${where} <span class="src-tier">تراثٌ في الملك العام</span></div>` +
				`</div>`
		}).join("")
		html += `</div>`
	}
	$("#sources-lib").innerHTML = html
}

/* ============================================================
   Layer: الآية تُضيء (verse scenes) — bespoke design that lights up
   each verse's meaning. The verse text stays fixed & respected;
   the canvas behind it is the aid.
   ============================================================ */
let sceneIdx = 0
let sceneSel = null
let sceneT = 0
let scenesRaf = null
let sceneDims = { w: 0, h: 0, dpr: 1 }
let sceneSetIdx = 0

// scene sets: al-Fatiha (words from D.surah) and al-Baqara greats (words from
// the whole-Quran morphology). Each set knows how to fetch a verse's words.
const SCENE_SETS = [
	{ name: "الفاتحة", verses: D.scenes.verses,
		wordsFor: (n) => D.surah.verses[n - 1].words },
	{ name: "البقرة (مختارات)", verses: (window.SCENES_BAQARA || { verses: [] }).verses,
		wordsFor: (n) => (EX.verse_words["2:" + n] || []).map(([text, root], i) => ({ i: i + 1, text, root })) },
	{ name: "آل عمران (مختارات)", verses: (window.SCENES_ALIMRAN || { verses: [] }).verses,
		wordsFor: (n) => (EX.verse_words["3:" + n] || []).map(([text, root], i) => ({ i: i + 1, text, root })) },
	{ name: "النساء (مختارات)", verses: (window.SCENES_NISA || { verses: [] }).verses,
		wordsFor: (n) => (EX.verse_words["4:" + n] || []).map(([text, root], i) => ({ i: i + 1, text, root })) },
].filter((st) => st.verses.length)
function sceneVerses() { return SCENE_SETS[sceneSetIdx].verses }
function sceneWords(n) { return SCENE_SETS[sceneSetIdx].wordsFor(n) }

function hexA(hex, a) {
	const n = parseInt(hex.slice(1), 16)
	return `rgba(${(n >> 16) & 255},${(n >> 8) & 255},${n & 255},${a})`
}
function glow(ctx, x, y, r, color, a) {
	const g = ctx.createRadialGradient(x, y, 0, x, y, r)
	g.addColorStop(0, hexA(color, a))
	g.addColorStop(1, hexA(color, 0))
	ctx.fillStyle = g
	ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.fill()
}

function buildScenes() {
	$("#scene-set").innerHTML = SCENE_SETS.map((st, i) =>
		`<button class="scene-set-btn${i === 0 ? " sel" : ""}" data-s="${i}">${st.name}</button>`).join("")
	$("#scene-set").querySelectorAll(".scene-set-btn").forEach((b) =>
		{ b.onclick = () => { sceneSetIdx = +b.dataset.s; buildSceneNav(); renderScene(0) } })
	buildSceneNav()
	renderScene(0)
}

function buildSceneNav() {
	$("#scene-set").querySelectorAll(".scene-set-btn").forEach((b, i) => b.classList.toggle("sel", i === sceneSetIdx))
	$("#scene-nav").innerHTML = sceneVerses().map((s, k) => `<button data-k="${k}">${arNum(s.n)}</button>`).join("")
	$("#scene-nav").querySelectorAll("button").forEach((b) =>
		{ b.onclick = () => renderScene(Number(b.dataset.k)) })
}

function renderScene(k) {
	sceneIdx = k
	sceneSel = null
	sceneT = 0
	const s = sceneVerses()[k]
	const vwords = sceneWords(s.n)
	const hot = {}
	s.hotspots.forEach((h) => { hot[h.word] = h })
	const words = vwords.map((w) =>
		`<span class="scene-word${hot[w.i] ? " hot" : ""}" data-wi="${w.i}">${w.text}</span>`).join(" ")
	$("#scene-stage").innerHTML =
		`<canvas class="scene-canvas" id="scene-canvas"></canvas>` +
		`<div class="scene-overlay">` +
		`<div class="scene-title">${s.title}</div>` +
		`<div class="scene-verse">﴿ ${words} <span class="vmark">${arNum(s.n)}</span> ﴾</div>` +
		`<div class="scene-hotnote" id="scene-hotnote">اضغط الكلمات المُضيئة لتتدبّرها</div>` +
		`</div>`
	$("#scene-stage").querySelectorAll(".scene-word.hot").forEach((el) =>
		{ el.onclick = () => selectSceneWord(s, Number(el.dataset.wi), el) })
	$("#scene-nav").querySelectorAll("button").forEach((b, i) => b.classList.toggle("active", i === k))
	$("#scene-rationale").innerHTML =
		`<b>${s.title}</b> ${gradeBadge(s.grade)}` +
		`<div style="margin-top:6px">${s.design_rationale}</div>` +
		`<div class="src">${s.sources}</div>`
	sizeSceneCanvas()
	if (!scenesRaf) { scenesLoop() }
}

function selectSceneWord(s, wi, el) {
	sceneSel = wi
	$("#scene-stage").querySelectorAll(".scene-word").forEach((e) => e.classList.remove("sel"))
	el.classList.add("sel")
	const h = s.hotspots.find((x) => x.word === wi)
	const w = sceneWords(s.n).find((x) => x.i === wi)
	$("#scene-hotnote").innerHTML =
		`<b>${h.label}</b>${w && w.root ? ` <span class="r">جذر: ${w.root}</span>` : ""} — ${h.note}`
}

function sizeSceneCanvas() {
	const c = $("#scene-canvas")
	if (!c) { return }
	const st = $("#scene-stage")
	const w = st.clientWidth, h = st.clientHeight
	const dpr = window.devicePixelRatio || 1
	c.width = w * dpr; c.height = h * dpr
	sceneDims = { w, h, dpr }
}

function scenesLoop() {
	const c = $("#scene-canvas")
	if (!c || !$("#layer-scenes").classList.contains("visible")) { scenesRaf = null; return }
	const { w, h, dpr } = sceneDims
	const ctx = c.getContext("2d")
	ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
	ctx.clearRect(0, 0, w, h)
	sceneT += 0.016
	const s = sceneVerses()[sceneIdx]
	;(SCENE_DRAW[s.scene_key] || (() => {}))(ctx, w, h, sceneT)
	scenesRaf = requestAnimationFrame(scenesLoop)
}

// deterministic pseudo-random points for a scene (index-seeded, no Math.random at draw)
const SCENE_DOTS = Array.from({ length: 40 }, (_, i) => {
	const a = i * 2.399963
	return { a, r: 0.35 + ((i * 97) % 100) / 100 * 0.6, ph: (i % 10) / 10 }
})

const SCENE_DRAW = {
	two_mercies(ctx, w, h) {
		const cx = w / 2, cy = h / 2, m = Math.min(w, h)
		const p = 0.5 + 0.5 * Math.sin(sceneT * 0.7)
		const wide = sceneSel === 4 ? 0.10 : 0.14 + 0.05 * p
		const core = sceneSel === 3 ? 0.10 : 0.16 + 0.08 * (1 - p)
		glow(ctx, cx, cy, m * 0.85, COLORS.aqua, wide)          // الرحمن: وسعت كل شيء
		glow(ctx, cx, cy, m * 0.32, "#e0a02a", core)            // الرحيم: قلبٌ دافئ
	},
	all_praise(ctx, w, h) {
		const cx = w / 2, cy = h / 2, R = Math.min(w, h) * 0.52
		SCENE_DOTS.forEach((d, i) => {
			const pulse = 0.85 + 0.15 * Math.sin(sceneT * 0.8 + i)
			const r = R * d.r * pulse
			const x = cx + Math.cos(d.a + sceneT * 0.04) * r
			const y = cy + Math.sin(d.a + sceneT * 0.04) * r * 0.7
			ctx.strokeStyle = hexA(COLORS.blue, 0.10)
			ctx.lineWidth = 1
			ctx.beginPath(); ctx.moveTo(cx, cy)
			ctx.lineTo(cx + (x - cx) * 0.62, cy + (y - cy) * 0.62)  // thread fades before the text
			ctx.stroke()
			glow(ctx, x, y, 10, COLORS.aqua, 0.5)
		})
		glow(ctx, cx, cy, 60, "#e0a02a", 0.18)
	},
	mercy_bridge(ctx, w, h) {
		const cy = h / 2, lx = w * 0.13, rx = w * 0.87
		const grad = ctx.createLinearGradient(lx, cy, rx, cy)
		grad.addColorStop(0, hexA(COLORS.blue, 0.0))
		grad.addColorStop(0.5, hexA("#e0a02a", 0.5))
		grad.addColorStop(1, hexA(COLORS.blue, 0.0))
		ctx.strokeStyle = grad; ctx.lineWidth = 4
		ctx.beginPath(); ctx.moveTo(lx, cy); ctx.lineTo(rx, cy); ctx.stroke()
		const px = lx + (rx - lx) * (0.5 + 0.5 * Math.sin(sceneT * 0.9))
		glow(ctx, px, cy, 40, "#e0a02a", 0.4)
		glow(ctx, lx, cy, 46, COLORS.blue, 0.4)
		glow(ctx, rx, cy, 46, COLORS.violet, 0.4)
		sceneLabel(ctx, "الربوبية (٢)", rx, cy + 62)
		sceneLabel(ctx, "الجزاء (٤)", lx, cy + 62)
	},
	sole_king(ctx, w, h) {
		const cx = w / 2
		ctx.fillStyle = "rgba(6,6,6,0.55)"; ctx.fillRect(0, 0, w, h)  // everything dims
		SCENE_DOTS.slice(0, 16).forEach((d) => {
			const fade = Math.max(0, 0.5 - (sceneT * 0.08 + d.ph) % 1.2)  // lesser lights die out
			const x = cx + Math.cos(d.a) * w * 0.4 * d.r
			const y = h * 0.5 + Math.sin(d.a) * h * 0.36 * d.r
			glow(ctx, x, y, 8, "#9a9a90", fade)
		})
		const p = 0.7 + 0.3 * Math.sin(sceneT * 1.1)
		glow(ctx, cx, h * 0.2, 70, "#e7c66a", 0.32 * p)             // only the Sovereign remains
		glow(ctx, cx, h * 0.2, 24, "#fff2cc", 0.5 * p)
	},
	exclusivity_turn(ctx, w, h) {
		const tx = w * 0.5, ty = h * 0.34  // converge onto «إياك» (upper-centre of the text)
		for (let i = 0; i < 10; i++) {
			const a = (i / 10) * Math.PI * 2
			const prog = (sceneT * 0.5 + i / 10) % 1
			const d0 = Math.min(w, h) * 0.5
			const sx = tx + Math.cos(a) * d0 * (1 - prog)
			const sy = ty + Math.sin(a) * d0 * 0.7 * (1 - prog)
			ctx.strokeStyle = hexA(COLORS.magenta, 0.5 * (1 - prog))
			ctx.lineWidth = 2
			ctx.beginPath(); ctx.moveTo(sx, sy)
			ctx.lineTo(tx + Math.cos(a) * 26, ty + Math.sin(a) * 18); ctx.stroke()
		}
		glow(ctx, tx, ty, 44, COLORS.magenta, 0.4)
		sceneLabel(ctx, "↯ الالتفات: من الغيبة إلى الخطاب", w / 2, h - 26, COLORS.magenta)
	},
	straight_path(ctx, w, h) {
		const cx = w / 2
		// crooked, fading side-paths
		ctx.strokeStyle = hexA("#6b6a64", 0.25); ctx.lineWidth = 2
		for (const s of [-1, 1]) {
			ctx.beginPath(); ctx.moveTo(cx + s * 40, h)
			ctx.bezierCurveTo(cx + s * 160, h * 0.7, cx - s * 120, h * 0.4, cx + s * 80, h * 0.12)
			ctx.stroke()
		}
		// the one straight, luminous path
		const grad = ctx.createLinearGradient(cx, h, cx, h * 0.1)
		grad.addColorStop(0, hexA(COLORS.blue, 0.0))
		grad.addColorStop(1, hexA("#cfe6ff", 0.8))
		ctx.strokeStyle = grad; ctx.lineWidth = 4
		ctx.beginPath(); ctx.moveTo(cx, h - 6); ctx.lineTo(cx, h * 0.1); ctx.stroke()
		const p = 0.7 + 0.3 * Math.sin(sceneT * 1.2)
		glow(ctx, cx, h * 0.12, 55, "#cfe6ff", 0.4 * p)            // the light at the end
	},
	role_and_bounds(ctx, w, h) {
		const cx = w / 2
		// two branches veering off into darkness
		const branch = (dir, color) => {
			ctx.strokeStyle = hexA(color, 0.35); ctx.lineWidth = 2
			ctx.beginPath(); ctx.moveTo(cx, h * 0.5)
			ctx.quadraticCurveTo(cx + dir * w * 0.2, h * 0.62, cx + dir * w * 0.42, h * 0.92)
			ctx.stroke()
		}
		branch(1, COLORS.red)      // المغضوب عليهم
		branch(-1, COLORS.orange)  // الضالّون
		sceneLabel(ctx, "المغضوب عليهم", cx + w * 0.30, h * 0.95, COLORS.red)
		sceneLabel(ctx, "الضالّون", cx - w * 0.30, h * 0.95, COLORS.orange)
		// the straight, lit path of the guided
		const grad = ctx.createLinearGradient(cx, h * 0.5, cx, h * 0.08)
		grad.addColorStop(0, hexA("#cfe6ff", 0.1))
		grad.addColorStop(1, hexA("#cfe6ff", 0.85))
		ctx.strokeStyle = grad; ctx.lineWidth = 4
		ctx.beginPath(); ctx.moveTo(cx, h * 0.5); ctx.lineTo(cx, h * 0.08); ctx.stroke()
		const p = 0.7 + 0.3 * Math.sin(sceneT * 1.1)
		glow(ctx, cx, h * 0.1, 50, "#cfe6ff", 0.4 * p)
	},
	// آية الكرسي: everything held & encompassed; a centre that never dims
	kursi(ctx, w, h) {
		const cx = w / 2, cy = h / 2, m = Math.min(w, h)
		const big = sceneSel === 42 ? 0.98 : 0.82                 // وسع كرسيّه
		glow(ctx, cx, cy, m * big, COLORS.blue, 0.10)            // the vast kursi
		ctx.strokeStyle = hexA(COLORS.aqua, 0.22); ctx.lineWidth = 1.5
		ctx.beginPath(); ctx.arc(cx, cy, m * big * 0.5, 0, Math.PI * 2); ctx.stroke()
		const orbR = m * 0.27                                     // heavens & earth held within
		;[0, Math.PI].forEach((base, idx) => {
			const a = base + sceneT * 0.11
			const x = cx + Math.cos(a) * orbR, y = cy + Math.sin(a) * orbR * 0.78
			glow(ctx, x, y, 15, idx ? COLORS.aqua : COLORS.violet, 0.45)
		})
		SCENE_DOTS.slice(0, 10).forEach((d) => {                 // intercessors kindle only by leave
			const rr = m * 0.37 * d.r
			const x = cx + Math.cos(d.a) * rr, y = cy + Math.sin(d.a) * rr * 0.78
			const dist = Math.hypot(x - cx, y - cy) / (m * 0.42)
			const permit = (sceneSel === 23 ? 0.6 : 0.22) - dist * (sceneSel === 23 ? 0.45 : 0.18)
			glow(ctx, x, y, 8, "#e0a02a", Math.max(0, permit))
		})
		const alive = sceneSel === 7 ? 1 : 0.82 + 0.05 * Math.sin(sceneT * 0.8)  // الحيّ القيّوم — never off
		glow(ctx, cx, cy, 74, "#f0c85a", 0.5 * alive)
		glow(ctx, cx, cy, 30, "#fff2cc", 0.6 * alive)
	},
	// خواتيم البقرة: burdens lifted, pleas rising and answered («قد فعلت»)
	// آل عمران ١٨: three witnesses converge on one truth, girt by tawhid twice,
	// held level by justice. Selecting a hotspot brightens its witness/beam.
	shahida(ctx, w, h) {
		const cx = w / 2, cy = h / 2, m = Math.min(w, h)
		const p = 0.5 + 0.5 * Math.sin(sceneT * 0.6)
		// the witnessed truth: a still central light — "لا إله إلا هو"
		glow(ctx, cx, cy, m * 0.30, "#e0a02a", 0.16 + 0.05 * p)
		// three witnesses, each a beam converging on the centre
		const wit = [
			{ a: -Math.PI / 2, sel: 1, c: "#e0a02a" },   // شهد الله — from above (highest)
			{ a: Math.PI * 0.75, sel: 8, c: COLORS.aqua }, // الملائكة
			{ a: Math.PI * 0.25, sel: 10, c: COLORS.blue }, // أولو العلم
		]
		wit.forEach((wt, i) => {
			const on = sceneSel === wt.sel
			const rr = m * 0.42
			const x = cx + Math.cos(wt.a) * rr, y = cy + Math.sin(wt.a) * rr
			const ph = 0.5 + 0.5 * Math.sin(sceneT * 0.9 + i * 2.1)
			ctx.strokeStyle = hexA(wt.c, (on ? 0.5 : 0.18) + 0.12 * ph)
			ctx.lineWidth = on ? 2.4 : 1.3
			ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(cx, cy); ctx.stroke()
			glow(ctx, x, y, m * (on ? 0.14 : 0.09), wt.c, on ? 0.4 : 0.22)
		})
		// tawhid girding the truth from both ends (لا إله إلا هو, twice)
		ctx.strokeStyle = hexA("#e0a02a", 0.22 + 0.08 * p)
		ctx.lineWidth = 1
		ctx.beginPath(); ctx.arc(cx, cy, m * 0.34, 0, Math.PI * 2); ctx.stroke()
		// قائمًا بالقسط: a perfectly level beam through the centre
		const lvl = sceneSel === 12
		ctx.strokeStyle = hexA("#cfe6ff", lvl ? 0.5 : 0.26)
		ctx.lineWidth = lvl ? 2.4 : 1.4
		ctx.beginPath(); ctx.moveTo(cx - m * 0.4, cy); ctx.lineTo(cx + m * 0.4, cy); ctx.stroke()
		if (lvl) { glow(ctx, cx, cy, m * 0.42, "#cfe6ff", 0.08) }
	},
	// آل عمران ٢٦: dominion given and stripped around one still owner; honour and
	// abasement alternate; a warm glow never leaves — all good is in His hand.
	malik_mulk(ctx, w, h) {
		const cx = w / 2, cy = h / 2, m = Math.min(w, h)
		// the still owner at the centre — "مالك الملك"
		glow(ctx, cx, cy, m * 0.16, "#e0a02a", 0.22)
		const R = m * 0.34
		const give = sceneSel === 5, take = sceneSel === 9
		// bestowing arc — sweeps inward (تؤتي الملك)
		const ga = sceneT * 0.5
		ctx.strokeStyle = hexA(COLORS.aqua, give ? 0.6 : 0.3)
		ctx.lineWidth = give ? 3 : 1.8
		ctx.beginPath(); ctx.arc(cx, cy, R, ga, ga + Math.PI * 0.7); ctx.stroke()
		// stripping arc — sweeps the other way (تنزع الملك)
		const ta = -sceneT * 0.5 + Math.PI
		ctx.strokeStyle = hexA(COLORS.muted, take ? 0.55 : 0.28)
		ctx.lineWidth = take ? 3 : 1.8
		ctx.beginPath(); ctx.arc(cx, cy, R, ta, ta + Math.PI * 0.7); ctx.stroke()
		// honour (warm) and abasement (cool) alternating around the rim
		const p = 0.5 + 0.5 * Math.sin(sceneT * 0.7)
		glow(ctx, cx + R, cy, m * 0.10, "#e0a02a", 0.14 + 0.12 * p)        // تعزّ
		glow(ctx, cx - R, cy, m * 0.10, COLORS.blue, 0.14 + 0.12 * (1 - p)) // تذلّ
		// بيدك الخير: a warm glow that never leaves the whole scene
		const kh = sceneSel === 19
		glow(ctx, cx, cy, m * (kh ? 0.5 : 0.42), "#e0a02a", kh ? 0.12 : 0.06)
	},
	// النساء ١٣٥: a balance whose beam stays level toward Allah; desire (الهوى)
	// gusts at it but cannot tip it — justice is not swayed by kin, wealth, or self.
	qist(ctx, w, h) {
		const cx = w / 2, cy = h / 2, m = Math.min(w, h)
		// شهداء لله: the anchor above that keeps the beam true
		glow(ctx, cx, cy - m * 0.34, m * 0.13, "#e0a02a", 0.16)
		// الهوى tries to tip it; the beam wobbles a hair then holds level
		const gust = sceneSel === 25
		const tilt = gust ? 0.05 * Math.sin(sceneT * 3) : 0.012 * Math.sin(sceneT * 1.1)
		if (gust) {
			for (let i = 0; i < 4; i++) {
				const yy = cy - m * 0.1 + i * m * 0.06
				const px = ((sceneT * 60 + i * 40) % (m * 0.5))
				ctx.strokeStyle = hexA(COLORS.red, 0.22)
				ctx.lineWidth = 1
				ctx.beginPath(); ctx.moveTo(cx - m * 0.28 + px, yy); ctx.lineTo(cx - m * 0.16 + px, yy); ctx.stroke()
			}
		}
		ctx.save()
		ctx.translate(cx, cy)
		ctx.rotate(tilt)
		// the fulcrum column, rooted (toward Allah)
		ctx.strokeStyle = hexA("#e0a02a", 0.5)
		ctx.lineWidth = 2.5
		ctx.beginPath(); ctx.moveTo(0, -m * 0.22); ctx.lineTo(0, 0); ctx.stroke()
		// the level beam
		const bw = m * 0.3, beamOn = sceneSel === 5 || sceneSel === 6
		ctx.strokeStyle = hexA(beamOn ? "#e0a02a" : COLORS.ink2, beamOn ? 0.7 : 0.5)
		ctx.lineWidth = beamOn ? 3 : 2
		ctx.beginPath(); ctx.moveTo(-bw, 0); ctx.lineTo(bw, 0); ctx.stroke()
		// two pans: near (self/kin) and far (rich/poor)
		const near = sceneSel === 11
		;[[-bw, near], [bw, false]].forEach(([x, hot]) => {
			ctx.strokeStyle = hexA(COLORS.muted, 0.4)
			ctx.lineWidth = 1
			ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, m * 0.08); ctx.stroke()
			glow(ctx, x, m * 0.1, m * (hot ? 0.09 : 0.05), hot ? COLORS.blue : COLORS.aqua, hot ? 0.35 : 0.18)
		})
		ctx.restore()
	},
	// النساء ١٧٤: darkness at the edges yields to a clear rising light (the Quran);
	// a sharp ray = برهان (proof to the mind), a soft glow = نور مبين (light to the heart).
	burhan_nur(ctx, w, h) {
		const cx = w / 2, cy = h / 2, m = Math.min(w, h)
		// darkness pooled at the edges (before the light)
		const vig = ctx.createRadialGradient(cx, cy, m * 0.1, cx, cy, m * 0.7)
		vig.addColorStop(0, hexA("#000000", 0))
		vig.addColorStop(1, hexA("#000000", 0.5))
		ctx.fillStyle = vig
		ctx.fillRect(0, 0, w, h)
		// نورًا مبينًا: a soft spreading glow that dispels the dark
		const nur = sceneSel === 10 || sceneSel === 11
		const p = 0.5 + 0.5 * Math.sin(sceneT * 0.6)
		glow(ctx, cx, cy, m * (nur ? 0.62 : 0.46 + 0.04 * p), "#e0a02a", nur ? 0.15 : 0.10)
		// برهان: a sharp, steady vertical ray that cuts the darkness of doubt
		const bur = sceneSel === 5
		const rw = bur ? 10 : 5
		const rg = ctx.createLinearGradient(cx - rw, 0, cx + rw, 0)
		rg.addColorStop(0, hexA("#cfe6ff", 0))
		rg.addColorStop(0.5, hexA("#cfe6ff", bur ? 0.5 : 0.28))
		rg.addColorStop(1, hexA("#cfe6ff", 0))
		ctx.fillStyle = rg
		ctx.fillRect(cx - rw, cy - m * 0.42, rw * 2, m * 0.84)
	},
	dua_end(ctx, w, h) {
		const cx = w / 2, m = Math.min(w, h)
		for (let i = 0; i < 5; i++) {
			const ph = (sceneT * 0.12 + i * 0.2) % 1
			const x = cx + (i - 2) * m * 0.15
			const y = h * 0.9 - ph * h * 0.72
			const a = Math.sin(ph * Math.PI)
			glow(ctx, x, y, 12, "#cfe6ff", 0.42 * a)             // a plea ascends
			if (ph > 0.72) { glow(ctx, x, h * 0.15, 22, "#e0a02a", 0.32 * (ph - 0.72) / 0.28) }  // answered
		}
		const lift = sceneSel === 24 ? 1 : 0.5 + 0.5 * Math.sin(sceneT * 0.5)   // الإصر يُرفع
		ctx.fillStyle = hexA(COLORS.violet, 0.16 * (1 - lift * 0.6))
		ctx.fillRect(cx - m * 0.22, h * 0.82 - lift * h * 0.26, m * 0.44, 9)
		if (sceneSel === 6) { glow(ctx, cx, h / 2, m * 0.5, "#cfe6ff", 0.10) }   // إلا وسعها: يُسر
		if (sceneSel === 39) { glow(ctx, cx, h / 2, m * 0.5, "#e0a02a", 0.12) }  // العفو والرحمة
		if (sceneSel === 45) { glow(ctx, cx, h / 2, m * 0.6, COLORS.aqua, 0.12) }  // مولانا: نصرٌ وحفظ
	},
}

function sceneLabel(ctx, text, x, y, color) {
	ctx.fillStyle = color || COLORS.ink2
	ctx.font = "14px system-ui"
	ctx.textAlign = "center"
	ctx.fillText(text, x, y)
}

/* ============================================================
   Layer: الميزان (the scale) — the prophetic division made visible
   ============================================================ */
let scaleSel = null
const SC_PRAISE = [1, 2, 3, 4], SC_PIVOT = 5, SC_PETITION = [6, 7]
const SC_COL = { praise: "#1c5cab", pivot: COLORS.magenta, petition: "#0e7a56" }

function scaleSide(n) {
	return n === SC_PIVOT ? "pivot" : SC_PRAISE.includes(n) ? "praise" : "petition"
}

function buildScale() {
	$("#scale-chips").innerHTML = D.surah.verses.map((v) =>
		`<button data-n="${v.n}">آية ${arNum(v.n)}</button>`).join("")
	$("#scale-chips").querySelectorAll("button").forEach((b) =>
		{ b.onclick = () => { scaleSel = Number(b.dataset.n); drawScale(); showScaleInfo(scaleSel) } })
	scaleDefaultInfo()
	drawScale()
}

function scaleDefaultInfo() {
	const pd = D.surah.ring_structure.prophetic_division
	$("#scale-info").innerHTML =
		`<b>«قسمتُ الصلاة بيني وبين عبدي نصفين، ولعبدي ما سأل»</b> ${gradeBadge("ma'thur")}` +
		`<div style="margin-top:8px">${pd.note}</div>` +
		`<div class="src">المصدر: ${pd.source}</div>` +
		`<div style="margin-top:10px;color:${COLORS.yellow}">↦ فإذا صلّيتَ الليلة، استحضر أن نصفها ثناؤك لربّك، ونصفها عطاؤه لك، ومفتاحها عهدُك: «إياك نعبد».</div>`
}

function scaleToken(ctx, x, y, n, side, big) {
	const r = big ? 24 : 17
	ctx.beginPath()
	ctx.arc(x, y, r, 0, Math.PI * 2)
	ctx.fillStyle = SC_COL[side]
	ctx.fill()
	ctx.lineWidth = scaleSel === n ? 3.5 : 2
	ctx.strokeStyle = scaleSel === n ? "#fff" : COLORS.surface
	ctx.stroke()
	ctx.fillStyle = "#fff"
	ctx.font = (big ? "19px" : "15px") + " 'Amiri',serif"
	ctx.textAlign = "center"
	ctx.textBaseline = "middle"
	ctx.fillText(arNum(n), x, y + 1)
	ctx.textBaseline = "alphabetic"
}

function drawScale() {
	const canvas = $("#scale-canvas")
	const cssW = canvas.parentElement.clientWidth - 40
	const dpr = window.devicePixelRatio || 1
	canvas.width = cssW * dpr
	canvas.height = 420 * dpr
	canvas.style.height = "420px"
	const ctx = canvas.getContext("2d")
	ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
	ctx.clearRect(0, 0, cssW, 420)
	const cx = cssW / 2, pivotY = 130, baseY = 356, panY = pivotY + 96
	const beamHalf = Math.min(cssW * 0.34, 300)

	// stand: post + fulcrum triangle + base plate
	ctx.strokeStyle = COLORS.baseline
	ctx.lineWidth = 4
	ctx.beginPath(); ctx.moveTo(cx, pivotY); ctx.lineTo(cx, baseY); ctx.stroke()
	ctx.beginPath(); ctx.moveTo(cx, pivotY + 2); ctx.lineTo(cx - 26, baseY); ctx.lineTo(cx + 26, baseY); ctx.closePath()
	ctx.fillStyle = "#2c2c2a"; ctx.fill(); ctx.strokeStyle = COLORS.baseline; ctx.stroke()
	ctx.fillStyle = COLORS.baseline; ctx.fillRect(cx - 72, baseY, 144, 6)

	// beam (level — the two halves balance perfectly)
	ctx.strokeStyle = "#6b6a64"; ctx.lineWidth = 6; ctx.lineCap = "round"
	ctx.beginPath(); ctx.moveTo(cx - beamHalf, pivotY); ctx.lineTo(cx + beamHalf, pivotY); ctx.stroke()

	const drawPan = (ex, verses, side, label) => {
		ctx.strokeStyle = "#4a4a48"; ctx.lineWidth = 1.5
		ctx.beginPath()
		ctx.moveTo(ex, pivotY); ctx.lineTo(ex - 32, panY)
		ctx.moveTo(ex, pivotY); ctx.lineTo(ex + 32, panY)
		ctx.stroke()
		ctx.strokeStyle = SC_COL[side]; ctx.lineWidth = 3
		ctx.beginPath(); ctx.arc(ex, panY, 44, 0.12 * Math.PI, 0.88 * Math.PI); ctx.stroke()
		verses.forEach((n, i) => {
			const tx = ex - ((verses.length - 1) / 2 - i) * 34
			scaleToken(ctx, tx, panY - 8, n, side)
		})
		ctx.fillStyle = COLORS.ink2; ctx.font = "14px system-ui"; ctx.textAlign = "center"
		ctx.fillText(label, ex, panY + 74)
	}
	// RTL: praise on the right, petition on the left
	drawPan(cx + beamHalf, SC_PRAISE, "praise", "ثناءٌ لله (١–٤)")
	drawPan(cx - beamHalf, SC_PETITION, "petition", "عطاءٌ للعبد (٦–٧)")

	// pivot: verse 5 rides the fulcrum — "between Me and My servant"
	ctx.fillStyle = COLORS.magenta; ctx.font = "13px system-ui"; ctx.textAlign = "center"
	ctx.fillText("↕ بيني وبين عبدي", cx, pivotY - 42)
	scaleToken(ctx, cx, pivotY - 2, SC_PIVOT, "pivot", true)
}

function showScaleInfo(n) {
	const verse = D.surah.verses[n - 1]
	const td = D.tadabbur.verses[n - 1]
	const side = scaleSide(n)
	const sideLabel = { praise: "كفّة الثناء لله", pivot: "نقطة الارتكاز — بين الله وعبده", petition: "كفّة العطاء للعبد" }[side]
	let html = `<b>﴿${verse.uthmani}﴾</b> <span style="color:${SC_COL[side]}">— ${sideLabel}</span>`
	if (td.divine_response) {
		html += `<div style="margin-top:8px;color:${COLORS.aqua}">قال الله: «${td.divine_response}» <span class="src">${td.divine_response_source}</span></div>`
	} else {
		html += `<div style="margin-top:8px;color:${COLORS.muted}">${td.divine_response_note}</div>`
	}
	html += `<div style="margin-top:8px">${td.reflection.text}</div><div class="src">${td.reflection.source} ${gradeBadge(td.reflection.grade)}</div>`
	$("#scale-info").innerHTML = html
	$("#scale-chips").querySelectorAll("button").forEach((b) =>
		b.classList.toggle("sel-a", Number(b.dataset.n) === n))
}

/* ============================================================
   Layer: المحاورة (dialogue) — worshipper wing
   ============================================================ */
let dlgIndex = 0
let dlgAudio = null
let dlgRaf = null

function buildDialogue() {
	renderDialogueVerse(0)
	const dots = D.surah.verses.map((v, i) =>
		`<span class="dot ${v.n === D.arc.pivot_verse ? "pivot" : ""}" data-i="${i}">${arNum(v.n)}</span>`).join("")
	$("#dialogue-controls").innerHTML =
		`<button id="dlg-prev">◀ السابقة</button>` +
		`<button id="dlg-play">▶ استمع وتأمّل</button>` +
		`<button id="dlg-reveal">أظهِر الجواب</button>` +
		`<button id="dlg-next">التالية ▶</button>` +
		`<div class="dlg-progress">${dots}</div>`
	$("#dlg-prev").onclick = () => renderDialogueVerse(Math.max(0, dlgIndex - 1))
	$("#dlg-next").onclick = () => renderDialogueVerse(Math.min(6, dlgIndex + 1))
	$("#dlg-play").onclick = () => playDialogue()
	$("#dlg-reveal").onclick = () => revealDialogue()
	document.querySelectorAll("#dialogue-controls .dot").forEach((d) =>
		{ d.onclick = () => renderDialogueVerse(Number(d.dataset.i)) })
}

function stopDialogue() {
	if (dlgAudio) { dlgAudio.pause(); dlgAudio = null }
	if (dlgRaf) { cancelAnimationFrame(dlgRaf); dlgRaf = null }
}

// Map each word index -> sourced balaghi/tafsir insights that touch it,
// built once from the golden semantic links (word-level tadabbur).
let WORD_INSIGHTS = null
function buildWordInsights() {
	WORD_INSIGHTS = new Map()
	const add = (i, ins) => {
		if (!WORD_INSIGHTS.has(i)) { WORD_INSIGHTS.set(i, []) }
		WORD_INSIGHTS.get(i).push(ins)
	}
	for (const l of D.surah.semantic_links) {
		const ins = { label: l.label, note: l.note, source: l.source, grade: l.grade, type: l.type }
		for (const i of l.from_words || []) { add(i, ins) }
		for (const i of l.to_words || []) { add(i, ins) }
	}
}

function renderDialogueVerse(i) {
	stopDialogue()
	dlgIndex = i
	const verse = D.surah.verses[i]
	const td = D.tadabbur.verses[i]
	const arcv = D.arc.verses[i]
	const names = td.divine_names.join(" · ")
	if (!WORD_INSIGHTS) { buildWordInsights() }

	const words = verse.words.map((w) =>
		`<span class="dlg-word${WORD_INSIGHTS.has(w.i) ? " has-insight" : ""}" data-wi="${w.i}">${w.text}</span>`
	).join(" ")
	let html = `<div class="dlg-verse" style="color:${COLORS.ink}">﴿ ${words} <span class="vmark">${arNum(verse.n)}</span> ﴾</div>`
	html += `<div class="dlg-word-info" id="dlg-word-info">اضغط أيّ كلمة لتتدبّر معناها وسرّها البلاغي</div>`
	html += `<canvas class="dlg-breath" id="dlg-breath"></canvas>`

	if (td.divine_response === null) {
		html += `<div class="dlg-basmala-note">${td.divine_response_note}</div>`
	} else {
		html += `<div class="dlg-response" id="dlg-response">
			<span class="lbl">فيقول الله${td.divine_response_continuation ? " (تتمّة الطلب)" : ""}:</span>
			«${td.divine_response}»
			${td.divine_response_variant ? `<span class="src">${td.divine_response_variant}</span>` : ""}
			<span class="src">${td.divine_response_source} · ${td.divine_response_note || ""}</span>
		</div>`
	}
	html += `<div class="dlg-reflect" id="dlg-reflect">
		<span class="mut" style="color:${COLORS.muted};font-size:12px">وقفة · الأسماء الفاعلة: ${names}</span>
		<div style="margin-top:6px">${td.reflection.text}</div>
		<span class="action">↦ ${td.action.text}</span>
		<span class="src">${td.reflection.source} ${gradeBadge(td.reflection.grade)} · حال القلب: ${td.heart_state.text} ${gradeBadge("ijtihadi")}</span>
	</div>`
	html += dialogueEchoHtml(verse.n)
	$("#dialogue-stage").innerHTML = html

	document.querySelectorAll("#dialogue-stage .dlg-word").forEach((el) =>
		{ el.onclick = () => showWordTadabbur(verse, Number(el.dataset.wi), el) })
	document.querySelectorAll("#dialogue-controls .dot").forEach((d, k) =>
		d.classList.toggle("active", k === i))
	drawBreath(arcv, 0)
}

// Bring the ayah's echo into worship, softly: while you ponder your verse, see
// how its words answer across the whole Book. Same computed data as the lab's
// «صدى الآية», but framed for tadabbur — for reflection, not for counting.
function dialogueEchoHtml(n) {
	const nbrs = (AL.links["1:" + n] || []).slice(0, 3)
	if (!nbrs.length) { return "" }
	const rows = nbrs.map(([o, sc, rs]) => {
		const [os, oa] = o.split(":")
		const chips = rs.map((r) => `<span class="ec-root">${r}</span>`).join("")
		const lf = echoLift(sc)
		return `<div class="dlg-echo-row"><span class="rx-ref">${sname(os)} ${arNum(oa)}</span> ${chips}` +
			`<span class="ec-band ${lf.cls}">${lf.label}</span>` +
			`<div class="dlg-echo-txt">${ayahText(os, oa)}</div></div>`
	}).join("")
	// honest framing: for al-Fatiha these shared-word links are near chance, so
	// we invite reading, not inference — and say so plainly (رقم القاعدة ٥).
	return `<div class="dlg-echo">` +
		`<span class="lbl">مواضعُ تشترك مع هذه الآية في لفظٍ مميّز — قد تعينك على تدبّرها. وأمانةً: هذا الاشتراك في الفاتحة <b>قريبٌ من الصدفة</b> غالبًا (قِسناه على نموذجٍ عشوائيّ)، فهو دعوةٌ للقراءة والتأمّل، لا دليلَ بناءٍ خفيّ:</span>` +
		`<div class="dlg-echo-list">${rows}</div>` +
		`<span class="src">اشتراكُ جذرٍ لفظيّ محسوب، موزونٌ على الصدفة — للتأمّل لا للاستدلال ${gradeBadge("ijtihadi")}</span>` +
		`</div>`
}

function showWordTadabbur(verse, wi, el) {
	const w = verse.words.find((x) => x.i === wi)
	document.querySelectorAll("#dialogue-stage .dlg-word").forEach((e) => e.classList.remove("sel"))
	el.classList.add("sel")
	const box = $("#dlg-word-info")
	let html = `<div class="wt-head"><b>${w.text}</b>${w.root ? ` <span class="wt-root">الجذر: ${w.root}</span>` : ""} <span class="wt-pos">${w.pos}</span></div>`
	html += `<div class="wt-gloss">${w.gloss}</div>`
	const insights = WORD_INSIGHTS.get(wi) || []
	for (const ins of insights) {
		const t = (LINK_TYPE[ins.type] || {}).label || ins.type
		html += `<div class="wt-insight"><span class="wt-type" style="color:${(LINK_TYPE[ins.type] || {}).color || COLORS.muted}">◆ ${ins.label} (${t})</span> ${ins.note} <span class="src">${ins.source} ${gradeBadge(ins.grade)}</span></div>`
	}
	box.innerHTML = html
	box.classList.add("filled")
}

function drawBreath(arcv, progress) {
	const canvas = $("#dlg-breath")
	if (!canvas) { return }
	const env = (D.acoustics.verses[arcv.n - 1] || {}).envelope || []
	const cssW = canvas.parentElement.clientWidth || 600
	const dpr = window.devicePixelRatio || 1
	canvas.width = cssW * dpr
	canvas.height = 60 * dpr
	const ctx = canvas.getContext("2d")
	ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
	ctx.clearRect(0, 0, cssW, 60)
	if (!env.length) { return }
	const col = mixWarmth(arcv.warmth)
	ctx.beginPath()
	ctx.moveTo(0, 58)
	env.forEach((v, i) => {
		const x = (i / (env.length - 1)) * cssW
		const y = 58 - v * 52
		ctx.lineTo(x, y)
	})
	ctx.lineTo(cssW, 58)
	ctx.closePath()
	ctx.fillStyle = col + "33"
	ctx.fill()
	ctx.beginPath()
	env.forEach((v, i) => {
		const x = (i / (env.length - 1)) * cssW
		const y = 58 - v * 52
		if (i === 0) { ctx.moveTo(x, y) } else { ctx.lineTo(x, y) }
	})
	ctx.strokeStyle = col
	ctx.lineWidth = 2
	ctx.stroke()
	if (progress > 0) {
		const px = progress * cssW
		ctx.beginPath()
		ctx.moveTo(px, 4)
		ctx.lineTo(px, 58)
		ctx.strokeStyle = "#fff"
		ctx.lineWidth = 1.5
		ctx.stroke()
	}
}

function mixWarmth(w) {
	// cool blue (praise) -> warm yellow (petition), driven by real intensity
	const cold = [57, 135, 229], hot = [201, 133, 0]
	const r = Math.round(cold[0] + (hot[0] - cold[0]) * w)
	const g = Math.round(cold[1] + (hot[1] - cold[1]) * w)
	const b = Math.round(cold[2] + (hot[2] - cold[2]) * w)
	return `rgb(${r},${g},${b})`
}

function playDialogue() {
	stopDialogue()
	const arcv = D.arc.verses[dlgIndex]
	const n = arcv.n
	const file = "00100" + n + ".mp3"
	dlgAudio = new Audio("../audio/" + file)
	const tick = () => {
		if (!dlgAudio) { return }
		const p = dlgAudio.duration ? dlgAudio.currentTime / dlgAudio.duration : 0
		drawBreath(arcv, p)
		dlgRaf = requestAnimationFrame(tick)
	}
	dlgAudio.addEventListener("ended", () => { revealDialogue(); stopDialogue() })
	dlgAudio.play().then(() => { tick() }).catch(() => { revealDialogue() })
}

function revealDialogue() {
	const resp = $("#dlg-response")
	if (resp) { resp.classList.add("show") }
	const refl = $("#dlg-reflect")
	if (refl) { setTimeout(() => refl.classList.add("show"), resp ? 500 : 0) }
	const echo = $(".dlg-echo")
	if (echo) { setTimeout(() => echo.classList.add("show"), resp ? 900 : 300) }
}
window.__revealDialogue = revealDialogue

/* ============================================================
   Layer: مرصد الفواصل (observatory) — researcher wing
   ============================================================ */
const F = window.FAWASIL_DATA
let obsFilter = "all"

function buildObservatory() {
	$("#obs-intro").innerHTML =
		`تجربة حيّة من <b style="font-family:inherit;color:${COLORS.ink}">دفتر الأسئلة المفتوحة</b> (السؤال ٢: هندسة الفواصل). ` +
		`حلّلنا حرف الفاصلة الأخير لكل آيات القرآن (${arNum(F.total_ayahs)} آية في ${arNum(F.surah_count)} سورة). ` +
		`أبرز نتيجة: حرف <b style="font-family:var(--arabic);color:${COLORS.ink}">النون</b> يهيمن على فواصل القرآن (${arNum(F.global_top_fasila[0][1])} آية، قرابة النصف) — الغنّة الأنفية الرخيّة — تليه ألف المد. ` +
		`${F.scope_note}`

	$("#obs-legend").innerHTML =
		`<span class="item"><span class="swatch" style="background:${COLORS.blue}"></span> مكية</span>` +
		`<span class="item"><span class="swatch" style="background:${COLORS.aqua}"></span> مدنية</span>` +
		`<span class="item" style="color:${COLORS.muted}">النقر على سورة يعرض بصمة فواصلها</span>`

	$("#obs-controls").innerHTML =
		`<button data-f="all" class="sel-a">الكل (١١٤)</button>` +
		`<button data-f="مكية">المكية</button>` +
		`<button data-f="مدنية">المدنية</button>`
	$("#obs-controls").querySelectorAll("button").forEach((b) =>
		{ b.onclick = () => { obsFilter = b.dataset.f; renderObsGrid() } })

	renderObsGrid()
	$("#obs-note").innerHTML = `اختر سورة من الخريطة أعلاه لعرض توزيع صفات فاصلتها.`
	drawObsChart()
	buildControl()
}

/* ---- control-sample experiment (the sieve) ---- */
const C = window.CONTROL_DATA

function buildControl() {
	const b = C.quran_baseline
	$("#control-intro").innerHTML =
		`قبل أن نَنسب أي نمطٍ للقرآن، نمرّره على نصوصٍ عربيةٍ ضابطة (شعر جاهلي وعباسي، سجع كهّان، خطب، نثر مرسل) — فما ظهر فيها بالقوة نفسها <b style="font-family:inherit;color:${COLORS.ink}">نشطبه بأمانة</b>. ` +
		`الوكلاء كُلّفوا بمحاولة <b style="font-family:inherit;color:${COLORS.ink}">إسقاط</b> التميّز لا إثباته، والطرف القرآني محسوبٌ حسابياً من ${arNum(b.total_ayahs)} آية. النتيجة: ` +
		`${arNum(C.synthesis.survived.length)} صمدت، و${arNum(C.synthesis.killed.length)} سقطت.`

	$("#control-legend").innerHTML =
		`<span class="item"><span class="swatch" style="background:${COLORS.yellow}"></span> القرآن</span>` +
		`<span class="item"><span class="swatch" style="background:${COLORS.blue}"></span> أعلى ضابط (شعر/نثر)</span>` +
		`<span class="item" style="color:${COLORS.muted}">نسبة الحرف/الأصوات الأغلب في النهايات</span>`

	drawControlChart()

	const VT = { "quran-distinctive": "صمد: تميّز قرآني", "arabic-general": "سقط: طبعٌ عربي عام", "inconclusive": "غير حاسم" }
	const VC = { "quran-distinctive": "survived", "arabic-general": "killed", "inconclusive": "inconclusive" }
	$("#control-verdicts").innerHTML = C.verdicts.map((v) => {
		const cls = VC[v.verdict]
		return `<div class="verdict-card ${cls}">
			<div class="vhead">
				<span class="dim">${v.dimension}</span>
				<span class="vtag ${cls}">${VT[v.verdict]}</span>
				<span class="conf">ثقة: ${{ high: "عالية", medium: "متوسطة", low: "منخفضة" }[v.confidence]}</span>
			</div>
			<div class="vbody"><span class="q">القرآن: ${v.quran}</span> · <span class="c">الضابط: ${v.control}</span></div>
			<div class="vnote">↦ ${v.note}</div>
		</div>`
	}).join("")

	const s = C.synthesis
	$("#control-summary").innerHTML =
		`<div class="control-cols">
			<div><h4 class="survived-h">صمد بعد الغربلة</h4><ul>${s.survived.map((x) => `<li>${x}</li>`).join("")}</ul></div>
			<div><h4 class="killed-h">سقط — لا يُنسب للقرآن</h4><ul>${s.killed.map((x) => `<li class="killed-item">${x}</li>`).join("")}</ul></div>
		</div>` +
		`<div style="margin-top:12px">${s.summary_ar}</div>` +
		`<div class="src">حدود المنهج: ${s.method_limits.join(" · ")}</div>` +
		`<div class="src">${C._meta.honesty}</div>`
}

function drawControlChart() {
	const canvas = $("#control-canvas")
	const cssW = canvas.parentElement.clientWidth - 40
	const dpr = window.devicePixelRatio || 1
	canvas.width = cssW * dpr
	canvas.height = 240 * dpr
	canvas.style.height = "240px"
	const ctx = canvas.getContext("2d")
	ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
	ctx.clearRect(0, 0, cssW, 240)
	const b = C.quran_baseline
	// three comparisons: nun dominance, soft endings, within-consistency
	const rows = [
		{ label: "هيمنة حرف واحد", q: b.nun_pct, ctrl: 18, ctrlLabel: "أعلى ضابط 18٪" },
		{ label: "الأصوات اللينة (ن+ا+م)", q: b.soft_naml_pct, ctrl: 40, ctrlLabel: "أرضية النثر 40٪" },
		{ label: "الاتساق داخل الوحدة", q: b.per_surah_dominant_median, ctrl: 100, ctrlLabel: "الشعر المقفّى 100٪" },
	]
	const padR = 150, padL = 20, padT = 10, rowH = (240 - padT - 10) / rows.length
	const plotW = cssW - padR - padL
	rows.forEach((r, i) => {
		const y = padT + i * rowH
		ctx.fillStyle = COLORS.ink2
		ctx.font = "13px system-ui"
		ctx.textAlign = "right"
		ctx.fillText(r.label, cssW - 6, y + 16)
		const barMax = plotW
		const drawBar = (val, yy, color, txt) => {
			const w = (val / 100) * barMax
			ctx.fillStyle = color
			ctx.beginPath()
			ctx.roundRect(padL, yy, w, 15, [0, 4, 4, 0])
			ctx.fill()
			ctx.fillStyle = COLORS.ink
			ctx.font = "12px system-ui"
			ctx.textAlign = "left"
			ctx.fillText(txt, padL + w + 6, yy + 12)
		}
		drawBar(r.q, y + 8, COLORS.yellow, r.q + "٪ قرآن")
		drawBar(r.ctrl, y + 28, COLORS.blue, r.ctrlLabel)
	})
}

function renderObsGrid() {
	document.querySelectorAll("#obs-controls button").forEach((b) =>
		b.classList.toggle("sel-a", b.dataset.f === obsFilter))
	const list = F.surahs.filter((s) => obsFilter === "all" || s.revelation === obsFilter)
	$("#obs-grid").innerHTML = list.map((s) => {
		const col = s.revelation === "مكية" ? COLORS.blue : COLORS.aqua
		return `<div class="obs-cell" data-n="${s.n}" style="border-color:${col}44">
			<span class="onum">${arNum(s.n)}</span>
			<span class="ofas">${s.dominant_fasila}</span>
			<span class="oname">${s.name.replace("سُورَةُ ", "").replace("ٱل", "ال")}</span>
		</div>`
	}).join("")
	document.querySelectorAll(".obs-cell").forEach((c) =>
		{ c.onclick = () => showObsSurah(Number(c.dataset.n)) })
}

function showObsSurah(n) {
	const s = F.surahs.find((x) => x.n === n)
	const fp = Object.entries(s.fingerprint).sort((a, b) => b[1] - a[1])
	const tags = { ghunna: "غنة", madd: "مد", jahr: "جهر", hams: "همس", shidda: "شدة", rakhawa: "رخاوة", tawassut: "توسط", istiala: "استعلاء", istifal: "استفال", itbaq: "إطباق", qalqala: "قلقلة", safir: "صفير", lin: "لين", inhiraf: "انحراف", takrir: "تكرير", tafashshi: "تفشٍّ", istitala: "استطالة" }
	const bars = fp.slice(0, 8).map(([k, v]) =>
		`<div style="display:flex;align-items:center;gap:8px;margin:3px 0">
			<span style="width:70px;font-size:12px;color:${COLORS.ink2}">${tags[k] || k}</span>
			<span style="flex:1;height:10px;background:#2c2c2a;border-radius:5px;overflow:hidden">
				<span style="display:block;height:100%;width:${v}%;background:${COLORS.blue}"></span></span>
			<span style="width:44px;font-size:12px;color:${COLORS.muted};font-variant-numeric:tabular-nums">${v}٪</span>
		</div>`).join("")
	const top = s.top_letters.map(([l, c]) => `${l} (${arNum(c)})`).join("، ")
	$("#obs-note").innerHTML =
		`<b>${s.name} — ${s.revelation}، ${arNum(s.ayah_count)} آية</b>` +
		`<div style="margin-top:4px;color:${COLORS.ink2}">الفاصلة الغالبة: <b style="font-family:var(--arabic)">${s.dominant_fasila}</b> بنسبة ${s.dominant_pct}٪ · أكثر حروف الفواصل: ${top}</div>` +
		`<div style="margin-top:10px">بصمة صفات الفواصل:</div>${bars}` +
		`<div class="src">${F.source}</div>`
}

function drawObsChart() {
	const canvas = $("#obs-canvas")
	const cssW = canvas.parentElement.clientWidth - 40
	const dpr = window.devicePixelRatio || 1
	canvas.width = cssW * dpr
	canvas.height = 360 * dpr
	canvas.style.height = "360px"
	const ctx = canvas.getContext("2d")
	ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
	ctx.clearRect(0, 0, cssW, 360)

	const data = F.global_top_fasila
	const max = data[0][1]
	const padR = 90, padL = 60, padT = 16, padB = 20
	const plotW = cssW - padR - padL
	const rowH = (360 - padT - padB) / data.length

	ctx.fillStyle = COLORS.ink
	ctx.font = "13px system-ui"
	ctx.textAlign = "right"
	ctx.fillText("توزيع حروف الفواصل في القرآن كاملاً", cssW - padL, padT - 2 + 14)

	data.forEach(([letter, count], i) => {
		const y = padT + i * rowH + 14
		const w = (count / max) * plotW
		// bar grows from the right (RTL)
		const x = cssW - padL - w
		ctx.fillStyle = i === 0 ? COLORS.yellow : COLORS.blue
		ctx.beginPath()
		ctx.roundRect(x, y, w, rowH - 12, [0, 4, 4, 0])
		ctx.fill()
		ctx.fillStyle = COLORS.ink
		ctx.font = "16px 'Amiri',serif"
		ctx.textAlign = "right"
		ctx.fillText(letter, cssW - padL + 22, y + rowH / 2)
		ctx.fillStyle = COLORS.muted
		ctx.font = "12px system-ui"
		ctx.textAlign = "left"
		ctx.fillText(arNum(count) + " آية", x - 8, y + rowH / 2 - 4)
	})
}

/* ============================================================
   Invitation — the front door that delivers the نور itself,
   with the mandatory honesty/disclaimer gate.
   ============================================================ */
const INV_VERSES = [2, 3, 4, 5]
let invStep = 0
let invAudio = null
let invRaf = null

function invStop() {
	if (invAudio) { invAudio.pause(); invAudio = null }
	if (invRaf) { cancelAnimationFrame(invRaf); invRaf = null }
}

function buildInvitation() {
	$("#reopen-invitation").onclick = () => { invStep = 0; $("#invitation").classList.remove("hidden"); invRender() }
	let seen = false
	try { seen = window.localStorage.getItem("qe_seen_invitation") === "1" } catch { seen = false }
	if (seen) { $("#invitation").classList.add("hidden") } else { invStep = 0; invRender() }
}

function closeInvitation() {
	invStop()
	try { window.localStorage.setItem("qe_seen_invitation", "1") } catch { /* ignore */ }
	$("#invitation").classList.add("hidden")
}

function invRender() {
	invStop()
	const stage = $("#inv-stage")
	const ctrl = $("#inv-controls")
	const prog = $("#inv-progress")
	prog.innerHTML = INV_VERSES.map((n, k) =>
		`<span class="idot ${n === D.arc.pivot_verse ? "pivot" : ""} ${invStep - 1 === k ? "on" : ""}"></span>`).join("")

	if (invStep === 0) {
		stage.innerHTML =
			`<div class="inv-hook-title">أنت تقرأ الفاتحة في صلاتك<br>سبع عشرة مرّة كل يوم</div>` +
			`<div class="inv-hook-sub">وأنت — غالبًا — غافلٌ عنها، تمرّ عليها مرور العادة.<br>لكنّك لستَ في مناجاةٍ من طرفٍ واحد.<br><b>أنت في حوار… والله يُجيبك بعد كل آية.</b></div>`
		ctrl.innerHTML = `<button class="primary" id="inv-start">ابدأ الرحلة</button><button class="ghost" id="inv-skip">تخطَّ إلى العمق</button>`
		$("#inv-start").onclick = () => { invStep = 1; invRender() }
		$("#inv-skip").onclick = () => { invStep = INV_VERSES.length + 2; invRender() }
		return
	}

	if (invStep >= 1 && invStep <= INV_VERSES.length) {
		const n = INV_VERSES[invStep - 1]
		const verse = D.surah.verses[n - 1]
		const td = D.tadabbur.verses[n - 1]
		const last = invStep === INV_VERSES.length
		stage.innerHTML =
			`<div class="inv-verse">﴿ ${verse.uthmani} <span class="vmark">${arNum(n)}</span> ﴾</div>` +
			`<canvas class="inv-breath" id="inv-breath"></canvas>` +
			`<div class="inv-response" id="inv-response"><span class="lbl">فيقول الله:</span>«${td.divine_response}»<span class="src">${td.divine_response_source}</span></div>`
		ctrl.innerHTML = `<button class="ghost" id="inv-replay">↻ أعِد</button><button class="primary" id="inv-next">${last ? "تأمّل الخاتمة" : "التالية"}</button>`
		$("#inv-next").onclick = () => { invStep += 1; invRender() }
		$("#inv-replay").onclick = () => invPlayVerse(n)
		invPlayVerse(n)
		return
	}

	if (invStep === INV_VERSES.length + 1) {
		stage.innerHTML =
			`<div class="inv-closing">رأيتَ بعينك: ما إن تُثني حتى تُجاب، وما إن تسأل حتى يُقال «ولعبدي ما سأل».<br>` +
			`فإذا قمتَ الليلة تصلّي، تذكّر أنك <b>تُخاطَب وتُجاب</b> — لا تناجي جدارًا.<br>` +
			`اقرأها متمهّلًا، وأنصت لجواب ربّك في قلبك.` +
			`<span class="action">↦ الليلة: صلِّ ركعتين، وقف عند كل آيةٍ لحظةً تستشعر جوابها.</span></div>`
		ctrl.innerHTML = `<button class="primary" id="inv-next2">تابع</button>`
		$("#inv-next2").onclick = () => { invStep += 1; invRender() }
		return
	}

	// disclaimer gate (mandatory — reachable from skip too)
	stage.innerHTML =
		`<div class="inv-disclaimer"><h3>تنبيهٌ وأمانة — قبل أن تدخل</h3>` +
		`الأدوات التي ستراها (أرقام، أنماط، خرائط) هي <b>عينُ ما يقع كثيرٌ من الناس في فخّه</b>: ` +
		`فيرفعون النمط الإحصائي إلى «إعجازٍ مثبت»، أو يُنزِّلون استنتاجاتِهم البشرية على كلام الله <b>فيفسّرون كلامه بكلامنا وأهوائنا</b>. ` +
		`ونحن نتبرأ إلى الله من ذلك: ما هنا كلُّه وصفٌ بشريٌّ اجتهاديٌّ قابل للخطأ، موسومٌ بدرجته، لا إثباتَ إعجازٍ ولا تفسيرَ قرآنٍ على كلامنا. ` +
		`القرآنُ غنيٌّ عن أرقامنا، وإنما النورُ في التدبّر والعمل. ` +
		`فما وافق الحقَّ فمن الله وحده، وما خالفه فمن أنفسنا، ونستغفر الله.</div>`
	ctrl.innerHTML = `<button class="primary" id="inv-enter">فهمتُ وقرأت — ادخل</button>`
	$("#inv-enter").onclick = () => closeInvitation()
}

function invPlayVerse(n) {
	invStop()
	const arcv = D.arc.verses[n - 1]
	invDrawBreath(arcv, 0)
	invAudio = new Audio("../audio/00100" + n + ".mp3")
	const tick = () => {
		if (!invAudio) { return }
		const p = invAudio.duration ? invAudio.currentTime / invAudio.duration : 0
		invDrawBreath(arcv, p)
		invRaf = requestAnimationFrame(tick)
	}
	invAudio.addEventListener("ended", () => { const r = $("#inv-response"); if (r) { r.classList.add("show") } invStop() })
	invAudio.play().then(() => tick()).catch(() => { const r = $("#inv-response"); if (r) { r.classList.add("show") } })
}

function invDrawBreath(arcv, progress) {
	const canvas = $("#inv-breath")
	if (!canvas) { return }
	const env = (D.acoustics.verses[arcv.n - 1] || {}).envelope || []
	const cssW = canvas.parentElement.clientWidth || 540
	const dpr = window.devicePixelRatio || 1
	canvas.width = cssW * dpr
	canvas.height = 54 * dpr
	const ctx = canvas.getContext("2d")
	ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
	ctx.clearRect(0, 0, cssW, 54)
	if (!env.length) { return }
	const col = mixWarmth(arcv.warmth)
	ctx.beginPath()
	env.forEach((v, i) => {
		const x = (i / (env.length - 1)) * cssW
		const y = 52 - v * 46
		if (i === 0) { ctx.moveTo(x, y) } else { ctx.lineTo(x, y) }
	})
	ctx.strokeStyle = col
	ctx.lineWidth = 2
	ctx.stroke()
	if (progress > 0) {
		const px = progress * cssW
		ctx.beginPath()
		ctx.moveTo(px, 2)
		ctx.lineTo(px, 52)
		ctx.strokeStyle = "#fff"
		ctx.lineWidth = 1.5
		ctx.stroke()
	}
}

/* ---------- boot ---------- */
buildInvitation()
buildDialogue()
buildScenes()
buildScale()
buildExplorer()
buildDiscoveries()
buildSources()
buildTadabburShort()
buildSurahMap()
buildRing()
graphInit()
buildPhonetic()
buildAcoustic()
buildFramework()
buildObservatory()
drawRadar()
window.addEventListener("resize", () => {
	graphResize(); drawRadar(); drawBridge(); drawObsChart(); drawScale(); sizeSceneCanvas(); smResize()
	if ($("#layer-dialogue").classList.contains("visible")) { drawBreath(D.arc.verses[dlgIndex], 0) }
})
