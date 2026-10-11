-- AI Radar push-to-talk: hold ⌥ Space, speak, release.
-- A small HUD above the Dock shows every stage: Listening → Transcribing → Heard "…" → Working → the reply.
hs.autoLaunch(true)
local radar = os.getenv("HOME") .. "/.local/bin/radar"

------------------------------------------------------------------ HUD
local hud, hideTimer, dotsTimer
local COLORS = {
  listen = { red = 0.38, green = 0.64, blue = 1.00 }, busy = { red = 0.65, green = 0.55, blue = 0.98 },
  ok = { red = 0.20, green = 0.83, blue = 0.60 }, err = { red = 0.97, green = 0.44, blue = 0.44 },
}

local function hide()
  if hideTimer then hideTimer:stop(); hideTimer = nil end
  if dotsTimer then dotsTimer:stop(); dotsTimer = nil end
  if hud then hud:delete(0.15); hud = nil end
end

-- show(kind, title, body, ttl, animate): replaces whatever is showing. ttl = seconds until it disappears (nil = stays).
local function show(kind, title, body, ttl, animate, extra)
  hide()
  body = body or ""
  extra = extra or ""
  local f = hs.screen.mainScreen():frame()
  local w = math.min(660, f.w - 80)
  local lines = math.max(1, math.ceil(#body / 62)) + select(2, body:gsub("\n", ""))
  local h = 58 + (body ~= "" and (lines * 21 + 4) or 0) + (extra ~= "" and 24 or 0)
  hud = hs.canvas.new({ x = f.x + (f.w - w) / 2, y = f.y + f.h - h - 28, w = w, h = h })
  hud:level(hs.canvas.windowLevels.overlay)
  hud:behavior({ "canJoinAllSpaces", "stationary" })
  local c = COLORS[kind] or COLORS.busy
  hud:appendElements(
    { type = "rectangle", action = "fill", roundedRectRadii = { xRadius = 18, yRadius = 18 }, fillColor = { red = 0.05, green = 0.07, blue = 0.10, alpha = 0.96 },
      strokeColor = { red = 1, green = 1, blue = 1, alpha = 0.10 }, strokeWidth = 1, withShadow = true,
      shadow = { blurRadius = 24, offset = { h = -8, w = 0 }, color = { alpha = 0.5 } } },
    { type = "rectangle", action = "fill", frame = { x = 16, y = 16, w = 4, h = h - 32 }, roundedRectRadii = { xRadius = 2, yRadius = 2 }, fillColor = c },
    { type = "text", text = title, textFont = ".AppleSystemUIFontBold", textSize = 16, textColor = c, frame = { x = 34, y = 14, w = w - 60, h = 24 } },
    { type = "text", text = body, textFont = ".AppleSystemUIFont", textSize = 15, textColor = { white = 0.93 }, frame = { x = 34, y = 40, w = w - 56, h = h - 46 }, textLineBreak = "wordWrap" },
    { type = "text", text = extra, textFont = ".AppleSystemUIFont", textSize = 12.5, textColor = { white = 0.62 }, frame = { x = 34, y = h - 34, w = w - 56, h = 20 } }
  )
  pcall(function() hud:canvasMouseEvents(true, false, false, false); hud:mouseCallback(function() hide() end) end)   -- click to dismiss
  hud:show(0.12)
  if animate then
    local n = 0
    dotsTimer = hs.timer.doEvery(0.4, function()
      n = (n % 3) + 1
      if hud then hud[3].text = title:gsub("…$", "") .. string.rep(".", n) end
    end)
  end
  if ttl then hideTimer = hs.timer.doAfter(ttl, hide) end
end

------------------------------------------------------------------ talking to the `radar` CLI (--ui prints "@stage<TAB>text<TAB>extra" lines)
local function handle(line)
  local stage, text, extra = line:match("^@(%w+)\t([^\t]*)\t?(.*)$")
  if not stage then return end
  if stage == "transcribing" then show("busy", "Transcribing…", nil, 30, true)
  elseif stage == "heard" then show("busy", "Working…", "“" .. text .. "”", 60, true)
  elseif stage == "working" then show("busy", "Working…", (hud and "" or "") .. text, 60, true)
  elseif stage == "reply" then
    show("ok", "✓ Done", text, math.max(5, math.min(14, 3 + (#text + #(extra or "")) * 0.06)), false, extra)
  elseif stage == "done" then hide()
  elseif stage == "error" then show("err", "Couldn't do that", text, 7) end
end

local function run(args, onExit)
  local buf, gotReply = "", false
  local t = hs.task.new(radar, function(code, _, err)
    if onExit then onExit(code, err, gotReply) end
  end, function(_, out)
    buf = buf .. (out or "")
    while true do
      local line, rest = buf:match("^(.-)\n(.*)$")
      if not line then break end
      buf = rest
      if line:match("^@reply") or line:match("^@error") then gotReply = true end
      handle(line)
    end
    return true
  end, args)
  t:start()
end

hs.hotkey.bind({ "alt" }, "space",
  function()
    show("listen", "🎙  Listening…", "Release ⌥ Space when you're done", 60)
    run({ "--ui", "voice", "start" })
  end,
  function()
    show("busy", "Transcribing…", nil, 30, true)
    run({ "--ui", "voice", "stop" }, function(code, err, gotReply)
      if code ~= 0 then show("err", "radar error", tostring(err or ""):sub(1, 240), 8)
      elseif not gotReply then hide() end
    end)
  end)

hs.alert.show("AI Radar voice ready — hold ⌥ Space", 2)

-- exported so the HUD can be driven/tested from the Hammerspoon console (`hs -c`)
return { handle = handle, show = show, hide = hide, run = run, current = function() return hud end }
