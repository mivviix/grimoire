---
summary: Working in Roblox Studio through the robloxstudio MCP: checking scripts without playtests, importing .rbxmx, big data dumps, edit-mode GUI measurement
tags: studio, mcp, execute_luau, import, playtest, verify
---
# Studio through the robloxstudio MCP

## Never playtest from the agent
Don't start or stop `solo_playtest` / `multiplayer_playtest`: stopping one crashed Studio twice and lost all unsaved work. Verify in edit mode, then ask the user to press Play.

## Checking without running
- Syntax-check a script: `loadstring(src)` in `execute_luau` returns nil plus the error on a syntax error.
- `execute_luau` can't `require` place modules (Network capability error); `loadstring(module.Source)()` works.
- Read scripts back and check that the instances you made exist; say what is still unverified.

## Moving data in and out
- `import_rbxm` takes `.rbxmx` (XML) as well as `.rbxm`: `source: {path: "/abs/x.rbxmx"}`, `parent_path: "game.StarterGui"`. Give each import a distinct top-level name or destroy the old one first: re-importing leaves both side by side.
- Big results: run a tiny local HTTP sink (Python `http.server`, POST `/<name>` writes the body to a file, port 8799) and `HttpService:PostAsync("http://127.0.0.1:8799/<name>", HttpService:JSONEncode(t))` inside pcall. Works from edit mode with no HttpEnabled change. Stop the server afterwards.
- GUI measurement: a ScreenGui in StarterGui is laid out live in the edit viewport. Read `AbsolutePosition` / `AbsoluteSize` / `TextBounds` after `task.wait(0.1)`; edit mode has no top-bar GuiInset. Layout facts: [[gui-layout]].

## Things the agent can't do
- `Lighting.Technology` can't be set by scripts or the MCP: ask the user to set it once in Properties.
- Syncing or importing doesn't save the place: remind the user to Ctrl+S. Keep source files (scripts, JSON, .rbxmx) on disk so a crash can be rebuilt.
