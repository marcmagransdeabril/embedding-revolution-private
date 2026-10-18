// styles/book.typ
// Typst template for standard book format (Springer 155x235mm / O'Reilly 7x9.1875in)

#let book(
  title: [The Embedding Revolution],
  subtitle: [Navigating High-Dimensional Knowledge Manifolds Through the Geek's Lens],
  author: [Marc Magrans de Abril],
  date: "2026",
  paper: "springer", // "springer" or "oreilly"
  body
) = {
  // Page setup based on paper format
  let (pwidth, pheight, margin_spec) = if paper == "oreilly" {
    (7in, 9.1875in, (inside: 0.85in, outside: 0.75in, top: 0.8in, bottom: 0.85in))
  } else {
    // Default Springer size (155mm x 235mm)
    (155mm, 235mm, (inside: 22mm, outside: 20mm, top: 24mm, bottom: 26mm))
  }

  set page(
    width: pwidth,
    height: pheight,
    margin: margin_spec,
    header: locate(loc => {
      let page_number = counter(page).at(loc).first()
      if page_number > 2 {
        let is_even = calc.even(page_number)
        if is_even {
          align(left)[#text(size: 9pt, fill: luma(100))[#page_number #h(1em) #title]]
        } else {
          align(right)[#text(size: 9pt, fill: luma(100))[#title #h(1em) #page_number]]
        }
      }
    }),
    footer: []
  )

  set text(
    font: ("Linux Libertine", "TeX Gyre Pagella", "Palatino", "Serif"),
    size: 10pt,
    lang: "en"
  )

  set par(
    justify: true,
    leading: 0.65em,
    first-line-indent: 1.5em
  )

  set heading(numbering: "1.1")
  show heading: it => {
    set text(fill: rgb(0, 51, 102), weight: "bold")
    block(below: 1em, above: 1.5em, it)
  }

  // Cover / Title Page
  align(center + horizon)[
    #text(size: 22pt, weight: "bold", fill: rgb(0, 51, 102))[#title]
    #v(0.8em)
    #text(size: 13pt, fill: rgb(60, 60, 60))[#subtitle]
    #v(2em)
    #text(size: 12pt, weight: "bold")[#author]
    #v(1em)
    #text(size: 10pt, fill: luma(120))[#date]
  ]

  pagebreak()

  body
}
