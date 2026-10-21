-- filters/book-questions.lua
--
-- Review questions with automatic numbering and bidirectional links to their
-- solutions (HTML, EPUB and PDF). Adapted from the little-book's
-- filters/custom-envs.lua so both books share the same markup and numbering.
--
-- Markup
--   In a chapter, at the end of a section:
--
--       ::: {.questions}
--       1. First question.
--
--       2. Second question.
--       :::
--
--   In chapters/solutions.qmd, ONE block per chapter, referencing the chapter
--   file stem (chapters/embedding_spaces.qmd -> ref="embedding_spaces"):
--
--       ::: {.answers ref="embedding_spaces"}
--       1. First solution.
--
--       2. Second solution.
--       :::
--
-- Numbering
--   The N-th numbered chapter of `_quarto.yml` (in book order, skipping
--   index.qmd and any file whose first heading is `{.unnumbered}`) is chapter N.
--   Questions of a chapter are numbered N.1, N.2, ... cumulatively across all
--   of its `.questions` blocks; the i-th item of a `.answers` block is the
--   solution to question N.i of the chapter given by `ref`.
--
-- Anchors
--   question N.i of chapter <stem> -> id  q-<stem>-i  (links to sol-<stem>-i)
--   solution N.i of chapter <stem> -> id  sol-<stem>-i (links to q-<stem>-i)
--
-- How the current chapter is found
--   * HTML renders every file in its own pandoc run: the chapter is identified
--     by the input file name.
--   * PDF and EPUB render one merged document: the chapter is recognised by
--     the text of its level-1 heading (Quarto also emits Part titles as
--     level-1 headings, so counting headings would be wrong).

local SOLUTIONS_FILE = "solutions"   -- stem of chapters/solutions.qmd
local CHAPTER_DIR_HTML = ""          -- chapters and solutions live in the same dir

local function is_latex() return FORMAT:match("latex") ~= nil end
local function is_html()  return FORMAT:match("html") ~= nil end

-- Chapter registry (filled from _quarto.yml) ---------------------------------

local chapter_num = {}     -- stem -> chapter number
local chapter_title = {}   -- stem -> chapter title
local title_to_stem = {}    -- normalized chapter title -> stem

local fixed_chapter = false  -- true when the file name identifies the chapter
local current_chapter = nil  -- stem of the chapter being walked

local q_count, s_count = {}, {}

local function bump(tbl, key)
  tbl[key] = (tbl[key] or 0) + 1
  return tbl[key]
end

local function normalize(text)
  return (text:lower():gsub("[^%w]", ""))
end

local function read_file(path)
  local f = io.open(path, "r")
  if not f then return nil end
  local content = f:read("*a")
  f:close()
  return content
end

local function project_dir()
  if quarto and quarto.project and quarto.project.directory then
    return quarto.project.directory
  end
  local input = quarto and quarto.doc and quarto.doc.input_file
  if input then
    return (input:gsub("/chapters/[^/]*$", ""):gsub("/[^/]*%.qmd$", ""))
  end
  return "."
end

local function stem_of(path)
  return (path:match("([^/]+)%.qmd$"))
end

-- Returns numbered?, title for a chapter source file.
local function inspect_chapter(path)
  local text = read_file(path)
  if not text then return false, nil end
  local title = nil
  local front = text:match("^%-%-%-\n(.-)\n%-%-%-")
  if front then
    title = ("\n" .. front):match("\ntitle:%s*[\"']?(.-)[\"']?%s*\n")
      or ("\n" .. front .. "\n"):match("\ntitle:%s*[\"']?(.-)[\"']?%s*\n")
  end
  local unnumbered = false
  local in_fence = false
  for line in text:gmatch("[^\n]+") do
    if line:match("^```") then in_fence = not in_fence end
    if not in_fence then
      local h = line:match("^# (.*)$")
      if h then
        unnumbered = h:match("{[^}]*%.unnumbered[^}]*}") ~= nil or h:match("{%-}") ~= nil
        title = title or h:gsub("%s*{.*}%s*$", "")
        break
      end
    end
  end
  return not unnumbered, title
end

local function load_registry()
  local root = project_dir()
  local yml = read_file(root .. "/_quarto.yml")
  if not yml then return end
  local n = 0
  for line in yml:gmatch("[^\n]+") do
    local path = line:match("^%s*%-%s+([%w_%-%./]+%.qmd)%s*$")
    if path and stem_of(path) ~= "index" then
      local numbered, title = inspect_chapter(root .. "/" .. path)
      if numbered then
        n = n + 1
        local stem = stem_of(path)
        chapter_num[stem] = n
        chapter_title[stem] = title or stem
        title_to_stem[normalize(title or stem)] = stem
      end
    end
  end
end

local function init(doc)
  load_registry()
  if is_html() and quarto and quarto.doc and quarto.doc.input_file then
    local stem = stem_of(quarto.doc.input_file)
    if stem and chapter_num[stem] then
      fixed_chapter = true
      current_chapter = stem
    end
  end
  return nil
end

-- Track the current chapter in merged (PDF / EPUB) documents. Quarto also
-- emits Part titles as level-1 headings, so chapters are recognised by their
-- title (taken from each chapter's source file) instead of by counting.
local function Header(el)
  if el.level == 1 and not fixed_chapter then
    current_chapter = title_to_stem[normalize(pandoc.utils.stringify(el.content))]
  end
  return nil
end

-- Link targets ---------------------------------------------------------------

-- In multi-page HTML, questions and solutions live in different pages, so
-- the link needs the target file; PDF and EPUB resolve a bare anchor.
local function href_to(stem, anchor)
  if is_html() then
    return CHAPTER_DIR_HTML .. stem .. ".html#" .. anchor
  end
  return "#" .. anchor
end

local function qid(stem, n) return "q-" .. stem .. "-" .. n end
local function sid(stem, n) return "sol-" .. stem .. "-" .. n end

-- LaTeX item builders --------------------------------------------------------

local function latex_question_item(item_blocks, q, s, label)
  local out = pandoc.List()
  out:insert(pandoc.RawBlock("latex", string.format(
    "\\hypertarget{%s}{}\\item[\\textbf{\\protect\\hyperlink{%s}{%s}}]",
    q, s, label)))
  for _, b in ipairs(item_blocks) do out:insert(b) end
  return out
end

local function latex_solution_item(item_blocks, q, s, label)
  local out = pandoc.List()
  local prefix = string.format(
    "\\hypertarget{%s}{}\\textbf{\\protect\\hyperlink{%s}{%s}} ", s, q, label)
  local first = item_blocks[1]
  if first and (first.t == "Para" or first.t == "Plain") then
    local inlines = pandoc.List({ pandoc.RawInline("latex", prefix) })
    inlines:extend(first.content)
    out:insert(first.t == "Para" and pandoc.Para(inlines) or pandoc.Plain(inlines))
    for i = 2, #item_blocks do out:insert(item_blocks[i]) end
  else
    out:insert(pandoc.RawBlock("latex", prefix))
    for _, b in ipairs(item_blocks) do out:insert(b) end
  end
  return out
end

-- HTML / EPUB item builder ---------------------------------------------------

local function html_item(item_blocks, anchor_id, target_href, label, css_class)
  local link = pandoc.Link({ pandoc.Strong({ pandoc.Str(label) }) }, target_href)
  link.classes:insert(css_class .. "-num")

  local first = item_blocks[1]
  local rest = {}
  for i = 2, #item_blocks do rest[#rest + 1] = item_blocks[i] end

  local new_first
  if first and (first.t == "Para" or first.t == "Plain") then
    local inlines = pandoc.List({ link, pandoc.Space() })
    inlines:extend(first.content)
    new_first = first.t == "Para" and pandoc.Para(inlines) or pandoc.Plain(inlines)
  else
    new_first = pandoc.Para({ link })
    if first then table.insert(rest, 1, first) end
  end

  local content = pandoc.List({ new_first })
  content:extend(rest)
  return pandoc.Div(content, pandoc.Attr(anchor_id, { css_class }))
end

-- Block handlers -------------------------------------------------------------

local function handle_questions(el)
  local stem = current_chapter
  local chap_n = stem and chapter_num[stem]
  if not chap_n then
    io.stderr:write("WARNING [book-questions]: .questions block outside a numbered chapter; not numbered\n")
    if is_latex() then
      local out = pandoc.List({ pandoc.RawBlock("latex", "\\begin{questions}") })
      out:extend(el.content)
      out:insert(pandoc.RawBlock("latex", "\\end{questions}"))
      return out
    end
    return el
  end

  if is_latex() then
    local out = pandoc.List({ pandoc.RawBlock("latex", "\\begin{questions}") })
    for _, block in ipairs(el.content) do
      if block.t == "OrderedList" then
        out:insert(pandoc.RawBlock("latex", "\\begin{enumerate}\\tightlist"))
        for _, item in ipairs(block.content) do
          local num = bump(q_count, stem)
          local label = chap_n .. "." .. num .. "."
          out:extend(latex_question_item(item, qid(stem, num), sid(stem, num), label))
        end
        out:insert(pandoc.RawBlock("latex", "\\end{enumerate}"))
      else
        out:insert(block)
      end
    end
    out:insert(pandoc.RawBlock("latex", "\\end{questions}"))
    return out
  end

  local new_content = pandoc.List()
  for _, block in ipairs(el.content) do
    if block.t == "OrderedList" then
      for _, item in ipairs(block.content) do
        local num = bump(q_count, stem)
        local label = chap_n .. "." .. num .. "."
        new_content:insert(html_item(item, qid(stem, num),
          href_to(SOLUTIONS_FILE, sid(stem, num)), label, "question"))
      end
    else
      new_content:insert(block)
    end
  end
  return pandoc.Div(new_content, el.attr)
end

local function handle_solution(el)
  local stem = el.attributes["ref"]
  if not stem or not chapter_num[stem] then
    error("[book-questions] .answers block has missing or unknown ref=\""
      .. tostring(stem) .. "\" (expected a numbered chapter file stem)")
  end
  local chap_n = chapter_num[stem]

  -- Automatic heading: "Chapter N. <title>", unnumbered.
  local heading = pandoc.Header(2,
    -- NBSP (U+00A0) keeps "Chapter N." together without tripping the
    -- "Chapter N" -> "Chapter~N" rewrite of book-typography.lua.
    { pandoc.Str("Chapter\u{00A0}" .. chap_n .. "."), pandoc.Space(),
      pandoc.Str(chapter_title[stem]) },
    pandoc.Attr("solutions-" .. stem, { "unnumbered" }))

  local out = pandoc.List({ heading })

  if is_latex() then
    for _, block in ipairs(el.content) do
      if block.t == "OrderedList" then
        for _, item in ipairs(block.content) do
          local num = bump(s_count, stem)
          local label = chap_n .. "." .. num .. "."
          out:extend(latex_solution_item(item, qid(stem, num), sid(stem, num), label))
        end
      else
        out:insert(block)
      end
    end
    return out
  end

  local new_content = pandoc.List()
  for _, block in ipairs(el.content) do
    if block.t == "OrderedList" then
      for _, item in ipairs(block.content) do
        local num = bump(s_count, stem)
        local label = chap_n .. "." .. num .. "."
        new_content:insert(html_item(item, sid(stem, num),
          href_to(stem, qid(stem, num)), label, "answer"))
      end
    else
      new_content:insert(block)
    end
  end
  out:insert(pandoc.Div(new_content, pandoc.Attr("", { "answer-list" })))
  return out
end

local function Div(el)
  if el.classes:includes("questions") then return handle_questions(el) end
  if el.classes:includes("answers") then
    -- Only authored blocks carry this class (generated items use `answer`).
    return handle_solution(el)
  end
  return nil
end

return {
  { Pandoc = init },
  { traverse = "topdown", Header = Header, Div = Div },
}
