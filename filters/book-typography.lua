-- filters/book-typography.lua
-- Custom Lua filter for book typographic enhancements (non-breaking spaces, math formatting)

function Str(el)
  -- Insert non-breaking space before cross-references like Chapter 1, Section 2, Figure 3, Eq. 4
  local text = el.text
  
  -- Replace Chapter X with Chapter~X in LaTeX
  if FORMAT:match("latex") then
    text = text:gsub("(Chapter)%s+(%d+)", "%1~%2")
    text = text:gsub("(Section)%s+(%d+)", "%1~%2")
    text = text:gsub("(Fig%.)%s+(%d+)", "%1~%2")
    text = text:gsub("(Figure)%s+(%d+)", "%1~%2")
    text = text:gsub("(Eq%.)%s+([%(%d])", "%1~%2")
    text = text:gsub("(Equation)%s+([%(%d])", "%1~%2")
  elseif FORMAT:match("html") or FORMAT:match("epub") then
    text = text:gsub("(Chapter)%s+(%d+)", "%1 %2")
    text = text:gsub("(Section)%s+(%d+)", "%1 %2")
    text = text:gsub("(Fig%.)%s+(%d+)", "%1 %2")
    text = text:gsub("(Figure)%s+(%d+)", "%1 %2")
    text = text:gsub("(Eq%.)%s+([%(%d])", "%1 %2")
    text = text:gsub("(Equation)%s+([%(%d])", "%1 %2")
  end

  el.text = text
  return el
end

return {
  { Str = Str }
}
