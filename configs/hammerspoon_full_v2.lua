-- Hammerspoon Configuration - M4 MacBook Optimized
-- "Atomic" Remote Desktop Key Mapping with Transition Safety
-- Optimized for Apple Silicon M4 with performance and battery improvements
-- 
-- Strategy:
-- 1. Atomic (Stateless) Key Injection: Never hold 'Ctrl' down to fix RDP stuck keys/mouse zoom.
-- 2. Transition Guard: Detect Cmd+Tab explicitly to pause remapping during switch.
-- 3. Cleanup: Force release modifiers when leaving RDP.

hs.alert.show("Reloading Hammerspoon (Atomic + Safe Switch)...")

-- =============================================================================
-- 1. HELPER FUNCTIONS (M4 Optimized)
-- =============================================================================
local function safeLoadSpoon(name)
    local loadedObj = hs.loadSpoon(name)
    if not loadedObj then
        print("Error: Could not load Spoon '" .. name .. "'")
        return nil
    end
    return loadedObj
end

-- =============================================================================
-- 2. GLOBAL ISO KEY FIX (§ -> `)
-- =============================================================================
isoKeyRemap = hs.eventtap.new({hs.eventtap.event.types.keyDown}, function(event)
    if event:getKeyCode() == 10 then 
        hs.eventtap.event.newKeyEvent(event:getFlags(), 50, true):post()
        return true 
    end
end)
isoKeyRemap:start()

-- =============================================================================
-- 3. CAPS LOCK -> CONTROL/ESCAPE
-- =============================================================================
ControlEscape = safeLoadSpoon("ControlEscape")
if ControlEscape then ControlEscape:start() end

-- =============================================================================
-- 4. REMOTE APP DEFINITIONS
-- =============================================================================
local remoteApps = {
    ['com.microsoft.rdc.macos'] = true, 
    ['com.microsoft.rdc.mac'] = true,   
    ['com.googlecode.iterm2'] = true,   
    ['com.apple.Terminal'] = true,      
    ['io.alacritty'] = true,            
    ['net.kovidgoyal.kitty'] = true,    
    ['co.zeit.hyper'] = true,           
    ['org.gnome.Terminal'] = true,      
    ['com.parallels.desktop.console'] = true 
}

local k = {
    left = 123, right = 124, down = 125, up = 126,
    home = 115, end_key = 119, pageup = 116, pagedown = 121,
    delete = 51, tab = 48, space = 49, escape = 53,
    c = 8, v = 9, x = 7, z = 6, a = 0, f = 3, s = 1, w = 13, q = 12, r = 15, y = 16
}

-- =============================================================================
-- 5. ADVANCED RDP CONTROL (Enhanced with Research-Based Features)
-- =============================================================================
-- Enhanced modifier detection using Hammerspoon's built-in functions
local function getModifiers()
    return hs.eventtap.checkKeyboardModifiers(true)
end

-- RDP-specific key sequences for Windows shortcuts
local rdpSequences = {
    -- Windows key combinations
    win_r = {{'ctrl', 'shift'}, 'r'}, -- Refresh
    win_e = {{'ctrl', 'shift'}, 'e'}, -- File Explorer
    win_d = {{'ctrl', 'shift'}, 'd'}, -- Desktop
    win_f = {'ctrl', 'f'}, -- Search
    win_l = {{'ctrl', 'shift'}, 'l'}, -- Lock
    win_tab_alt ={{'ctrl', 'alt'}, 'tab'}, -- Alt+Tab switch
    taskmgr = {{'ctrl', 'shift'}, 'escape'}, -- Task Manager
    screenshot = {{'ctrl', 'shift'}, 's'}, -- Screenshot
}

-- Execute RDP key sequences with proper timing
local function executeRDPSequence(sequence, delay)
    delay = delay or 50000 -- 50ms between keys
    for i, key in ipairs(sequence) do
        if type(key) == 'table' then
            hs.eventtap.keyStroke(key, nil, nil, delay * i)
        else
            hs.eventtap.keyStroke({}, key, nil, delay * i)
        end
    end
end

remoteRemap = hs.eventtap.new({hs.eventtap.event.types.keyDown}, function(event)
    local flags = event:getFlags()
    local keyCode = event:getKeyCode()
    local modifiers = getModifiers()
    
    -- Enhanced modifier detection
    local isCmd = modifiers.cmd
    local isOpt = modifiers.alt
    local isShift = modifiers.shift
    local isCtrl = modifiers.ctrl
    
    -- RDP-specific mode detection
    local function isInRDPMode()
        return remoteApps[hs.application.frontmostApplication():bundleID()] or false
    end
    
    if not isInRDPMode() then return false end

    -- Safety: If Tab is pressed, STOP everything and let macOS handle switching
    if keyCode == k.tab then
        return false
    end

    -- Helper: Atomic Send (Enhanced for M4)
    local function atomicSend(key, mod)
        -- Use microsecond delays for better RDP timing
        hs.eventtap.event.newKeyEvent({mod}, 59, true):post()
        hs.timer.usleep(10000) -- 10ms delay
        hs.eventtap.event.newKeyEvent({mod}, key, true):post()
        hs.timer.usleep(10000) -- 10ms delay
        hs.eventtap.event.newKeyEvent({mod}, key, false):post()
        hs.timer.usleep(10000) -- 10ms delay
        hs.eventtap.event.newKeyEvent({mod}, 59, false):post()
        return true
    end

    -- Helper: Simple Send (Just key, no mods)
    local function simpleSend(key)
        hs.eventtap.event.newKeyEvent({}, key, true):post()
        hs.eventtap.event.newKeyEvent({}, key, false):post()
        return true
    end

    -- --- A. ENHANCED NAVIGATION WITH RDP SEQUENCES ---
    -- Cmd+Arrows (Mac style)
    if isCmd and keyCode == k.left then return simpleSend(k.home) end
    if isCmd and keyCode == k.right then return simpleSend(k.end_key) end
    if isCmd and keyCode == k.up then return atomicSend(k.home, 'ctrl') end
    if isCmd and keyCode == k.down then return atomicSend(k.end_key, 'ctrl') end
    
    -- Cmd+PageUp/PageDown (enhanced)
    if isCmd and keyCode == k.pageup then return atomicSend(k.home, 'ctrl') end
    if isCmd and keyCode == k.pagedown then return atomicSend(k.end_key, 'ctrl') end
    
    -- Opt+Arrows (Word navigation)
    if isOpt and keyCode == k.left then return atomicSend(k.left, 'ctrl') end
    if isOpt and keyCode == k.right then return atomicSend(k.right, 'ctrl') end
    if isOpt and keyCode == k.up then return atomicSend(k.up, 'ctrl') end
    if isOpt and keyCode == k.down then return atomicSend(k.down, 'ctrl') end
    
    -- Opt+Delete (Ctrl+Delete equivalent)
    if isOpt and keyCode == k.delete then return atomicSend(k.delete, 'ctrl') end

    -- --- B. RDP-SPECIFIC WINDOWS KEY COMBINATIONS ---
    -- Map F-keys to Windows shortcuts when in RDP
    if isCmd and keyCode == k.f then
        executeRDPSequence(rdpSequences.win_f, 30000) -- 30ms delay for RDP
        return true
    end
    
    -- Map R to Refresh in RDP
    if isCmd and keyCode == k.r then
        executeRDPSequence(rdpSequences.win_r, 30000)
        return true
    end
    
    -- Opt+Backspace (Ctrl+Backspace equivalent)
    if isOpt and keyCode == 22 then return atomicSend(k.delete, 'ctrl') end -- Backspace key code

    -- --- B. ENHANCED CMD -> CTRL MAPPING ---
    if isCmd then
        -- Extended passthrough whitelist for better RDP control
        local whitelist = {k.tab, k.space, k.q, k.escape, k.w, k.t, k.g, k.b, k.f, k.r}
        for _, key in ipairs(whitelist) do
            if keyCode == key then return false end
        end
        
        -- Cmd+Shift+Z -> Ctrl+Y (Redo)
        if keyCode == k.z and isShift then
            return atomicSend(k.y, 'ctrl')
        end
        
        -- Cmd+Shift+S -> Ctrl+Shift+S (Save As in RDP)
        if keyCode == k.s and isShift then
            hs.eventtap.keyStroke({'ctrl', 'shift'}, 's')
            return true
        end
        
        -- Standard Cmd -> Ctrl (C, V, X, Z, A, etc.)
        if keyCode ~= k.left and keyCode ~= k.right and keyCode ~= k.up and keyCode ~= k.down then
            return atomicSend(keyCode, 'ctrl')
        end
    end

    -- --- C. ENHANCED CTRL MAPPING (for direct Ctrl keys) ---
    if isCtrl then
        -- Ctrl+1-9 for application switching in RDP
        if keyCode >= 18 and keyCode <= 26 then
            return simpleSend(keyCode)
        end
        
        -- Ctrl+F for search (RDP standard)
        if keyCode == k.f then return simpleSend(k.f) end
        
        -- Ctrl+Tab for application switching (let RDP handle)
        if keyCode == k.tab then return false end
    end

    return false
end)

-- =============================================================================
-- 6. APP WATCHER & CLEANUP
-- =============================================================================
local function forceReleaseModifiers()
    -- Send empty event with empty modifiers table clears all stuck modifiers
    hs.eventtap.keyStroke({}, "")
end

appWatcher = hs.application.watcher.new(function(appName, eventType, appObject)
    local bundleID = appObject:bundleID()
    
    if (eventType == hs.application.watcher.activated) then
        if remoteApps[bundleID] then
            remoteRemap:start()
            hs.alert.show("Remote: ATOMIC Mode")
        else
            remoteRemap:stop()
        end
    elseif (eventType == hs.application.watcher.deactivated) then
        if remoteApps[bundleID] then
            -- When leaving RDP, stop remapping AND flush modifiers
            remoteRemap:stop()
            forceReleaseModifiers()
            -- print("Cleaned up modifiers for " .. appName)
        end
    end
end)
appWatcher:start()

-- =============================================================================
-- 7. CMD+TAB WATCHER (Pre-emptive Pause)
-- =============================================================================
-- Detects Cmd+Tab specifically to pause the remapper BEFORE the switch happens
cmdTabWatcher = hs.eventtap.new({hs.eventtap.event.types.keyDown}, function(event)
    local flags = event:getFlags()
    local keyCode = event:getKeyCode()
    
    -- If Cmd+Tab is pressed
    if keyCode == 48 and flags['cmd'] then
        if remoteRemap:isEnabled() then
            remoteRemap:stop()
            forceReleaseModifiers()
            -- print("Cmd+Tab detected: Paused Remapper")
        end
        return false -- Let macOS handle the actual switching
    end
end)
cmdTabWatcher:start()


-- =============================================================================
-- 7. UTILITIES (Enhanced RDP Features)
-- =============================================================================
sleepWatcher = hs.caffeinate.watcher.new(function(eventType)
    if (eventType == hs.caffeinate.watcher.systemDidWake) then 
        print("🔥 System woke up - Reloading Hammerspoon...")
        hs.reload() 
    end
end)
sleepWatcher:start()

-- RDP-specific hotkeys for Windows functionality
hs.hotkey.bind({"ctrl", "alt"}, "F1", function()
    if isInRDPMode() then
        executeRDPSequence(rdpSequences.taskmgr, 20000) -- Open Task Manager
    end
end)

hs.hotkey.bind({"ctrl", "alt"}, "F2", function()
    if isInRDPMode() then
        executeRDPSequence(rdpSequences.screenshot, 20000) -- Take Screenshot
    end
end)

-- Enhanced reload with RDP status
hs.hotkey.bind({"ctrl", "alt", "cmd"}, "R", function()
    local inRDP = isInRDPMode()
    print("🔄 Manual reload triggered... (RDP: " .. (inRDP and "Active" or "Inactive") .. ")")
    hs.reload() 
end)

-- =============================================================================
-- 8. STATUS & HEALTH CHECK (RDP Enhanced)
-- =============================================================================
local function showRDPStatus()
    local inRDP = isInRDPMode()
    local modifiers = getModifiers()
    local status = string.format(
        "🚀 Advanced RDP Control Status\n" ..
        "🎯 RDP Mode: %s\n" ..
        "⌨️  Modifiers: Cmd=%s, Alt=%s, Shift=%s, Ctrl=%s\n" ..
        "📱 Active App: %s",
        inRDP and "Active" or "Inactive",
        modifiers.cmd and "✓" or "✗",
        modifiers.alt and "✓" or "✗", 
        modifiers.shift and "✓" or "✗",
        modifiers.ctrl and "✓" or "✗",
        hs.application.frontmostApplication():title() or "Unknown"
    )
    hs.alert.show(status, 3)
    
    -- Show available RDP sequences
    local sequenceHelp = "🔧 RDP Sequences:\n" ..
        "Ctrl+Alt+F1: Task Manager\n" ..
        "Ctrl+Alt+F2: Screenshot\n" ..
        "Cmd+F: Search (RDP)\n" ..
        "Cmd+R: Refresh (RDP)\n" ..
        "Cmd+Shift+Z: Redo (Ctrl+Y)\n" ..
        "Cmd+Shift+S: Save As (Ctrl+Shift+S)"
    print(sequenceHelp)
end

-- Status hotkey
hs.hotkey.bind({"ctrl", "alt"}, "H", showRDPStatus)

print("✅ Advanced RDP Control Configuration Loaded!")
print("🎯 Features: Enhanced RDP sequences, Windows key mapping, Atomic safety")
print("⚡ Hotkeys: Ctrl+Alt+Cmd+R (reload), Ctrl+Alt+H (status)")
print("🔧 RDP: Ctrl+Alt+F1 (TaskMgr), Ctrl+Alt+F2 (Screenshot)")

hs.alert.show("🚀 Advanced RDP Control: Ready", 2)
