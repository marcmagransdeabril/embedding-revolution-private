-- filters/book-callouts.lua
-- Custom Lua filter for book callout styling across LaTeX and HTML targets

local function is_latex()
  return FORMAT:match("latex") ~= nil
end

local function is_html_or_epub()
  return FORMAT:match("html") ~= nil or FORMAT:match("epub") ~= nil
end

function Div(el)
  -- Test of likeness: framed question (see styles); HTML keeps the div class
  if el.classes:includes("test") and is_latex() then
    local out = pandoc.List({ pandoc.RawBlock("latex", "\\begin{liketest}") })
    out:extend(el.content)
    out:insert(pandoc.RawBlock("latex", "\\end{liketest}"))
    return out
  end

  -- Check if div is a callout
  local callout_type = nil
  for _, class in ipairs(el.classes) do
    if class:match("^callout%-") then
      callout_type = class:gsub("^callout%-", "")
      break
    end
  end

  if not callout_type then
    return el
  end

  -- Detect Geek's Epiphany / Geek's Lens custom box
  local is_geek_box = false
  for _, class in ipairs(el.classes) do
    if class == "geek-epiphany" or class == "geek-lens" then
      is_geek_box = true
      break
    end
  end

  if is_html_or_epub() and is_geek_box then
    table.insert(el.classes, "callout-geek-epiphany")
  end

  return el
end

return {
  { Div = Div }
}
