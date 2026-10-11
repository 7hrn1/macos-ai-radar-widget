-- AI Radar push-to-talk: hold ⌥ Space, speak, release.
hs.autoLaunch(true)
local radar = os.getenv("HOME") .. "/.local/bin/radar"
local function run(args)
  hs.task.new(radar, function(code, out, err)
    if code ~= 0 then hs.alert.show("radar error: " .. tostring(err):sub(1, 100), 4) end
  end, args):start()
end
hs.hotkey.bind({"alt"}, "space",
  function() hs.alert.closeAll(); hs.alert.show("🎙  Listening…", {textSize = 22}, hs.screen.mainScreen(), 60); run({"voice", "start"}) end,
  function() hs.alert.closeAll(); hs.alert.show("⏳  Thinking…", {textSize = 22}, hs.screen.mainScreen(), 3); run({"voice", "stop"}) end)
hs.alert.show("AI Radar voice ready — hold ⌥ Space", 2)
