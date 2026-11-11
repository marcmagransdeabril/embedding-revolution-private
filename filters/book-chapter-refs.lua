-- Chapter references in the HTML book (workaround for quarto-dev/quarto-cli#14132, open, milestone 1.12).
-- Quarto renders @sec-ch-<stem> as "3 Title" instead of "Chapter 3" in HTML pages that have no chapter number
-- (index, epilogue, solutions), and ignores [-@sec-ch-<stem>] there. So in HTML every chapter reference is resolved
-- here, in all pages: @sec-ch-<stem> gives "Chapter N", [-@sec-ch-<stem>] gives "N" (for "Chapters [-@a] to [-@b]").
-- PDF and EPUB are left to Quarto, which renders both forms correctly in every page.
-- N is the position of the chapter among the numbered files of _quarto.yml (a file is numbered unless its first
-- level-1 heading has the class .unnumbered). The label of a chapter is "sec-ch-" .. file stem with "_" as "-".
-- An unknown label stops the build.
if not FORMAT:match("html") then return {} end

-- Quarto replaces the global `error` by a function that logs and returns, so a failure must stop the build explicitly.
local function fail(message)
  io.stderr:write("ERROR book-chapter-refs: " .. message .. "\n")
  os.exit(1)
end

local function read(path)
  local f = io.open(path, "r")
  if not f then return nil end
  local s = f:read("a"); f:close(); return s
end

-- Quarto runs the filter in the directory of the page: the project root for index.qmd, chapters/ for the others.
local root = read("_quarto.yml") and "" or (read("../_quarto.yml") and "../" or fail("_quarto.yml not found"))

local function chapter_numbers()
  local cfg = read(root .. "_quarto.yml")
  local nums, n = {}, 0
  for stem in cfg:gmatch("chapters/([%w_]+)%.qmd") do
    local src = read(root .. "chapters/" .. stem .. ".qmd") or fail("missing chapters/" .. stem .. ".qmd (listed in _quarto.yml)")
    local h1 = src:match("\n# [^\n]*") or src:match("^# [^\n]*") or ""
    if not h1:find("{[^}]*%.unnumbered") then
      n = n + 1
      nums["sec-ch-" .. stem:gsub("_", "-")] = { n = n, stem = stem }
    end
  end
  return nums
end

local nums = chapter_numbers()
local prefix = (root == "") and "chapters/" or ""

function Cite(c)
  local cit = c.citations[1]
  if not cit.id:match("^sec%-ch%-") then return nil end
  if #c.citations ~= 1 or #cit.prefix > 0 or #cit.suffix > 0 then
    fail("write a chapter reference alone, as @" .. cit.id .. " or [-@" .. cit.id .. "], not with a prefix, a suffix or other citations")
  end
  local t = nums[cit.id] or fail("no numbered chapter for @" .. cit.id .. " (labels are sec-ch- plus the file stem with - for _)")
  local text = (cit.mode == "SuppressAuthor") and tostring(t.n) or ("Chapter " .. t.n)
  return pandoc.Link(text, prefix .. t.stem .. ".qmd#" .. cit.id)
end
