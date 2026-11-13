--- Lua filter: swap .pdf image paths to .png for non-PDF output formats.
--- For LaTeX/PDF: keeps .pdf paths (vector quality via \includegraphics).
--- For HTML/EPUB: rewrites .pdf to .png (rasterized at 300 DPI by the Makefile).

function Image(el)
  if not (FORMAT:match("latex") or FORMAT:match("pdf")) then
    el.src = el.src:gsub("%.pdf$", ".png")
  end
  return el
end
