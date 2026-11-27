---
summary: Instance streaming: what the client may not have yet, safe teleports, ModelStreamingMode; read before client code that touches workspace or any teleport
tags: streaming, streamingenabled, teleport, client, waitforchild
---
# Instance streaming

With `Workspace.StreamingEnabled` on (default for new places) the client only has the parts near its player.

- Client code must never assume a workspace part exists: `WaitForChild` (with a timeout) or listen for `ChildAdded`. Things outside workspace (ReplicatedStorage, the player's GUI) are always there.
- A server teleport into an area the client hasn't loaded freezes the character mid-air (the default `StreamOutBehavior` / `PauseOutsideLoadedArea`). Call `player:RequestStreamAroundAsync(position)` on the server first; it can take seconds.
- Models: `ModelStreamingMode = Atomic` streams the whole model in at once (no half-loaded doors), `Persistent` keeps it loaded for everyone, `PersistentPerPlayer` for chosen players (`model:AddPersistentPlayer(player)`).
- `StreamingMinRadius` is what is guaranteed loaded, `StreamingTargetRadius` what the engine tries for.
