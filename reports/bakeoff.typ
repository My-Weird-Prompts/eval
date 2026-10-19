// Bakeoff reading copy: run → prompt → model → script.
// Data: a JSON file written by scripts/build_bakeoff_pdf.py (passed via --input data=...).
// Footer on every page: run, model, page number.

#let data = json(sys.inputs.at("data", default: "bakeoff-2026-10-19.json"))

#let navy = rgb("#0f172a")
#let indigo = rgb("#4f46e5")
#let gray = rgb("#60739f")
#let gray-light = rgb("#e5e9f0")
#let ink = rgb("#1f2433")

#set document(title: data.title + " — " + data.date, author: "My Weird Prompts")
#set text(font: "Libertinus Serif", size: 12pt, fill: ink, lang: "en")
#set par(leading: 0.78em, spacing: 0.95em, justify: false)

#let section-marker(run, model) = [#metadata((run: run, model: model)) <sec>]

#set page(
  paper: "a4",
  margin: (x: 2.3cm, top: 2.2cm, bottom: 2.6cm),
  footer: context {
    let secs = query(selector(<sec>).before(here()))
    let label = if secs.len() == 0 { "Contents" } else {
      let v = secs.last().value
      if v.run == 0 { v.model } else { "Run " + str(v.run) + "  ·  " + v.model }
    }
    set text(font: "Inter", size: 8.5pt, fill: gray)
    line(length: 100%, stroke: 0.5pt + gray-light)
    v(3pt)
    grid(columns: (1fr, auto),
      align(left)[#label],
      align(right)[#counter(page).display() / #counter(page).final().first()])
  },
)

#show heading: set text(font: "Inter", fill: navy)
#show heading.where(level: 1): it => { set text(size: 24pt, weight: "bold"); it; v(4pt) }
#show heading.where(level: 2): it => { set text(size: 17pt, weight: "bold"); it; v(2pt) }

// One paragraph per turn; speaker label as a small uppercase tag.
#let render(script) = {
  for raw-line in script.split("\n") {
    let t = raw-line.trim()
    if t == "" { continue }
    let m = t.match(regex("^([A-Z][A-Za-z .'-]{0,30}):\s*(.*)$"))
    if m != none {
      par[#box(text(font: "Inter", size: 8.5pt, weight: "bold", fill: indigo, tracking: 0.06em)[#upper(m.captures.at(0))]) #h(0.35em) #m.captures.at(1)]
    } else {
      par[#t]
    }
  }
}

// ---- Cover ---------------------------------------------------------------
#section-marker(0, "About this booklet")
#v(2.5cm)
#text(font: "Inter", size: 11pt, fill: indigo, weight: "bold", tracking: 0.08em)[MY WEIRD PROMPTS · SCRIPT WRITER BAKEOFF]
#v(6pt)
#text(font: "Inter", size: 30pt, weight: "bold", fill: navy)[Five writers, three prompts]
#v(4pt)
#text(font: "Inter", size: 13pt, fill: gray)[#data.date · #data.runs.len() runs · #data.runs.first().entries.len() models per run]
#v(1.2cm)

Each run is one real listener prompt from the show. Every model wrote a full episode script from the same prompt and the same instructions: about 3,800 words of dialogue between Corn and Herman. Models appear in the same order in every run. Each script starts on a new page, and the footer names the run and the model.

#v(0.6cm)
#text(font: "Inter", size: 10pt, weight: "bold", fill: navy)[CONTENTS]
#v(2pt)
#set text(font: "Inter", size: 10pt)
#for r in data.runs [
  *Run #r.run* — #r.prompt.slice(0, calc.min(90, r.prompt.len())).trim()… \
  #for e in r.entries [
    #h(1.2em) #e.model #h(0.4em) #text(fill: gray)[(#e.words words)] \
  ]
  #v(4pt)
]
#set text(font: "Libertinus Serif", size: 12pt)

// ---- Runs ----------------------------------------------------------------
#for r in data.runs {
  pagebreak()
  section-marker(r.run, "Prompt")
  heading(level: 1)[Run #r.run]
  text(font: "Inter", size: 10pt, fill: gray)[The prompt as the show received it]
  v(10pt)
  block(fill: rgb("#f1f5f9"), inset: 14pt, radius: 6pt, width: 100%)[
    #for p in r.prompt.split("\n") { if p.trim() != "" { par[#p.trim()] } }
  ]
  for e in r.entries {
    pagebreak()
    section-marker(r.run, e.model)
    heading(level: 2)[#e.model]
    text(font: "Inter", size: 9.5pt, fill: gray)[Run #r.run · #e.words words]
    v(8pt)
    render(e.script)
  }
}

// ---- Appendix: what the AI judge thought (read after, not before) ---------
#pagebreak()
#section-marker(0, "Appendix: judge scores")
#heading(level: 1)[Appendix: judge scores]
#text(font: "Inter", size: 10pt, fill: gray)[Claude Opus 5.5 as judge, 1–5 per axis. Read these after the scripts, so they don't steer you.]
#v(8pt)
#set text(font: "Inter", size: 9.5pt)
#table(
  columns: (auto, 1fr, auto, auto, auto, auto, auto),
  stroke: 0.5pt + gray-light, inset: 6pt,
  table.header([*Run*], [*Model*], [*Holds the middle*], [*Fun*], [*Candour*], [*Liveness*], [*Words*]),
  ..data.runs.map(r => r.entries.map(e => (
    str(r.run), e.model,
    str(calc.round(e.scores.long_form_coherence, digits: 1)), str(calc.round(e.scores.fun, digits: 1)),
    str(calc.round(e.scores.candour, digits: 1)), str(calc.round(e.scores.liveness, digits: 1)), str(e.words),
  ))).flatten().flatten(),
)
